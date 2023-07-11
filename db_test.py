from sqlalchemy import text

from models.Transactions import engine

with engine.connect() as conn:
    res = conn.execute(text('SELECT * FROM transactions;'))

