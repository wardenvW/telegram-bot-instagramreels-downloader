from .connection import get_connection

def init_database():
    with get_connection() as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    role varchar(50) DEFAULT 'user'
                );
            """)