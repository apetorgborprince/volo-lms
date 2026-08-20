from flask import Blueprint, render_template, session, redirect, url_for
from .security import login_required, role_required

bp = Blueprint("web", __name__)

@bp.route("/")
def index(): return redirect(url_for("auth.login"))

@bp.route("/dashboard")
@login_required
def dashboard(): return render_template("dashboard.html")

@bp.route("/courses")
@login_required
def courses(): return render_template("courses.html")

@bp.route("/curriculum")
@login_required
def curriculum(): return render_template("curriculum.html")

@bp.route("/course/<int:course_id>")
@login_required
def course_detail(course_id): return render_template("course_detail.html", course_id=course_id)

@bp.route("/lesson/<int:lesson_id>")
@login_required
def lesson_detail(lesson_id): return render_template("lesson_detail.html", lesson_id=lesson_id)

@bp.route("/course/<int:course_id>/quiz/<int:quiz_id>")
@role_required("student")
def quiz(course_id, quiz_id): return render_template("quiz.html", course_id=course_id, quiz_id=quiz_id)

@bp.route("/course/<int:course_id>/assignment/<int:assignment_id>")
@login_required
def assignment(course_id, assignment_id): return render_template("assignment.html", course_id=course_id, assignment_id=assignment_id)

@bp.route("/practical-studio")
@login_required
def practical_studio(): return render_template("practical_studio.html")

@bp.route("/students")
@role_required("admin","tutor","super_admin")
def students(): return render_template("students.html")

@bp.route("/manage-courses")
@role_required("admin","tutor","super_admin")
def manage_courses(): return render_template("manage_courses.html")

@bp.route("/studio")
@role_required("student")
def studio(): return render_template("studio.html")

@bp.route("/ai")
@role_required("student","tutor","admin","super_admin")
def ai(): return render_template("ai.html")
