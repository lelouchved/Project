import os
import shutil
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IS_VERCEL = bool(os.environ.get("VERCEL"))

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    if IS_VERCEL:
        # On Vercel serverless functions, project directory is read-only, but /tmp is writable
        tmp_db = "/tmp/club_tracker.db"
        local_db = os.path.join(BASE_DIR, "club_tracker.db")
        if not os.path.exists(tmp_db):
            if os.path.exists(local_db):
                try:
                    shutil.copyfile(local_db, tmp_db)
                except Exception:
                    pass
            elif os.path.exists("./club_tracker.db"):
                try:
                    shutil.copyfile("./club_tracker.db", tmp_db)
                except Exception:
                    pass
        DATABASE_URL = f"sqlite:///{tmp_db}"
    else:
        DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'club_tracker.db')}"

# Directory setup for uploads (serverless-compatible)
if IS_VERCEL:
    UPLOADS_DIR = "/tmp/uploads"
    src_uploads = os.path.join(BASE_DIR, "uploads")
    if not os.path.exists(UPLOADS_DIR):
        try:
            if os.path.exists(src_uploads):
                shutil.copytree(src_uploads, UPLOADS_DIR, dirs_exist_ok=True)
            else:
                os.makedirs(UPLOADS_DIR, exist_ok=True)
        except Exception:
            pass
else:
    UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

LOGOS_DIR = os.path.join(UPLOADS_DIR, "logos")
AVATARS_DIR = os.path.join(UPLOADS_DIR, "avatars")
DELIVERABLES_DIR = os.path.join(UPLOADS_DIR, "deliverables")
RECEIPTS_DIR = os.path.join(UPLOADS_DIR, "receipts")
CERTIFICATES_DIR = os.path.join(UPLOADS_DIR, "certificates")

for _d in [UPLOADS_DIR, LOGOS_DIR, AVATARS_DIR, DELIVERABLES_DIR, RECEIPTS_DIR, CERTIFICATES_DIR]:
    try:
        os.makedirs(_d, exist_ok=True)
    except OSError:
        pass

# Connect args: only SQLite needs check_same_thread
connect_args = {"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

# Enable SQLite foreign keys & WAL mode for high concurrency
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()
        except Exception:
            pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def auto_migrate(db_engine):
    """Safely runs lightweight migrations for SQLite tables if new columns are added."""
    try:
        with db_engine.connect() as conn:
            # Check users table
            res = conn.execute(text("PRAGMA table_info(users)"))
            cols = [r[1] for r in res.fetchall()]
            if cols:
                if "user_category" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN user_category VARCHAR(50) DEFAULT 'STUDENT_MEMBER'"))
                if "is_mirai_entity" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_mirai_entity BOOLEAN DEFAULT 1"))
                if "teacher_type" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN teacher_type VARCHAR(50)"))
                if "student_type" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN student_type VARCHAR(50)"))

            # Check club_memberships table
            res_m = conn.execute(text("PRAGMA table_info(club_memberships)"))
            m_cols = [r[1] for r in res_m.fetchall()]
            if m_cols:
                if "branch" not in m_cols:
                    conn.execute(text("ALTER TABLE club_memberships ADD COLUMN branch VARCHAR(100)"))

            conn.commit()
    except Exception:
        pass

auto_migrate(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

