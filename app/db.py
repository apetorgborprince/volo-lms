import sqlite3
from flask import current_app, g

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','tutor','parent','admin','super_admin')),
    full_name TEXT NOT NULL,
    class_name TEXT,
    subject_focus TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    phone TEXT, email TEXT, avatar_url TEXT, bio TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parent_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship TEXT DEFAULT 'Parent/Guardian',
    UNIQUE(parent_id, student_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL, description TEXT, badge TEXT,
    awarded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    color TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    material_type TEXT NOT NULL,
    content TEXT,
    file_path TEXT,
    external_url TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    tutor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);

CREATE TABLE IF NOT EXISTS lesson_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    UNIQUE(student_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    time_limit_minutes INTEGER,
    attempts_allowed INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option INTEGER NOT NULL,
    points INTEGER NOT NULL DEFAULT 1,
    position INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score REAL NOT NULL DEFAULT 0,
    total_points REAL NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submitted_at TEXT
);

CREATE TABLE IF NOT EXISTS quiz_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    selected_option INTEGER,
    awarded_points REAL NOT NULL DEFAULT 0
);

-- V5.1 Assessment Engine: structured assignments and teacher-reviewed submissions.
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    instructions TEXT NOT NULL,
    max_points REAL NOT NULL DEFAULT 100,
    due_at TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assignment_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    answer_text TEXT,
    file_path TEXT,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'submitted' CHECK(status IN ('draft','submitted','graded','returned')),
    score REAL,
    feedback TEXT,
    graded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    graded_at TEXT,
    UNIQUE(assignment_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id, active);
CREATE INDEX IF NOT EXISTS idx_assignment_submissions_student ON assignment_submissions(student_id, status);


CREATE TABLE IF NOT EXISTS tutor_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tutor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tutor_id, student_id)
);

CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    audience_role TEXT,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    read_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Official curriculum metadata is intentionally separate from teacher-created content.
CREATE TABLE IF NOT EXISTS curriculum_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    source_title TEXT NOT NULL,
    published_on TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS curriculum_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    curriculum_version_id INTEGER NOT NULL REFERENCES curriculum_versions(id) ON DELETE RESTRICT,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE(curriculum_version_id, code)
);

CREATE TABLE IF NOT EXISTS curriculum_strands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    curriculum_version_id INTEGER NOT NULL REFERENCES curriculum_versions(id) ON DELETE RESTRICT,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE(curriculum_version_id, code)
);

CREATE TABLE IF NOT EXISTS curriculum_substrands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    curriculum_year_id INTEGER NOT NULL REFERENCES curriculum_years(id) ON DELETE RESTRICT,
    strand_id INTEGER NOT NULL REFERENCES curriculum_strands(id) ON DELETE RESTRICT,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE(curriculum_year_id, strand_id, code)
);

CREATE TABLE IF NOT EXISTS content_standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    substrand_id INTEGER NOT NULL REFERENCES curriculum_substrands(id) ON DELETE RESTRICT,
    code TEXT NOT NULL,
    description TEXT NOT NULL,
    source_page INTEGER NOT NULL,
    UNIQUE(substrand_id, code)
);

CREATE TABLE IF NOT EXISTS learning_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    substrand_id INTEGER NOT NULL REFERENCES curriculum_substrands(id) ON DELETE RESTRICT,
    code TEXT NOT NULL,
    description TEXT NOT NULL,
    source_page INTEGER NOT NULL,
    UNIQUE(substrand_id, code)
);

CREATE TABLE IF NOT EXISTS learning_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_standard_id INTEGER NOT NULL REFERENCES content_standards(id) ON DELETE RESTRICT,
    learning_outcome_id INTEGER REFERENCES learning_outcomes(id) ON DELETE RESTRICT,
    code TEXT NOT NULL,
    description TEXT NOT NULL,
    assessment_code TEXT,
    source_page INTEGER NOT NULL,
    UNIQUE(content_standard_id, code)
);

CREATE TABLE IF NOT EXISTS curriculum_lesson_links (
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    learning_indicator_id INTEGER NOT NULL REFERENCES learning_indicators(id) ON DELETE RESTRICT,
    PRIMARY KEY(lesson_id, learning_indicator_id)
);

CREATE TABLE IF NOT EXISTS practical_designs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    learning_indicator_id INTEGER NOT NULL REFERENCES learning_indicators(id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    objective TEXT NOT NULL,
    apparatus TEXT NOT NULL,
    safety_instructions TEXT NOT NULL,
    procedure TEXT NOT NULL,
    assessment_prompt TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_practical_designs_indicator ON practical_designs(learning_indicator_id);

CREATE TABLE IF NOT EXISTS lesson_preparations (
    lesson_id INTEGER PRIMARY KEY REFERENCES lessons(id) ON DELETE CASCADE,
    source_file TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_page INTEGER NOT NULL,
    alignment_status TEXT NOT NULL,
    learning_outcomes_json TEXT NOT NULL,
    prior_knowledge TEXT NOT NULL,
    vocabulary_json TEXT NOT NULL,
    engage TEXT NOT NULL,
    investigate TEXT NOT NULL,
    explain TEXT NOT NULL,
    elaborate TEXT NOT NULL,
    practical_work TEXT NOT NULL,
    safety_notes TEXT NOT NULL,
    assessment TEXT NOT NULL,
    extension TEXT NOT NULL,
    lab_ids_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_curriculum_substrands_year ON curriculum_substrands(curriculum_year_id);
CREATE INDEX IF NOT EXISTS idx_content_standards_substrand ON content_standards(substrand_id);
CREATE INDEX IF NOT EXISTS idx_learning_outcomes_substrand ON learning_outcomes(substrand_id);
CREATE INDEX IF NOT EXISTS idx_learning_indicators_standard ON learning_indicators(content_standard_id);
"""

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()
