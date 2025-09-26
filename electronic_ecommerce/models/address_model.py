# electronic_ecommerce/models/address_model.py

from .db import get_db_connection

def get_buyer_addresses(buyer_id):
    """Fetches all saved addresses for a specific buyer."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM addresses WHERE buyer_id = %s ORDER BY is_default DESC, created_at DESC"
        cursor.execute(query, (buyer_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching addresses for buyer {buyer_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def add_new_address(buyer_id, address_data):
    """Adds a new address for a buyer and can set it as default."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        conn.start_transaction()

        is_default = address_data.get('is_default', False)
        # If this new address is set as default, unset any other default addresses first.
        if is_default:
            cursor.execute("UPDATE addresses SET is_default = FALSE WHERE buyer_id = %s", (buyer_id,))

        sql = """
            INSERT INTO addresses (buyer_id, address_type, label, recipient_name, 
                                 address_line1, address_line2, city, state, zip_code, 
                                 country, phone, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            buyer_id,
            address_data.get('address_type', 'shipping'),
            address_data.get('label'),
            address_data.get('recipient_name'),
            address_data.get('address_line1'),
            address_data.get('address_line2'),
            address_data.get('city'),
            address_data.get('state'),
            address_data.get('zip_code'),
            address_data.get('country'),
            address_data.get('phone'),
            is_default
        )
        cursor.execute(sql, values)
        conn.commit()
        return True, "Address added successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error adding new address: {e}")
        return False, "An internal error occurred while saving the address."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def delete_address(buyer_id, address_id):
    """Deletes a specific address belonging to a buyer."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        # Ensure the address belongs to the buyer before deleting
        cursor.execute("DELETE FROM addresses WHERE address_id = %s AND buyer_id = %s", (address_id, buyer_id))
        conn.commit()
        return cursor.rowcount > 0 # Returns True if a row was deleted
    except Exception as e:
        conn.rollback()
        print(f"Error deleting address {address_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()