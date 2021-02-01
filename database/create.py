import pymysql
from dotenv import load_dotenv, find_dotenv
from os import environ as env
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

db_name = env.get("db_name")
db_host = env.get("db_host")
db_user = env.get("db_user")
db_pass = env.get("db_pass")



def create_connection(db):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        print(type(db_host))
        db = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name)
        return db
    except Exception as e:
        print("Connection to the database could not be created: ", e)
        return None


def create_tables(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        conn.commit()
    except Exception as e:
        print("Tables could not be created:", e)


def create_db():
    """
    A function used to create a database file to store all the data
    """
    connection = create_connection(db_name)
    users_table = """
    CREATE TABLE IF NOT EXISTS users (
                                  id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                  email text,
                                  time timestamp DEFAULT CURRENT_TIMESTAMP
                                ); """

    user_words_table = """
    CREATE TABLE IF NOT EXISTS user_words (
                                  id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                  user_id INTEGER,
                                  word text,
                                  time timestamp DEFAULT CURRENT_TIMESTAMP,
                                  FOREIGN KEY(user_id) REFERENCES users(id)
                                ); """

    user_data_table = """
    CREATE TABLE IF NOT EXISTS user_data (
                                  id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                  user_id INTEGER,
                                  word text,
                                  input_word text,
                                  time timestamp DEFAULT CURRENT_TIMESTAMP,
                                  FOREIGN KEY(user_id) REFERENCES users(id)
                                ); """
    sql_create_conversation_log_table = """
                                  CREATE TABLE IF NOT EXISTS conversation_log (
                                  id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                  username text NOT NULL,
                                  is_bot boolean,
                                  convo text,
                                  time timestamp DEFAULT CURRENT_TIMESTAMP
                                ); """

    for table_query in [
        users_table,
        user_words_table,
        user_data_table,
        sql_create_conversation_log_table,
    ]:
        create_tables(conn=connection, create_table_sql=table_query)


if __name__ == "__main__":

    create_db()
