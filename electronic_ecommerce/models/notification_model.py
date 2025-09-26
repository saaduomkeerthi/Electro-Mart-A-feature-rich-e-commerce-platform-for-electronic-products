# electronic_ecommerce/models/notification_model.py

from .db import get_db_connection

def create_notification(user_id, message, link_url=None):
    """
    Creates a new notification for a specific user.
    """
    conn = get_db_connection()
    if not conn:
        print("ERROR: Could not create notification, database connection failed.")
        return False
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO notifications (user_id, message, link_url) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, message, link_url))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating notification for user_id {user_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_unread_notifications(user_id):
    """
    Fetches all unread notifications for a specific user.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        # Fetch the most recent 10 unread notifications
        sql = """
            SELECT notification_id, message, link_url, created_at 
            FROM notifications 
            WHERE user_id = %s AND is_read = FALSE 
            ORDER BY created_at DESC
            LIMIT 10;
        """
        cursor.execute(sql, (user_id,))
        notifications = cursor.fetchall()
        for notif in notifications:
            # Format the timestamp for better display on the frontend
            notif['created_at'] = notif['created_at'].strftime('%b %d, %H:%M')
        return notifications
    except Exception as e:
        print(f"Error fetching unread notifications for user_id {user_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def mark_notifications_as_read(user_id, notification_ids):
    """
    Marks a list of notifications as read for a specific user.
    """
    if not notification_ids:
        return True # Nothing to mark, so it's a success
        
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        # Using a placeholder string like "%s, %s, %s" for security and efficiency
        placeholders = ', '.join(['%s'] * len(notification_ids))
        sql = f"UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND notification_id IN ({placeholders})"
        
        # The parameters must be a single tuple
        params = (user_id,) + tuple(notification_ids)
        cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error marking notifications as read for user_id {user_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_unread_notification_count(user_id):
    """
    Efficiently counts the number of unread notifications for a user.
    """
    conn = get_db_connection()
    if not conn: return 0
    try:
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT COUNT(notification_id) as unread_count FROM notifications WHERE user_id = %s AND is_read = FALSE"
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        return result['unread_count'] if result else 0
    except Exception as e:
        print(f"Error counting unread notifications for user_id {user_id}: {e}")
        return 0
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()