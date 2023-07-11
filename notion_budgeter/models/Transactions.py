from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

from . import engine

Base = declarative_base()


class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, autoincrement=True, primary_key=True)
    t_id = Column(Integer, unique=True)

    def __init__(self, name):
        self.name = name


Base.metadata.create_all(engine)
