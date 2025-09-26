# electronic_ecommerce/models/cart_model.py

from .db import get_db_connection

def add_to_cart(buyer_id, product_id, quantity):
    """Adds a product to the cart or updates the quantity if it already exists."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        # Check if the product is already in the cart
        cursor.execute(
            "SELECT quantity FROM cart WHERE buyer_id = %s AND product_id = %s",
            (buyer_id, product_id)
        )
        existing_item = cursor.fetchone()

        if existing_item:
            # If item exists, update its quantity
            new_quantity = existing_item[0] + quantity
            cursor.execute(
                "UPDATE cart SET quantity = %s WHERE buyer_id = %s AND product_id = %s",
                (new_quantity, buyer_id, product_id)
            )
        else:
            # If item does not exist, insert it
            cursor.execute(
                "SELECT price FROM products WHERE product_id = %s", (product_id,)
            )
            product = cursor.fetchone()
            if not product:
                return False, "Product not found."
            
            cursor.execute(
                "INSERT INTO cart (buyer_id, product_id, quantity, added_price) VALUES (%s, %s, %s, %s)",
                (buyer_id, product_id, quantity, product[0])
            )
        
        conn.commit()
        return True, "Item added to cart successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error adding to cart: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_cart_items(buyer_id):
    """Retrieves all items in a buyer's cart with product details."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                c.cart_id,
                c.product_id,
                c.quantity,
                p.name,
                p.price,
                p.stock_quantity,
                (p.price * c.quantity) AS subtotal,
                (SELECT image_url FROM product_images WHERE product_id = p.product_id AND is_primary = TRUE LIMIT 1) as image_url
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.buyer_id = %s
            ORDER BY c.created_at DESC;
        """
        cursor.execute(query, (buyer_id,))
        items = cursor.fetchall()
        for item in items:
            item['price'] = float(item['price'])
            item['subtotal'] = float(item['subtotal'])
        return items
    except Exception as e:
        print(f"Error getting cart items: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_cart_item_quantity(buyer_id, product_id, quantity):
    """Updates the quantity of a specific item in the cart."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE cart SET quantity = %s WHERE buyer_id = %s AND product_id = %s",
            (quantity, buyer_id, product_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating cart quantity: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def remove_from_cart(buyer_id, product_id):
    """Removes an item completely from the buyer's cart."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM cart WHERE buyer_id = %s AND product_id = %s",
            (buyer_id, product_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error removing from cart: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_cart_item_count(buyer_id):
    """Gets the total number of items in the cart."""
    conn = get_db_connection()
    if not conn: return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(quantity) FROM cart WHERE buyer_id = %s", (buyer_id,))
        count = cursor.fetchone()[0]
        return int(count) if count else 0
    except Exception as e:
        print(f"Error getting cart count: {e}")
        return 0
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- ADD THIS NEW FUNCTION AT THE END OF THE FILE ---
def get_cart_status_for_products(buyer_id, product_ids):
    """
    Checks which of a list of product IDs are in the buyer's cart.
    Returns a dictionary mapping product_id to a boolean (True if in cart).
    """
    if not product_ids:
        return {}
        
    conn = get_db_connection()
    if not conn: return {pid: False for pid in product_ids}
    
    try:
        cursor = conn.cursor()
        # Create a string of placeholders like "%s, %s, %s"
        placeholders = ', '.join(['%s'] * len(product_ids))
        query = f"SELECT product_id FROM cart WHERE buyer_id = %s AND product_id IN ({placeholders})"
        
        params = [buyer_id] + product_ids
        cursor.execute(query, params)
        
        # Create a set of product IDs that are in the cart for fast lookups
        in_cart_ids = {row[0] for row in cursor.fetchall()}
        
        # Build the final status dictionary
        status = {pid: (pid in in_cart_ids) for pid in product_ids}
        return status
    except Exception as e:
        print(f"Error getting cart status: {e}")
        return {pid: False for pid in product_ids}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()            


# electronic_ecommerce/models/cart_model.py

# ... (all your existing functions in this file) ...

# --- ADD THIS NEW FUNCTION AT THE END OF THE FILE ---

def validate_and_get_coupon(coupon_code, cart_total):
    """
    Validates a coupon code against the database and cart total.
    Returns the coupon details if valid, otherwise returns an error message.
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed."

    try:
        cursor = conn.cursor(dictionary=True)
        # Fetch the coupon, ensuring it's active and within its valid date range
        query = """
            SELECT * FROM discounts 
            WHERE code = %s AND is_active = TRUE
            AND (start_date IS NULL OR start_date <= CURRENT_TIMESTAMP)
            AND (end_date IS NULL OR end_date >= CURRENT_TIMESTAMP)
        """
        cursor.execute(query, (coupon_code.upper(),))
        coupon = cursor.fetchone()

        if not coupon:
            return None, "Invalid or expired coupon code."

        # Check usage limit
        if coupon['times_used'] >= coupon['usage_limit']:
            return None, "This coupon has reached its usage limit."

        # Check minimum purchase amount
        if cart_total < coupon['min_purchase_amount']:
            min_amount_str = f"${float(coupon['min_purchase_amount']):.2f}"
            return None, f"A minimum purchase of {min_amount_str} is required to use this coupon."
        
        # All checks passed, return the valid coupon details
        return coupon, "Coupon applied successfully!"

    except Exception as e:
        print(f"Error validating coupon '{coupon_code}': {e}")
        return None, "An internal error occurred while validating the coupon."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()            