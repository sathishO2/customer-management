from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import scoped_session,sessionmaker

db_url = "postgresql://postgres:1234@localhost:5432/cmdb"


engine = create_engine(db_url)

Base = declarative_base()
SessionLocal = scoped_session(sessionmaker(bind=engine,autoflush=False))

def get_db():
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
