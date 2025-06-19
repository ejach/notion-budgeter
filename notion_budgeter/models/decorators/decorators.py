from functools import wraps
from inspect import getframeinfo, currentframe
from traceback import format_exc

from sqlalchemy.exc import OperationalError

from notion_budgeter.models import DatabaseSession
from notion_budgeter.logger.logger import Logger


# Connect to the database and roll back commits when exceptions are thrown
def db_connector(f):
    @wraps(f)
    def with_connection_(*args, **kwargs):
        result = None
        with DatabaseSession() as conn:
            try:
                result = f(*args, connection=conn, **kwargs)
            except (OperationalError, TypeError):
                Logger.log.exception(
                    f'{f.__name__} failed\n{format_exc()}'
                )
                conn.rollback()
            finally:
                conn.close()
        return result

    return with_connection_
