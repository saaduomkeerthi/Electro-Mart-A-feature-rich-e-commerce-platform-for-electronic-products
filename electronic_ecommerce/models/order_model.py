import traceback
import json
import decimal
import math
from flask import session
from .db import get_db_connection

def create_order_from_cart(buyer_id, address_id, payment_method):
    """
    Creates one or more orders from the buyer's cart, now with discount support.
    It reads coupon details from the session, applies the discount, and updates
    the discount usage count in a single database transaction.
    """
    conn = get_db_connection()
    if not conn: 
        return False, "Database connection failed.", None

    try:
        cursor = conn.cursor(dictionary=True)
        
        # --- START TRANSACTION ---
        conn.start_transaction()

        # 1. Fetch cart items AND verify stock levels
        cursor.execute("""
            SELECT c.product_id, c.quantity, p.price, p.seller_id, p.name, p.brand, p.model, p.stock_quantity 
            FROM cart c 
            JOIN products p ON c.product_id = p.product_id 
            WHERE c.buyer_id = %s
        """, (buyer_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            conn.rollback()
            return False, "Your cart is empty.", None
            
        # Verify stock for every item before proceeding
        for item in cart_items:
            if item['quantity'] > item['stock_quantity']:
                conn.rollback()
                return False, f"Not enough stock for {item['name']}. Only {item['stock_quantity']} available.", None

        # 2. Get shipping address
        cursor.execute("SELECT * FROM addresses WHERE address_id = %s AND buyer_id = %s", (address_id, buyer_id))
        address = cursor.fetchone()
        if not address:
            conn.rollback()
            return False, "Invalid shipping address selected.", None
        shipping_address_str = f"{address['recipient_name']}, {address['address_line1']}, {address['city']}, {address['state']} {address['zip_code']}, {address['country']}"

        # 3. Group items by seller
        orders_by_seller = {}
        for item in cart_items:
            seller_id = item['seller_id']
            if seller_id not in orders_by_seller:
                orders_by_seller[seller_id] = []
            orders_by_seller[seller_id].append(item)
            
        # 4. Get applied coupon from session
        applied_coupon = session.get('applied_coupon')
        total_discount_amount = 0
        discount_id_to_log = None
        if applied_coupon:
            total_discount_amount = applied_coupon.get('discount_amount', 0)
            discount_id_to_log = applied_coupon.get('discount_id')

        # Calculate subtotal across all sellers to prorate the discount
        grand_subtotal = sum(item['price'] * item['quantity'] for item in cart_items)

        order_numbers = []
        for seller_id, items in orders_by_seller.items():
            # Calculate this seller's portion of the order
            seller_subtotal = sum(item['price'] * item['quantity'] for item in items)

            # Prorate the discount for this specific seller's order
            seller_discount = 0
            if grand_subtotal > 0 and total_discount_amount > 0:
                seller_discount = (seller_subtotal / grand_subtotal) * total_discount_amount
            
            # Calculate final total for this order
            total_amount = seller_subtotal - seller_discount
            
            # Generate a unique order number
            cursor.execute("SELECT generate_order_number() AS order_num")
            order_number = cursor.fetchone()['order_num']
            order_numbers.append(order_number)

            # Insert order with new discount fields
            order_sql = """
                INSERT INTO orders (order_number, buyer_id, seller_id, total_amount, subtotal_amount, 
                                    discount_amount, discount_id, status, shipping_address, billing_address, 
                                    payment_method, payment_status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'confirmed', %s, %s, %s, 'completed')
            """
            order_values = (
                order_number, buyer_id, seller_id, total_amount, seller_subtotal, 
                seller_discount, discount_id_to_log, shipping_address_str, 
                shipping_address_str, payment_method
            )
            cursor.execute(order_sql, order_values)
            order_id = cursor.lastrowid

            # Insert order items and update stock
            order_item_sql = "INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price, product_data) VALUES (%s, %s, %s, %s, %s, %s)"
            update_stock_sql = "UPDATE products SET stock_quantity = stock_quantity - %s WHERE product_id = %s"
            
            for item in items:
                product_snapshot = json.dumps({'name': item['name'], 'brand': item['brand'], 'model': item['model']})
                item_values = (order_id, item['product_id'], item['quantity'], item['price'], item['price'] * item['quantity'], product_snapshot)
                cursor.execute(order_item_sql, item_values)
                cursor.execute(update_stock_sql, (item['quantity'], item['product_id']))

        # Increment coupon usage count if a coupon was used
        if discount_id_to_log:
            cursor.execute("UPDATE discounts SET times_used = times_used + 1 WHERE discount_id = %s", (discount_id_to_log,))

        # 5. Clear the cart and the session coupon
        cursor.execute("DELETE FROM cart WHERE buyer_id = %s", (buyer_id,))
        session.pop('applied_coupon', None)
        
        # --- COMMIT TRANSACTION ---
        conn.commit()
        session.modified = True
        
        return True, "Order placed successfully!", order_numbers

    except Exception as e:
        conn.rollback()
        if 'applied_coupon' in session:
            session.pop('applied_coupon', None)
            session.modified = True
        print(f"--- ERROR IN create_order_from_cart ---: {e}")
        traceback.print_exc()
        return False, "An internal error occurred while placing your order.", None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_order_details_for_buyer(buyer_id, order_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        order_query = "SELECT o.*, s.business_name, cr.status as cancellation_status FROM orders o JOIN sellers s ON o.seller_id = s.seller_id LEFT JOIN cancellation_requests cr ON o.order_id = cr.order_id WHERE o.order_id = %s AND o.buyer_id = %s"
        cursor.execute(order_query, (order_id, buyer_id))
        order_details = cursor.fetchone()
        if not order_details:
            return None
        items_query = "SELECT oi.quantity, oi.unit_price, oi.total_price, p.product_id, p.name, (SELECT image_url FROM product_images WHERE product_id = p.product_id AND is_primary = TRUE LIMIT 1) as image_url FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id = %s"
        cursor.execute(items_query, (order_id,))
        order_items = cursor.fetchall()
        for key, value in order_details.items():
            if isinstance(value, decimal.Decimal):
                order_details[key] = float(value)
        for item in order_items:
             for key, value in item.items():
                if isinstance(value, decimal.Decimal):
                    item[key] = float(value)
        return {"details": order_details, "items": order_items}
    except Exception as e:
        print(f"Error fetching order details for order {order_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def create_cancellation_request(order_id, buyer_id, seller_id, reason, comments):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT request_id FROM cancellation_requests WHERE order_id = %s", (order_id,))
        if cursor.fetchone():
            return False, "A cancellation request for this order already exists."
        cursor.execute("SELECT status FROM orders WHERE order_id = %s AND buyer_id = %s", (order_id, buyer_id))
        order_status = cursor.fetchone()
        if not order_status or order_status[0] not in ['confirmed', 'processing']:
            return False, "This order can no longer be cancelled."
        sql = "INSERT INTO cancellation_requests (order_id, buyer_id, seller_id, reason, comments) VALUES (%s, %s, %s, %s, %s)"
        values = (order_id, buyer_id, seller_id, reason, comments)
        cursor.execute(sql, values)
        conn.commit()
        return True, "Cancellation request submitted successfully. The seller has been notified."
    except Exception as e:
        conn.rollback()
        print(f"--- ERROR in create_cancellation_request for order {order_id}: {e} ---")
        return False, "An internal error occurred while submitting your request."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_cancellation_request_details(request_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT cr.buyer_id, cr.seller_id, cr.order_id, o.order_number FROM cancellation_requests cr JOIN orders o ON cr.order_id = o.order_id WHERE cr.request_id = %s"
        cursor.execute(query, (request_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching cancellation request details for ID {request_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_paginated_orders_for_buyer(buyer_id, status=None, search_term=None, page=1, per_page=10):
    """
    Fetches a paginated, searchable, and filterable list of orders for a specific buyer,
    including a list of product images for each order.
    """
    conn = get_db_connection()
    if not conn:
        return {'orders': [], 'total_count': 0, 'total_pages': 0}

    try:
        cursor = conn.cursor(dictionary=True)
        # Note: DISTINCT is important in the base query to avoid counting an order multiple times if it has multiple items.
        base_query = "FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id"
        where_clauses = ["o.buyer_id = %s"]
        params = [buyer_id]

        if status:
            where_clauses.append("o.status = %s")
            params.append(status)
        
        if search_term:
            where_clauses.append("(p.name LIKE %s OR o.order_number LIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])

        where_sql = " WHERE " + " AND ".join(where_clauses)
        
        count_query = f"SELECT COUNT(DISTINCT o.order_id) AS total_count {base_query} {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        
        query = f"""
            SELECT
                o.order_id, o.order_number, o.order_date, o.total_amount, o.status,
                GROUP_CONCAT(p.name SEPARATOR ', ') as products,
                GROUP_CONCAT(DISTINCT p_img.primary_image SEPARATOR '||') as product_images
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN (
                SELECT product_id, (SELECT image_url FROM product_images WHERE product_id = p.product_id AND is_primary = TRUE LIMIT 1) as primary_image
                FROM products p
            ) AS p_img ON oi.product_id = p_img.product_id
            {where_sql}
            GROUP BY o.order_id
            ORDER BY o.order_date DESC
            LIMIT %s OFFSET %s
        """
        
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        cursor.execute(query, tuple(params))
        orders = cursor.fetchall()

        for order in orders:
            order['total_amount'] = float(order['total_amount'])
            if order['product_images']:
                order['product_images'] = [img for img in order['product_images'].split('||') if img]
            else:
                order['product_images'] = []
        
        return {
            'orders': orders,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    except Exception as e:
        print(f"Error fetching paginated orders for buyer {buyer_id}: {e}")
        return {'orders': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()