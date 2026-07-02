from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import text

from app.config import settings

engine = create_engine(settings.database_url, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)
    with engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(meeting)"))]
        if "recording_path" not in cols:
            conn.execute(text("ALTER TABLE meeting ADD COLUMN recording_path VARCHAR DEFAULT ''"))


def get_session():
    with Session(engine) as session:
        yield session
