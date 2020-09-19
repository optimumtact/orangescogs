"""
Gets record count of all tables.
also serves as a validation of model specification
"""

from sqlalchemy import *

from ..models import tgschema as models

# opens db connection.
# Param: connection string  Format: "driver://user:password@dbserver_ip/db_name"
engine = create_engine('mysql://tgs:tgstation13@127.0.0.1/tgs13')

with engine.connect() as connection:
    for name, model in models.__dict__.items():
        if(isinstance(model,Table)):
            result = connection.execute(model.select(text("count(*)")))
            print(name + " " + str(result.first()[0]))
