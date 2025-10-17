from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.config import Config

app_config = Config.get_current_config()

engine = create_engine(f"sqlite:///{app_config.database_file}", echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["engine", "SessionLocal"]
