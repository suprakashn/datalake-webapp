from sqlalchemy import create_engine
from sqlalchemy import inspect

db_uri = 'sqlite:////mnt/d/Data/solaris/python_workspace/myPython/datalake-webapp/sqlite/dlFmwrk.db'


engine = create_engine(db_uri)

inspector = inspect(engine)

# Get table information
print(inspector.get_table_names())