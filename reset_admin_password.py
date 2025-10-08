# reset_admin_password.py

import bcrypt
import mysql.connector
from mysql.connector import Error

# --- IMPORTANT: CONFIGURE YOUR DATABASE CONNECTION HERE ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_db_user',        # <-- CHANGE THIS to your database username
    'password': 'your_db_password',  # <-- CHANGE THIS to your database password
    'database': 'electronics_ecommerce_db'
}

def resetold_password():
    """Connects to the DB and forcefully updates the admin password."""
    admin_email = "admin@electronics.com"
    
    # The password we want to set
    new_password_plain = 'adminpassword'
    
    # Hashing the password just like in your user_model
    password_bytes = new_password_plain.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    try:
        print("Connecting to the database...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print(f"Looking for admin user: {admin_email}")
        
        # SQL to update the user's password hash
        sql_update_query = """
            UPDATE users 
            SET password_hash = %s 
            WHERE email = %s
        """
        cursor.execute(sql_update_query, (hashed_password, admin_email))
        
        # Check if any row was actually updated
        if cursor.rowcount > 0:
            conn.commit()
            print("\nSUCCESS!")
            print(f"Password for '{admin_email}' has been reset to '{new_password_plain}'.")
        else:
            print("\nERROR!")
            print(f"Could not find a user with the email '{admin_email}'.")
            print("Please make sure the default admin user was created first.")

    except Error as e:
        print(f"\nDATABASE ERROR: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    reset_password()
