import json
import os
from pathlib import Path
from .db import get_db
from .security import hash_password

def ensure_admin():
    """Create the single initial Administrator from environment variables.

    No administrator username/password is embedded in source code.
    ADMIN_PASSWORD is mandatory on a fresh production database.
    """
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
    if existing:
        return

    username = (os.getenv("ADMIN_USERNAME") or "").strip()
    password = os.getenv("ADMIN_PASSWORD") or ""
    full_name = (os.getenv("ADMIN_FULL_NAME") or "System Administrator").strip()

    if not username or not password:
        raise RuntimeError(
            "No Administrator exists. Set ADMIN_USERNAME and ADMIN_PASSWORD before starting Volo LMS."
        )
    if len(password) < 12:
        raise RuntimeError("ADMIN_PASSWORD must contain at least 12 characters.")
    if not username or len(username) < 4:
        raise RuntimeError("ADMIN_USERNAME must contain at least 4 characters.")

    db.execute(
        """INSERT INTO users(username,password_hash,role,full_name)
           VALUES(?,?,?,?)""",
        (username, hash_password(password), "admin", full_name)
    )
    db.commit()

def seed_curriculum(db):
    """Seed verified curriculum metadata only; never seed demo accounts."""
    db.execute("""INSERT OR IGNORE INTO curriculum_versions(name,source_title,published_on)
                  VALUES(?,?,?)""", (
        "General Science SHS 1–3 (September 2023)",
        "General Science Curriculum for Secondary Education (SHS 1–3), NaCCA/GES, September 2023",
        "2023-09-01",
    ))
    version = db.execute(
        "SELECT id FROM curriculum_versions WHERE name=?",
        ("General Science SHS 1–3 (September 2023)",)
    ).fetchone()["id"]

    db.execute("""INSERT OR IGNORE INTO curriculum_years(curriculum_version_id,code,title,position)
                  VALUES(?,?,?,?)""", (version, "SHS 1", "SHS 1 General Science", 1))
    year = db.execute(
        "SELECT id FROM curriculum_years WHERE curriculum_version_id=? AND code=?",
        (version, "SHS 1")
    ).fetchone()["id"]

    db.execute("""INSERT OR IGNORE INTO curriculum_strands(curriculum_version_id,code,title,position)
                  VALUES(?,?,?,?)""", (version, "1", "Exploring Materials", 1))
    strand = db.execute(
        "SELECT id FROM curriculum_strands WHERE curriculum_version_id=? AND code=?",
        (version, "1")
    ).fetchone()["id"]

    db.execute("""INSERT OR IGNORE INTO curriculum_substrands(curriculum_year_id,strand_id,code,title,position)
                  VALUES(?,?,?,?,?)""", (year, strand, "1", "Science and Materials in Nature", 1))
    substrand = db.execute(
        """SELECT id FROM curriculum_substrands
           WHERE curriculum_year_id=? AND strand_id=? AND code=?""",
        (year, strand, "1")
    ).fetchone()["id"]

    standards = [
        ("1.1.1.CS.1", "Demonstrate knowledge and understanding of the characteristics of science and show how they are applied in everyday life.", 28),
        ("1.1.1.CS.2", "Know, understand, and identify the roles of solids in life.", 30),
    ]
    for code, description, page in standards:
        db.execute(
            """INSERT OR IGNORE INTO content_standards(substrand_id,code,description,source_page)
               VALUES(?,?,?,?)""",
            (substrand, code, description, page)
        )

    outcomes = [
        ("1.1.1.LO.1", "Evaluate the characteristics of science.", 26),
        ("1.1.1.LO.2", "Explain the functions of solids in life.", 26),
    ]
    for code, description, page in outcomes:
        db.execute(
            """INSERT OR IGNORE INTO learning_outcomes(substrand_id,code,description,source_page)
               VALUES(?,?,?,?)""",
            (substrand, code, description, page)
        )

    outcome_ids = {r["code"]: r["id"] for r in db.execute(
        "SELECT id,code FROM learning_outcomes WHERE substrand_id=?", (substrand,)
    )}
    standard_ids = {r["code"]: r["id"] for r in db.execute(
        "SELECT id,code FROM content_standards WHERE substrand_id=?", (substrand,)
    )}

    indicators = [
        ("1.1.1.CS.1", "1.1.1.LO.1", "1.1.1.LI.1", "Explain the characteristics of science in nature.", "1.1.1.AS.1", 28),
        ("1.1.1.CS.1", "1.1.1.LO.1", "1.1.1.LI.2", "Design projects using the characteristics of science.", "1.1.1.AS.2", 28),
        ("1.1.1.CS.1", "1.1.1.LO.1", "1.1.1.LI.3", "Apply the characteristics of science where appropriate.", "1.1.1.AS.3", 28),
        ("1.1.1.CS.2", "1.1.1.LO.2", "1.1.1.LI.1", "Classify different solids and their uses.", "1.1.1.AS.1", 30),
        ("1.1.1.CS.2", "1.1.1.LO.2", "1.1.1.LI.2", "Apply the properties of solids to everyday use.", "1.1.1.AS.2", 30),
        ("1.1.1.CS.2", "1.1.1.LO.2", "1.1.1.LI.3", "Discuss the relationship between binary compounds, the composition of binary compounds and the names of compounds.", "1.1.1.AS.3", 32),
    ]
    for standard_code, outcome_code, code, description, assessment_code, page in indicators:
        db.execute(
            """INSERT OR IGNORE INTO learning_indicators(
               content_standard_id,learning_outcome_id,code,description,assessment_code,source_page)
               VALUES(?,?,?,?,?,?)""",
            (standard_ids[standard_code], outcome_ids[outcome_code], code, description, assessment_code, page)
        )

def seed_learning_modules(db):
    modules_path = Path(__file__).resolve().parent / "data" / "module_lessons.json"
    if not modules_path.exists():
        return
    for module in json.loads(modules_path.read_text(encoding="utf-8")):
        db.execute(
            """INSERT OR IGNORE INTO courses(code,title,description,color)
               VALUES(?,?,?,?)""",
            (module["course_code"], module["course_title"], module["course_description"], module["color"])
        )
        course_id = db.execute(
            "SELECT id FROM courses WHERE code=?", (module["course_code"],)
        ).fetchone()["id"]

        lesson = db.execute(
            "SELECT id FROM lessons WHERE course_id=? AND title=?",
            (course_id, module["title"])
        ).fetchone()

        if not lesson:
            lesson_id = db.execute(
                """INSERT INTO lessons(course_id,title,material_type,content,position)
                   VALUES(?,?,?,?,?)""",
                (course_id, module["title"], "Guided learning module", module["overview"], 1)
            ).lastrowid
        else:
            lesson_id = lesson["id"]

        db.execute(
            """INSERT OR IGNORE INTO lesson_preparations(
               lesson_id,source_file,source_section,source_page,alignment_status,
               learning_outcomes_json,prior_knowledge,vocabulary_json,engage,
               investigate,explain,elaborate,practical_work,safety_notes,
               assessment,extension,lab_ids_json)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                lesson_id, module["source_file"], module["source_section"], module["source_page"],
                module["alignment_status"], json.dumps(module["learning_outcomes"]),
                module["prior_knowledge"], json.dumps(module["vocabulary"]), module["engage"],
                module["investigate"], module["explain"], module["elaborate"],
                module["practical_work"], module["safety_notes"], module["assessment"],
                module["extension"], json.dumps(module["lab_ids"])
            )
        )

        for indicator_code in module.get("verified_indicator_codes", []):
            indicators = db.execute(
                "SELECT id FROM learning_indicators WHERE code=?", (indicator_code,)
            ).fetchall()
            for indicator in indicators:
                db.execute(
                    """INSERT OR IGNORE INTO curriculum_lesson_links
                       (lesson_id,learning_indicator_id) VALUES(?,?)""",
                    (lesson_id, indicator["id"])
                )

def seed_database():
    db = get_db()
    # Curriculum and verified learning modules are content, not user/demo accounts.
    seed_curriculum(db)
    seed_learning_modules(db)
    db.commit()
    ensure_admin()
