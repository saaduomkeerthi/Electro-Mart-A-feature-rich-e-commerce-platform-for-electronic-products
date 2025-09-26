# # electronic_ecommerce/models/admin_model.py

# import json
# from .db import get_db_connection


# # -----------------------------------------------------------------------------
# # DASHBOARD DATA FUNCTIONS
# # -----------------------------------------------------------------------------


# def get_dashboard_stats():
#     """Fetches key statistics for the admin dashboard."""
#     conn = get_db_connection()
#     if not conn: return {}
#     try:
#         cursor = conn.cursor(dictionary=True)
#         stats = {}
        
#         # --- START: MODIFIED USER COUNT QUERIES ---
#         # Get total number of buyers
#         cursor.execute("SELECT COUNT(user_id) AS total_buyers FROM users WHERE role = 'buyer';")
#         stats['total_buyers'] = cursor.fetchone()['total_buyers']
        
#         # Get total number of sellers
#         cursor.execute("SELECT COUNT(user_id) AS total_sellers FROM users WHERE role = 'seller';")
#         stats['total_sellers'] = cursor.fetchone()['total_sellers']
#         # --- END: MODIFIED USER COUNT QUERIES ---

#         cursor.execute("SELECT COUNT(seller_id) AS pending_sellers FROM sellers WHERE verification_status = 'pending';")
#         stats['pending_sellers'] = cursor.fetchone()['pending_sellers']
        
#         cursor.execute("SELECT COUNT(order_id) AS orders_today FROM orders WHERE DATE(order_date) = CURDATE();")
#         stats['orders_today'] = cursor.fetchone()['orders_today']
        
#         sales_query = """
#             SELECT SUM(total_amount) AS sales_today 
#             FROM orders 
#             WHERE 
#                 payment_status = 'completed' 
#                 AND status NOT IN ('cancelled', 'returned', 'refunded')
#                 AND DATE(order_date) = CURDATE();
#         """
#         cursor.execute(sales_query)
#         sales = cursor.fetchone()['sales_today']
#         stats['sales_today'] = float(sales) if sales else 0.0
        
#         cursor.execute("SELECT COUNT(request_id) AS pending_cancellations FROM cancellation_requests WHERE status = 'pending';")
#         stats['pending_cancellations'] = cursor.fetchone()['pending_cancellations']

#         return stats
#     except Exception as e:
#         print(f"Error fetching dashboard stats: {e}")
#         return {}
#     finally:
#         if conn and conn.is_connected(): 
#             cursor.close()
#             conn.close()    

# def get_recent_orders(limit=5):
#     """Fetches the most recent orders for the dashboard."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT o.order_number, u.full_name AS buyer_name, o.total_amount, o.status
#             FROM orders o JOIN users u ON o.buyer_id = u.user_id
#             ORDER BY o.order_date DESC LIMIT %s;
#         """
#         cursor.execute(query, (limit,))
#         orders = cursor.fetchall()
#         for order in orders:
#             order['total_amount'] = float(order['total_amount'])
#         return orders
#     except Exception as e:
#         print(f"Error fetching recent orders: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def get_new_sellers(limit=5):
#     """Fetches the newest sellers pending verification for the dashboard."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT s.business_name, u.email, s.verification_status, s.created_at
#             FROM sellers s JOIN users u ON s.seller_id = u.user_id
#             WHERE s.verification_status = 'pending'
#             ORDER BY s.created_at DESC LIMIT %s;
#         """
#         cursor.execute(query, (limit,))
#         sellers = cursor.fetchall()
#         for seller in sellers:
#             seller['created_at'] = seller['created_at'].strftime('%Y-%m-%d %H:%M')
#         return sellers
#     except Exception as e:
#         print(f"Error fetching new sellers: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# # -----------------------------------------------------------------------------
# # USER MANAGEMENT FUNCTIONS
# # -----------------------------------------------------------------------------

# def get_all_users():
#     """Fetches a list of all users for the management page."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = "SELECT user_id, full_name, email, role, is_active, created_at, last_login FROM users ORDER BY created_at DESC;"
#         cursor.execute(query)
#         users = cursor.fetchall()
#         for user in users:
#             user['created_at'] = user['created_at'].strftime('%Y-%m-%d')
#             user['last_login'] = user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else 'Never'
#         return users
#     except Exception as e:
#         print(f"Error fetching all users: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def update_user_status(user_id, is_active, admin_id):
#     """Updates a user's is_active status and logs the action."""
#     conn = get_db_connection()
#     if not conn: return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         cursor.execute("UPDATE users SET is_active = %s WHERE user_id = %s", (is_active, user_id))
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"set_active_to": bool(is_active)})
#         log_values = (admin_id, 'update_user_status', 'user', user_id, action_details)
#         cursor.execute(log_query, log_values)
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating user status for ID {user_id}: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# # -----------------------------------------------------------------------------
# # SELLER MANAGEMENT FUNCTIONS
# # -----------------------------------------------------------------------------

# def get_all_sellers():
#     """Fetches a list of all sellers for the management page."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = "SELECT s.seller_id, s.business_name, u.email, s.business_phone, s.verification_status, s.created_at FROM sellers s JOIN users u ON s.seller_id = u.user_id ORDER BY s.created_at DESC;"
#         cursor.execute(query)
#         sellers = cursor.fetchall()
#         for seller in sellers:
#             seller['created_at'] = seller['created_at'].strftime('%Y-%m-%d %H:%M')
#         return sellers
#     except Exception as e:
#         print(f"Error fetching all sellers: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def update_seller_status(seller_id, new_status, admin_id):
#     """Updates a seller's verification status and logs the action."""
#     conn = get_db_connection()
#     if not conn: return False
#     valid_statuses = ['pending', 'approved', 'rejected', 'suspended']
#     if new_status not in valid_statuses:
#         print(f"Invalid status update attempted: {new_status}")
#         return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         cursor.execute("UPDATE sellers SET verification_status = %s WHERE seller_id = %s", (new_status, seller_id))
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"updated_status_to": new_status})
#         log_values = (admin_id, 'update_seller_status', 'seller', seller_id, action_details)
#         cursor.execute(log_query, log_values)
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating seller status for ID {seller_id}: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# # -----------------------------------------------------------------------------
# # PRODUCT MANAGEMENT FUNCTIONS
# # -----------------------------------------------------------------------------

# def get_all_products():
#     """Fetches a list of all products for the management page."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT p.product_id, p.name, s.business_name, c.name as category_name, p.price, p.stock_quantity, p.is_approved, p.is_active, p.is_featured 
#             FROM products p 
#             JOIN sellers s ON p.seller_id = s.seller_id
#             LEFT JOIN categories c ON p.category_id = c.category_id
#             ORDER BY p.created_at DESC;
#         """
#         cursor.execute(query)
#         products = cursor.fetchall()
#         for product in products:
#             product['price'] = float(product['price'])
#         return products
#     except Exception as e:
#         print(f"Error fetching all products: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def update_product_status(product_id, field, new_value, admin_id):
#     """Updates a product's status field (is_active, is_approved, or is_featured)."""
#     conn = get_db_connection()
#     if not conn: return False
#     if field not in ['is_active', 'is_approved', 'is_featured']:
#         print(f"Invalid field update attempted: {field}")
#         return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         update_query = f"UPDATE products SET {field} = %s WHERE product_id = %s"
#         cursor.execute(update_query, (new_value, product_id))
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"field_updated": field, "new_value": bool(new_value)})
#         log_values = (admin_id, 'update_product_status', 'product', product_id, action_details)
#         cursor.execute(log_query, log_values)
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating product status for ID {product_id}: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def delete_product(product_id, admin_id):
#     """Permanently deletes a product and logs the action."""
#     conn = get_db_connection()
#     if not conn: return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"note": "Product permanently deleted from system."})
#         log_values = (admin_id, 'delete_product', 'product', product_id, action_details)
#         cursor.execute(log_query, log_values)
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error deleting product ID {product_id}: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()
        
# # -----------------------------------------------------------------------------
# # CATEGORY MANAGEMENT FUNCTIONS
# # -----------------------------------------------------------------------------

# def get_all_categories_for_management():
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = "SELECT category_id, name, parent_category_id, is_active FROM categories ORDER BY parent_category_id, name"
#         cursor.execute(query)
#         all_cats = cursor.fetchall()
#         category_map = {cat['category_id']: cat for cat in all_cats}
#         structured_list = []
#         for cat in all_cats:
#             if cat['parent_category_id']:
#                 parent = category_map.get(cat['parent_category_id'])
#                 if parent:
#                     if 'subcategories' not in parent:
#                         parent['subcategories'] = []
#                     parent['subcategories'].append(cat)
#             else:
#                 structured_list.append(cat)
#         return structured_list
#     except Exception as e:
#         print(f"Error fetching categories for admin management: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def update_category_activation_status(active_ids):
#     conn = get_db_connection()
#     if not conn: return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         cursor.execute("UPDATE categories SET is_active = FALSE")
#         if active_ids:
#             placeholders = ', '.join(['%s'] * len(active_ids))
#             sql = f"UPDATE categories SET is_active = TRUE WHERE category_id IN ({placeholders})"
#             cursor.execute(sql, tuple(active_ids))
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating category activation status: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()       

# def update_category_name(category_id, new_name):
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."
#     try:
#         cursor = conn.cursor()
#         cursor.execute("SELECT parent_category_id FROM categories WHERE category_id = %s", (category_id,))
#         parent = cursor.fetchone()
#         parent_id = parent[0] if parent else None
#         if parent_id:
#             check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id = %s AND category_id != %s"
#             cursor.execute(check_sql, (new_name, parent_id, category_id))
#         else:
#             check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id IS NULL AND category_id != %s"
#             cursor.execute(check_sql, (new_name, category_id))
#         if cursor.fetchone():
#             return False, "Another category with this name already exists at the same level."
#         cursor.execute("UPDATE categories SET name = %s WHERE category_id = %s", (new_name, category_id))
#         conn.commit()
#         return True, "Category renamed successfully."
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating category {category_id}: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def delete_category(category_id):
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."
#     try:
#         cursor = conn.cursor(dictionary=True)
#         conn.start_transaction()
#         check_query = """
#             SELECT p.product_id FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#             WHERE c.category_id = %s OR c.parent_category_id = %s
#             LIMIT 1;
#         """
#         cursor.execute(check_query, (category_id, category_id))
#         if cursor.fetchone():
#             conn.rollback()
#             return False, "Cannot delete. At least one product is assigned to this category or one of its subcategories."
#         cursor.execute("DELETE FROM categories WHERE parent_category_id = %s", (category_id,))
#         cursor.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
#         conn.commit()
#         return True, "Category and its subcategories (if any) were deleted successfully."
#     except Exception as e:
#         conn.rollback()
#         print(f"Error deleting category {category_id}: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def add_new_category(name, parent_id=None):
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."
#     try:
#         cursor = conn.cursor()
#         if parent_id:
#             check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id = %s"
#             cursor.execute(check_sql, (name, parent_id))
#         else:
#             check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id IS NULL"
#             cursor.execute(check_sql, (name,))
#         if cursor.fetchone():
#             return False, "A category with this name already exists at this level."
#         sql = "INSERT INTO categories (name, parent_category_id) VALUES (%s, %s)"
#         cursor.execute(sql, (name, parent_id))
#         new_id = cursor.lastrowid
#         conn.commit()
#         return True, new_id
#     except Exception as e:
#         conn.rollback()
#         print(f"Error adding new category: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# # --- CANCELLATION MANAGEMENT FUNCTIONS FOR ADMIN ---

# def get_all_pending_cancellations():
#     """
#     Fetches all pending cancellation requests with associated order,
#     buyer, and seller details for the admin management page.
#     """
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT
#                 cr.request_id,
#                 cr.reason,
#                 cr.comments,
#                 cr.requested_at,
#                 o.order_number,
#                 o.total_amount,
#                 buyer.full_name AS buyer_name,
#                 seller.business_name AS seller_name
#             FROM cancellation_requests cr
#             JOIN orders o ON cr.order_id = o.order_id
#             JOIN users buyer ON cr.buyer_id = buyer.user_id
#             JOIN sellers seller ON cr.seller_id = seller.seller_id
#             WHERE cr.status = 'pending'
#             ORDER BY cr.requested_at ASC;
#         """
#         cursor.execute(query)
#         requests = cursor.fetchall()
#         for req in requests:
#             req['total_amount'] = float(req['total_amount'])
#             req['requested_at'] = req['requested_at'].strftime('%Y-%m-%d %H:%M')
#         return requests
#     except Exception as e:
#         print(f"Error fetching pending cancellation requests: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def admin_process_cancellation_request(admin_id, request_id, action):
#     """
#     Handles an admin's decision on a cancellation request within a transaction.
#     Logs the action in admin_activities.
#     """
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."
#     if action not in ['approved', 'rejected']:
#         return False, "Invalid action specified."

#     try:
#         cursor = conn.cursor(dictionary=True)
#         conn.start_transaction()

#         cursor.execute("SELECT * FROM cancellation_requests WHERE request_id = %s", (request_id,))
#         request_details = cursor.fetchone()
#         if not request_details:
#             conn.rollback()
#             return False, "Request not found."
#         if request_details['status'] != 'pending':
#             conn.rollback()
#             return False, f"This request has already been {request_details['status']}."

#         update_request_sql = "UPDATE cancellation_requests SET status = %s, handled_at = CURRENT_TIMESTAMP, handled_by = %s WHERE request_id = %s"
#         cursor.execute(update_request_sql, (action, admin_id, request_id))

#         if action == 'approved':
#             order_id = request_details['order_id']
#             cursor.execute("UPDATE orders SET status = 'cancelled' WHERE order_id = %s", (order_id,))
#             cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
#             items_to_restock = cursor.fetchall()
#             restock_sql = "UPDATE products SET stock_quantity = stock_quantity + %s WHERE product_id = %s"
#             for item in items_to_restock:
#                 cursor.execute(restock_sql, (item['quantity'], item['product_id']))
        
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"request_id": request_id, "action_taken": action})
#         log_values = (admin_id, 'process_cancellation', 'order', request_details['order_id'], action_details)
#         cursor.execute(log_query, log_values)

#         conn.commit()
#         return True, f"Cancellation request has been successfully {action}."
        
#     except Exception as e:
#         conn.rollback()
#         print(f"--- ERROR in admin_process_cancellation_request for request {request_id}: {e} ---")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()














# electronic_ecommerce/models/admin_model.py

# import json
# from .db import get_db_connection


# # -----------------------------------------------------------------------------
# # DASHBOARD DATA FUNCTIONS
# # -----------------------------------------------------------------------------


# def get_dashboard_stats():
#     """Fetches key statistics for the admin dashboard."""
#     conn = get_db_connection()
#     if not conn: return {}
#     try:
#         cursor = conn.cursor(dictionary=True)
#         stats = {}
        
#         cursor.execute("SELECT COUNT(user_id) AS total_buyers FROM users WHERE role = 'buyer';")
#         stats['total_buyers'] = cursor.fetchone()['total_buyers']
        
#         cursor.execute("SELECT COUNT(user_id) AS total_sellers FROM users WHERE role = 'seller';")
#         stats['total_sellers'] = cursor.fetchone()['total_sellers']

#         cursor.execute("SELECT COUNT(seller_id) AS pending_sellers FROM sellers WHERE verification_status = 'pending';")
#         stats['pending_sellers'] = cursor.fetchone()['pending_sellers']
        
#         cursor.execute("SELECT COUNT(order_id) AS orders_today FROM orders WHERE DATE(order_date) = CURDATE();")
#         stats['orders_today'] = cursor.fetchone()['orders_today']
        
#         sales_today_query = """
#             SELECT SUM(total_amount) AS sales_today 
#             FROM orders 
#             WHERE 
#                 payment_status = 'completed' 
#                 AND status NOT IN ('cancelled', 'returned', 'refunded')
#                 AND DATE(order_date) = CURDATE();
#         """
#         cursor.execute(sales_today_query)
#         sales_today = cursor.fetchone()['sales_today']
#         stats['sales_today'] = float(sales_today) if sales_today else 0.0

#         total_sales_query = """
#             SELECT SUM(total_amount) AS total_sales
#             FROM orders
#             WHERE
#                 payment_status = 'completed'
#                 AND status NOT IN ('cancelled', 'returned', 'refunded');
#         """
#         cursor.execute(total_sales_query)
#         total_sales = cursor.fetchone()['total_sales']
#         stats['total_sales'] = float(total_sales) if total_sales else 0.0
        
#         cursor.execute("SELECT COUNT(request_id) AS pending_cancellations FROM cancellation_requests WHERE status = 'pending';")
#         stats['pending_cancellations'] = cursor.fetchone()['pending_cancellations']

#         return stats
#     except Exception as e:
#         print(f"Error fetching dashboard stats: {e}")
#         return {}
#     finally:
#         if conn and conn.is_connected(): 
#             cursor.close()
#             conn.close()    

# def get_recent_orders(limit=5):
#     """Fetches the most recent orders for the dashboard."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT o.order_number, u.full_name AS buyer_name, o.total_amount, o.status
#             FROM orders o JOIN users u ON o.buyer_id = u.user_id
#             ORDER BY o.order_date DESC LIMIT %s;
#         """
#         cursor.execute(query, (limit,))
#         orders = cursor.fetchall()
#         for order in orders:
#             order['total_amount'] = float(order['total_amount'])
#         return orders
#     except Exception as e:
#         print(f"Error fetching recent orders: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def get_new_sellers(limit=5):
#     """Fetches the newest sellers pending verification for the dashboard."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT s.business_name, u.email, s.verification_status, s.created_at
#             FROM sellers s JOIN users u ON s.seller_id = u.user_id
#             WHERE s.verification_status = 'pending'
#             ORDER BY s.created_at DESC LIMIT %s;
#         """
#         cursor.execute(query, (limit,))
#         sellers = cursor.fetchall()
#         for seller in sellers:
#             seller['created_at'] = seller['created_at'].strftime('%Y-%m-%d %H:%M')
#         return sellers
#     except Exception as e:
#         print(f"Error fetching new sellers: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# # -----------------------------------------------------------------------------
# # USER MANAGEMENT FUNCTIONS
# # -----------------------------------------------------------------------------

# def get_all_users():
#     """Fetches a list of all users for the management page."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = "SELECT user_id, full_name, email, role, is_active, created_at, last_login FROM users ORDER BY created_at DESC;"
#         cursor.execute(query)
#         users = cursor.fetchall()
#         for user in users:
#             user['created_at'] = user['created_at'].strftime('%Y-%m-%d')
#             user['last_login'] = user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else 'Never'
#         return users
#     except Exception as e:
#         print(f"Error fetching all users: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def update_user_status(user_id, is_active, admin_id):
#     """Updates a user's is_active status and logs the action."""
#     conn = get_db_connection()
#     if not conn: return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         cursor.execute("UPDATE users SET is_active = %s WHERE user_id = %s", (is_active, user_id))
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"set_active_to": bool(is_active)})
#         log_values = (admin_id, 'update_user_status', 'user', user_id, action_details)
#         cursor.execute(log_query, log_values)
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating user status for ID {user_id}: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# # -----------------------------------------------------------------------------
# # SELLER MANAGEMENT FUNCTIONS
# # -----------------------------------------------------------------------------

# def get_all_sellers():
#     """Fetches a list of all sellers for the management page."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = "SELECT s.seller_id, s.business_name, u.email, s.business_phone, s.verification_status, s.created_at FROM sellers s JOIN users u ON s.seller_id = u.user_id ORDER BY s.created_at DESC;"
#         cursor.execute(query)
#         sellers = cursor.fetchall()
#         for seller in sellers:
#             seller['created_at'] = seller['created_at'].strftime('%Y-%m-%d %H:%M')
#         return sellers
#     except Exception as e:
#         print(f"Error fetching all sellers: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def update_seller_status(seller_id, new_status, admin_id):
#     """Updates a seller's verification status and logs the action."""
#     conn = get_db_connection()
#     if not conn: return False
#     valid_statuses = ['pending', 'approved', 'rejected', 'suspended']
#     if new_status not in valid_statuses:
#         print(f"Invalid status update attempted: {new_status}")
#         return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         cursor.execute("UPDATE sellers SET verification_status = %s WHERE seller_id = %s", (new_status, seller_id))
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"updated_status_to": new_status})
#         log_values = (admin_id, 'update_seller_status', 'seller', seller_id, action_details)
#         cursor.execute(log_query, log_values)
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating seller status for ID {seller_id}: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# # -----------------------------------------------------------------------------
# # PRODUCT MANAGEMENT FUNCTIONS
# # -----------------------------------------------------------------------------

# def get_all_products():
#     """Fetches a list of all products for the management page."""
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT p.product_id, p.name, s.business_name, c.name as category_name, p.price, p.stock_quantity, p.is_approved, p.is_active, p.is_featured 
#             FROM products p 
#             JOIN sellers s ON p.seller_id = s.seller_id
#             LEFT JOIN categories c ON p.category_id = c.category_id
#             ORDER BY p.created_at DESC;
#         """
#         cursor.execute(query)
#         products = cursor.fetchall()
#         for product in products:
#             product['price'] = float(product['price'])
#         return products
#     except Exception as e:
#         print(f"Error fetching all products: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def update_product_status(product_id, field, new_value, admin_id):
#     """Updates a product's status field (is_active, is_approved, or is_featured)."""
#     conn = get_db_connection()
#     if not conn: return False
#     if field not in ['is_active', 'is_approved', 'is_featured']:
#         print(f"Invalid field update attempted: {field}")
#         return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         update_query = f"UPDATE products SET {field} = %s WHERE product_id = %s"
#         cursor.execute(update_query, (new_value, product_id))
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"field_updated": field, "new_value": bool(new_value)})
#         log_values = (admin_id, 'update_product_status', 'product', product_id, action_details)
#         cursor.execute(log_query, log_values)
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating product status for ID {product_id}: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def delete_product(product_id, admin_id):
#     """Permanently deletes a product and logs the action."""
#     conn = get_db_connection()
#     if not conn: return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"note": "Product permanently deleted from system."})
#         log_values = (admin_id, 'delete_product', 'product', product_id, action_details)
#         cursor.execute(log_query, log_values)
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error deleting product ID {product_id}: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()
        
# # -----------------------------------------------------------------------------
# # CATEGORY MANAGEMENT FUNCTIONS
# # -----------------------------------------------------------------------------

# def get_all_categories_for_management():
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = "SELECT category_id, name, parent_category_id, is_active FROM categories ORDER BY parent_category_id, name"
#         cursor.execute(query)
#         all_cats = cursor.fetchall()
#         category_map = {cat['category_id']: cat for cat in all_cats}
#         structured_list = []
#         for cat in all_cats:
#             if cat['parent_category_id']:
#                 parent = category_map.get(cat['parent_category_id'])
#                 if parent:
#                     if 'subcategories' not in parent:
#                         parent['subcategories'] = []
#                     parent['subcategories'].append(cat)
#             else:
#                 structured_list.append(cat)
#         return structured_list
#     except Exception as e:
#         print(f"Error fetching categories for admin management: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def update_category_activation_status(active_ids):
#     conn = get_db_connection()
#     if not conn: return False
#     try:
#         cursor = conn.cursor()
#         conn.start_transaction()
#         cursor.execute("UPDATE categories SET is_active = FALSE")
#         if active_ids:
#             placeholders = ', '.join(['%s'] * len(active_ids))
#             sql = f"UPDATE categories SET is_active = TRUE WHERE category_id IN ({placeholders})"
#             cursor.execute(sql, tuple(active_ids))
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating category activation status: {e}")
#         return False
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()       

# def update_category_name(category_id, new_name):
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."
#     try:
#         cursor = conn.cursor()
#         cursor.execute("SELECT parent_category_id FROM categories WHERE category_id = %s", (category_id,))
#         parent = cursor.fetchone()
#         parent_id = parent if parent else None
#         if parent_id:
#             check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id = %s AND category_id != %s"
#             cursor.execute(check_sql, (new_name, parent_id, category_id))
#         else:
#             check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id IS NULL AND category_id != %s"
#             cursor.execute(check_sql, (new_name, category_id))
#         if cursor.fetchone():
#             return False, "Another category with this name already exists at the same level."
#         cursor.execute("UPDATE categories SET name = %s WHERE category_id = %s", (new_name, category_id))
#         conn.commit()
#         return True, "Category renamed successfully."
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating category {category_id}: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def delete_category(category_id):
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."
#     try:
#         cursor = conn.cursor(dictionary=True)
#         conn.start_transaction()
#         check_query = """
#             SELECT p.product_id FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#             WHERE c.category_id = %s OR c.parent_category_id = %s
#             LIMIT 1;
#         """
#         cursor.execute(check_query, (category_id, category_id))
#         if cursor.fetchone():
#             conn.rollback()
#             return False, "Cannot delete. At least one product is assigned to this category or one of its subcategories."
#         cursor.execute("DELETE FROM categories WHERE parent_category_id = %s", (category_id,))
#         cursor.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
#         conn.commit()
#         return True, "Category and its subcategories (if any) were deleted successfully."
#     except Exception as e:
#         conn.rollback()
#         print(f"Error deleting category {category_id}: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def add_new_category(name, parent_id=None):
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."
#     try:
#         cursor = conn.cursor()
#         if parent_id:
#             check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id = %s"
#             cursor.execute(check_sql, (name, parent_id))
#         else:
#             check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id IS NULL"
#             cursor.execute(check_sql, (name,))
#         if cursor.fetchone():
#             return False, "A category with this name already exists at this level."
#         sql = "INSERT INTO categories (name, parent_category_id) VALUES (%s, %s)"
#         cursor.execute(sql, (name, parent_id))
#         new_id = cursor.lastrowid
#         conn.commit()
#         return True, new_id
#     except Exception as e:
#         conn.rollback()
#         print(f"Error adding new category: {e}")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# # --- CANCELLATION MANAGEMENT FUNCTIONS FOR ADMIN ---

# def get_all_pending_cancellations():
#     """
#     Fetches all pending cancellation requests with associated order,
#     buyer, and seller details for the admin management page.
#     """
#     conn = get_db_connection()
#     if not conn: return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT
#                 cr.request_id,
#                 cr.reason,
#                 cr.comments,
#                 cr.requested_at,
#                 o.order_number,
#                 o.total_amount,
#                 buyer.full_name AS buyer_name,
#                 seller.business_name AS seller_name
#             FROM cancellation_requests cr
#             JOIN orders o ON cr.order_id = o.order_id
#             JOIN users buyer ON cr.buyer_id = buyer.user_id
#             JOIN sellers seller ON cr.seller_id = seller.seller_id
#             WHERE cr.status = 'pending'
#             ORDER BY cr.requested_at ASC;
#         """
#         cursor.execute(query)
#         requests = cursor.fetchall()
#         for req in requests:
#             req['total_amount'] = float(req['total_amount'])
#             req['requested_at'] = req['requested_at'].strftime('%Y-%m-%d %H:%M')
#         return requests
#     except Exception as e:
#         print(f"Error fetching pending cancellation requests: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()

# def admin_process_cancellation_request(admin_id, request_id, action):
#     """
#     Handles an admin's decision on a cancellation request within a transaction.
#     Logs the action in admin_activities.
#     """
#     conn = get_db_connection()
#     if not conn: return False, "Database connection failed."
#     if action not in ['approved', 'rejected']:
#         return False, "Invalid action specified."

#     try:
#         cursor = conn.cursor(dictionary=True)
#         conn.start_transaction()

#         cursor.execute("SELECT * FROM cancellation_requests WHERE request_id = %s", (request_id,))
#         request_details = cursor.fetchone()
#         if not request_details:
#             conn.rollback()
#             return False, "Request not found."
#         if request_details['status'] != 'pending':
#             conn.rollback()
#             return False, f"This request has already been {request_details['status']}."

#         update_request_sql = "UPDATE cancellation_requests SET status = %s, handled_at = CURRENT_TIMESTAMP, handled_by = %s WHERE request_id = %s"
#         cursor.execute(update_request_sql, (action, admin_id, request_id))

#         if action == 'approved':
#             order_id = request_details['order_id']
#             cursor.execute("UPDATE orders SET status = 'cancelled' WHERE order_id = %s", (order_id,))
#             cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
#             items_to_restock = cursor.fetchall()
#             restock_sql = "UPDATE products SET stock_quantity = stock_quantity + %s WHERE product_id = %s"
#             for item in items_to_restock:
#                 cursor.execute(restock_sql, (item['quantity'], item['product_id']))
        
#         log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
#         action_details = json.dumps({"request_id": request_id, "action_taken": action})
#         log_values = (admin_id, 'process_cancellation', 'order', request_details['order_id'], action_details)
#         cursor.execute(log_query, log_values)

#         conn.commit()
#         return True, f"Cancellation request has been successfully {action}."
        
#     except Exception as e:
#         conn.rollback()
#         print(f"--- ERROR in admin_process_cancellation_request for request {request_id}: {e} ---")
#         return False, "An internal error occurred."
#     finally:
#         if conn and conn.is_connected(): cursor.close(); conn.close()







import json
from .db import get_db_connection
from flask import url_for
import os
import math


def get_structured_paginated_categories(search_term=None, page=1, per_page=10):
    # This function is unchanged
    conn = get_db_connection()
    if not conn:
        return {'categories': [], 'total_count': 0, 'total_pages': 0}
    try:
        cursor = conn.cursor(dictionary=True)
        main_cat_where_clauses = ["parent_category_id IS NULL"]
        params = []
        if search_term:
            main_cat_where_clauses.append("name LIKE %s")
            params.append(f"%{search_term}%")
        where_sql = " WHERE " + " AND ".join(main_cat_where_clauses)
        count_query = f"SELECT COUNT(category_id) AS total_count FROM categories {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        offset = (page - 1) * per_page
        main_cat_query = f"SELECT category_id, name, is_active FROM categories {where_sql} ORDER BY name LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        cursor.execute(main_cat_query, tuple(params))
        main_categories = cursor.fetchall()
        if not main_categories:
            return {'categories': [], 'total_count': 0, 'total_pages': 0}
        main_category_ids = [cat['category_id'] for cat in main_categories]
        placeholders = ', '.join(['%s'] * len(main_category_ids))
        sub_cat_query = f"SELECT category_id, name, parent_category_id, is_active FROM categories WHERE parent_category_id IN ({placeholders}) ORDER BY name"
        cursor.execute(sub_cat_query, tuple(main_category_ids))
        sub_categories = cursor.fetchall()
        category_map = {cat['category_id']: cat for cat in main_categories}
        for cat in main_categories:
            cat['subcategories'] = []
        for sub_cat in sub_categories:
            parent_id = sub_cat['parent_category_id']
            if parent_id in category_map:
                category_map[parent_id]['subcategories'].append(sub_cat)
        return {'categories': main_categories, 'total_count': total_count, 'total_pages': total_pages, 'current_page': page}
    except Exception as e:
        print(f"Error fetching structured paginated categories: {e}")
        return {'categories': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_dashboard_stats():
    # This function is unchanged
    conn = get_db_connection()
    if not conn: return {}
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {}
        cursor.execute("SELECT COUNT(user_id) AS total_buyers FROM users WHERE role = 'buyer';")
        stats['total_buyers'] = cursor.fetchone()['total_buyers']
        cursor.execute("SELECT COUNT(user_id) AS total_sellers FROM users WHERE role = 'seller';")
        stats['total_sellers'] = cursor.fetchone()['total_sellers']
        cursor.execute("SELECT COUNT(seller_id) AS pending_sellers FROM sellers WHERE verification_status = 'pending';")
        stats['pending_sellers'] = cursor.fetchone()['pending_sellers']
        cursor.execute("SELECT COUNT(order_id) AS orders_today FROM orders WHERE DATE(order_date) = CURDATE();")
        stats['orders_today'] = cursor.fetchone()['orders_today']
        sales_today_query = "SELECT SUM(total_amount) AS sales_today FROM orders WHERE payment_status = 'completed' AND status NOT IN ('cancelled', 'returned', 'refunded') AND DATE(order_date) = CURDATE();"
        cursor.execute(sales_today_query)
        sales_today = cursor.fetchone()['sales_today']
        stats['sales_today'] = float(sales_today) if sales_today else 0.0
        total_sales_query = "SELECT SUM(total_amount) AS total_sales FROM orders WHERE payment_status = 'completed' AND status NOT IN ('cancelled', 'returned', 'refunded');"
        cursor.execute(total_sales_query)
        total_sales = cursor.fetchone()['total_sales']
        stats['total_sales'] = float(total_sales) if total_sales else 0.0
        cursor.execute("SELECT COUNT(request_id) AS pending_cancellations FROM cancellation_requests WHERE status = 'pending';")
        stats['pending_cancellations'] = cursor.fetchone()['pending_cancellations']
        return stats
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        return {}
    finally:
        if conn and conn.is_connected(): 
            cursor.close()
            conn.close()    

def get_recent_orders(limit=5):
    # This function is unchanged
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT o.order_number, u.full_name AS buyer_name, o.total_amount, o.status FROM orders o JOIN users u ON o.buyer_id = u.user_id ORDER BY o.order_date DESC LIMIT %s;"
        cursor.execute(query, (limit,))
        orders = cursor.fetchall()
        for order in orders:
            order['total_amount'] = float(order['total_amount'])
        return orders
    except Exception as e:
        print(f"Error fetching recent orders: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_new_sellers(limit=5):
    # This function is unchanged
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT s.business_name, u.email, s.verification_status, s.created_at FROM sellers s JOIN users u ON s.seller_id = u.user_id WHERE s.verification_status = 'pending' ORDER BY s.created_at DESC LIMIT %s;"
        cursor.execute(query, (limit,))
        sellers = cursor.fetchall()
        for seller in sellers:
            seller['created_at'] = seller['created_at'].strftime('%Y-%m-%d %H:%M')
        return sellers
    except Exception as e:
        print(f"Error fetching new sellers: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_all_users(role=None, search_term=None, page=1, per_page=10):
    # This function is unchanged
    conn = get_db_connection()
    if not conn:
        return {'users': [], 'total_count': 0, 'total_pages': 0}
    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []
        if role:
            where_clauses.append("role = %s")
            params.append(role)
        if search_term:
            where_clauses.append("(full_name LIKE %s OR email LIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        count_query = f"SELECT COUNT(user_id) AS total_count FROM users {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        offset = (page - 1) * per_page
        query = f"SELECT user_id, full_name, email, role, is_active, created_at, last_login, profile_image FROM users {where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        cursor.execute(query, tuple(params))
        users = cursor.fetchall()
        for user in users:
            user['created_at'] = user['created_at'].strftime('%Y-%m-%d')
            user['last_login'] = user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else 'Never'
            if user.get('profile_image'):
                user['profile_image_url'] = url_for('serve_upload', filename=os.path.basename(user['profile_image']))
            else:
                user['profile_image_url'] = None
        return {'users': users, 'total_count': total_count, 'total_pages': total_pages, 'current_page': page}
    except Exception as e:
        print(f"Error fetching all users with pagination/filters: {e}")
        return {'users': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_user_status(user_id, is_active, admin_id):
    # This function is unchanged
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("UPDATE users SET is_active = %s WHERE user_id = %s", (is_active, user_id))
        log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
        action_details = json.dumps({"set_active_to": bool(is_active)})
        log_values = (admin_id, 'update_user_status', 'user', user_id, action_details)
        cursor.execute(log_query, log_values)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating user status for ID {user_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

# -----------------------------------------------------------------------------
# SELLER MANAGEMENT FUNCTIONS
# -----------------------------------------------------------------------------

# --- START: NEW FUNCTION TO ADD ---
def get_seller_by_id(seller_id):
    """Fetches basic seller details by their ID."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT seller_id, business_name FROM sellers WHERE seller_id = %s"
        cursor.execute(query, (seller_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching seller by ID {seller_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
# --- END: NEW FUNCTION ---

def get_all_sellers(status=None, search_term=None, page=1, per_page=10):
    # This function is already updated from our previous step
    conn = get_db_connection()
    if not conn:
        return {'sellers': [], 'total_count': 0, 'total_pages': 0}
    try:
        cursor = conn.cursor(dictionary=True)
        base_query = "FROM sellers s JOIN users u ON s.seller_id = u.user_id"
        where_clauses = []
        params = []
        if status:
            where_clauses.append("s.verification_status = %s")
            params.append(status)
        if search_term:
            where_clauses.append("(u.full_name LIKE %s OR s.business_name LIKE %s OR u.email LIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        count_query = f"SELECT COUNT(s.seller_id) AS total_count {base_query} {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        query = f"""
            SELECT s.seller_id, u.full_name, s.business_name, u.email, s.business_phone, 
                   s.verification_status, s.created_at, u.profile_image
            {base_query} {where_sql}
            ORDER BY s.created_at DESC LIMIT %s OFFSET %s
        """
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        cursor.execute(query, tuple(params))
        sellers = cursor.fetchall()
        for seller in sellers:
            seller['created_at'] = seller['created_at'].strftime('%Y-%m-%d %H:%M')
            if seller.get('profile_image'):
                seller['profile_image_url'] = url_for('serve_upload', filename=os.path.basename(seller['profile_image']))
            else:
                seller['profile_image_url'] = None
        return {'sellers': sellers, 'total_count': total_count, 'total_pages': total_pages, 'current_page': page}
    except Exception as e:
        print(f"Error fetching all sellers with pagination/filters: {e}")
        return {'sellers': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_seller_status(seller_id, new_status, admin_id):
    # This function is unchanged
    conn = get_db_connection()
    if not conn: return False
    valid_statuses = ['pending', 'approved', 'rejected', 'suspended']
    if new_status not in valid_statuses:
        print(f"Invalid status update attempted: {new_status}")
        return False
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("UPDATE sellers SET verification_status = %s WHERE seller_id = %s", (new_status, seller_id))
        log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
        action_details = json.dumps({"updated_status_to": new_status})
        log_values = (admin_id, 'update_seller_status', 'seller', seller_id, action_details)
        cursor.execute(log_query, log_values)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating seller status for ID {seller_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

# --- START: NEW FUNCTIONS FOR PERMISSIONS ---
def get_all_active_main_categories():
    """Fetches a simple list of all ACTIVE main categories for the permissions page."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT category_id, name FROM categories WHERE parent_category_id IS NULL AND is_active = TRUE ORDER BY name"
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching active main categories: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_seller_allowed_category_ids(seller_id):
    """Fetches a list of category IDs that a seller is currently allowed to post in."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        query = "SELECT category_id FROM seller_allowed_categories WHERE seller_id = %s AND is_active = TRUE"
        cursor.execute(query, (seller_id,))
        # Return a simple list of IDs, e.g., [1, 5, 8]
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching seller allowed categories for seller {seller_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def update_seller_category_permissions(seller_id, category_ids, admin_id):
    """
    Updates the category permissions for a seller in a single transaction.
    It deactivates all old permissions and inserts the new ones.
    """
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        conn.start_transaction()

        # Step 1: Deactivate all existing permissions for this seller
        cursor.execute("UPDATE seller_allowed_categories SET is_active = FALSE WHERE seller_id = %s", (seller_id,))

        # Step 2: Insert the new set of permissions
        if category_ids: # Only proceed if there are categories to add
            insert_query = """
                INSERT INTO seller_allowed_categories (seller_id, category_id, allowed_by, is_active)
                VALUES (%s, %s, %s, TRUE)
            """
            # Prepare a list of tuples for executemany
            values_to_insert = [(seller_id, cat_id, admin_id) for cat_id in category_ids]
            cursor.executemany(insert_query, values_to_insert)
        
        # Log this admin action
        log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
        action_details = json.dumps({"updated_permissions_to_ids": category_ids})
        log_values = (admin_id, 'update_permissions', 'seller', seller_id, action_details)
        cursor.execute(log_query, log_values)

        conn.commit()
        return True, "Seller permissions updated successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error updating seller permissions for seller {seller_id}: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()
# --- END: NEW FUNCTIONS FOR PERMISSIONS ---

# -----------------------------------------------------------------------------
# PRODUCT MANAGEMENT FUNCTIONS
# -----------------------------------------------------------------------------

def get_paginated_products_for_admin(category_id=None, search_term=None, page=1, per_page=10):
    """
    Fetches a paginated, searchable, and filterable list of all products for the admin panel.
    """
    conn = get_db_connection()
    if not conn:
        return {'products': [], 'total_count': 0, 'total_pages': 0}

    try:
        cursor = conn.cursor(dictionary=True)
        base_query = """
            FROM products p
            JOIN sellers s ON p.seller_id = s.seller_id
            LEFT JOIN categories c ON p.category_id = c.category_id
        """
        where_clauses = []
        params = []

        if search_term:
            where_clauses.append("p.name LIKE %s")
            params.append(f"%{search_term}%")
        
        if category_id:
            where_clauses.append("(c.category_id = %s OR c.parent_category_id = %s)")
            params.extend([category_id, category_id])

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)
        
        count_query = f"SELECT COUNT(p.product_id) AS total_count {base_query} {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        
        product_query = f"""
            SELECT p.product_id, p.name, s.business_name, c.name as category_name, 
                   p.price, p.stock_quantity, p.is_approved, p.is_active, p.is_featured
            {base_query}
            {where_sql}
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        cursor.execute(product_query, tuple(params))
        products = cursor.fetchall()

        for product in products:
            product['price'] = float(product['price'])

        return {
            'products': products,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    except Exception as e:
        print(f"Error fetching paginated products for admin: {e}")
        return {'products': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_all_products():
    """DEPRECATED: Use get_paginated_products_for_admin instead. Kept for potential other uses."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.product_id, p.name, s.business_name, c.name as category_name, p.price, p.stock_quantity, p.is_approved, p.is_active, p.is_featured 
            FROM products p 
            JOIN sellers s ON p.seller_id = s.seller_id
            LEFT JOIN categories c ON p.category_id = c.category_id
            ORDER BY p.created_at DESC;
        """
        cursor.execute(query)
        products = cursor.fetchall()
        for product in products:
            product['price'] = float(product['price'])
        return products
    except Exception as e:
        print(f"Error fetching all products: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def update_product_status(product_id, field, new_value, admin_id):
    conn = get_db_connection()
    if not conn: return False
    if field not in ['is_active', 'is_approved', 'is_featured']:
        print(f"Invalid field update attempted: {field}")
        return False
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        update_query = f"UPDATE products SET {field} = %s WHERE product_id = %s"
        cursor.execute(update_query, (new_value, product_id))
        log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
        action_details = json.dumps({"field_updated": field, "new_value": bool(new_value)})
        log_values = (admin_id, 'update_product_status', 'product', product_id, action_details)
        cursor.execute(log_query, log_values)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating product status for ID {product_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def delete_product(product_id, admin_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
        action_details = json.dumps({"note": "Product permanently deleted from system."})
        log_values = (admin_id, 'delete_product', 'product', product_id, action_details)
        cursor.execute(log_query, log_values)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error deleting product ID {product_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()
        
# -----------------------------------------------------------------------------
# CATEGORY MANAGEMENT FUNCTIONS
# -----------------------------------------------------------------------------

def get_all_main_categories():
    """Fetches a simple list of all main categories for filter dropdowns."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT category_id, name FROM categories WHERE parent_category_id IS NULL ORDER BY name"
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching main categories: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()


def get_all_categories_for_management():
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT category_id, name, parent_category_id, is_active FROM categories ORDER BY parent_category_id, name"
        cursor.execute(query)
        all_cats = cursor.fetchall()
        category_map = {cat['category_id']: cat for cat in all_cats}
        structured_list = []
        for cat in all_cats:
            if cat['parent_category_id']:
                parent = category_map.get(cat['parent_category_id'])
                if parent:
                    if 'subcategories' not in parent:
                        parent['subcategories'] = []
                    parent['subcategories'].append(cat)
            else:
                structured_list.append(cat)
        return structured_list
    except Exception as e:
        print(f"Error fetching categories for admin management: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def update_category_activation_status(active_ids):
    """
    Efficiently updates the is_active status for a list of category IDs.
    """
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("UPDATE categories SET is_active = FALSE")
        if active_ids:
            placeholders = ', '.join(['%s'] * len(active_ids))
            sql = f"UPDATE categories SET is_active = TRUE WHERE category_id IN ({placeholders})"
            cursor.execute(sql, tuple(active_ids))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating category activation status: {e}")
        return False
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def update_category_name(category_id, new_name):
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT parent_category_id FROM categories WHERE category_id = %s", (category_id,))
        parent = cursor.fetchone()
        parent_id = parent[0] if parent else None
        if parent_id:
            check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id = %s AND category_id != %s"
            cursor.execute(check_sql, (new_name, parent_id, category_id))
        else:
            check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id IS NULL AND category_id != %s"
            cursor.execute(check_sql, (new_name, category_id))
        if cursor.fetchone():
            return False, "Another category with this name already exists at the same level."
        cursor.execute("UPDATE categories SET name = %s WHERE category_id = %s", (new_name, category_id))
        conn.commit()
        return True, "Category renamed successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error updating category {category_id}: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def delete_category(category_id):
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()
        check_query = """
            SELECT p.product_id FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE c.category_id = %s OR c.parent_category_id = %s
            LIMIT 1;
        """
        cursor.execute(check_query, (category_id, category_id))
        if cursor.fetchone():
            conn.rollback()
            return False, "Cannot delete. At least one product is assigned to this category or one of its subcategories."
        cursor.execute("DELETE FROM categories WHERE parent_category_id = %s", (category_id,))
        cursor.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
        conn.commit()
        return True, "Category and its subcategories (if any) were deleted successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error deleting category {category_id}: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def add_new_category(name, parent_id=None):
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        if parent_id:
            check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id = %s"
            cursor.execute(check_sql, (name, parent_id))
        else:
            check_sql = "SELECT category_id FROM categories WHERE name = %s AND parent_category_id IS NULL"
            cursor.execute(check_sql, (name,))
        if cursor.fetchone():
            return False, "A category with this name already exists at this level."
        sql = "INSERT INTO categories (name, parent_category_id) VALUES (%s, %s)"
        cursor.execute(sql, (name, parent_id))
        new_id = cursor.lastrowid
        conn.commit()
        return True, new_id
    except Exception as e:
        conn.rollback()
        print(f"Error adding new category: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

# --- CANCELLATION MANAGEMENT FUNCTIONS FOR ADMIN ---

def get_all_pending_cancellations():
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                cr.request_id,
                cr.reason,
                cr.comments,
                cr.requested_at,
                o.order_number,
                o.total_amount,
                buyer.full_name AS buyer_name,
                seller.business_name AS seller_name
            FROM cancellation_requests cr
            JOIN orders o ON cr.order_id = o.order_id
            JOIN users buyer ON cr.buyer_id = buyer.user_id
            JOIN sellers seller ON cr.seller_id = seller.seller_id
            WHERE cr.status = 'pending'
            ORDER BY cr.requested_at ASC;
        """
        cursor.execute(query)
        requests = cursor.fetchall()
        for req in requests:
            req['total_amount'] = float(req['total_amount'])
            req['requested_at'] = req['requested_at'].strftime('%Y-%m-%d %H:%M')
        return requests
    except Exception as e:
        print(f"Error fetching pending cancellation requests: {e}")
        return []
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def admin_process_cancellation_request(admin_id, request_id, action):
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    if action not in ['approved', 'rejected']:
        return False, "Invalid action specified."

    try:
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        cursor.execute("SELECT * FROM cancellation_requests WHERE request_id = %s", (request_id,))
        request_details = cursor.fetchone()
        if not request_details:
            conn.rollback()
            return False, "Request not found."
        if request_details['status'] != 'pending':
            conn.rollback()
            return False, f"This request has already been {request_details['status']}."

        update_request_sql = "UPDATE cancellation_requests SET status = %s, handled_at = CURRENT_TIMESTAMP, handled_by = %s WHERE request_id = %s"
        cursor.execute(update_request_sql, (action, admin_id, request_id))

        if action == 'approved':
            order_id = request_details['order_id']
            cursor.execute("UPDATE orders SET status = 'cancelled' WHERE order_id = %s", (order_id,))
            cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
            items_to_restock = cursor.fetchall()
            restock_sql = "UPDATE products SET stock_quantity = stock_quantity + %s WHERE product_id = %s"
            for item in items_to_restock:
                cursor.execute(restock_sql, (item['quantity'], item['product_id']))
        
        log_query = "INSERT INTO admin_activities (admin_id, action_type, target_type, target_id, action_details) VALUES (%s, %s, %s, %s, %s)"
        action_details = json.dumps({"request_id": request_id, "action_taken": action})
        log_values = (admin_id, 'process_cancellation', 'order', request_details['order_id'], action_details)
        cursor.execute(log_query, log_values)

        conn.commit()
        return True, f"Cancellation request has been successfully {action}."
        
    except Exception as e:
        conn.rollback()
        print(f"--- ERROR in admin_process_cancellation_request for request {request_id}: {e} ---")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

def get_sales_revenue_over_time():
    """
    Fetches monthly sales data for the entire platform for a line chart.
    We define a "sale" as an order that is processing, shipped, or delivered.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                DATE_FORMAT(order_date, '%Y-%m') AS month,
                SUM(total_amount) AS monthly_sales
            FROM orders
            WHERE status IN ('processing', 'shipped', 'delivered')
            GROUP BY month
            ORDER BY month ASC
            LIMIT 12;
        """
        cursor.execute(query)
        sales_data = cursor.fetchall()
        for row in sales_data:
            row['monthly_sales'] = float(row['monthly_sales'])
        return sales_data
    except Exception as e:
        print(f"Error fetching platform sales over time: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_top_performing_categories():
    """
    Fetches the top 5 best-selling categories based on total sales amount.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                c.name AS category_name,
                SUM(oi.total_price) AS total_sales
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE o.status IN ('processing', 'shipped', 'delivered')
            GROUP BY c.name
            ORDER BY total_sales DESC
            LIMIT 5;
        """
        cursor.execute(query)
        category_data = cursor.fetchall()
        for row in category_data:
            row['total_sales'] = float(row['total_sales'])
        return category_data
    except Exception as e:
        print(f"Error fetching top performing categories: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()



# --- ADD THESE TWO NEW FUNCTIONS AT THE END OF THE FILE ---

def get_paginated_orders_for_admin(category_id=None, search_term=None, page=1, per_page=10):
    """
    Fetches a paginated, searchable, and filterable list of ALL orders for the admin panel.
    """
    conn = get_db_connection()
    if not conn:
        return {'orders': [], 'total_count': 0, 'total_pages': 0}

    try:
        cursor = conn.cursor(dictionary=True)

        # Base query joins all necessary tables for displaying and filtering
        base_query = """
            FROM orders o
            JOIN users u_buyer ON o.buyer_id = u_buyer.user_id
            JOIN sellers s ON o.seller_id = s.seller_id
        """
        where_clauses = []
        params = []

        # Filter by search term (order number, buyer name, or seller name)
        if search_term:
            where_clauses.append("(o.order_number LIKE %s OR u_buyer.full_name LIKE %s OR s.business_name LIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        # Filter by category. This is a complex condition that checks if ANY item
        # in the order belongs to the specified main category or its subcategories.
        if category_id:
            where_clauses.append("""
                EXISTS (
                    SELECT 1 FROM order_items oi
                    JOIN products p ON oi.product_id = p.product_id
                    JOIN categories c ON p.category_id = c.category_id
                    WHERE oi.order_id = o.order_id 
                    AND (c.category_id = %s OR c.parent_category_id = %s)
                )
            """)
            params.extend([category_id, category_id])

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Get total count of orders for pagination
        count_query = f"SELECT COUNT(o.order_id) AS total_count {base_query} {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        
        # Main query to fetch the order data
        query = f"""
            SELECT 
                o.order_id, o.order_number, o.order_date, o.total_amount, o.status,
                u_buyer.full_name AS buyer_name,
                s.business_name AS seller_name
            {base_query}
            {where_sql}
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

        return {
            'orders': orders,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    except Exception as e:
        print(f"Error fetching paginated orders for admin: {e}")
        return {'orders': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_all_main_categories():
    """Fetches a simple list of all main categories for filter dropdowns."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT category_id, name FROM categories WHERE parent_category_id IS NULL ORDER BY name"
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching main categories: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()            






# --- ADD THESE THREE NEW FUNCTIONS AT THE END OF THE FILE ---

# In electronic_ecommerce/models/admin_model.py

def get_paginated_discounts(page=1, per_page=15):
    """Fetches a paginated list of all discounts for the admin panel."""
    conn = get_db_connection()
    if not conn:
        return {'discounts': [], 'total_count': 0, 'total_pages': 0}
    try:
        cursor = conn.cursor(dictionary=True)
        count_query = "SELECT COUNT(discount_id) AS total_count FROM discounts"
        cursor.execute(count_query)
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
        
        offset = (page - 1) * per_page
        
        # --- THIS IS THE NEW, MORE EXPLICIT QUERY ---
        query = """
            SELECT 
                d.discount_id,
                d.code,
                d.discount_type,
                d.value,
                d.min_purchase_amount,
                d.start_date,
                d.end_date,
                d.usage_limit,
                d.times_used,
                d.is_active,
                d.created_at,
                COALESCE(u.full_name, 'N/A') as created_by_name
            FROM discounts d
            LEFT JOIN users u ON d.created_by = u.user_id
            ORDER BY d.created_at DESC
            LIMIT %s OFFSET %s
        """
        # --- END OF CHANGE ---

        cursor.execute(query, (per_page, offset))
        discounts = cursor.fetchall()

        # This conversion loop is still good practice
        for d in discounts:
            if d.get('value'):
                d['value'] = float(d['value'])
            if d.get('min_purchase_amount'):
                d['min_purchase_amount'] = float(d['min_purchase_amount'])

        return {
            'discounts': discounts,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }
    except Exception as e:
        print(f"Error fetching paginated discounts: {e}")
        return {'discounts': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ... (the rest of the file)
def create_new_discount(admin_id, data):
    """Creates a new discount code in the database."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        # Ensure the code is unique
        cursor.execute("SELECT discount_id FROM discounts WHERE code = %s", (data['code'],))
        if cursor.fetchone():
            return False, "This discount code already exists."

        sql = """
            INSERT INTO discounts (code, discount_type, value, min_purchase_amount, 
                                 start_date, end_date, usage_limit, is_active, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Handle optional date fields which might be empty strings
        start_date = data.get('start_date') or None
        end_date = data.get('end_date') or None
        
        values = (
            data['code'].upper(),
            data['discount_type'],
            data['value'],
            data.get('min_purchase_amount', 0),
            start_date,
            end_date,
            data.get('usage_limit', 1),
            data.get('is_active', True),
            admin_id
        )
        cursor.execute(sql, values)
        conn.commit()
        return True, "Discount created successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error creating new discount: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_discount_status(discount_id, is_active):
    """Updates the is_active status of a discount."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        sql = "UPDATE discounts SET is_active = %s WHERE discount_id = %s"
        cursor.execute(sql, (is_active, discount_id))
        conn.commit()
        return True, "Discount status updated."
    except Exception as e:
        conn.rollback()
        print(f"Error updating discount status for ID {discount_id}: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()            



# --- START: NEW FUNCTIONS FOR CAROUSEL MANAGEMENT ---

def get_all_products_for_carousel_management():
    """
    Fetches a simple list of all products (ID, name, seller, carousel status)
    for the admin's carousel management page.
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        # We only need a few columns for the selection list
        query = """
            SELECT p.product_id, p.name, p.is_carousel, s.business_name
            FROM products p
            JOIN sellers s ON p.seller_id = s.seller_id
            WHERE p.is_active = TRUE AND p.is_approved = TRUE
            ORDER BY p.name ASC;
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching all products for carousel management: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_carousel_products(product_ids):
    """
    Updates the is_carousel flag for all products in a single transaction.
    It sets the flag to TRUE for selected IDs and FALSE for all others.
    """
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        conn.start_transaction()

        # Step 1: Set is_carousel to FALSE for ALL products first.
        # This clears the old selection completely.
        cursor.execute("UPDATE products SET is_carousel = FALSE")

        # Step 2: Set is_carousel to TRUE only for the products in the provided list.
        if product_ids: # Only run if the list is not empty
            # Create a string of placeholders like "%s, %s, %s"
            placeholders = ', '.join(['%s'] * len(product_ids))
            update_query = f"UPDATE products SET is_carousel = TRUE WHERE product_id IN ({placeholders})"
            cursor.execute(update_query, tuple(product_ids))
        
        conn.commit()
        return True, "Carousel products updated successfully."
    except Exception as e:
        conn.rollback()
        print(f"Error updating carousel products: {e}")
        return False, "An internal error occurred."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- END: NEW FUNCTIONS ---            