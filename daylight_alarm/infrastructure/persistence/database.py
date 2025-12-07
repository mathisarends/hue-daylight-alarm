from pathlib import Path
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine


class DatabaseConfig:
    def __init__(self, database_url: str = "sqlite:///./data/alarms.db"):
        self.database_url = database_url

        self._ensure_directory_exists()

        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False}
            if "sqlite" in database_url
            else {},
            echo=False,
            pool_pre_ping=True,
        )

    def _ensure_directory_exists(self):
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def create_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        with Session(self.engine) as session:
            yield session

    def dispose(self):
        self.engine.dispose()


db_config = DatabaseConfig()
