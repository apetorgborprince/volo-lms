from pathlib import Path
import json
import os, json, csv, io, sqlite3
from flask import Blueprint, jsonify, request, session, current_app
from werkzeug.utils import secure_filename
from .db import get_db
from .security import login_required, role_required, hash_password

bp = Blueprint("api", __name__)

def ok(data=None, **kwargs):
    out = {"ok": True}
    if data is not None: out["data"] = data
    out.update(kwargs)
    return jsonify(out)

@bp.get("/me")
@login_required
def me():
    u = get_db().execute("SELECT id,username,role,full_name,class_name,subject_focus FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return ok(dict(u))

@bp.get("/stats")
@login_required
def stats():
    db = get_db()
    return ok(
        students=db.execute("SELECT COUNT(*) n FROM users WHERE role='student' AND active=1").fetchone()["n"],
        tutors=db.execute("SELECT COUNT(*) n FROM users WHERE role='tutor' AND active=1").fetchone()["n"],
        courses=db.execute("SELECT COUNT(*) n FROM courses WHERE active=1").fetchone()["n"],
        lessons=db.execute("SELECT COUNT(*) n FROM lessons").fetchone()["n"],
    )

@bp.get("/courses")
@login_required
def list_courses():
    rows = get_db().execute("""
      SELECT c.id,c.code,c.title,c.description,c.color,
             COUNT(l.id) lesson_count
      FROM courses c LEFT JOIN lessons l ON l.course_id=c.id
      WHERE c.active=1 GROUP BY c.id ORDER BY c.id
    """).fetchall()
    return ok([dict(r) for r in rows])

@bp.post("/courses")
@role_required("admin")
def create_course():
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    if not title: return jsonify(ok=False,error="Course title is required"),400
    db = get_db()
    cur = db.execute("INSERT INTO courses(code,title,description,color) VALUES(?,?,?,?)",
                     (data.get("code"), title, data.get("description",""), data.get("color","#3E6C8A")))
    db.commit()
    return ok(id=cur.lastrowid)

@bp.get("/courses/<int:course_id>/lessons")
@login_required
def course_lessons(course_id):
    rows = get_db().execute("""SELECT l.*, CASE WHEN lp.lesson_id IS NULL THEN 0 ELSE 1 END has_preparation
                             FROM lessons l LEFT JOIN lesson_preparations lp ON lp.lesson_id=l.id
                             WHERE l.course_id=? ORDER BY l.position,id""",(course_id,)).fetchall()
    return ok([dict(r) for r in rows])

@bp.get("/lessons/<int:lesson_id>/preparation")
@login_required
def lesson_preparation(lesson_id):
    row = get_db().execute("""SELECT l.id,l.title,l.material_type,c.title course_title,p.*
                            FROM lessons l JOIN courses c ON c.id=l.course_id
                            JOIN lesson_preparations p ON p.lesson_id=l.id WHERE l.id=?""", (lesson_id,)).fetchone()
    if not row:
        return jsonify(ok=False, error="A prepared learning-module lesson was not found"), 404
    data = dict(row)
    for key in ("learning_outcomes_json", "vocabulary_json", "lab_ids_json"):
        data[key.removesuffix("_json")] = json.loads(data.pop(key))
    return ok(data)

@bp.post("/courses/<int:course_id>/lessons")
@role_required("admin","tutor")
def create_lesson(course_id):
    title = (request.form.get("title") or "").strip()
    material_type = request.form.get("material_type","Reading")
    content = request.form.get("content","")
    external_url = request.form.get("external_url","")
    indicator_ids = [value for value in request.form.getlist("learning_indicator_id") if value.isdigit()]
    if not title: return jsonify(ok=False,error="Lesson title is required"),400
    file_path = None
    f = request.files.get("file")
    if f and f.filename:
        filename = secure_filename(f.filename)
        if not filename: return jsonify(ok=False,error="Invalid filename"),400
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        f.save(path)
        file_path = filename
    db = get_db()
    valid_ids = {row["id"] for row in db.execute(
        "SELECT id FROM learning_indicators WHERE id IN ({})".format(",".join("?" * len(indicator_ids)) or "NULL"), indicator_ids
    ).fetchall()}
    if not indicator_ids or len(valid_ids) != len(set(map(int, indicator_ids))):
        return jsonify(ok=False,error="Select at least one verified learning indicator"),400
    pos = db.execute("SELECT COALESCE(MAX(position),0)+1 p FROM lessons WHERE course_id=?",(course_id,)).fetchone()["p"]
    cur = db.execute("""INSERT INTO lessons(course_id,title,material_type,content,file_path,external_url,position)
                        VALUES(?,?,?,?,?,?,?)""",
                     (course_id,title,material_type,content,file_path,external_url,pos))
    for indicator_id in valid_ids:
        db.execute("INSERT INTO curriculum_lesson_links(lesson_id,learning_indicator_id) VALUES(?,?)",
                   (cur.lastrowid, indicator_id))
    db.commit()
    return ok(id=cur.lastrowid)

@bp.get("/students")
@role_required("admin","tutor")
def list_students():
    db = get_db()
    if session["role"]=="tutor":
        rows = db.execute("""
          SELECT u.id,u.username,u.full_name,u.class_name,
                 COUNT(DISTINCT e.course_id) courses
          FROM users u LEFT JOIN enrollments e ON e.student_id=u.id
          WHERE u.role='student' AND u.active=1
          GROUP BY u.id ORDER BY u.full_name
        """).fetchall()
    else:
        rows = db.execute("""
          SELECT u.id,u.username,u.full_name,u.class_name,
                 COUNT(DISTINCT e.course_id) courses
          FROM users u LEFT JOIN enrollments e ON e.student_id=u.id
          WHERE u.role='student' AND u.active=1
          GROUP BY u.id ORDER BY u.full_name
        """).fetchall()
    return ok([dict(r) for r in rows])


@bp.post("/teachers")
@role_required("admin")
def create_teacher():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    name = (data.get("full_name") or "").strip()
    if not username or not name or len(password) < 12:
        return jsonify(ok=False, error="Full name, username and a password of at least 12 characters are required."), 400
    db = get_db()
    try:
        cur = db.execute(
            """INSERT INTO users(username,password_hash,role,full_name,class_name,subject_focus)
               VALUES(?,?,?,?,?,?)""",
            (username, hash_password(password), "tutor", name, data.get("class_name"), data.get("subject_focus"))
        )
        db.commit()
        return ok(id=cur.lastrowid)
    except sqlite3.IntegrityError:
        return jsonify(ok=False, error="Username already exists."), 409

@bp.post("/students")
@role_required("admin")
def create_student():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    name = (data.get("full_name") or "").strip()
    if not username or not name or len(password) < 12:
        return jsonify(ok=False, error="Full name, username and a password of at least 12 characters are required."), 400
    db = get_db()
    try:
        cur = db.execute(
            """INSERT INTO users(username,password_hash,role,full_name,class_name)
               VALUES(?,?,?,?,?)""",
            (username, hash_password(password), "student", name, data.get("class_name"))
        )
        db.commit()
        return ok(id=cur.lastrowid)
    except sqlite3.IntegrityError:
        return jsonify(ok=False, error="Username already exists."), 409

@bp.get("/teachers")
@role_required("admin")
def list_teachers():
    rows = get_db().execute(
        """SELECT id,username,full_name,class_name,subject_focus,active,created_at
           FROM users WHERE role='tutor' ORDER BY full_name"""
    ).fetchall()
    return ok([dict(r) for r in rows])


@bp.post("/progress/<int:lesson_id>/complete")
@role_required("student")
def complete_lesson(lesson_id):
    db = get_db()
    db.execute("""INSERT INTO lesson_progress(student_id,lesson_id,completed,completed_at)
                  VALUES(?,?,1,CURRENT_TIMESTAMP)
                  ON CONFLICT(student_id,lesson_id) DO UPDATE SET completed=1,completed_at=CURRENT_TIMESTAMP""",
               (session["user_id"],lesson_id))
    db.execute("INSERT INTO activity_log(user_id,action,details) VALUES(?,?,?)",
               (session["user_id"],"lesson_completed",str(lesson_id)))
    db.commit()
    return ok()

@bp.get("/reports/overview")
@role_required("admin")
def report_overview():
    db = get_db()
    courses = db.execute("SELECT id,title FROM courses WHERE active=1 ORDER BY id").fetchall()
    result=[]
    for c in courses:
        total_students=db.execute("SELECT COUNT(*) n FROM users WHERE role='student' AND active=1").fetchone()["n"]
        completed=db.execute("""SELECT COUNT(*) n FROM lesson_progress lp
          JOIN lessons l ON l.id=lp.lesson_id
          WHERE l.course_id=? AND lp.completed=1""",(c["id"],)).fetchone()["n"]
        result.append({"course":c["title"],"students":total_students,"completed_lesson_records":completed})
    return ok(result)

@bp.post("/import/students")
@role_required("admin","tutor")
def import_students():
    f=request.files.get("file")
    if not f: return jsonify(ok=False,error="File is required"),400
    raw=f.read()
    rows=[]
    if f.filename.lower().endswith(".csv"):
        rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    elif f.filename.lower().endswith((".xlsx",".xlsm")):
        from openpyxl import load_workbook
        wb=load_workbook(io.BytesIO(raw),read_only=True,data_only=True)
        ws=wb.active
        values=list(ws.values)
        if values:
            headers=[str(x).strip() if x is not None else "" for x in values[0]]
            rows=[dict(zip(headers,r)) for r in values[1:]]
    else:
        return jsonify(ok=False,error="Use CSV or XLSX"),400

    db=get_db(); created=0; skipped=0
    for r in rows:
        name=str(r.get("Name") or r.get("name") or "").strip()
        username=str(r.get("Username") or r.get("username") or "").strip()
        password=str(r.get("Password") or r.get("password") or "").strip()
        cls=str(r.get("Class") or r.get("class") or "").strip()
        if not name or not username:
            skipped+=1; continue
        try:
            db.execute("""INSERT INTO users(username,password_hash,role,full_name,class_name)
                          VALUES(?,?,?,?,?)""",
                       (username,hash_password(password),"student",name,cls))
            created+=1
        except sqlite3.IntegrityError:
            skipped+=1
    db.commit()
    return ok(created=created,skipped=skipped)


@bp.get("/courses/<int:course_id>")
@login_required
def course_detail(course_id):
    db = get_db()
    course = db.execute("SELECT * FROM courses WHERE id=? AND active=1", (course_id,)).fetchone()
    if not course:
        return jsonify(ok=False,error="Course not found"),404
    lessons = db.execute("""
      SELECT l.*, COALESCE(lp.completed,0) completed,CASE WHEN prep.lesson_id IS NULL THEN 0 ELSE 1 END has_preparation
      FROM lessons l
      LEFT JOIN lesson_progress lp ON lp.lesson_id=l.id AND lp.student_id=?
      LEFT JOIN lesson_preparations prep ON prep.lesson_id=l.id
      WHERE l.course_id=? ORDER BY l.position,l.id
    """,(session["user_id"],course_id)).fetchall()
    quiz = db.execute("SELECT * FROM quizzes WHERE course_id=? ORDER BY id LIMIT 1",(course_id,)).fetchone()
    assignments = db.execute("""
      SELECT a.id,a.title,a.instructions,a.max_points,a.due_at,a.created_at,
             u.full_name creator, s.status submission_status,s.score submission_score
      FROM assignments a
      JOIN users u ON u.id=a.created_by
      LEFT JOIN assignment_submissions s
        ON s.assignment_id=a.id AND s.student_id=?
      WHERE a.course_id=? AND a.active=1
      ORDER BY CASE WHEN a.due_at IS NULL THEN 1 ELSE 0 END, a.due_at, a.id DESC
    """,(session["user_id"],course_id)).fetchall()
    return ok(course=dict(course),lessons=[dict(x) for x in lessons],quiz=dict(quiz) if quiz else None,
              assignments=[dict(x) for x in assignments])

@bp.post("/quizzes")
@role_required("admin","tutor")
def create_quiz():
    data=request.get_json(force=True)
    course_id=data.get("course_id")
    title=(data.get("title") or "Assessment").strip()
    if not course_id: return jsonify(ok=False,error="course_id is required"),400
    db=get_db()
    cur=db.execute("INSERT INTO quizzes(course_id,title,time_limit_minutes,attempts_allowed) VALUES(?,?,?,?)",
                   (course_id,title,data.get("time_limit_minutes"),data.get("attempts_allowed",1)))
    db.commit()
    return ok(id=cur.lastrowid)

@bp.post("/quizzes/<int:quiz_id>/questions")
@role_required("admin","tutor")
def add_question(quiz_id):
    data=request.get_json(force=True)
    required=["question_text","option_a","option_b","option_c","option_d","correct_option"]
    if any(data.get(k) in (None,"") for k in required):
        return jsonify(ok=False,error="All question fields are required"),400
    db=get_db()
    pos=db.execute("SELECT COALESCE(MAX(position),0)+1 p FROM questions WHERE quiz_id=?",(quiz_id,)).fetchone()["p"]
    cur=db.execute("""INSERT INTO questions(quiz_id,question_text,option_a,option_b,option_c,option_d,correct_option,points,position)
                      VALUES(?,?,?,?,?,?,?,?,?)""",
                   (quiz_id,data["question_text"],data["option_a"],data["option_b"],data["option_c"],data["option_d"],
                    int(data["correct_option"]),int(data.get("points",1)),pos))
    db.commit()
    return ok(id=cur.lastrowid)

@bp.get("/quizzes/<int:quiz_id>")
@role_required("student","tutor","admin")
def get_quiz(quiz_id):
    db=get_db()
    q=db.execute("SELECT * FROM quizzes WHERE id=?",(quiz_id,)).fetchone()
    if not q:return jsonify(ok=False,error="Quiz not found"),404
    questions=db.execute("""SELECT id,question_text,option_a,option_b,option_c,option_d,points,position
                            FROM questions WHERE quiz_id=? ORDER BY position,id""",(quiz_id,)).fetchall()
    return ok(quiz=dict(q),questions=[dict(x) for x in questions])

@bp.post("/quizzes/<int:quiz_id>/submit")
@role_required("student")
def submit_quiz(quiz_id):
    payload=request.get_json(force=True)
    answers=payload.get("answers",{})
    db=get_db()
    quiz=db.execute("SELECT * FROM quizzes WHERE id=?",(quiz_id,)).fetchone()
    if not quiz:return jsonify(ok=False,error="Quiz not found"),404
    previous=db.execute("SELECT COUNT(*) n FROM quiz_attempts WHERE quiz_id=? AND student_id=?",(quiz_id,session["user_id"])).fetchone()["n"]
    if previous >= quiz["attempts_allowed"]:
        return jsonify(ok=False,error="Attempt limit reached"),409
    questions=db.execute("SELECT * FROM questions WHERE quiz_id=? ORDER BY position,id",(quiz_id,)).fetchall()
    total=sum(q["points"] for q in questions)
    score=0
    for q in questions:
        try: selected=int(answers.get(str(q["id"]))) if answers.get(str(q["id"])) is not None else None
        except: selected=None
        if selected==q["correct_option"]: score += q["points"]
    cur=db.execute("""INSERT INTO quiz_attempts(quiz_id,student_id,score,total_points,submitted_at)
                      VALUES(?,?,?,?,CURRENT_TIMESTAMP)""",
                   (quiz_id,session["user_id"],score,total))
    attempt_id=cur.lastrowid
    for q in questions:
        raw=answers.get(str(q["id"]))
        try: selected=int(raw) if raw is not None else None
        except: selected=None
        awarded=q["points"] if selected==q["correct_option"] else 0
        db.execute("""INSERT INTO quiz_answers(attempt_id,question_id,selected_option,awarded_points)
                      VALUES(?,?,?,?)""",(attempt_id,q["id"],selected,awarded))
    db.execute("INSERT INTO activity_log(user_id,action,details) VALUES(?,?,?)",
               (session["user_id"],"quiz_submitted",f"quiz={quiz_id};score={score}/{total}"))
    db.commit()
    return ok(attempt_id=attempt_id,score=score,total=total,percentage=round((score/total*100) if total else 0,1))

@bp.get("/assignments/<int:assignment_id>")
@role_required("student","tutor","admin")
def get_assignment(assignment_id):
    db=get_db()
    a=db.execute("""SELECT a.*,c.title course_title,u.full_name creator
                   FROM assignments a JOIN courses c ON c.id=a.course_id
                   JOIN users u ON u.id=a.created_by WHERE a.id=? AND a.active=1""",(assignment_id,)).fetchone()
    if not a:return jsonify(ok=False,error="Assignment not found"),404
    submission=None
    if session["role"]=="student":
        submission=db.execute("SELECT * FROM assignment_submissions WHERE assignment_id=? AND student_id=?",(assignment_id,session["user_id"])).fetchone()
    return ok(assignment=dict(a),submission=dict(submission) if submission else None)

@bp.post("/courses/<int:course_id>/assignments")
@role_required("tutor","admin","admin")
def create_assignment(course_id):
    data=request.get_json(force=True)
    title=(data.get("title") or "").strip()
    instructions=(data.get("instructions") or "").strip()
    if not title or not instructions:return jsonify(ok=False,error="Title and instructions are required"),400
    db=get_db()
    if not db.execute("SELECT 1 FROM courses WHERE id=? AND active=1",(course_id,)).fetchone():
        return jsonify(ok=False,error="Course not found"),404
    try:max_points=float(data.get("max_points",100))
    except (TypeError,ValueError):return jsonify(ok=False,error="max_points must be numeric"),400
    if max_points<=0:return jsonify(ok=False,error="max_points must be greater than zero"),400
    cur=db.execute("""INSERT INTO assignments(course_id,created_by,title,instructions,max_points,due_at)
                      VALUES(?,?,?,?,?,?)""",(course_id,session["user_id"],title,instructions,max_points,data.get("due_at")))
    db.execute("INSERT INTO activity_log(user_id,action,details) VALUES(?,?,?)",(session["user_id"],"assignment_created",f"assignment={cur.lastrowid};course={course_id}"))
    db.commit(); return ok(id=cur.lastrowid)

@bp.post("/assignments/<int:assignment_id>/submit")
@role_required("student")
def submit_assignment(assignment_id):
    data=request.get_json(force=True)
    answer=(data.get("answer_text") or "").strip()
    if not answer and not data.get("file_path"):
        return jsonify(ok=False,error="Provide an answer or file reference"),400
    db=get_db()
    a=db.execute("SELECT * FROM assignments WHERE id=? AND active=1",(assignment_id,)).fetchone()
    if not a:return jsonify(ok=False,error="Assignment not found"),404
    enrolled=db.execute("SELECT 1 FROM enrollments WHERE student_id=? AND course_id=?",(session["user_id"],a["course_id"])).fetchone()
    if not enrolled:return jsonify(ok=False,error="You are not enrolled in this course"),403
    existing=db.execute("SELECT id,status FROM assignment_submissions WHERE assignment_id=? AND student_id=?",(assignment_id,session["user_id"])).fetchone()
    if existing and existing["status"]=="graded":return jsonify(ok=False,error="A graded submission cannot be overwritten"),409
    if existing:
        db.execute("""UPDATE assignment_submissions SET answer_text=?,file_path=?,submitted_at=CURRENT_TIMESTAMP,status='submitted'
                      WHERE id=?""",(answer,data.get("file_path"),existing["id"]))
        sid=existing["id"]
    else:
        cur=db.execute("""INSERT INTO assignment_submissions(assignment_id,student_id,answer_text,file_path)
                          VALUES(?,?,?,?)""",(assignment_id,session["user_id"],answer,data.get("file_path")))
        sid=cur.lastrowid
    db.execute("INSERT INTO activity_log(user_id,action,details) VALUES(?,?,?)",(session["user_id"],"assignment_submitted",f"assignment={assignment_id};submission={sid}"))
    db.commit(); return ok(submission_id=sid)

@bp.get("/assignments/<int:assignment_id>/submissions")
@role_required("tutor","admin","admin")
def assignment_submissions(assignment_id):
    db=get_db()
    a=db.execute("SELECT * FROM assignments WHERE id=? AND active=1",(assignment_id,)).fetchone()
    if not a:return jsonify(ok=False,error="Assignment not found"),404
    rows=db.execute("""SELECT s.*,u.full_name,u.username,u.class_name
                      FROM assignment_submissions s JOIN users u ON u.id=s.student_id
                      WHERE s.assignment_id=? ORDER BY s.submitted_at DESC""",(assignment_id,)).fetchall()
    return ok(assignment=dict(a),submissions=[dict(r) for r in rows])

@bp.post("/submissions/<int:submission_id>/grade")
@role_required("tutor","admin","admin")
def grade_submission(submission_id):
    data=request.get_json(force=True)
    db=get_db()
    sub=db.execute("""SELECT s.*,a.max_points,a.title assignment_title FROM assignment_submissions s
                     JOIN assignments a ON a.id=s.assignment_id WHERE s.id=?""",(submission_id,)).fetchone()
    if not sub:return jsonify(ok=False,error="Submission not found"),404
    try:score=float(data.get("score"))
    except (TypeError,ValueError):return jsonify(ok=False,error="score must be numeric"),400
    if score<0 or score>sub["max_points"]:return jsonify(ok=False,error=f"score must be between 0 and {sub['max_points']}"),400
    feedback=(data.get("feedback") or "").strip()
    db.execute("""UPDATE assignment_submissions SET score=?,feedback=?,status='graded',graded_by=?,graded_at=CURRENT_TIMESTAMP WHERE id=?""",(score,feedback,session["user_id"],submission_id))
    db.execute("INSERT INTO notifications(user_id,title,body) VALUES(?,?,?)",(sub["student_id"],"Assignment graded",f"Your submission for {sub['assignment_title']} has been graded: {score}/{sub['max_points']}."))
    db.execute("INSERT INTO activity_log(user_id,action,details) VALUES(?,?,?)",(session["user_id"],"assignment_graded",f"submission={submission_id};score={score}"))
    db.commit();return ok(submission_id=submission_id,score=score,feedback=feedback)

@bp.get("/v5/assessment-summary")
@login_required
def assessment_summary():
    db=get_db();uid,role=session["user_id"],session["role"]
    if role=="student":
        quiz=db.execute("SELECT COUNT(*) n FROM quiz_attempts WHERE student_id=?",(uid,)).fetchone()["n"]
        graded=db.execute("SELECT COUNT(*) n FROM assignment_submissions WHERE student_id=? AND status='graded'",(uid,)).fetchone()["n"]
        pending=db.execute("SELECT COUNT(*) n FROM assignment_submissions WHERE student_id=? AND status='submitted'",(uid,)).fetchone()["n"]
        avg=db.execute("""SELECT AVG(CASE WHEN max_points>0 THEN score*100.0/max_points END) v
                         FROM assignment_submissions s JOIN assignments a ON a.id=s.assignment_id
                         WHERE s.student_id=? AND s.status='graded'""",(uid,)).fetchone()["v"]
        return ok(data={"quiz_attempts":quiz,"assignments_graded":graded,"assignments_pending":pending,"assignment_average":round(avg or 0,1)})
    assignments=db.execute("SELECT COUNT(*) n FROM assignments WHERE active=1").fetchone()["n"]
    pending=db.execute("SELECT COUNT(*) n FROM assignment_submissions WHERE status='submitted'").fetchone()["n"]
    graded=db.execute("SELECT COUNT(*) n FROM assignment_submissions WHERE status='graded'").fetchone()["n"]
    return ok(data={"assignments":assignments,"submissions_pending":pending,"submissions_graded":graded})

@bp.get("/students/<int:student_id>/performance")
@role_required("admin","tutor")
def student_performance(student_id):
    db=get_db()
    student=db.execute("SELECT id,username,full_name,class_name FROM users WHERE id=? AND role='student'",(student_id,)).fetchone()
    if not student:return jsonify(ok=False,error="Student not found"),404
    rows=db.execute("""
      SELECT c.id course_id,c.title,
        COUNT(DISTINCT l.id) lesson_count,
        COUNT(DISTINCT CASE WHEN lp.completed=1 THEN lp.lesson_id END) completed_lessons,
        MAX(qa.score) latest_score, MAX(qa.total_points) latest_total
      FROM courses c
      LEFT JOIN lessons l ON l.course_id=c.id
      LEFT JOIN lesson_progress lp ON lp.lesson_id=l.id AND lp.student_id=?
      LEFT JOIN quizzes q ON q.course_id=c.id
      LEFT JOIN quiz_attempts qa ON qa.quiz_id=q.id AND qa.student_id=?
      WHERE c.active=1 GROUP BY c.id
    """,(student_id,student_id)).fetchall()
    return ok(student=dict(student),courses=[dict(r) for r in rows])

@bp.post("/tutors/<int:tutor_id>/assign-student")
@role_required("admin")
def assign_student(tutor_id):
    data=request.get_json(force=True); student_id=data.get("student_id")
    db=get_db()
    tutor=db.execute("SELECT id FROM users WHERE id=? AND role='tutor'",(tutor_id,)).fetchone()
    student=db.execute("SELECT id FROM users WHERE id=? AND role='student'",(student_id,)).fetchone()
    if not tutor or not student:return jsonify(ok=False,error="Tutor or student not found"),404
    db.execute("INSERT OR IGNORE INTO tutor_assignments(tutor_id,student_id) VALUES(?,?)",(tutor_id,student_id))
    db.execute("UPDATE enrollments SET tutor_id=? WHERE student_id=?",(tutor_id,student_id))
    db.execute("INSERT INTO activity_log(user_id,action,details) VALUES(?,?,?)",
               (session["user_id"],"tutor_assignment",f"tutor={tutor_id};student={student_id}"))
    db.commit()
    return ok()

@bp.get("/notifications")
@login_required
def notifications():
    rows=get_db().execute("""SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 30""",
                          (session["user_id"],)).fetchall()
    return ok([dict(r) for r in rows])

@bp.post("/notifications/<int:notification_id>/read")
@login_required
def mark_notification(notification_id):
    db=get_db()
    db.execute("UPDATE notifications SET read_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
               (notification_id,session["user_id"]))
    db.commit()
    return ok()

@bp.get("/announcements")
@login_required
def announcements():
    role=session.get("role")
    rows=get_db().execute("""SELECT a.*,u.full_name author FROM announcements a
                             LEFT JOIN users u ON u.id=a.author_id
                             WHERE a.audience_role IS NULL OR a.audience_role=?
                             ORDER BY a.published_at DESC LIMIT 30""",(role,)).fetchall()
    return ok([dict(r) for r in rows])

@bp.post("/announcements")
@role_required("admin","tutor")
def create_announcement():
    data=request.get_json(force=True)
    title=(data.get("title") or "").strip(); body=(data.get("body") or "").strip()
    if not title or not body:return jsonify(ok=False,error="Title and body are required"),400
    db=get_db()
    cur=db.execute("""INSERT INTO announcements(author_id,title,body,audience_role,course_id)
                      VALUES(?,?,?,?,?)""",(session["user_id"],title,body,data.get("audience_role"),data.get("course_id")))
    # Create notifications for matching active users.
    sql="SELECT id FROM users WHERE active=1"
    params=[]
    if data.get("audience_role"):
        sql+=" AND role=?"; params.append(data["audience_role"])
    users=db.execute(sql,params).fetchall()
    for u in users:
        db.execute("INSERT INTO notifications(user_id,title,body) VALUES(?,?,?)",(u["id"],title,body))
    db.commit()
    return ok(id=cur.lastrowid)


@bp.get("/practicals")
@login_required
def practical_registry():
    path = Path(current_app.root_path) / "data" / "practicals.json"
    practicals = json.loads(path.read_text())
    for practical in practicals:
        practical.setdefault("alignment", {"classification": "Extension / enrichment", "note": "Curriculum mapping has not yet been verified from the supplied source PDF."})
    return ok(practicals=practicals)

@bp.post("/practical-designs")
@role_required("admin", "tutor")
def create_practical_design():
    data = request.get_json(force=True)
    required = ("learning_indicator_id", "title", "objective", "apparatus", "safety_instructions", "procedure", "assessment_prompt")
    if any(not str(data.get(key) or "").strip() for key in required):
        return jsonify(ok=False, error="Complete every practical design field"), 400
    db = get_db()
    indicator = db.execute("SELECT id FROM learning_indicators WHERE id=?", (data["learning_indicator_id"],)).fetchone()
    if not indicator:
        return jsonify(ok=False, error="Select a verified learning indicator"), 400
    cur = db.execute("""INSERT INTO practical_designs(created_by,learning_indicator_id,title,objective,apparatus,safety_instructions,procedure,assessment_prompt)
                      VALUES(?,?,?,?,?,?,?,?)""", (session["user_id"], data["learning_indicator_id"], data["title"].strip(), data["objective"].strip(), data["apparatus"].strip(), data["safety_instructions"].strip(), data["procedure"].strip(), data["assessment_prompt"].strip()))
    db.commit()
    return ok(id=cur.lastrowid)

@bp.get("/curriculum")
@login_required
def curriculum_records():
    """Read-only official curriculum explorer; no teacher write path exists."""
    db = get_db()
    year = (request.args.get("year") or "").strip()
    strand = (request.args.get("strand") or "").strip()
    query = (request.args.get("q") or "").strip()
    sql = """
        SELECT y.code year_code,y.title year_title,s.code strand_code,s.title strand_title,
               ss.code substrand_code,ss.title substrand_title,
               cs.code standard_code,cs.description standard_description,cs.source_page standard_page,
               lo.code outcome_code,lo.description outcome_description,lo.source_page outcome_page,
               li.id indicator_id,li.code indicator_code,li.description indicator_description,
               li.assessment_code,li.source_page,
               (SELECT COUNT(*) FROM curriculum_lesson_links cl WHERE cl.learning_indicator_id=li.id) lesson_count
        FROM learning_indicators li
        JOIN content_standards cs ON cs.id=li.content_standard_id
        LEFT JOIN learning_outcomes lo ON lo.id=li.learning_outcome_id
        JOIN curriculum_substrands ss ON ss.id=cs.substrand_id
        JOIN curriculum_years y ON y.id=ss.curriculum_year_id
        JOIN curriculum_strands s ON s.id=ss.strand_id
        WHERE 1=1
    """
    params = []
    if year:
        sql += " AND y.code=?"; params.append(year)
    if strand:
        sql += " AND s.code=?"; params.append(strand)
    if query:
        sql += " AND (li.code LIKE ? OR li.description LIKE ? OR cs.code LIKE ? OR cs.description LIKE ? OR lo.code LIKE ? OR lo.description LIKE ?)"
        like = f"%{query}%"; params.extend([like] * 6)
    sql += " ORDER BY y.position,s.position,ss.position,cs.code,li.code"
    return ok([dict(row) for row in db.execute(sql, params).fetchall()])

@bp.get("/curriculum/facets")
@login_required
def curriculum_facets():
    db = get_db()
    years = [dict(row) for row in db.execute("SELECT code,title FROM curriculum_years ORDER BY position").fetchall()]
    strands = [dict(row) for row in db.execute("SELECT code,title FROM curriculum_strands ORDER BY position").fetchall()]
    counts = db.execute("""SELECT COUNT(DISTINCT cs.id) standards,COUNT(DISTINCT lo.id) outcomes,
                                 COUNT(DISTINCT li.id) indicators
                          FROM learning_indicators li JOIN content_standards cs ON cs.id=li.content_standard_id
                          LEFT JOIN learning_outcomes lo ON lo.id=li.learning_outcome_id""").fetchone()
    return ok(years=years, strands=strands, counts=dict(counts))


# V5 Core Platform
@bp.get("/v5/overview")
@login_required
def v5_overview():
    db = get_db()
    uid, role = session["user_id"], session["role"]
    unread = db.execute("SELECT COUNT(*) n FROM notifications WHERE user_id=? AND read_at IS NULL", (uid,)).fetchone()["n"]
    if role == "admin":
        data = {
            "role": role,
            "students": db.execute("SELECT COUNT(*) n FROM users WHERE role='student' AND active=1").fetchone()["n"],
            "teachers": db.execute("SELECT COUNT(*) n FROM users WHERE role='tutor' AND active=1").fetchone()["n"],
            "courses": db.execute("SELECT COUNT(*) n FROM courses WHERE active=1").fetchone()["n"],
            "practicals": 30,
            "notifications": unread
        }
    elif role == "tutor":
        data = {"role": role,
                "students": db.execute("SELECT COUNT(*) n FROM users WHERE role='student' AND active=1").fetchone()["n"],
                "courses": db.execute("SELECT COUNT(*) n FROM courses WHERE active=1").fetchone()["n"],
                "assignments": db.execute("SELECT COUNT(*) n FROM assignments WHERE active=1").fetchone()["n"],
                "submissions_pending": db.execute("SELECT COUNT(*) n FROM assignment_submissions WHERE status='submitted'").fetchone()["n"],
                "notifications": unread}
    else:
        data = {"role": role,
                "courses": db.execute("SELECT COUNT(*) n FROM enrollments WHERE student_id=?", (uid,)).fetchone()["n"],
                "lessons_completed": db.execute("SELECT COUNT(*) n FROM lesson_progress WHERE student_id=? AND completed=1", (uid,)).fetchone()["n"],
                "assessments": db.execute("SELECT COUNT(*) n FROM quiz_attempts WHERE student_id=?", (uid,)).fetchone()["n"] +
                              db.execute("SELECT COUNT(*) n FROM assignment_submissions WHERE student_id=?", (uid,)).fetchone()["n"],
                "practicals": 0, "notifications": unread}
    return ok(data=data)

@bp.get("/v5/profile")
@login_required
def v5_profile():
    db = get_db()
    u = db.execute("""SELECT u.id,u.username,u.role,u.full_name,u.class_name,u.subject_focus,
                             p.phone,p.email,p.avatar_url,p.bio
                      FROM users u LEFT JOIN user_profiles p ON p.user_id=u.id
                      WHERE u.id=?""", (session["user_id"],)).fetchone()
    return ok(data=dict(u))
