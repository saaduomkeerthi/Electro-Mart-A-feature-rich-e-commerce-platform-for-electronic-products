import bcrypt
from .db import get_db_connection
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def register_user(data):
    """Registers a new user (buyer or seller) in the database."""
    conn = get_db_connection()
    if not conn: return {"error": "Database connection failed."}, 500

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT user_id FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            return {"error": "An account with this email already exists."}, 409

        password_bytes = data['password'].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)

        user_sql = """
            INSERT INTO users (full_name, email, password_hash, phone, role)
            VALUES (%s, %s, %s, %s, %s)
        """
        user_values = (data['full_name'], data['email'], hashed_password.decode('utf-8'), data.get('phone'), data['role'])
        cursor.execute(user_sql, user_values)
        user_id = cursor.lastrowid

        if data['role'] == 'buyer':
            cursor.execute("INSERT INTO buyers (buyer_id) VALUES (%s)", (user_id,))
        elif data['role'] == 'seller':
            seller_sql = """
                INSERT INTO sellers (seller_id, business_name, business_email, business_phone,
                                     business_address, business_country, business_state, business_city, business_zip_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            seller_values = (
                user_id, data['business_name'], data['email'], data['business_phone'],
                data['business_address'], data['business_country'], data['business_state'],
                data['business_city'], data['business_zip_code']
            )
            cursor.execute(seller_sql, seller_values)

        conn.commit()
        return {"message": "Registration successful! Please log in."}, 201
    except Exception as e:
        conn.rollback()
        print(f"Error during registration: {e}")
        return {"error": "An internal error occurred. Please try again later."}, 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def create_default_admin():
    """Checks if a default admin user exists and creates one if not."""
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database to create admin.")
        return

    try:
        cursor = conn.cursor(dictionary=True)
        admin_email = "admin@electronics.com"
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (admin_email,))
        if cursor.fetchone():
            return

        print(f"Creating default admin user: {admin_email}")
        password_to_hash = 'adminpassword'.encode('utf-8')
        hashed_password = bcrypt.hashpw(password_to_hash, bcrypt.gensalt())
        admin_sql = """
            INSERT INTO users (full_name, email, password_hash, role, is_active, email_verified)
            VALUES (%s, %s, %s, 'admin', TRUE, TRUE)
        """
        admin_values = ("System Admin", admin_email, hashed_password.decode('utf-8'))
        cursor.execute(admin_sql, admin_values)
        conn.commit()
        print("Default admin user created successfully.")
    except Exception as e:
        print(f"An error occurred while creating the default admin: {e}")
        conn.rollback()
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def login_user(email, password):
    """Verifies user credentials against the database."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND is_active = TRUE", (email,))
        user = cursor.fetchone()
        if user:
            password_bytes = password.encode('utf-8')
            hashed_password_bytes = user['password_hash'].encode('utf-8')
            if bcrypt.checkpw(password_bytes, hashed_password_bytes):
                return user
        return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_user_by_id(user_id):
    """Fetches a single user's details by their user_id."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        # --- MODIFIED ---
        # Now fetches the profile_image column as well.
        query = "SELECT user_id, email, full_name, role, phone, profile_image FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"Error fetching user by ID {user_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def change_password(user_id, old_password, new_password):
    """
    Changes a user's password after verifying their old password.
    Returns a tuple: (success_boolean, message_string).
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return False, "User not found."

        old_password_bytes = old_password.encode('utf-8')
        current_hash_bytes = user['password_hash'].encode('utf-8')
        if not bcrypt.checkpw(old_password_bytes, current_hash_bytes):
            return False, "Incorrect old password. Please try again."

        new_password_bytes = new_password.encode('utf-8')
        new_hash_bytes = bcrypt.hashpw(new_password_bytes, bcrypt.gensalt())
        new_hash_str = new_hash_bytes.decode('utf-8')

        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash_str, user_id))
        conn.commit()
        return True, "Password updated successfully."

    except Exception as e:
        conn.rollback()
        print(f"Error changing password for user_id {user_id}: {e}")
        return False, "An internal error occurred. Please try again later."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_user_by_email(email):
    """Fetches a single user by their email address."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT user_id, email, full_name FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"Error fetching user by email {email}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_password_reset_token(user_id):
    """
    Generates a secure, timed token for password reset.
    Token expires in 30 minutes (1800 seconds).
    """
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(user_id, salt='password-reset-salt')

def verify_password_reset_token(token, max_age=1800):
    """
    Verifies the password reset token and returns the user_id.
    Returns None if the token is invalid or expired.
    """
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, salt='password-reset-salt', max_age=max_age)
    except Exception:
        return None
    return user_id   

def update_password_for_user(user_id, new_password):
    """
    Hashes a new password and updates it in the database for a given user_id.
    Returns a tuple: (success_boolean, message_string).
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        password_bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        sql = "UPDATE users SET password_hash = %s WHERE user_id = %s"
        cursor.execute(sql, (hashed_password.decode('utf-8'), user_id))
        conn.commit()
        return True, "Password has been updated successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error updating password for user_id {user_id}: {e}")
        return False, "An internal error occurred while updating the password."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- REPLACED FUNCTION ---
def update_profile_details(user_id, data, image_path=None):
    """
    Updates a user's general profile information (full_name, phone, and profile_image).
    Returns a tuple: (success_boolean, message_string, old_image_path).
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed.", None
    
    old_image_path = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # If a new image is being uploaded, first get the path of the old one for cleanup
        if image_path:
            cursor.execute("SELECT profile_image FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if result and result['profile_image']:
                old_image_path = result['profile_image']

        # Dynamically build the UPDATE query
        fields_to_update = []
        values = []

        if 'full_name' in data and data['full_name']:
            fields_to_update.append("full_name = %s")
            values.append(data['full_name'])
        
        if 'phone' in data:
            fields_to_update.append("phone = %s")
            values.append(data['phone'])
        
        if image_path:
            fields_to_update.append("profile_image = %s")
            values.append(image_path)
            
        if not fields_to_update:
            return False, "No data provided to update.", None
            
        sql = f"UPDATE users SET {', '.join(fields_to_update)} WHERE user_id = %s"
        values.append(user_id)

        # Use a non-dictionary cursor for the execute operation
        cursor_execute = conn.cursor()
        cursor_execute.execute(sql, tuple(values))
        conn.commit()
        
        if cursor_execute.rowcount == 0:
            return False, "User not found or data is the same.", None

        return True, "Profile updated successfully.", old_image_path
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating profile for user_id {user_id}: {e}")
        return False, "An internal error occurred.", None
    finally:
        if conn and conn.is_connected():
            # The dictionary cursor was defined in the try block, so check for its existence
            if 'cursor' in locals() and cursor.is_open():
                cursor.close()
            if 'cursor_execute' in locals() and cursor_execute.is_open():
                cursor_execute.close()
            conn.close()

# Add this function to user_model.py
def get_all_admins():
    """Fetches user_id for all admin accounts."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM users WHERE role = 'admin' AND is_active = TRUE")
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching all admins: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()            