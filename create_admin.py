import pymysql
import pymysql.cursors
import hashlib
from getpass import getpass

# --- Database Connection ---
def connect_db():
    """Establishes a connection to the database"""
    try:
        return pymysql.connect(
            host='localhost',
            user='root',
            password='java0603',
            database='restaurant-inventory-db',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    except pymysql.Error as e:
        print(f"Database Error: {e}")
        return None

def create_admin_user():
    """Securely creates the first admin user"""
    conn = connect_db()
    if not conn:
        return

    print("--- Creating Initial Admin User ---")
    try:
        username = input("Enter admin username: ")
        password = getpass("Enter admin password: ")
        
        # Hash the password using SHA-256
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        with conn.cursor() as cursor:
            # Create the user account
            sql_user = "INSERT INTO user_account (username, password_hash) VALUES (%s, %s)"
            cursor.execute(sql_user, (username, password_hash))
            user_id = cursor.lastrowid
            print(f"User account '{username}' created with ID: {user_id}")

            # Create the corresponding employee record
            sql_employee = """
            INSERT INTO employee (role, fname, lname, email, uid) 
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_employee, ('admin', 'Admin', 'User', f'{username}@restaurant.com', user_id))
            employee_id = cursor.lastrowid
            print(f"Employee record created with ID: {employee_id}")

        print("\nAdmin user created successfully!")

    except pymysql.IntegrityError as e:
        # error if the username already exists
        if e.args[0] == 1062:
            print(f"\nError: Username '{username}' already exists. Please choose a different username.")
        else:
            print(f"\nDatabase Integrity Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin_user()