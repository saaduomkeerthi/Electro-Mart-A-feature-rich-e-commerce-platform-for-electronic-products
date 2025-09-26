# electronic_ecommerce/models/wishlist_model.py

from .db import get_db_connection

def add_to_wishlist(buyer_id, product_id):
    """Adds a product to the buyer's wishlist if it's not already there."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        # The UNIQUE KEY on (buyer_id, product_id) prevents duplicates.
        # We can use INSERT IGNORE to safely handle attempts to add an existing item.
        sql = "INSERT IGNORE INTO wishlist (buyer_id, product_id) VALUES (%s, %s)"
        cursor.execute(sql, (buyer_id, product_id))
        conn.commit()
        # Check if a row was actually inserted
        if cursor.rowcount > 0:
            return True, "Product added to your wishlist."
        else:
            return False, "Product is already in your wishlist."
    except Exception as e:
        conn.rollback()
        print(f"Error adding to wishlist: {e}")
        return False, "An error occurred."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def remove_from_wishlist(buyer_id, product_id):
    """Removes a product from the buyer's wishlist."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM wishlist WHERE buyer_id = %s AND product_id = %s"
        cursor.execute(sql, (buyer_id, product_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Product removed from your wishlist."
        else:
            return False, "Product not found in your wishlist."
    except Exception as e:
        conn.rollback()
        print(f"Error removing from wishlist: {e}")
        return False, "An error occurred."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_wishlist_items(buyer_id):
    """Retrieves all items in a buyer's wishlist with product details."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                w.wishlist_id,
                p.product_id,
                p.name,
                p.price,
                p.stock_quantity,
                (SELECT image_url FROM product_images WHERE product_id = p.product_id AND is_primary = TRUE LIMIT 1) as image_url
            FROM wishlist w
            JOIN products p ON w.product_id = p.product_id
            WHERE w.buyer_id = %s AND p.is_active = TRUE
            ORDER BY w.added_date DESC;
        """
        cursor.execute(query, (buyer_id,))
        items = cursor.fetchall()
        for item in items:
            item['price'] = float(item['price'])
        return items
    except Exception as e:
        print(f"Error getting wishlist items: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_wishlist_status_for_products(buyer_id, product_ids):
    """Checks which of a list of product IDs are in the buyer's wishlist."""
    if not product_ids:
        return {}
    conn = get_db_connection()
    if not conn: return {}
    try:
        cursor = conn.cursor()
        # Create a string of placeholders like "%s, %s, %s"
        placeholders = ', '.join(['%s'] * len(product_ids))
        query = f"SELECT product_id FROM wishlist WHERE buyer_id = %s AND product_id IN ({placeholders})"
        
        params = [buyer_id] + product_ids
        cursor.execute(query, params)
        
        wishlist_product_ids = {row[0] for row in cursor.fetchall()}
        
        status = {pid: (pid in wishlist_product_ids) for pid in product_ids}
        return status
    except Exception as e:
        print(f"Error getting wishlist status: {e}")
        return {}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()