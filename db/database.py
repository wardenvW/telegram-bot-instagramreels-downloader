from .connection import get_connection

def get_user_role(id: int):
    with get_connection() as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT role FROM users WHERE id = %s;
            """, (id,))

            role_tuple = cursor.fetchone()

            if not role_tuple:
                cursor.execute("""
                    INSERT INTO users (id, role) VALUES (%s, 'user')
                """, (id,))

                return 'user'
            
            role = role_tuple[0]

            return role
            
            
def get_all_users():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users;
            """)

            return cursor.fetchall()
        


def find_user(id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, role FROM users WHERE id = %s;
            """, (id,))

            return cursor.fetchone()

def add_admin(id:int):
    with get_connection() as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET role = 'admin' WHERE ID = %s
            """, (id,))

            if not cursor.rowcount:
                return False
            return True

def delete_admin(id:int):
    with get_connection() as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET role = 'user' WHERE ID = %s
            """, (id,))

            if not cursor.rowcount:
                return False
            return True

        

def block_user(id: int) -> bool:
    with get_connection() as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:

            cursor.execute("""
                UPDATE users SET role = %s WHERE id = %s
            """, ('blocked', id))

            if not cursor.rowcount:
                return False
            return True
        

def unblock_user(id: int) -> bool:
    with get_connection() as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:

            cursor.execute("""
                UPDATE users SET role = 'user' WHERE id = %s 
            """, (id,))

            if not cursor.rowcount:
                return False
            return True