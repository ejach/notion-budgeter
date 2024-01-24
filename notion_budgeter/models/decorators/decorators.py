from inspect import getframeinfo, currentframe

from sqlalchemy.exc import OperationalError

from notion_budgeter.models import DatabaseSession
from notion_budgeter.logger.logger import Logger


# Connect to the database and roll back commits when exceptions are thrown
def db_connector(f):
    def with_connection_(*args, **kwargs):
        with DatabaseSession() as conn:
            try:
                result = f(*args, connection=conn, **kwargs)
            except OperationalError as e:
                Logger.log.exception(str(getframeinfo(currentframe()).function) + '\n' + 'Line: ' +
                      str(getframeinfo(currentframe()).lineno) + '\n' + str(e))
                conn.rollback()
            except TypeError as e:
                Logger.log.exception(str(getframeinfo(currentframe()).function) + '\n' + 'Line: ' +
                      str(getframeinfo(currentframe()).lineno) + '\n' + str(e))
                conn.rollback()
            finally:
                conn.close()
            return result

    return with_connection_
