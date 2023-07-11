from inspect import getframeinfo, currentframe

from src.models import DatabaseSession
from sqlalchemy.exc import OperationalError


# Connect to the database and roll back commits when exceptions are thrown
def db_connector(f):
    def with_connection_(*args, **kwargs):
        with DatabaseSession() as conn:
            try:
                result = f(*args, connection=conn, **kwargs)
            except OperationalError as e:
                print(str(getframeinfo(currentframe()).function) + '\n' + 'Line: ' +
                      str(getframeinfo(currentframe()).lineno) + '\n' + str(e))
                conn.rollback()
            except TypeError as e:
                print(str(getframeinfo(currentframe()).function) + '\n' + 'Line: ' +
                      str(getframeinfo(currentframe()).lineno) + '\n' + str(e) + '\n'
                      + 'Blank input detected, database not manipulated')
                conn.rollback()
            finally:
                conn.close()
            return result

    return with_connection_
