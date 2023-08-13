from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base

# create in-memory database
engine = create_engine('sqlite://')
Base = declarative_base()


class DatabaseSession:

    def __enter__(self):
        self.session = Session(engine)

        self.session.expire_on_commit = False

        Base.metadata.create_all(engine)

        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
