from sqlalchemy import Column, Integer

from . import Base


class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, autoincrement=True, primary_key=True)
    t_id = Column(Integer, unique=True)

    def __init__(self, name):
        self.name = name
