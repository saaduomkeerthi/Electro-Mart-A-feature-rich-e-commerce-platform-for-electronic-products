# # electronic_ecommerce/seller/routes.py

# import os
# import json
# from flask import Blueprint, render_template, jsonify, session, redirect, url_for, request, current_app
# from werkzeug.utils import secure_filename

# # --- UPDATED: Import the new model functions for profile editing ---
# from ..models.seller_model import (
#     get_seller_dashboard_stats,
#     get_seller_product_performance,
#     get_seller_sales_over_time,
#     get_seller_allowed_categories,
#     add_new_product,
#     get_seller_products,
#     get_product_for_editing,
#     update_product,
#     delete_product,
#     get_seller_profile,
#     update_seller_profile
# )
# from ..models.db import get_db_connection

# seller_bp = Blueprint('seller_bp', __name__, url_prefix='/seller', template_folder='templates')

# @seller_bp.before_request
# def check_seller():
#     if session.get('user_role') != 'seller':
#         return redirect(url_for('auth_bp.login'))

# # --- Page Rendering Routes ---
# @seller_bp.route('/dashboard')
# def dashboard():
#     return render_template('seller_dashboard.html')

# @seller_bp.route('/add_product')
# def add_product_page():
#     return render_template('add_product.html')

# @seller_bp.route('/edit_product/<int:product_id>')
# def edit_product_page(product_id):
#     return render_template('edit_product.html', product_id=product_id)

# @seller_bp.route('/edit_profile')
# def edit_profile_page():
#     return render_template('seller_edit_profile.html')

# # --- NEW: Route to render the full product list page ---
# @seller_bp.route('/products')
# def view_products_page():
#     return render_template('view_products.html')


# # --- API Routes ---
# # ... (The rest of your file remains exactly the same) ...
# # --- API Routes for Dashboard and Products (Unchanged) ---
# @seller_bp.route('/api/stats')
# def api_seller_stats():
#     stats = get_seller_dashboard_stats(session.get('user_id'))
#     return jsonify(stats)

# @seller_bp.route('/api/product_performance')
# def api_product_performance():
#     performance_data = get_seller_product_performance(session.get('user_id'))
#     return jsonify(performance_data)

# @seller_bp.route('/api/sales_over_time')
# def api_sales_over_time():
#     sales_data = get_seller_sales_over_time(session.get('user_id'))
#     return jsonify(sales_data)

# @seller_bp.route('/api/allowed_categories')
# def api_get_allowed_categories():
#     categories = get_seller_allowed_categories(session.get('user_id'))
#     return jsonify(categories)

# @seller_bp.route('/api/products')
# def api_seller_products():
#     products = get_seller_products(session.get('user_id'))
#     return jsonify(products)

# @seller_bp.route('/api/product/<int:product_id>')
# def api_get_product_for_edit(product_id):
#     seller_id = session.get('user_id')
#     product_data = get_product_for_editing(seller_id, product_id)
#     if product_data is None:
#         return jsonify({"error": "Product not found or permission denied."}), 404
#     return jsonify(product_data)


# # --- START: NEW API ROUTES FOR SELLER PROFILE ---

# @seller_bp.route('/api/profile', methods=['GET'])
# def api_get_seller_profile():
#     """API endpoint to fetch the current seller's profile data."""
#     seller_id = session.get('user_id')
#     profile_data = get_seller_profile(seller_id)
#     if profile_data:
#         return jsonify(profile_data)
#     return jsonify({"error": "Could not retrieve seller profile."}), 404

# @seller_bp.route('/api/profile', methods=['POST'])
# def api_update_seller_profile():
#     """API endpoint to update the seller's profile."""
#     seller_id = session.get('user_id')
#     profile_data = request.form.to_dict()
#     logo_file = request.files.get('logo_url')
    
#     logo_db_path = None
    
#     # Handle the logo file upload
#     if logo_file and logo_file.filename != '':
#         # Fetch current logo to delete it after a successful update
#         current_profile = get_seller_profile(seller_id)
#         old_logo_path = current_profile.get('logo_url') if current_profile else None

#         # Create a secure, unique filename
#         unique_filename = secure_filename(f"logo_{seller_id}_{logo_file.filename}")
#         full_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
#         logo_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
        
#         # Save the new logo file
#         logo_file.save(full_save_path)
    
#     # Call the model function to update the database
#     success, message = update_seller_profile(seller_id, profile_data, logo_db_path)

#     if success:
#         # If the update was successful and a new logo was uploaded, delete the old one
#         if logo_db_path and old_logo_path:
#             try:
#                 old_logo_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(old_logo_path))
#                 if os.path.exists(old_logo_full_path):
#                     os.remove(old_logo_full_path)
#             except Exception as e:
#                 print(f"Error deleting old logo file {old_logo_path}: {e}")

#         # Update the full_name in the session if it was changed
#         if 'full_name' in profile_data:
#             session['full_name'] = profile_data['full_name']
            
#         return jsonify({"message": message}), 200
#     else:
#         # If the DB update failed, clean up the newly uploaded logo if it exists
#         if logo_db_path:
#             newly_uploaded_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(logo_db_path))
#             if os.path.exists(newly_uploaded_path):
#                 os.remove(newly_uploaded_path)

#         return jsonify({"error": message}), 500

# # --- END: NEW API ROUTES FOR SELLER PROFILE ---


# # --- Product Management API Routes (Unchanged) ---
# @seller_bp.route('/api/add_product', methods=['POST'])
# def api_add_product():
#     seller_id = session.get('user_id')
#     product_data = request.form.to_dict()
#     images = request.files.getlist('images')
#     if not images or images[0].filename == '':
#         return jsonify({"error": "At least one image is required."}), 400
#     db_image_paths, saved_file_paths = [], []
#     for image in images:
#         if image and image.filename != '':
#             sku = product_data.get('sku', 'NOSKU')
#             unique_filename = secure_filename(f"{seller_id}_{sku}_{image.filename}")
#             full_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
#             relative_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
#             image.save(full_save_path)
#             db_image_paths.append(relative_db_path)
#             saved_file_paths.append(full_save_path)
#     specs_data = json.loads(request.form.get('specifications', '[]'))
#     success, message = add_new_product(seller_id, product_data, db_image_paths, specs_data)
#     if success:
#         return jsonify({"message": message}), 201
#     else:
#         for file_path in saved_file_paths:
#             if os.path.exists(file_path): os.remove(file_path)
#         return jsonify({"error": message}), 500

# @seller_bp.route('/api/update_product/<int:product_id>', methods=['POST'])
# def api_update_product(product_id):
#     seller_id = session.get('user_id')
#     product_data = request.form.to_dict()
#     new_images = request.files.getlist('new_images')
#     new_db_image_paths, new_saved_file_paths = [], []
#     for image in new_images:
#         if image and image.filename != '':
#             sku = product_data.get('sku', 'NOSKU')
#             unique_filename = secure_filename(f"{seller_id}_{sku}_new_{image.filename}")
#             full_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
#             relative_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
#             image.save(full_save_path)
#             new_db_image_paths.append(relative_db_path)
#             new_saved_file_paths.append(full_save_path)
#     images_to_delete = request.form.getlist('images_to_delete[]')
#     specs_data = json.loads(request.form.get('specifications', '[]'))
#     image_paths_to_delete_from_disk = []
#     if images_to_delete:
#         conn = get_db_connection()
#         try:
#             cursor = conn.cursor()
#             safe_ids = [int(img_id) for img_id in images_to_delete]
#             query = "SELECT image_url FROM product_images WHERE image_id IN ({})".format(','.join(['%s'] * len(safe_ids)))
#             cursor.execute(query, safe_ids)
#             for row in cursor.fetchall():
#                 image_paths_to_delete_from_disk.append(os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(row[0])))
#         finally:
#             if conn and conn..is_connected(): conn.close()
#     success, message = update_product(seller_id, product_id, product_data, new_db_image_paths, images_to_delete, specs_data)
#     if success:
#         for file_path in image_paths_to_delete_from_disk:
#             if os.path.exists(file_path): os.remove(file_path)
#         return jsonify({"message": message}), 200
#     else:
#         for file_path in new_saved_file_paths:
#             if os.path.exists(file_path): os.remove(file_path)
#         return jsonify({"error": message}), 500

# @seller_bp.route('/api/product/<int:product_id>', methods=['DELETE'])
# def api_delete_product(product_id):
#     seller_id = session.get('user_id')
#     success, message, image_paths = delete_product(seller_id, product_id)
#     if success:
#         for relative_path in image_paths:
#             full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(relative_path))
#             if os.path.exists(full_path):
#                 try: os.remove(full_path)
#                 except OSError as e: print(f"Error deleting product image file {full_path}: {e}")
#         return jsonify({"message": message}), 200
#     else:
#         return jsonify({"error": message}), 403


# electronic_ecommerce/seller/routes.py

# electronic_ecommerce/seller/routes.py
# electronic_ecommerce/seller/routes.py

# electronic_ecommerce/seller/routes.py
import os
import json
from flask import Blueprint, render_template, jsonify, session, redirect, url_for, request, current_app
from werkzeug.utils import secure_filename

# --- START: MODIFIED MODEL IMPORTS ---
from ..models.notification_model import create_notification
from ..models.seller_model import (
    get_seller_dashboard_stats,
    get_seller_product_performance,
    get_seller_sales_over_time,
    get_all_categories_structured,
    add_new_product,
    get_product_for_editing,
    update_product,
    delete_product,
    get_seller_profile,
    update_seller_profile,
    # get_orders_for_seller, # This is now replaced by the new function below
    get_order_details_for_seller,
    update_order_status_for_seller,
    process_cancellation_request,
    get_paginated_seller_products,
    get_seller_product_categories,
    get_orders_for_seller,
    get_sales_by_category,
    get_order_status_summary,
    get_recent_products_for_dashboard # <-- IMPORT THE NEW MAIN FUNCTION
)
# --- END: MODIFIED MODEL IMPORTS ---
from ..models.user_model import change_password, get_all_admins
from ..models.db import get_db_connection
from ..models.order_model import get_cancellation_request_details

seller_bp = Blueprint('seller_bp', __name__, url_prefix='/seller', template_folder='templates')

@seller_bp.before_request
def check_seller():
    if session.get('user_role') != 'seller':
        return redirect(url_for('auth_bp.login'))


@seller_bp.route('/api/products/recent')
def api_get_recent_products():
    """Provides a simple list of the 5 most recent products for the dashboard."""
    products = get_recent_products_for_dashboard(session.get('user_id'))
    return jsonify(products)


@seller_bp.route('/api/sales_by_category')
def api_sales_by_category():
    """Provides data for the sales by category donut chart."""
    data = get_sales_by_category(session.get('user_id'))
    return jsonify(data)

@seller_bp.route('/api/order_status_summary')
def api_order_status_summary():
    """Provides data for the order status pie chart."""
    data = get_order_status_summary(session.get('user_id'))
    return jsonify(data)




# -----------------------------------------------------------------------------
# PAGE RENDERING ROUTES
# -----------------------------------------------------------------------------

@seller_bp.route('/dashboard')
def dashboard():
    return render_template('seller_dashboard.html')

@seller_bp.route('/add_product')
def add_product_page():
    return render_template('add_product.html')

@seller_bp.route('/edit_product/<int:product_id>')
def edit_product_page(product_id):
    return render_template('edit_product.html', product_id=product_id)

@seller_bp.route('/edit_profile')
def edit_profile_page():
    return render_template('seller_edit_profile.html')

@seller_bp.route('/products')
def view_products_page():
    return render_template('view_products.html')

@seller_bp.route('/change_password')
def change_password_page():
    return render_template('change_password.html')

@seller_bp.route('/orders')
def seller_manage_orders_page(): # <--- NEW, SPECIFIC NAME
    return render_template('manage_orders.html')

# -----------------------------------------------------------------------------
# API ROUTES
# -----------------------------------------------------------------------------

@seller_bp.route('/api/change_password', methods=['POST'])
def api_change_password():
    data = request.get_json()
    user_id = session.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not all([user_id, old_password, new_password]):
        return jsonify({"error": "Missing required fields."}), 400
    success, message = change_password(user_id, old_password, new_password)
    if success:
        return jsonify({"message": message}), 200
    else:
        status_code = 400 if "Incorrect old password" in message else 500
        return jsonify({"error": message}), status_code

@seller_bp.route('/api/stats')
def api_seller_stats():
    stats = get_seller_dashboard_stats(session.get('user_id'))
    return jsonify(stats)

@seller_bp.route('/api/product_performance')
def api_product_performance():
    performance_data = get_seller_product_performance(session.get('user_id'))
    return jsonify(performance_data)

@seller_bp.route('/api/sales_over_time')
def api_sales_over_time():
    sales_data = get_seller_sales_over_time(session.get('user_id'))
    return jsonify(sales_data)

@seller_bp.route('/api/categories')
def api_get_categories():
    categories = get_all_categories_structured()
    return jsonify(categories)

@seller_bp.route('/api/products')
def api_seller_products():
    seller_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', None)
    category_id = request.args.get('category_id', None, type=int)
    product_data = get_paginated_seller_products(
        seller_id=seller_id,
        category_id=category_id,
        search_term=search_term,
        page=page,
        per_page=10
    )
    return jsonify(product_data)

@seller_bp.route('/api/my_categories')
def api_get_my_categories():
    seller_id = session.get('user_id')
    categories = get_seller_product_categories(seller_id)
    return jsonify(categories)

@seller_bp.route('/api/product/<int:product_id>')
def api_get_product_for_edit(product_id):
    seller_id = session.get('user_id')
    product_data = get_product_for_editing(seller_id, product_id)
    if product_data is None:
        return jsonify({"error": "Product not found or permission denied."}), 404
    return jsonify(product_data)

@seller_bp.route('/api/profile', methods=['GET', 'POST'])
def api_seller_profile():
    seller_id = session.get('user_id')
    if request.method == 'POST':
        profile_data = request.form.to_dict()
        logo_file = request.files.get('logo_url')
        profile_image_file = request.files.get('profile_image')
        logo_db_path = None
        profile_image_db_path = None
        if logo_file and logo_file.filename != '':
            current_profile = get_seller_profile(seller_id)
            old_logo_path = current_profile.get('logo_url') if current_profile else None
            unique_filename = secure_filename(f"logo_{seller_id}_{logo_file.filename}")
            full_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            logo_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
            logo_file.save(full_save_path)
        if profile_image_file and profile_image_file.filename != '':
            unique_filename = secure_filename(f"profile_{seller_id}_{profile_image_file.filename}")
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            profile_image_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
            profile_image_file.save(save_path)
        success, message, old_profile_image = update_seller_profile(seller_id, profile_data, logo_db_path, profile_image_db_path)
        if success:
            if logo_db_path and old_logo_path:
                try:
                    old_logo_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(old_logo_path))
                    if os.path.exists(old_logo_full_path): os.remove(old_logo_full_path)
                except Exception as e: print(f"Error deleting old logo file {old_logo_path}: {e}")
            if old_profile_image:
                try:
                    old_profile_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(old_profile_image))
                    if os.path.exists(old_profile_full_path): os.remove(old_profile_full_path)
                except Exception as e: print(f"Error deleting old profile image {old_profile_image}: {e}")
            if 'full_name' in profile_data: session['full_name'] = profile_data['full_name']
            return jsonify({"message": message}), 200
        else:
            if logo_db_path:
                logo_path_to_check = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(logo_db_path))
                if os.path.exists(logo_path_to_check): os.remove(logo_path_to_check)
            if profile_image_db_path:
                profile_path_to_check = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(profile_image_db_path))
                if os.path.exists(profile_path_to_check): os.remove(profile_path_to_check)
            return jsonify({"error": message}), 500
    profile_data = get_seller_profile(seller_id)
    if profile_data:
        if profile_data.get('profile_image'):
            profile_data['profile_image_url'] = url_for('serve_upload', filename=os.path.basename(profile_data['profile_image']))
        else:
            profile_data['profile_image_url'] = None
        return jsonify(profile_data)
    return jsonify({"error": "Could not retrieve seller profile."}), 404

@seller_bp.route('/api/add_product', methods=['POST'])
def api_add_product():
    seller_id = session.get('user_id')
    product_data = request.form.to_dict()
    images = request.files.getlist('images')
    if not images or images[0].filename == '':
        return jsonify({"error": "At least one image is required."}), 400
    db_image_paths, saved_file_paths = [], []
    for image in images:
        if image and image.filename != '':
            sku = product_data.get('sku', 'NOSKU')
            unique_filename = secure_filename(f"{seller_id}_{sku}_{image.filename}")
            full_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            relative_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
            image.save(full_save_path)
            db_image_paths.append(relative_db_path)
            saved_file_paths.append(full_save_path)
    specs_data = json.loads(request.form.get('specifications', '[]'))
    success, message = add_new_product(seller_id, product_data, db_image_paths, specs_data)
    if success:
        return jsonify({"message": message}), 201
    else:
        for file_path in saved_file_paths:
            if os.path.exists(file_path): os.remove(file_path)
        return jsonify({"error": message}), 500

@seller_bp.route('/api/update_product/<int:product_id>', methods=['POST'])
def api_update_product(product_id):
    seller_id = session.get('user_id')
    product_data = request.form.to_dict()
    new_images = request.files.getlist('new_images')
    new_db_image_paths, new_saved_file_paths = [], []
    for image in new_images:
        if image and image.filename != '':
            sku = product_data.get('sku', 'NOSKU')
            unique_filename = secure_filename(f"{seller_id}_{sku}_new_{image.filename}")
            full_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            relative_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
            image.save(full_save_path)
            new_db_image_paths.append(relative_db_path)
            new_saved_file_paths.append(full_save_path)
    images_to_delete = request.form.getlist('images_to_delete[]')
    specs_data = json.loads(request.form.get('specifications', '[]'))
    image_paths_to_delete_from_disk = []
    if images_to_delete:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            safe_ids = [int(img_id) for img_id in images_to_delete]
            query = "SELECT image_url FROM product_images WHERE image_id IN ({})".format(','.join(['%s'] * len(safe_ids)))
            cursor.execute(query, safe_ids)
            for row in cursor.fetchall():
                image_paths_to_delete_from_disk.append(os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(row[0])))
        finally:
            if conn and conn.is_connected(): conn.close()
    success, message = update_product(seller_id, product_id, product_data, new_db_image_paths, images_to_delete, specs_data)
    if success:
        for file_path in image_paths_to_delete_from_disk:
            if os.path.exists(file_path): os.remove(file_path)
        return jsonify({"message": message}), 200
    else:
        for file_path in new_saved_file_paths:
            if os.path.exists(file_path): os.remove(file_path)
        return jsonify({"error": message}), 500

@seller_bp.route('/api/product/<int:product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    seller_id = session.get('user_id')
    success, message, image_paths = delete_product(seller_id, product_id)
    if success:
        for relative_path in image_paths:
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(relative_path))
            if os.path.exists(full_path):
                try: os.remove(full_path)
                except OSError as e: print(f"Error deleting product image file {full_path}: {e}")
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 403

# --- START: MODIFIED API ENDPOINT FOR SELLER ORDERS ---
@seller_bp.route('/api/orders')
def api_get_seller_orders():
    """
    Handles fetching a seller's orders with optional filters, search, and pagination.
    """
    seller_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', None)
    status = request.args.get('status', None)

    # Call the new, powerful function from our model
    order_data = get_orders_for_seller(
        seller_id=seller_id,
        status=status,
        search_term=search_term,
        page=page,
        per_page=10 # You can adjust items per page here
    )
    return jsonify(order_data)
# --- END: MODIFIED API ENDPOINT ---

@seller_bp.route('/api/order/<int:order_id>')
def api_get_seller_order_details(order_id):
    seller_id = session.get('user_id')
    order_details = get_order_details_for_seller(seller_id, order_id)
    if order_details:
        return jsonify(order_details)
    return jsonify({"error": "Order not found or you do not have permission to view it."}), 404

@seller_bp.route('/api/order/update_status', methods=['POST'])
def api_update_order_status():
    seller_id = session.get('user_id')
    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('new_status')

    if not order_id or not new_status:
        return jsonify({"error": "Missing order_id or new_status."}), 400

    success, message = update_order_status_for_seller(seller_id, order_id, new_status)

    if success:
        # Simplified notification logic
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT buyer_id, order_number FROM orders WHERE order_id = %s", (order_id,))
            order_info = cursor.fetchone()
            if order_info:
                notif_message = f"An update on your order #{order_info['order_number']}: it has been {new_status}."
                link = url_for('buyer_bp.order_details_page', order_id=order_id)
                create_notification(order_info['buyer_id'], notif_message, link)
            cursor.close()
            conn.close()
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 403

@seller_bp.route('/api/order/handle_cancellation', methods=['POST'])
def api_handle_cancellation():
    seller_id = session.get('user_id')
    data = request.get_json()
    request_id = data.get('request_id')
    action = data.get('action')

    if not all([request_id, action]):
        return jsonify({"error": "Missing required data (request_id, action)."}), 400

    request_details = get_cancellation_request_details(request_id)
    if not request_details:
        return jsonify({"error": "Cancellation request not found."}), 404

    success, message = process_cancellation_request(seller_id, request_id, action)

    if success:
        buyer_id = request_details['buyer_id']
        order_number = request_details['order_number']
        
        buyer_message = f"Your cancellation request for Order #{order_number} has been {action} by the seller."
        buyer_link = url_for('buyer_bp.order_details_page', order_id=request_details['order_id'])
        create_notification(buyer_id, buyer_message, buyer_link)
        
        admins = get_all_admins()
        admin_message = f"Seller '{session['full_name']}' has {action} the cancellation request for Order #{order_number}."
        admin_link = url_for('admin_bp.manage_cancellations_page')
        for admin in admins:
            create_notification(admin['user_id'], admin_message, admin_link)
            
        return jsonify({"message": message}), 200
    else:
        status_code = 409 if "already been" in message else 500
        return jsonify({"error": message}), status_code