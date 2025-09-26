import decimal 
import json
from .db import get_db_connection
import mysql.connector
import math

def get_seller_dashboard_stats(seller_id):
    """
    Fetches key statistics for a specific seller's dashboard.
    """
    conn = get_db_connection()
    if not conn:
        return {
            'total_products': 0, 'pending_products': 0, 'active_listings': 0,
            'total_sales': 0.0, 'orders_to_process': 0, 'pending_cancellations': 0
        }
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT
            (SELECT COUNT(p.product_id) FROM products p WHERE p.seller_id = %s) AS total_products,
            (SELECT SUM(CASE WHEN p.is_approved = FALSE THEN 1 ELSE 0 END) FROM products p WHERE p.seller_id = %s) AS pending_products,
            (SELECT SUM(CASE WHEN p.is_approved = TRUE AND p.is_active = TRUE THEN 1 ELSE 0 END) FROM products p WHERE p.seller_id = %s) AS active_listings,
            (SELECT SUM(o.total_amount) FROM orders o WHERE o.seller_id = %s AND o.status IN ('processing', 'shipped', 'delivered')) AS total_sales,
            (SELECT COUNT(o.order_id) FROM orders o WHERE o.seller_id = %s AND o.status IN ('confirmed', 'processing')) AS orders_to_process,
            (SELECT COUNT(cr.request_id) FROM cancellation_requests cr WHERE cr.seller_id = %s AND cr.status = 'pending') AS pending_cancellations;
        """
        cursor.execute(query, (seller_id, seller_id, seller_id, seller_id, seller_id, seller_id))
        stats = cursor.fetchone()

        if stats:
            stats['total_sales'] = float(stats['total_sales']) if stats['total_sales'] else 0.0
            for key in ['total_products', 'pending_products', 'active_listings', 'orders_to_process', 'pending_cancellations']:
                if stats[key] is None:
                    stats[key] = 0
            return stats
        else: # Should not happen, but as a fallback
            return {'total_products': 0, 'pending_products': 0, 'active_listings': 0, 'total_sales': 0.0, 'orders_to_process': 0, 'pending_cancellations': 0}

    except mysql.connector.Error as e:
        print(f"Database error fetching seller stats for seller_id {seller_id}: {e}")
        return {'total_products': 0, 'pending_products': 0, 'active_listings': 0, 'total_sales': 0.0, 'orders_to_process': 0, 'pending_cancellations': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_seller_product_performance(seller_id, limit=5):
    """Fetches the best-selling products for a specific seller."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.name, SUM(oi.quantity) as total_sold
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.seller_id = %s AND o.status IN ('processing', 'shipped', 'delivered')
            GROUP BY p.product_id, p.name
            ORDER BY total_sold DESC
            LIMIT 5;
        """
        cursor.execute(query, (seller_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching product performance for seller_id {seller_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_seller_sales_over_time(seller_id):
    """Fetches monthly sales data for a specific seller for a line chart."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                DATE_FORMAT(order_date, '%Y-%m') AS month, 
                SUM(total_amount) AS monthly_sales
            FROM orders 
            WHERE seller_id = %s AND status IN ('processing', 'shipped', 'delivered')
            GROUP BY month 
            ORDER BY month ASC
            LIMIT 12;
        """
        cursor.execute(query, (seller_id,))
        sales_data = cursor.fetchall()
        for row in sales_data:
            row['monthly_sales'] = float(row['monthly_sales'])
        return sales_data
    except Exception as e:
        print(f"Error fetching sales over time for seller_id {seller_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_all_categories_structured():
    """Fetches all ACTIVE categories and structures them into a two-level hierarchy."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        main_categories_query = "SELECT category_id, name FROM categories WHERE parent_category_id IS NULL AND is_active = TRUE ORDER BY name;"
        cursor.execute(main_categories_query)
        structured_list = cursor.fetchall()
        main_cat_map = {cat['category_id']: cat for cat in structured_list}
        for cat in structured_list:
            cat['subcategories'] = []
        sub_categories_query = "SELECT category_id, name, parent_category_id FROM categories WHERE parent_category_id IS NOT NULL AND is_active = TRUE ORDER BY name;"
        cursor.execute(sub_categories_query)
        sub_categories = cursor.fetchall()
        for sub_cat in sub_categories:
            parent_id = sub_cat['parent_category_id']
            if parent_id in main_cat_map:
                main_cat_map[parent_id]['subcategories'].append(sub_cat)
        return structured_list
    except Exception as e:
        print(f"Error fetching structured categories: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def add_new_product(seller_id, product_data, image_filenames, specs_data):
    """Adds a new product, its images, and specifications in a single transaction."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        product_sql = """
            INSERT INTO products (seller_id, name, description, short_description, category_id, brand, model, sku,
                                  price, compare_price, stock_quantity, video_url, is_active, is_approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, FALSE)
        """
        product_values = (seller_id, product_data.get('name'), product_data.get('description'), product_data.get('short_description'), product_data.get('category_id'), product_data.get('brand'), product_data.get('model'), product_data.get('sku'), product_data.get('price'), product_data.get('compare_price') or None, product_data.get('stock_quantity'), product_data.get('video_url') or None)
        cursor.execute(product_sql, product_values)
        product_id = cursor.lastrowid
        if image_filenames:
            image_sql = "INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)"
            image_values = [(product_id, filename, i == 0) for i, filename in enumerate(image_filenames)]
            cursor.executemany(image_sql, image_values)
        if specs_data:
            spec_sql = "INSERT INTO product_specifications (product_id, spec_name, spec_value) VALUES (%s, %s, %s)"
            spec_values = [(product_id, spec.get('name'), spec.get('value')) for spec in specs_data]
            cursor.executemany(spec_sql, spec_values)
        conn.commit()
        return True, "Product added successfully and is pending admin approval."
    except Exception as e:
        conn.rollback()
        print(f"Error adding new product for seller {seller_id}: {e}")
        if 'Duplicate entry' in str(e) and 'for key \'products.sku\'' in str(e):
             return False, "This SKU is already in use. Please choose a unique SKU."
        return False, "An internal error occurred while adding the product."
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_seller_product_categories(seller_id):
    """Fetches a simple list of main categories that the seller has products in."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT DISTINCT 
                COALESCE(parent_cat.category_id, c.category_id) AS category_id,
                COALESCE(parent_cat.name, c.name) AS name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN categories parent_cat ON c.parent_category_id = parent_cat.category_id
            WHERE p.seller_id = %s
            ORDER BY name;
        """
        cursor.execute(query, (seller_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching seller product categories for seller {seller_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_paginated_seller_products(seller_id, category_id=None, search_term=None, page=1, per_page=10):
    """
    Fetches a paginated, searchable, and filterable list of products for a specific seller.
    """
    conn = get_db_connection()
    if not conn:
        return {'products': [], 'total_count': 0, 'total_pages': 0}
    try:
        cursor = conn.cursor(dictionary=True)
        base_query = "FROM products p LEFT JOIN categories c ON p.category_id = c.category_id"
        where_clauses = ["p.seller_id = %s"]
        params = [seller_id]
        if search_term:
            where_clauses.append("(p.name LIKE %s OR p.sku LIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        if category_id:
            where_clauses.append("(c.category_id = %s OR c.parent_category_id = %s)")
            params.extend([category_id, category_id])
        where_sql = " WHERE " + " AND ".join(where_clauses)
        count_query = f"SELECT COUNT(p.product_id) AS total_count {base_query} {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        query = f"""
            SELECT p.product_id, p.name, p.sku, p.price, p.stock_quantity, p.is_active, p.is_approved,
                   (SELECT image_url FROM product_images WHERE product_id = p.product_id AND is_primary = TRUE LIMIT 1) as primary_image
            {base_query}
            {where_sql}
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        cursor.execute(query, tuple(params))
        products = cursor.fetchall()
        return {'products': products, 'total_count': total_count, 'total_pages': total_pages, 'current_page': page}
    except Exception as e:
        print(f"Error fetching paginated products for seller {seller_id}: {e}")
        return {'products': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_seller_products(seller_id):
    """DEPRECATED: Use get_paginated_seller_products. Fetches a list of all products for a given seller."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.product_id, p.name, p.sku, p.price, p.stock_quantity, p.is_active, p.is_approved,
                   (SELECT image_url FROM product_images WHERE product_id = p.product_id AND is_primary = TRUE LIMIT 1) as primary_image
            FROM products p WHERE p.seller_id = %s ORDER BY p.created_at DESC;
        """
        cursor.execute(query, (seller_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching products for seller_id {seller_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_product_for_editing(seller_id, product_id):
    """Fetches all product details, ensuring it belongs to the seller."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        product_query = """
            SELECT p.*, c.parent_category_id FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.product_id = %s AND p.seller_id = %s;
        """
        cursor.execute(product_query, (product_id, seller_id))
        product = cursor.fetchone()
        if not product: return None
        cursor.execute("SELECT image_id, image_url FROM product_images WHERE product_id = %s ORDER BY is_primary DESC", (product_id,))
        images = cursor.fetchall()
        cursor.execute("SELECT spec_id, spec_name, spec_value FROM product_specifications WHERE product_id = %s", (product_id,))
        specifications = cursor.fetchall()
        return {"product": product, "images": images, "specifications": specifications}
    except Exception as e:
        print(f"Error fetching product for editing (product_id {product_id}): {e}")
        return None
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def update_product(seller_id, product_id, product_data, new_images, images_to_delete, specs_data):
    """Updates a product, its images, and specifications in a single transaction."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("SELECT seller_id FROM products WHERE product_id = %s", (product_id,))
        product_owner = cursor.fetchone()
        if not product_owner or product_owner[0] != seller_id:
            conn.rollback()
            return False, "Permission denied. You do not own this product."
        product_sql = """
            UPDATE products SET name = %s, description = %s, short_description = %s, category_id = %s,
                brand = %s, model = %s, sku = %s, price = %s, compare_price = %s,
                stock_quantity = %s, video_url = %s, is_approved = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = %s AND seller_id = %s;
        """
        product_values = (product_data.get('name'), product_data.get('description'), product_data.get('short_description'), product_data.get('category_id'), product_data.get('brand'), product_data.get('model'), product_data.get('sku'), product_data.get('price'), product_data.get('compare_price') or None, product_data.get('stock_quantity'), product_data.get('video_url') or None, product_id, seller_id)
        cursor.execute(product_sql, product_values)
        if images_to_delete:
            safe_image_ids = [int(img_id) for img_id in images_to_delete]
            delete_sql = "DELETE FROM product_images WHERE image_id IN ({}) AND product_id = %s".format(','.join(['%s'] * len(safe_image_ids)))
            cursor.execute(delete_sql, safe_image_ids + [product_id])
        if new_images:
            cursor.execute("SELECT 1 FROM product_images WHERE product_id = %s AND is_primary = TRUE", (product_id,))
            primary_exists = cursor.fetchone()
            image_sql = "INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)"
            cursor.executemany(image_sql, [(product_id, filename, not primary_exists and i == 0) for i, filename in enumerate(new_images)])
        cursor.execute("DELETE FROM product_specifications WHERE product_id = %s", (product_id,))
        if specs_data:
            spec_sql = "INSERT INTO product_specifications (product_id, spec_name, spec_value) VALUES (%s, %s, %s)"
            cursor.executemany(spec_sql, [(product_id, spec.get('name'), spec.get('value')) for spec in specs_data])
        conn.commit()
        return True, "Product updated successfully. It is now pending re-approval from an admin."
    except Exception as e:
        conn.rollback()
        print(f"Error updating product {product_id}: {e}")
        if 'Duplicate entry' in str(e) and 'for key \'products.sku\'' in str(e):
             return False, "This SKU is already in use by another product."
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def delete_product(seller_id, product_id):
    """Deletes a product, verifying ownership and returning image URLs for cleanup."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed.", []
    try:
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()
        cursor.execute("SELECT image_url FROM product_images WHERE product_id = %s AND EXISTS (SELECT 1 FROM products WHERE product_id = %s AND seller_id = %s)", (product_id, product_id, seller_id))
        images_to_delete = [row['image_url'] for row in cursor.fetchall()]
        delete_sql = "DELETE FROM products WHERE product_id = %s AND seller_id = %s"
        cursor.execute(delete_sql, (product_id, seller_id))
        if cursor.rowcount == 0:
            conn.rollback()
            return False, "Product not found or you do not have permission to delete it.", []
        conn.commit()
        return True, "Product deleted successfully.", images_to_delete
    except Exception as e:
        conn.rollback()
        print(f"Error deleting product {product_id}: {e}")
        return False, "An internal error occurred.", []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_seller_profile(seller_id):
    """Fetches the combined profile data for a seller from users and sellers tables."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT u.full_name, u.email, u.phone, u.profile_image, s.business_name, s.business_email, 
                   s.business_phone, s.business_address, s.business_city, s.business_state, 
                   s.business_zip_code, s.business_country, s.tax_id, s.business_description, 
                   s.website_url, s.logo_url
            FROM users u JOIN sellers s ON u.user_id = s.seller_id
            WHERE u.user_id = %s;
        """
        cursor.execute(query, (seller_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching seller profile for seller_id {seller_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def update_seller_profile(seller_id, data, logo_path=None, profile_image_path=None):
    """Updates seller profile information, including logo and personal profile image."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed.", None
    old_profile_image = None
    try:
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()
        if profile_image_path:
            cursor.execute("SELECT profile_image FROM users WHERE user_id = %s", (seller_id,))
            result = cursor.fetchone()
            if result and result['profile_image']:
                old_profile_image = result['profile_image']
        user_fields_to_update = ["full_name = %s", "phone = %s"]
        user_values = [data.get('full_name'), data.get('phone')]
        if profile_image_path:
            user_fields_to_update.append("profile_image = %s")
            user_values.append(profile_image_path)
        user_sql = f"UPDATE users SET {', '.join(user_fields_to_update)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s"
        user_values.append(seller_id)
        cursor_execute = conn.cursor()
        cursor_execute.execute(user_sql, tuple(user_values))
        seller_sql = """
            UPDATE sellers SET business_name = %s, business_phone = %s, business_address = %s,
                business_city = %s, business_state = %s, business_zip_code = %s, business_country = %s,
                tax_id = %s, business_description = %s, website_url = %s, updated_at = CURRENT_TIMESTAMP
            WHERE seller_id = %s;
        """
        seller_values = (data.get('business_name'), data.get('business_phone'), data.get('business_address'), data.get('business_city'), data.get('business_state'), data.get('business_zip_code'), data.get('business_country'), data.get('tax_id'), data.get('business_description'), data.get('website_url'), seller_id)
        cursor_execute.execute(seller_sql, seller_values)
        if logo_path:
            cursor_execute.execute("UPDATE sellers SET logo_url = %s WHERE seller_id = %s", (logo_path, seller_id))
        conn.commit()
        return True, "Profile updated successfully.", old_profile_image
    except Exception as e:
        conn.rollback()
        print(f"Error updating seller profile for seller {seller_id}: {e}")
        return False, "An internal error occurred.", None
    finally:
        if conn and conn.is_connected(): 
            if 'cursor' in locals() and cursor.is_open(): cursor.close()
            if 'cursor_execute' in locals() and cursor_execute.is_open(): cursor_execute.close()
            conn.close()

# --- START: REPLACED AND UPGRADED FUNCTION ---
def get_orders_for_seller(seller_id, status=None, search_term=None, page=1, per_page=10):
    """
    Fetches a paginated, searchable, and filterable list of orders for a specific seller,
    including product images.
    """
    conn = get_db_connection()
    if not conn:
        return {'orders': [], 'total_count': 0, 'total_pages': 0}

    try:
        cursor = conn.cursor(dictionary=True)

        # Base query joins all necessary tables
        base_query = """
            FROM orders o
            JOIN users u ON o.buyer_id = u.user_id
            LEFT JOIN cancellation_requests cr ON o.order_id = cr.order_id AND cr.status = 'pending'
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
        """
        where_clauses = ["o.seller_id = %s"]
        params = [seller_id]

        # Add filters to the WHERE clause
        if status:
            where_clauses.append("o.status = %s")
            params.append(status)
        
        if search_term:
            where_clauses.append("(o.order_number LIKE %s OR u.full_name LIKE %s OR p.name LIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

        where_sql = " WHERE " + " AND ".join(where_clauses)
        
        # Get total count of distinct orders for pagination
        count_query = f"SELECT COUNT(DISTINCT o.order_id) AS total_count {base_query} {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        
        # This subquery is used to get the primary image for EACH product in an order
        # and then group them together for the main query.
        query = f"""
            SELECT 
                o.order_id, o.order_number, o.order_date, o.total_amount, o.status,
                u.full_name AS buyer_name,
                cr.status AS cancellation_status,
                GROUP_CONCAT(DISTINCT p_img.primary_image SEPARATOR '||') as product_images
            FROM orders o
            JOIN users u ON o.buyer_id = u.user_id
            LEFT JOIN cancellation_requests cr ON o.order_id = cr.order_id AND cr.status = 'pending'
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN (
                SELECT p.product_id, (SELECT pi.image_url FROM product_images pi WHERE pi.product_id = p.product_id AND pi.is_primary = TRUE LIMIT 1) as primary_image
                FROM products p
            ) AS p_img ON oi.product_id = p_img.product_id
            {where_sql.replace('p.name', '(SELECT name FROM products WHERE product_id = oi.product_id)')} 
            GROUP BY o.order_id
            ORDER BY o.order_date DESC
            LIMIT %s OFFSET %s
        """
        
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        cursor.execute(query, tuple(params))
        orders = cursor.fetchall()

        # Format data for the frontend
        for order in orders:
            order['total_amount'] = float(order['total_amount'])
            order['order_date'] = order['order_date'].strftime('%Y-%m-%d %H:%M')
            # Split the concatenated image URLs into a list
            if order['product_images']:
                order['product_images'] = order['product_images'].split('||')
            else:
                order['product_images'] = []

        return {
            'orders': orders,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }
    except Exception as e:
        print(f"Error fetching paginated orders for seller {seller_id}: {e}")
        return {'orders': [], 'total_count': 0, 'total_pages': 0}
# --- END: REPLACED AND UPGRADED FUNCTION ---


def get_order_details_for_seller(seller_id, order_id):
    """Fetches order details, now including cancellation request info if it exists."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        order_query = """
            SELECT o.order_number, o.order_date, o.total_amount, o.status, o.shipping_address, 
                   o.payment_method, u.full_name AS buyer_name, u.email AS buyer_email, u.user_id as buyer_id
            FROM orders o JOIN users u ON o.buyer_id = u.user_id
            WHERE o.order_id = %s AND o.seller_id = %s;
        """
        cursor.execute(order_query, (order_id, seller_id))
        order_details = cursor.fetchone()
        if not order_details: return None
        items_query = """
            SELECT oi.quantity, oi.unit_price, oi.total_price, p.name AS product_name, p.sku
            FROM order_items oi JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s;
        """
        cursor.execute(items_query, (order_id,))
        order_items = cursor.fetchall()
        cancellation_query = "SELECT * FROM cancellation_requests WHERE order_id = %s AND seller_id = %s"
        cursor.execute(cancellation_query, (order_id, seller_id))
        cancellation_details = cursor.fetchone()
        order_details['total_amount'] = float(order_details['total_amount'])
        order_details['order_date'] = order_details['order_date'].strftime('%Y-%m-%d %H:%M')
        for item in order_items:
            item['unit_price'] = float(item['unit_price'])
            item['total_price'] = float(item['total_price'])
        return {"details": order_details, "items": order_items, "cancellation": cancellation_details}
    except Exception as e:
        print(f"Error fetching order details for seller {seller_id}, order {order_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def update_order_status_for_seller(seller_id, order_id, new_status):
    """Updates the status of an order, ensuring it belongs to the seller."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    allowed_statuses = ['processing', 'shipped', 'delivered', 'cancelled']
    if new_status not in allowed_statuses:
        return False, "Invalid status provided."
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        query = "UPDATE orders SET status = %s WHERE order_id = %s AND seller_id = %s"
        cursor.execute(query, (new_status, order_id, seller_id))
        if cursor.rowcount == 0:
            conn.rollback()
            return False, "Order not found or you do not have permission to update it."
        conn.commit()
        return True, "Order status updated successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error updating order status for seller {seller_id}, order {order_id}: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_cancellation_request(seller_id, request_id):
    """Fetches a single cancellation request, verifying it belongs to the seller."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM cancellation_requests WHERE request_id = %s AND seller_id = %s"
        cursor.execute(query, (request_id, seller_id))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching cancellation request {request_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def process_cancellation_request(seller_id, request_id, action):
    """
    Processes a cancellation request by a seller (approve/reject).
    """
    conn = get_db_connection()
    if not conn: 
        return False, "Database connection failed."
    if action not in ['approved', 'rejected']:
        return False, "Invalid action specified."

    try:
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        cursor.execute("SELECT * FROM cancellation_requests WHERE request_id = %s AND seller_id = %s", (request_id, seller_id))
        request_details = cursor.fetchone()

        if not request_details:
            conn.rollback()
            return False, "Request not found or you do not have permission to process it."
        if request_details['status'] != 'pending':
            conn.rollback()
            return False, f"This request has already been {request_details['status']}."

        update_request_sql = "UPDATE cancellation_requests SET status = %s, handled_at = CURRENT_TIMESTAMP, handled_by = %s WHERE request_id = %s"
        cursor.execute(update_request_sql, (action, seller_id, request_id))

        if action == 'approved':
            order_id = request_details['order_id']
            cursor.execute("UPDATE orders SET status = 'cancelled' WHERE order_id = %s AND seller_id = %s", (order_id, seller_id))
            cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
            items_to_restock = cursor.fetchall()
            restock_sql = "UPDATE products SET stock_quantity = stock_quantity + %s WHERE product_id = %s"
            for item in items_to_restock:
                cursor.execute(restock_sql, (item['quantity'], item['product_id']))
        
        conn.commit()
        return True, f"Cancellation request has been successfully {action}."
        
    except Exception as e:
        conn.rollback()
        print(f"--- ERROR in process_cancellation_request for request {request_id}: {e} ---")
        return False, "An internal error occurred while processing the request."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()



# --- START: NEW FUNCTIONS FOR ADDITIONAL SELLER DASHBOARD CHARTS ---

def get_sales_by_category(seller_id):
    """
    Fetches the seller's total sales revenue, grouped by main product category.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        # This query joins up to the main parent category for cleaner chart labels
        query = """
            SELECT
                COALESCE(parent_cat.name, c.name) AS main_category_name,
                SUM(oi.total_price) AS total_sales
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN categories parent_cat ON c.parent_category_id = parent_cat.category_id
            WHERE o.seller_id = %s AND o.status IN ('processing', 'shipped', 'delivered')
            GROUP BY main_category_name
            ORDER BY total_sales DESC;
        """
        cursor.execute(query, (seller_id,))
        data = cursor.fetchall()
        for row in data:
            row['total_sales'] = float(row['total_sales'])
        return data
    except Exception as e:
        print(f"Error fetching seller sales by category for seller {seller_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_order_status_summary(seller_id):
    """
    Counts the number of orders per operational status for a specific seller.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        # This query groups statuses for a cleaner operational view
        query = """
            SELECT 
                CASE 
                    WHEN status IN ('confirmed', 'processing') THEN 'To Fulfill'
                    WHEN status = 'shipped' THEN 'Shipped'
                    WHEN status = 'delivered' THEN 'Delivered'
                END AS status_group,
                COUNT(order_id) AS order_count
            FROM orders
            WHERE seller_id = %s AND status IN ('confirmed', 'processing', 'shipped', 'delivered')
            GROUP BY status_group;
        """
        cursor.execute(query, (seller_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching order status summary for seller {seller_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- END: NEW FUNCTIONS ---



# In electronic_ecommerce/models/seller_model.py

# ... (add this function anywhere in the file)

def get_recent_products_for_dashboard(seller_id, limit=5):
    """Fetches the 5 most recently added products for the seller dashboard table."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                p.product_id, p.name, p.sku, p.price, p.stock_quantity, p.is_active, p.is_approved,
                (SELECT image_url FROM product_images WHERE product_id = p.product_id AND is_primary = TRUE LIMIT 1) as primary_image
            FROM products p 
            WHERE p.seller_id = %s 
            ORDER BY p.created_at DESC
            LIMIT %s;
        """
        cursor.execute(query, (seller_id, limit))
        products = cursor.fetchall()
        for p in products:
            if p.get('price'):
                p['price'] = float(p['price'])
        return products
    except Exception as e:
        print(f"Error fetching recent products for seller dashboard (seller_id {seller_id}): {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()