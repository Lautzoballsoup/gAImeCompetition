import pymysql
import click
from .database.db_config import *
from flask import current_app, g
from flask.cli import with_appcontext

def parse_sql(filename):
     with current_app.open_resource(filename) as file:
          data = file.read().decode('utf8').split('\n')
          statements = []
          DELIMITER = ';'
          statement = ''

          for line_num, line in enumerate(data):
               if not line.strip():
                    continue

               elif DELIMITER not in line:
                    statement += line

               elif statement:
                    statement += line
                    statements.append(statement.strip())
                    statement = ''
               else:
                    statements.append(line.strip())
          return statements
               

def open_db():
     if 'db' not in g:
          g.db = pymysql.connect(host=sql_vals['host'],
                          port=sql_vals['port'],
                          db=sql_vals['db'],
                          user=sql_vals['user'],
                          password=sql_vals['password'])
     return g.db

def get_db():
    c = open_db()
    return c.cursor(pymysql.cursors.DictCursor)

def close_db(e=None):
     db = g.pop('db', None)

     if db is not None:
          db.close()

def init_db():
     #database hasn't been created, so we use a new connection to make it
     db = pymysql.connect(host=sql_vals['host'],
                          port=sql_vals['port'],
                          user=sql_vals['user'],
                          password=sql_vals['password'])
     statements = parse_sql('database/schema.sql')

     with db.cursor() as cursor:
          for statement in statements:
               cursor.execute(statement)
     db.commit()

def commit_db():
     db = open_db()
     db.commit()

def rollback_db():
     db = open_db()
     db.rollback()

def query_db(query, num_rows=-1):
     db = open_db()
     with db.cursor(pymysql.cursors.DictCursor) as cursor:
          cursor.execute(query)
     if num_rows == 1:
          return cursor.fetchone()
     elif num_rows == -1:
          return cursor.fetchall()
     else:
          return cursor.fetchmany(num_rows)

def insert_db(table, commit=True, **kwargs):
     keys = []
     values = []
     for key, value in kwargs.items():
          keys.append(key)
          if isinstance(value, str):
              values.append("'" + value + "'")
          else:
              values.append(str(value))
     key_string = '(' + ', '.join(keys) + ')'
     value_string = '(' + ', '.join(values) + ')'
     
     transaction = 'INSERT INTO {0} {1} VALUES {2};'.format(
                          table, key_string, value_string)

     db = open_db()
     with db.cursor() as cursor:
          success = cursor.execute(transaction)
     if commit:
         db.commit()
     return success

def update_db(update, commit=True):
     db = open_db()
     with db.cursor() as cursor:
          success = cursor.execute(update)
     if commit:
          db.commit()
     return success

def get_db_row(table, id):
     table_ids = {'users':'username', 'languages':'language_id',
                  'games':'game_id', 'uploads':'upload_id',
                  'matches':'match_id', 'moves':'move_id'}
     id_type = table_ids.get(table.lower())
     if not id_type:
          return None
     query = 'SELECT * FROM {0} WHERE {1}={2}'.format(table, id_type, id)
     return query_db(query, 1)
     
def get_all_rows(table):
     query = 'SELECT * FROM {0}'.format(table)
     return query_db(query, -1)


@click.command('init-db')
@with_appcontext
def init_db_command():
     init_db()
     click.echo('Initialized the database.')

def init_app(app):
     app.teardown_appcontext(close_db)
     app.cli.add_command(init_db_command)
