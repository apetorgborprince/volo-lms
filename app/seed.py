import json
from pathlib import Path
from .db import get_db
from .security import hash_password

def seed_database():
    db=get_db()
    if db.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]==0:
        users=[
          ("admin","admin123","admin","Mrs. Adjoa Boateng",None,"System Administrator"),
          ("parent.a","parent123","parent","Ama Owusu",None,"Parent/Guardian"),
          ("tutor.k","tutor123","tutor","Mr. Kojo Ansah",None,"Integrated Science"),
          ("kwame.m","student123","student","Kwame Mensah","Form 2A",None),
          ("abena.o","student123","student","Abena Owusu","Form 2A",None),
          ("kofi.a","student123","student","Kofi Asante","Form 2B",None),
        ]
        for u in users:
            db.execute("""INSERT INTO users(username,password_hash,role,full_name,class_name,subject_focus)
                          VALUES(?,?,?,?,?,?)""",
                       (u[0],hash_password(u[1]),u[2],u[3],u[4],u[5]))
    if db.execute("SELECT COUNT(*) n FROM courses").fetchone()["n"]==0:
        courses=[
          ("M0","Module 0 — Diagnostic & Bridging","Check the JHS foundation before we begin.","#3E6C8A"),
          ("M1","Module 1 — Active Conceptual Learning","Diffusion and osmosis explained in your own words.","#52785D"),
          ("M2","Module 2 — Practical & Applied Skills","Low-cost practicals using local materials.","#A9752E"),
          ("M3","Module 3 — Exam-Ready Reasoning","WASSCE-style application, analysis and evaluation.","#8A5A54"),
        ]
        for c in courses:
            db.execute("INSERT INTO courses(code,title,description,color) VALUES(?,?,?,?)",c)
        lesson_sets=[
          [("Measurement & Units check","Reading"),("Cells & Living Organisms check","Reading"),("Forces & Motion check","Reading")],
          [("Diffusion: particles on the move","Reading"),("Osmosis explainer video","Video"),("Class assessment (Google Form)","GoogleForm")],
          [("Potato-strip osmosis practical guide","PDF"),("Simple circuit build","Reading")],
          [("Applying concepts to new scenarios","Reading"),("Analysing experimental results","Reading")],
        ]
        for ci, lessons in enumerate(lesson_sets):
            cid=db.execute("SELECT id FROM courses WHERE code=?",(f"M{ci}",)).fetchone()["id"]
            for pos,(title,typ) in enumerate(lessons,1):
                db.execute("""INSERT INTO lessons(course_id,title,material_type,position)
                              VALUES(?,?,?,?)""",(cid,title,typ,pos))
    parent = db.execute("SELECT id FROM users WHERE username='parent.a'").fetchone()
    child = db.execute("SELECT id FROM users WHERE username='abena.o'").fetchone()
    if parent and child:
        db.execute("INSERT OR IGNORE INTO parent_links(parent_id,student_id,relationship) VALUES(?,?,?)",
                   (parent["id"], child["id"], "Mother"))
    seed_curriculum(db)
    seed_learning_modules(db)
    db.commit()


def seed_curriculum(db):
    """Seed only records transcribed from the supplied NaCCA curriculum PDF.

    The schema deliberately permits gradual, reviewed expansion; unverified topics
    are never represented as official curriculum metadata.
    """
    db.execute("""INSERT OR IGNORE INTO curriculum_versions(name,source_title,published_on)
                  VALUES(?,?,?)""", (
        "General Science SHS 1–3 (September 2023)",
        "General Science Curriculum for Secondary Education (SHS 1–3), NaCCA/GES, September 2023",
        "2023-09-01",
    ))
    version = db.execute("SELECT id FROM curriculum_versions WHERE name=?", (
        "General Science SHS 1–3 (September 2023)",
    )).fetchone()["id"]
    db.execute("INSERT OR IGNORE INTO curriculum_years(curriculum_version_id,code,title,position) VALUES(?,?,?,?)",
               (version, "SHS 1", "SHS 1 General Science", 1))
    year = db.execute("SELECT id FROM curriculum_years WHERE curriculum_version_id=? AND code=?", (version, "SHS 1")).fetchone()["id"]
    db.execute("INSERT OR IGNORE INTO curriculum_strands(curriculum_version_id,code,title,position) VALUES(?,?,?,?)",
               (version, "1", "Exploring Materials", 1))
    strand = db.execute("SELECT id FROM curriculum_strands WHERE curriculum_version_id=? AND code=?", (version, "1")).fetchone()["id"]
    db.execute("""INSERT OR IGNORE INTO curriculum_substrands(curriculum_year_id,strand_id,code,title,position)
                  VALUES(?,?,?,?,?)""", (year, strand, "1", "Science and Materials in Nature", 1))
    substrand = db.execute("""SELECT id FROM curriculum_substrands
                              WHERE curriculum_year_id=? AND strand_id=? AND code=?""", (year, strand, "1")).fetchone()["id"]

    standards = [
        ("1.1.1.CS.1", "Demonstrate knowledge and understanding of the characteristics of science and show how they are applied in everyday life.", 28),
        ("1.1.1.CS.2", "Know, understand, and identify the roles of solids in life.", 30),
    ]
    for code, description, page in standards:
        db.execute("""INSERT OR IGNORE INTO content_standards(substrand_id,code,description,source_page)
                      VALUES(?,?,?,?)""", (substrand, code, description, page))
    db.execute("""INSERT OR IGNORE INTO learning_outcomes(substrand_id,code,description,source_page)
                  VALUES(?,?,?,?)""", (substrand, "1.1.1.LO.1", "Evaluate the characteristics of science.", 26))
    db.execute("""INSERT OR IGNORE INTO learning_outcomes(substrand_id,code,description,source_page)
                  VALUES(?,?,?,?)""", (substrand, "1.1.1.LO.2", "Explain the functions of solids in life.", 26))
    outcomes = {row["code"]: row["id"] for row in db.execute(
        "SELECT id,code FROM learning_outcomes WHERE substrand_id=?", (substrand,)
    ).fetchall()}
    standard_ids = {row["code"]: row["id"] for row in db.execute(
        "SELECT id,code FROM content_standards WHERE substrand_id=?", (substrand,)
    ).fetchall()}
    indicators = [
        ("1.1.1.CS.1", "1.1.1.LO.1", "1.1.1.LI.1", "Explain the characteristics of science in nature.", "1.1.1.AS.1", 28),
        ("1.1.1.CS.1", "1.1.1.LO.1", "1.1.1.LI.2", "Design projects using the characteristics of science.", "1.1.1.AS.2", 28),
        ("1.1.1.CS.1", "1.1.1.LO.1", "1.1.1.LI.3", "Apply the characteristics of science where appropriate.", "1.1.1.AS.3", 28),
        ("1.1.1.CS.2", "1.1.1.LO.2", "1.1.1.LI.1", "Classify different solids and their uses.", "1.1.1.AS.1", 30),
        ("1.1.1.CS.2", "1.1.1.LO.2", "1.1.1.LI.2", "Apply the properties of solids to everyday use.", "1.1.1.AS.2", 30),
        ("1.1.1.CS.2", "1.1.1.LO.2", "1.1.1.LI.3", "Discuss the relationship between binary compounds, the composition of binary compounds and the names of compounds.", "1.1.1.AS.3", 32),
    ]
    for standard_code, outcome_code, code, description, assessment_code, page in indicators:
        db.execute("""INSERT OR IGNORE INTO learning_indicators(
                       content_standard_id,learning_outcome_id,code,description,assessment_code,source_page)
                      VALUES(?,?,?,?,?,?)""", (standard_ids[standard_code], outcomes[outcome_code], code, description, assessment_code, page))


def seed_learning_modules(db):
    modules_path = Path(__file__).resolve().parent / "data" / "module_lessons.json"
    for module in json.loads(modules_path.read_text(encoding="utf-8")):
        db.execute("""INSERT OR IGNORE INTO courses(code,title,description,color)
                      VALUES(?,?,?,?)""", (module["course_code"], module["course_title"], module["course_description"], module["color"]))
        course_id = db.execute("SELECT id FROM courses WHERE code=?", (module["course_code"],)).fetchone()["id"]
        lesson = db.execute("SELECT id FROM lessons WHERE course_id=? AND title=?", (course_id, module["title"])).fetchone()
        if not lesson:
            lesson_id = db.execute("""INSERT INTO lessons(course_id,title,material_type,content,position)
                                    VALUES(?,?,?,?,?)""", (course_id, module["title"], "Guided learning module", module["overview"], 1)).lastrowid
        else:
            lesson_id = lesson["id"]
        db.execute("""INSERT OR IGNORE INTO lesson_preparations(
                       lesson_id,source_file,source_section,source_page,alignment_status,learning_outcomes_json,prior_knowledge,vocabulary_json,engage,investigate,explain,elaborate,practical_work,safety_notes,assessment,extension,lab_ids_json)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            lesson_id, module["source_file"], module["source_section"], module["source_page"], module["alignment_status"],
            json.dumps(module["learning_outcomes"]), module["prior_knowledge"], json.dumps(module["vocabulary"]),
            module["engage"], module["investigate"], module["explain"], module["elaborate"], module["practical_work"],
            module["safety_notes"], module["assessment"], module["extension"], json.dumps(module["lab_ids"]),
        ))
        for indicator_code in module.get("verified_indicator_codes", []):
            indicators = db.execute("SELECT id FROM learning_indicators WHERE code=?", (indicator_code,)).fetchall()
            for indicator in indicators:
                db.execute("INSERT OR IGNORE INTO curriculum_lesson_links(lesson_id,learning_indicator_id) VALUES(?,?)", (lesson_id, indicator["id"]))
