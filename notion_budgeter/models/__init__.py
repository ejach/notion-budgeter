from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine('sqlite:///%s/db.sqlite' % getenv('data_dir'), echo=True)


class DatabaseSession:

    def __enter__(self):
        self.session = Session(engine)

        self.session.expire_on_commit = False

        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
