import psycopg2

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="cricket-simulator",
            user="postgres",
            password="shishir",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None, None

def close_db_connection(conn, cursor):
    cursor.close()
    conn.close()