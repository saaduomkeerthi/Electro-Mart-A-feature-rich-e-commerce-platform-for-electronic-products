# # electronic_ecommerce/models/buyer_model.py

# from .db import get_db_connection
# import bcrypt
# def get_buyer_dashboard_stats(buyer_id):
#     """Fetches key statistics for a specific buyer's dashboard."""
#     conn = get_db_connection()
#     if not conn: 
#         return {
#             'total_orders': 0,
#             'pending_orders': 0,
#             'completed_orders': 0,
#             'total_spent': 0.0
#         }
#     try:
#         cursor = conn.cursor(dictionary=True)
#         stats = {}
        
#         # This single query is more efficient and calculates all stats at once.
#         query = """
#         SELECT 
#             COUNT(order_id) as total_orders,
#             SUM(CASE WHEN status IN ('pending', 'confirmed', 'processing', 'shipped') THEN 1 ELSE 0 END) as pending_orders,
#             SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as completed_orders,

#             -- THIS IS THE CORRECTED LOGIC FOR TOTAL SPENT --
#             SUM(CASE 
#                 WHEN payment_status = 'completed' AND status NOT IN ('cancelled', 'returned', 'refunded') 
#                 THEN total_amount 
#                 ELSE 0 
#             END) as total_spent

#         FROM orders 
#         WHERE buyer_id = %s;
#         """
        
#         cursor.execute(query, (buyer_id,))
#         result = cursor.fetchone()

#         if result:
#             stats['total_orders'] = result.get('total_orders') or 0
#             stats['pending_orders'] = result.get('pending_orders') or 0
#             stats['completed_orders'] = result.get('completed_orders') or 0
#             # Ensure the value is a float for JSON compatibility
#             stats['total_spent'] = float(result.get('total_spent')) if result.get('total_spent') else 0.0
#         else:
#              stats = { 'total_orders': 0, 'pending_orders': 0, 'completed_orders': 0, 'total_spent': 0.0 }
            
#         return stats
#     except Exception as e:
#         print(f"Error fetching buyer dashboard stats for buyer_id {buyer_id}: {e}")
#         return {}
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_buyer_recent_orders(buyer_id, limit=5):
#     """Fetches the most recent orders for a specific buyer."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT 
#                 o.order_id,
#                 o.order_number,
#                 o.order_date,
#                 o.total_amount,
#                 o.status,
#                 s.business_name as seller_name
#             FROM orders o
#             JOIN sellers s ON o.seller_id = s.seller_id
#             WHERE o.buyer_id = %s
#             ORDER BY o.order_date DESC
#             LIMIT %s;
#         """
#         cursor.execute(query, (buyer_id, limit))
#         orders = cursor.fetchall()
#         for order in orders:
#             order['order_date'] = order['order_date'].strftime('%Y-%m-%d %H:%M')
#             order['total_amount'] = float(order['total_amount'])
#         return orders
#     except Exception as e:
#         print(f"Error fetching recent orders for buyer_id {buyer_id}: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_buyer_profile(buyer_id):
#     """Fetches the profile data for a buyer from users and buyers tables."""
#     conn = get_db_connection()
#     if not conn: return None
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT 
#                 u.full_name, u.email, u.phone, u.profile_image,
#                 b.default_address, b.default_city, b.default_state, 
#                 b.default_zip_code, b.default_country, b.loyalty_points
#             FROM users u
#             JOIN buyers b ON u.user_id = b.buyer_id
#             WHERE u.user_id = %s;
#         """
#         cursor.execute(query, (buyer_id,))
#         return cursor.fetchone()
#     except Exception as e:
#         print(f"Error fetching buyer profile for buyer_id {buyer_id}: {e}")
#         return None
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_buyer_order_history(buyer_id):
#     """Fetches the entire order history for a specific buyer."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT 
#                 o.order_id,
#                 o.order_number,
#                 o.order_date,
#                 o.total_amount,
#                 o.status,
#                 s.business_name as seller_name,
#                 GROUP_CONCAT(p.name SEPARATOR ', ') as products
#             FROM orders o
#             JOIN sellers s ON o.seller_id = s.seller_id
#             JOIN order_items oi ON o.order_id = oi.order_id
#             JOIN products p ON oi.product_id = p.product_id
#             WHERE o.buyer_id = %s
#             GROUP BY o.order_id, o.order_number, o.order_date, o.total_amount, o.status, s.business_name
#             ORDER BY o.order_date DESC;
#         """
#         cursor.execute(query, (buyer_id,))
#         orders = cursor.fetchall()
#         for order in orders:
#             order['order_date'] = order['order_date'].strftime('%Y-%m-%d')
#             order['total_amount'] = float(order['total_amount'])
#         return orders
#     except Exception as e:
#         print(f"Error fetching order history for buyer_id {buyer_id}: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# def update_buyer_profile(buyer_id, profile_data, image_path=None):
#     """Updates a buyer's general profile information in the users table."""
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."

#     try:
#         cursor = conn.cursor()
        
#         # Build the update query dynamically based on provided data
#         fields_to_update = []
#         values = []
        
#         if 'full_name' in profile_data and profile_data['full_name']:
#             fields_to_update.append("full_name = %s")
#             values.append(profile_data['full_name'])
        
#         if 'phone' in profile_data:
#             fields_to_update.append("phone = %s")
#             values.append(profile_data['phone'])
            
#         if image_path:
#             fields_to_update.append("profile_image = %s")
#             values.append(image_path)
            
#         if not fields_to_update:
#             return False, "No data provided to update."

#         sql = f"UPDATE users SET {', '.join(fields_to_update)} WHERE user_id = %s"
#         values.append(buyer_id)
        
#         cursor.execute(sql, tuple(values))
#         conn.commit()

#         return True, "Profile updated successfully."
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating buyer profile for ID {buyer_id}: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()


# def update_buyer_password(buyer_id, old_password, new_password):
#     """Updates a buyer's password after verifying the old one."""
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."

#     try:
#         cursor = conn.cursor(dictionary=True)
        
#         # 1. Fetch the current password hash
#         cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (buyer_id,))
#         user = cursor.fetchone()
#         if not user:
#             return False, "User not found."

#         # 2. Verify the old password
#         if not bcrypt.checkpw(old_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
#             return False, "Incorrect current password."

#         # 3. Hash the new password
#         new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

#         # 4. Update the database with the new hash
#         cursor.execute(
#             "UPDATE users SET password_hash = %s WHERE user_id = %s",
#             (new_hashed_password.decode('utf-8'), buyer_id)
#         )
#         conn.commit()

#         return True, "Password updated successfully."
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating password for user ID {buyer_id}: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()


# def get_buyer_profile(buyer_id):
#     """Fetches the profile data for a buyer from users and buyers tables."""
#     conn = get_db_connection()
#     if not conn: return None
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT 
#                 u.full_name, u.email, u.phone, u.profile_image,
#                 b.default_address, b.default_city, b.default_state, 
#                 b.default_zip_code, b.default_country, b.loyalty_points
#             FROM users u
#             JOIN buyers b ON u.user_id = b.buyer_id
#             WHERE u.user_id = %s;
#         """
#         cursor.execute(query, (buyer_id,))
#         return cursor.fetchone()
#     except Exception as e:
#         print(f"Error fetching buyer profile for buyer_id {buyer_id}: {e}")
#         return None
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# # --- ADD THE TWO FUNCTIONS BELOW ---

# def update_buyer_profile(buyer_id, profile_data, image_path=None):
#     """Updates a buyer's general profile information in the users table."""
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."

#     try:
#         cursor = conn.cursor()
        
#         # Build the update query dynamically based on provided data
#         fields_to_update = []
#         values = []
        
#         if 'full_name' in profile_data and profile_data['full_name']:
#             fields_to_update.append("full_name = %s")
#             values.append(profile_data['full_name'])
        
#         if 'phone' in profile_data:
#             fields_to_update.append("phone = %s")
#             values.append(profile_data['phone'])
            
#         if image_path:
#             fields_to_update.append("profile_image = %s")
#             values.append(image_path)
            
#         if not fields_to_update:
#             return False, "No data provided to update."

#         sql = f"UPDATE users SET {', '.join(fields_to_update)} WHERE user_id = %s"
#         values.append(buyer_id)
        
#         cursor.execute(sql, tuple(values))
#         conn.commit()

#         return True, "Profile updated successfully."
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating buyer profile for ID {buyer_id}: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()


# def update_buyer_password(buyer_id, old_password, new_password):
#     """Updates a buyer's password after verifying the old one."""
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."

#     try:
#         cursor = conn.cursor(dictionary=True)
        
#         # 1. Fetch the current password hash
#         cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (buyer_id,))
#         user = cursor.fetchone()
#         if not user:
#             return False, "User not found."

#         # 2. Verify the old password
#         if not bcrypt.checkpw(old_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
#             return False, "Incorrect current password."

#         # 3. Hash the new password
#         new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

#         # 4. Update the database with the new hash
#         cursor.execute(
#             "UPDATE users SET password_hash = %s WHERE user_id = %s",
#             (new_hashed_password.decode('utf-8'), buyer_id)
#         )
#         conn.commit()

#         return True, "Password updated successfully."
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating password for user ID {buyer_id}: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()















# electronic_ecommerce/models/buyer_model.py

from .db import get_db_connection
import bcrypt

def get_buyer_dashboard_stats(buyer_id):
    """Fetches key statistics for a specific buyer's dashboard."""
    conn = get_db_connection()
    if not conn: 
        return {
            'total_orders': 0,
            'pending_orders': 0,
            'completed_orders': 0,
            'total_spent': 0.0
        }
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {}
        
        query = """
        SELECT 
            COUNT(order_id) as total_orders,
            SUM(CASE WHEN status IN ('pending', 'confirmed', 'processing', 'shipped') THEN 1 ELSE 0 END) as pending_orders,
            SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as completed_orders,
            SUM(CASE 
                WHEN status NOT IN ('cancelled', 'returned', 'refunded') 
                THEN total_amount 
                ELSE 0 
            END) as total_spent
        FROM orders 
        WHERE buyer_id = %s;
        """
        
        cursor.execute(query, (buyer_id,))
        result = cursor.fetchone()

        if result:
            stats['total_orders'] = result.get('total_orders') or 0
            stats['pending_orders'] = result.get('pending_orders') or 0
            stats['completed_orders'] = result.get('completed_orders') or 0
            stats['total_spent'] = float(result.get('total_spent')) if result.get('total_spent') else 0.0
        else:
             stats = { 'total_orders': 0, 'pending_orders': 0, 'completed_orders': 0, 'total_spent': 0.0 }
            
        return stats
    except Exception as e:
        print(f"Error fetching buyer dashboard stats for buyer_id {buyer_id}: {e}")
        return {}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_buyer_recent_orders(buyer_id, limit=5):
    """Fetches the most recent orders for a specific buyer."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                o.order_id, o.order_number, o.order_date, o.total_amount, o.status,
                o.seller_id,
                s.business_name AS seller_name,
                cr.status AS cancellation_status
            FROM orders o
            JOIN sellers s ON o.seller_id = s.seller_id
            LEFT JOIN cancellation_requests cr ON o.order_id = cr.order_id AND cr.status = 'pending'
            WHERE o.buyer_id = %s
            ORDER BY o.order_date DESC
            LIMIT %s;
        """
        cursor.execute(query, (buyer_id, limit))
        orders = cursor.fetchall()
        for order in orders:
            order['order_date'] = order['order_date'].strftime('%Y-%m-%d %H:%M')
            order['total_amount'] = float(order['total_amount'])
        return orders
    except Exception as e:
        print(f"Error fetching recent orders for buyer_id {buyer_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_buyer_order_history(buyer_id):
    """Fetches the entire order history for a specific buyer."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                o.order_id, o.order_number, o.order_date, o.total_amount, o.status,
                s.business_name as seller_name,
                GROUP_CONCAT(p.name SEPARATOR ', ') as products
            FROM orders o
            JOIN sellers s ON o.seller_id = s.seller_id
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.buyer_id = %s
            GROUP BY o.order_id, o.order_number, o.order_date, o.total_amount, o.status, s.business_name
            ORDER BY o.order_date DESC;
        """
        cursor.execute(query, (buyer_id,))
        orders = cursor.fetchall()
        for order in orders:
            order['order_date'] = order['order_date'].strftime('%Y-%m-%d')
            order['total_amount'] = float(order['total_amount'])
        return orders
    except Exception as e:
        print(f"Error fetching order history for buyer_id {buyer_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_buyer_profile(buyer_id):
    """Fetches the profile data for a buyer, including the profile_image."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                u.full_name, u.email, u.phone, u.profile_image,
                b.default_address, b.default_city, b.default_state, 
                b.default_zip_code, b.default_country, b.loyalty_points
            FROM users u
            LEFT JOIN buyers b ON u.user_id = b.buyer_id
            WHERE u.user_id = %s;
        """
        cursor.execute(query, (buyer_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching buyer profile for buyer_id {buyer_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_buyer_profile(buyer_id, profile_data, image_path=None):
    """
    Updates a buyer's profile info (name, phone, image).
    Returns a tuple: (success_boolean, message_string, old_image_path).
    """
    conn = get_db_connection()
    if not conn: return False, "Database connection failed.", None

    old_image_path = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        if image_path:
            cursor.execute("SELECT profile_image FROM users WHERE user_id = %s", (buyer_id,))
            result = cursor.fetchone()
            if result and result['profile_image']:
                old_image_path = result['profile_image']
        
        fields_to_update = []
        values = []
        
        if 'full_name' in profile_data and profile_data['full_name']:
            fields_to_update.append("full_name = %s")
            values.append(profile_data['full_name'])
        if 'phone' in profile_data:
            fields_to_update.append("phone = %s")
            values.append(profile_data['phone'])
        if image_path:
            fields_to_update.append("profile_image = %s")
            values.append(image_path)
            
        if not fields_to_update:
            return False, "No data provided to update.", None

        sql = f"UPDATE users SET {', '.join(fields_to_update)} WHERE user_id = %s"
        values.append(buyer_id)
        
        cursor_execute = conn.cursor()
        cursor_execute.execute(sql, tuple(values))
        conn.commit()

        return True, "Profile updated successfully.", old_image_path
    except Exception as e:
        conn.rollback()
        print(f"Error updating buyer profile for ID {buyer_id}: {e}")
        return False, "An internal error occurred.", None
    finally:
        if conn and conn.is_connected():
            if 'cursor' in locals() and cursor.is_open(): cursor.close()
            if 'cursor_execute' in locals() and cursor_execute.is_open(): cursor_execute.close()
            conn.close()

def update_buyer_password(buyer_id, old_password, new_password):
    """Updates a buyer's password after verifying the old one."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (buyer_id,))
        user = cursor.fetchone()
        if not user:
            return False, "User not found."

        if not bcrypt.checkpw(old_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return False, "Incorrect current password."

        new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        cursor_execute = conn.cursor()
        cursor_execute.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (new_hashed_password.decode('utf-8'), buyer_id)
        )
        conn.commit()

        return True, "Password updated successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error updating password for user ID {buyer_id}: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected():
            if 'cursor' in locals() and cursor.is_open(): cursor.close()
            if 'cursor_execute' in locals() and cursor_execute.is_open(): cursor_execute.close()
            conn.close()


def get_spending_by_category(buyer_id):
    """
    Fetches the buyer's total spending, grouped by product category.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                c.name AS category_name,
                SUM(oi.total_price) AS total_spent
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE o.buyer_id = %s AND o.status NOT IN ('cancelled', 'returned', 'refunded')
            GROUP BY c.name
            HAVING total_spent > 0
            ORDER BY total_spent DESC;
        """
        cursor.execute(query, (buyer_id,))
        data = cursor.fetchall()
        for row in data:
            row['total_spent'] = float(row['total_spent'])
        return data
    except Exception as e:
        print(f"Error fetching buyer spending by category for buyer {buyer_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_monthly_spending(buyer_id):
    """
    Fetches the buyer's total spending for each of the last 12 months.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                DATE_FORMAT(order_date, '%Y-%m') AS month,
                SUM(total_amount) AS total_spent
            FROM orders
            WHERE buyer_id = %s
              AND status NOT IN ('cancelled', 'returned', 'refunded')
              AND order_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY month
            ORDER BY month ASC;
        """
        cursor.execute(query, (buyer_id,))
        data = cursor.fetchall()
        for row in data:
            row['total_spent'] = float(row['total_spent'])
        return data
    except Exception as e:
        print(f"Error fetching buyer monthly spending for buyer {buyer_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- START: NEW FUNCTIONS FOR ADDITIONAL DASHBOARD CHARTS ---

def get_order_status_distribution(buyer_id):
    """
    Counts the number of orders per status for a specific buyer.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        # We group statuses like 'pending', 'confirmed', and 'processing' into a single "In Progress" category for a cleaner chart.
        query = """
            SELECT 
                CASE 
                    WHEN status IN ('pending', 'confirmed', 'processing') THEN 'In Progress'
                    WHEN status = 'shipped' THEN 'Shipped'
                    WHEN status = 'delivered' THEN 'Delivered'
                    ELSE 'Other'
                END AS status_group,
                COUNT(order_id) AS order_count
            FROM orders
            WHERE buyer_id = %s AND status NOT IN ('cancelled', 'returned', 'refunded')
            GROUP BY status_group;
        """
        cursor.execute(query, (buyer_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching order status distribution for buyer {buyer_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_top_brands_by_spending(buyer_id, limit=5):
    """
    Fetches the top 5 brands a buyer has spent the most money on.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                p.brand,
                SUM(oi.total_price) AS total_spent
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.buyer_id = %s 
              AND o.status NOT IN ('cancelled', 'returned', 'refunded')
              AND p.brand IS NOT NULL
            GROUP BY p.brand
            ORDER BY total_spent DESC
            LIMIT %s;
        """
        cursor.execute(query, (buyer_id, limit))
        data = cursor.fetchall()
        for row in data:
            row['total_spent'] = float(row['total_spent'])
        return data
    except Exception as e:
        print(f"Error fetching top brands by spending for buyer {buyer_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- END: NEW FUNCTIONS ---