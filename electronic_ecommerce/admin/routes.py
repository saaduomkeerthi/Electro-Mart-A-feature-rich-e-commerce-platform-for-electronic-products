# # electronic_ecommerce/admin/routes.py

# import os
# from flask import Blueprint, render_template, jsonify, session, redirect, url_for, request, current_app
# from werkzeug.utils import secure_filename
# from ..models.notification_model import create_notification
# from ..models.order_model import get_cancellation_request_details

# # All necessary model functions are imported here cleanly
# from ..models.admin_model import (
#     get_dashboard_stats,
#     get_recent_orders,
#     get_new_sellers,
#     get_all_sellers,
#     update_seller_status,
#     get_all_products,
#     update_product_status,
#     delete_product,
#     get_all_users,
#     update_user_status,
#     get_all_categories_for_management,
#     update_category_activation_status,
#     add_new_category,
#     update_category_name,
#     delete_category,
#     get_all_pending_cancellations,
#     admin_process_cancellation_request
# )
# # --- USER MODEL IMPORTS (Already correct) ---
# from ..models.user_model import get_user_by_id, update_profile_details, change_password

# # Define the blueprint for all admin-related routes
# admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin', template_folder='templates')

# @admin_bp.before_request
# def check_admin():
#     """Protects all routes in this blueprint, redirecting non-admins to the login page."""
#     if session.get('user_role') != 'admin':
#         return redirect(url_for('auth_bp.login'))

# # =============================================================================
# # PAGE RENDERING ROUTES (Routes that show an HTML page)
# # =============================================================================

# @admin_bp.route('/dashboard')
# def dashboard():
#     return render_template('admin_dashboard.html')

# @admin_bp.route('/manage_sellers')
# def manage_sellers_page():
#     return render_template('manage_sellers.html')

# @admin_bp.route('/manage_products')
# def manage_products_page():
#     return render_template('manage_products.html')

# @admin_bp.route('/manage_users')
# def manage_users_page():
#     return render_template('users.html')

# @admin_bp.route('/manage_cancellations')
# def manage_cancellations_page():
#     """Renders the page for managing order cancellation requests."""
#     return render_template('manage_cancellations.html')

# @admin_bp.route('/add_category')
# def add_category_page():
#     return render_template('add_category.html')

# @admin_bp.route('/manage_categories')
# def manage_categories_page():
#     return render_template('manage_categories.html')

# @admin_bp.route('/profile')
# def admin_profile_page():
#     """Renders the admin's own profile page."""
#     return render_template('admin_profile.html')

# @admin_bp.route('/change_password')
# def admin_change_password_page():
#     """Renders the admin's change password page."""
#     return render_template('admin_change_password.html')


# # =============================================================================
# # API ROUTES (Routes that return JSON data for JavaScript)
# # =============================================================================

# # --- Dashboard & Profile APIs ---
# @admin_bp.route('/api/stats')
# def api_stats():
#     stats = get_dashboard_stats()
#     return jsonify(stats)

# @admin_bp.route('/api/recent_orders')
# def api_recent_orders():
#     orders = get_recent_orders()
#     return jsonify(orders)

# @admin_bp.route('/api/new_sellers')
# def api_new_sellers():
#     sellers = get_new_sellers()
#     return jsonify(sellers)

# @admin_bp.route('/api/profile', methods=['GET', 'POST'])
# def api_admin_profile():
#     admin_id = session.get('user_id')
#     if request.method == 'POST':
#         profile_data = request.form.to_dict()
#         profile_image_file = request.files.get('profile_image')
#         image_db_path = None
#         if not profile_data.get('full_name'):
#             return jsonify({"error": "Full Name cannot be empty."}), 400
#         if profile_image_file and profile_image_file.filename != '':
#             unique_filename = secure_filename(f"profile_{admin_id}_{profile_image_file.filename}")
#             save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
#             image_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
#             profile_image_file.save(save_path)
#         success, message, old_image_path = update_profile_details(admin_id, profile_data, image_db_path)
#         if success:
#             session['full_name'] = profile_data.get('full_name')
#             if old_image_path:
#                 try:
#                     old_file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(old_image_path))
#                     if os.path.exists(old_file_full_path):
#                         os.remove(old_file_full_path)
#                 except Exception as e:
#                     print(f"Error deleting old profile image {old_image_path}: {e}")
#             return jsonify({"message": message}), 200
#         else:
#             if image_db_path:
#                 os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(image_db_path)))
#             return jsonify({"error": message}), 500
#     user_data = get_user_by_id(admin_id)
#     if user_data:
#         image_url = None
#         if user_data.get('profile_image'):
#             image_url = url_for('serve_upload', filename=os.path.basename(user_data['profile_image']))
#         profile_info = {
#             "full_name": user_data['full_name'], "email": user_data['email'],
#             "phone": user_data.get('phone'), "profile_image_url": image_url
#         }
#         return jsonify(profile_info)
#     return jsonify({"error": "Admin profile not found."}), 404

# @admin_bp.route('/api/password/change', methods=['POST'])
# def api_admin_change_password():
#     admin_id = session.get('user_id')
#     data = request.get_json()
#     old_password = data.get('old_password')
#     new_password = data.get('new_password')
#     if not all([old_password, new_password]):
#         return jsonify({"error": "All password fields are required."}), 400
#     success, message = change_password(admin_id, old_password, new_password)
#     if success:
#         return jsonify({"message": message}), 200
#     else:
#         status_code = 400 if "Incorrect" in message else 500
#         return jsonify({"error": message}), status_code

# # --- Cancellation Management APIs ---
# @admin_bp.route('/api/cancellations/pending')
# def api_get_pending_cancellations():
#     requests_data = get_all_pending_cancellations()
#     return jsonify(requests_data)

# @admin_bp.route('/api/cancellations/process', methods=['POST'])
# def api_process_cancellation():
#     admin_id = session.get('user_id')
#     data = request.get_json()
#     request_id = data.get('request_id')
#     action = data.get('action')

#     if not all([request_id, action]):
#         return jsonify({"error": "Missing required data."}), 400
    
#     request_details = get_cancellation_request_details(request_id)
#     if not request_details:
#         return jsonify({"error": "Request not found or already processed."}), 404

#     success, message = admin_process_cancellation_request(admin_id, request_id, action)

#     if success:
#         buyer_id = request_details['buyer_id']
#         seller_id = request_details['seller_id']
#         order_number = request_details['order_number']
        
#         buyer_message = f"Your cancellation request for Order #{order_number} has been {action}."
#         buyer_link = url_for('buyer_bp.order_details_page', order_id=request_details['order_id'])
#         create_notification(buyer_id, buyer_message, buyer_link)
        
#         seller_message = f"The cancellation request for Order #{order_number} was {action} by an admin."
#         seller_link = url_for('seller_bp.manage_orders_page')
#         create_notification(seller_id, seller_message, seller_link)
        
#         return jsonify({"message": message}), 200
#     else:
#         return jsonify({"error": message}), 500

# # --- Seller Management APIs ---
# @admin_bp.route('/api/sellers')
# def api_get_all_sellers():
#     sellers = get_all_sellers()
#     return jsonify(sellers)

# # --- THIS IS THE ONE AND ONLY VERSION OF THIS FUNCTION ---
# @admin_bp.route('/api/seller/update_status', methods=['POST'])
# def api_update_seller_status():
#     data = request.get_json()
#     seller_id = data.get('seller_id')
#     new_status = data.get('status')
#     admin_id = session.get('user_id')

#     if not all([seller_id, new_status, admin_id]):
#         return jsonify({"error": "Missing required data."}), 400

#     success = update_seller_status(seller_id, new_status, admin_id)

#     if success:
#         if new_status == 'approved':
#             message = "Congratulations! Your seller application has been approved."
#             link = url_for('seller_bp.dashboard')
#             create_notification(seller_id, message, link)
#         return jsonify({"message": f"Seller status updated to {new_status}."}), 200
#     else:
#         return jsonify({"error": "Failed to update seller status."}), 500

# # --- Product Management APIs ---
# @admin_bp.route('/api/products')
# def api_get_all_products():
#     products = get_all_products()
#     return jsonify(products)

# @admin_bp.route('/api/product/update_status', methods=['POST'])
# def api_update_product_status():
#     data = request.get_json()
#     admin_id = session.get('user_id')
#     product_id = data.get('product_id')
#     field_to_update = data.get('field')
#     new_value = data.get('value')
#     if not all([product_id, field_to_update, admin_id]) or new_value is None:
#         return jsonify({"error": "Missing required data."}), 400
#     success = update_product_status(product_id, field_to_update, new_value, admin_id)
#     if success:
#         return jsonify({"message": "Product status updated successfully."}), 200
#     else:
#         return jsonify({"error": "Failed to update product status."}), 500

# @admin_bp.route('/api/product/delete', methods=['POST'])
# def api_delete_product():
#     data = request.get_json()
#     admin_id = session.get('user_id')
#     product_id = data.get('product_id')
#     if not all([product_id, admin_id]):
#         return jsonify({"error": "Missing required data."}), 400
#     success = delete_product(product_id, admin_id)
#     if success:
#         return jsonify({"message": "Product deleted successfully."}), 200
#     else:
#         return jsonify({"error": "Failed to delete product."}), 500

# # --- User Management APIs ---
# @admin_bp.route('/api/users')
# def api_get_all_users():
#     users = get_all_users()
#     return jsonify(users)

# @admin_bp.route('/api/user/update_status', methods=['POST'])
# def api_update_user_status():
#     data = request.get_json()
#     admin_id = session.get('user_id')
#     user_id_to_update = data.get('user_id')
#     is_active = data.get('is_active')
#     if not all([user_id_to_update, admin_id]) or is_active is None:
#         return jsonify({"error": "Missing required data."}), 400
#     if user_id_to_update == admin_id:
#         return jsonify({"error": "You cannot deactivate your own account."}), 403
#     success = update_user_status(user_id_to_update, is_active, admin_id)
#     if success:
#         return jsonify({"message": "User status updated successfully."}), 200
#     else:
#         return jsonify({"error": "Failed to update user status."}), 500

# # --- Store Category Management APIs ---
# @admin_bp.route('/api/manageable_categories')
# def api_get_all_manageable_categories():
#     categories = get_all_categories_for_management()
#     return jsonify(categories)

# @admin_bp.route('/api/categories/add', methods=['POST'])
# def api_add_category():
#     data = request.get_json()
#     main_category_name = data.get('main_category_name', '').strip()
#     sub_category_names = data.get('sub_category_names', [])
#     if not main_category_name:
#         return jsonify({"error": "Main Category name cannot be empty."}), 400
#     success, new_id_or_message = add_new_category(main_category_name, parent_id=None)
#     if not success:
#         return jsonify({"error": new_id_or_message}), 500
#     new_parent_id = new_id_or_message
#     if sub_category_names:
#         for sub_name in sub_category_names:
#             sub_name_clean = sub_name.strip()
#             if sub_name_clean:
#                 add_new_category(sub_name_clean, new_parent_id)
#     return jsonify({"message": "Category and its subcategories were added successfully!"}), 201

# @admin_bp.route('/api/categories/update_status', methods=['POST'])
# def api_update_category_status():
#     data = request.get_json()
#     active_ids = data.get('active_ids', [])
#     if not isinstance(active_ids, list):
#         return jsonify({"error": "Invalid data format."}), 400
#     success = update_category_activation_status(active_ids)
#     if success:
#         return jsonify({"message": "Category visibility updated successfully."}), 200
#     else:
#         return jsonify({"error": "Failed to update category statuses."}), 500

# @admin_bp.route('/api/categories/update', methods=['POST'])
# def api_update_category():
#     data = request.get_json()
#     category_id = data.get('category_id')
#     new_name = data.get('new_name')
#     if not all([category_id, new_name]):
#         return jsonify({"error": "Missing required data."}), 400
#     success, message = update_category_name(category_id, new_name)
#     if success:
#         return jsonify({"message": message}), 200
#     else:
#         return jsonify({"error": message}), 409

# @admin_bp.route('/api/categories/delete', methods=['POST'])
# def api_delete_category():
#     data = request.get_json()
#     category_id = data.get('category_id')
#     if not category_id:
#         return jsonify({"error": "Missing category ID."}), 400
#     success, message = delete_category(category_id)
#     if success:
#         return jsonify({"message": message}), 200
#     else:
#         return jsonify({"error": message}), 409








# electronic_ecommerce/admin/routes.py
import os
from flask import Blueprint, render_template, jsonify, session, redirect, url_for, request, current_app, flash
from werkzeug.utils import secure_filename
from ..models.notification_model import create_notification
from ..models.order_model import get_cancellation_request_details

# --- START: MODIFIED IMPORT BLOCK ---
from ..models.admin_model import (
    get_dashboard_stats,
    get_recent_orders,
    get_new_sellers,
    get_all_sellers,
    update_seller_status,
    update_product_status,
    delete_product,
    get_all_users,
    update_user_status,
    get_structured_paginated_categories,
    update_category_activation_status,
    add_new_category,
    update_category_name,
    delete_category,
    get_all_pending_cancellations,
    admin_process_cancellation_request,
    get_sales_revenue_over_time,
    get_top_performing_categories,
    get_paginated_products_for_admin, 
    get_all_main_categories,
    # ADDED: Import for seller category permissions
    get_seller_by_id,
    get_all_active_main_categories,
    get_seller_allowed_category_ids,
    update_seller_category_permissions,
    get_paginated_orders_for_admin,
    get_paginated_discounts,
    create_new_discount,
    update_discount_status,
    get_all_products_for_carousel_management,
    update_carousel_products 
)
# --- END: MODIFIED IMPORT BLOCK ---

from ..models.user_model import get_user_by_id, update_profile_details, change_password

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin', template_folder='templates')

@admin_bp.before_request
def check_admin():
    """Protects all routes in this blueprint, redirecting non-admins to the login page."""
    if session.get('user_role') != 'admin':
        return redirect(url_for('auth_bp.login'))

# =============================================================================
# PAGE RENDERING ROUTES
# =============================================================================

@admin_bp.route('/dashboard')
def dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/manage_sellers')
def manage_sellers_page():
    return render_template('manage_sellers.html')
    
# ADDED: Route for the new permissions page
@admin_bp.route('/seller_permissions/<int:seller_id>')
def seller_permissions_page(seller_id):
    seller = get_seller_by_id(seller_id)
    if not seller:
        flash('Seller not found.', 'danger')
        return redirect(url_for('admin_bp.manage_sellers_page'))
    return render_template('manage_permissions.html', seller=seller)

@admin_bp.route('/manage_products')
def manage_products_page():
    return render_template('manage_products.html')

@admin_bp.route('/manage_users')
def manage_users_page():
    return render_template('users.html')

@admin_bp.route('/manage_cancellations')
def manage_cancellations_page():
    return render_template('manage_cancellations.html')

@admin_bp.route('/add_category')
def add_category_page():
    return render_template('add_category.html')

@admin_bp.route('/manage_categories')
def manage_categories_page():
    return render_template('manage_categories.html')

@admin_bp.route('/profile')
def admin_profile_page():
    return render_template('admin_profile.html')

@admin_bp.route('/change_password')
def admin_change_password_page():
    return render_template('admin_change_password.html')


# =============================================================================
# API ROUTES
# =============================================================================

# --- Dashboard & Profile APIs ---
@admin_bp.route('/api/stats')
def api_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)

@admin_bp.route('/api/recent_orders')
def api_recent_orders():
    orders = get_recent_orders()
    return jsonify(orders)

@admin_bp.route('/api/new_sellers')
def api_new_sellers():
    sellers = get_new_sellers()
    return jsonify(sellers)

@admin_bp.route('/api/profile', methods=['GET', 'POST'])
def api_admin_profile():
    admin_id = session.get('user_id')
    if request.method == 'POST':
        profile_data = request.form.to_dict()
        profile_image_file = request.files.get('profile_image')
        image_db_path = None
        if not profile_data.get('full_name'):
            return jsonify({"error": "Full Name cannot be empty."}), 400
        if profile_image_file and profile_image_file.filename != '':
            unique_filename = secure_filename(f"profile_{admin_id}_{profile_image_file.filename}")
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            image_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
            profile_image_file.save(save_path)
        success, message, old_image_path = update_profile_details(admin_id, profile_data, image_db_path)
        if success:
            session['full_name'] = profile_data.get('full_name')
            if old_image_path:
                try:
                    old_file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(old_image_path))
                    if os.path.exists(old_file_full_path): os.remove(old_file_full_path)
                except Exception as e: print(f"Error deleting old profile image {old_image_path}: {e}")
            return jsonify({"message": message}), 200
        else:
            if image_db_path:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(image_db_path)))
            return jsonify({"error": message}), 500
    user_data = get_user_by_id(admin_id)
    if user_data:
        image_url = None
        if user_data.get('profile_image'):
            image_url = url_for('serve_upload', filename=os.path.basename(user_data['profile_image']))
        profile_info = {"full_name": user_data['full_name'], "email": user_data['email'], "phone": user_data.get('phone'), "profile_image_url": image_url}
        return jsonify(profile_info)
    return jsonify({"error": "Admin profile not found."}), 404

@admin_bp.route('/api/password/change', methods=['POST'])
def api_admin_change_password():
    admin_id = session.get('user_id')
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not all([old_password, new_password]):
        return jsonify({"error": "All password fields are required."}), 400
    success, message = change_password(admin_id, old_password, new_password)
    if success:
        return jsonify({"message": message}), 200
    else:
        status_code = 400 if "Incorrect" in message else 500
        return jsonify({"error": message}), status_code

# --- Cancellation Management APIs ---
@admin_bp.route('/api/cancellations/pending')
def api_get_pending_cancellations():
    requests_data = get_all_pending_cancellations()
    return jsonify(requests_data)

@admin_bp.route('/api/cancellations/process', methods=['POST'])
def api_process_cancellation():
    admin_id = session.get('user_id')
    data = request.get_json()
    request_id, action = data.get('request_id'), data.get('action')
    if not all([request_id, action]):
        return jsonify({"error": "Missing required data."}), 400
    request_details = get_cancellation_request_details(request_id)
    if not request_details:
        return jsonify({"error": "Request not found or already processed."}), 404
    success, message = admin_process_cancellation_request(admin_id, request_id, action)
    if success:
        buyer_id, seller_id, order_number = request_details['buyer_id'], request_details['seller_id'], request_details['order_number']
        buyer_message = f"Your cancellation request for Order #{order_number} has been {action}."
        buyer_link = url_for('buyer_bp.order_details_page', order_id=request_details['order_id'])
        create_notification(buyer_id, buyer_message, buyer_link)
        seller_message = f"The cancellation request for Order #{order_number} was {action} by an admin."
        seller_link = url_for('seller_bp.manage_orders_page')
        create_notification(seller_id, seller_message, seller_link)
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500

# --- Seller Management APIs ---

# --- START: THIS IS THE MODIFIED API ENDPOINT ---
@admin_bp.route('/api/sellers')
def api_get_all_sellers():
    """
    Handles fetching sellers with optional filters, search, and pagination.
    """
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', None)
    status = request.args.get('status', None)

    seller_data = get_all_sellers(
        status=status,
        search_term=search_term,
        page=page,
        per_page=10
    )
    return jsonify(seller_data)
# --- END: MODIFIED API ENDPOINT ---


@admin_bp.route('/api/seller/update_status', methods=['POST'])
def api_update_seller_status():
    data = request.get_json()
    seller_id, new_status, admin_id = data.get('seller_id'), data.get('status'), session.get('user_id')
    if not all([seller_id, new_status, admin_id]):
        return jsonify({"error": "Missing required data."}), 400
    success = update_seller_status(seller_id, new_status, admin_id)
    if success:
        if new_status == 'approved':
            message = "Congratulations! Your seller application has been approved."
            link = url_for('seller_bp.dashboard')
            create_notification(seller_id, message, link)
        return jsonify({"message": f"Seller status updated to {new_status}."}), 200
    else:
        return jsonify({"error": "Failed to update seller status."}), 500

# ADDED: New API endpoint for seller category permissions
@admin_bp.route('/api/seller/<int:seller_id>/permissions', methods=['GET', 'POST'])
def api_seller_permissions(seller_id):
    admin_id = session.get('user_id')
    if request.method == 'POST':
        data = request.get_json()
        category_ids = data.get('category_ids', [])
        success, message = update_seller_category_permissions(seller_id, category_ids, admin_id)
        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 500
    
    # GET request logic
    all_categories = get_all_active_main_categories()
    assigned_ids = get_seller_allowed_category_ids(seller_id)
    return jsonify({
        'all_categories': all_categories,
        'assigned_ids': assigned_ids
    })

# --- Product Management APIs (and the rest of the file is unchanged) ---
# ...

# --- Product Management APIs ---
@admin_bp.route('/api/products')
def api_get_all_products():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', None)
    category_id = request.args.get('category_id', None, type=int)
    product_data = get_paginated_products_for_admin(
        category_id=category_id,
        search_term=search_term,
        page=page,
        per_page=10
    )
    return jsonify(product_data)

@admin_bp.route('/api/product/update_status', methods=['POST'])
def api_update_product_status():
    data = request.get_json()
    admin_id = session.get('user_id')
    product_id = data.get('product_id')
    field_to_update = data.get('field')
    new_value = data.get('value')
    if not all([product_id, field_to_update, admin_id]) or new_value is None:
        return jsonify({"error": "Missing required data."}), 400
    success = update_product_status(product_id, field_to_update, new_value, admin_id)
    if success:
        return jsonify({"message": "Product status updated successfully."}), 200
    else:
        return jsonify({"error": "Failed to update product status."}), 500

@admin_bp.route('/api/product/delete', methods=['POST'])
def api_delete_product():
    data = request.get_json()
    admin_id = session.get('user_id')
    product_id = data.get('product_id')
    if not all([product_id, admin_id]):
        return jsonify({"error": "Missing required data."}), 400
    success = delete_product(product_id, admin_id)
    if success:
        return jsonify({"message": "Product deleted successfully."}), 200
    else:
        return jsonify({"error": "Failed to delete product."}), 500

# --- User Management APIs ---

# --- START: THIS IS THE MODIFIED API ENDPOINT ---
@admin_bp.route('/api/users')
def api_get_all_users():
    """
    Handles fetching users with optional filters, search, and pagination.
    """
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', None)
    role = request.args.get('role', None)

    # Call the updated model function with the parameters
    user_data = get_all_users(
        role=role,
        search_term=search_term,
        page=page,
        per_page=10 # You can adjust items per page here
    )
    return jsonify(user_data)
# --- END: MODIFIED API ENDPOINT ---


@admin_bp.route('/api/user/<int:user_id>')
def api_get_user_details(user_id):
    if session.get('user_role') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    user_data = get_user_by_id(user_id)

    if user_data:
        if user_data.get('profile_image'):
            user_data['profile_image_url'] = url_for('serve_upload', filename=os.path.basename(user_data['profile_image']))
        else:
            user_data['profile_image_url'] = url_for('static', filename='images/placeholder_profile.png')
        return jsonify(user_data)
    else:
        return jsonify({"error": "User not found"}), 404

@admin_bp.route('/api/user/update_status', methods=['POST'])
def api_update_user_status():
    data = request.get_json()
    admin_id = session.get('user_id')
    user_id_to_update = data.get('user_id')
    is_active = data.get('is_active')
    if not all([user_id_to_update, admin_id]) or is_active is None:
        return jsonify({"error": "Missing required data."}), 400
    if int(user_id_to_update) == int(admin_id):
        return jsonify({"error": "You cannot deactivate your own account."}), 403
    success = update_user_status(user_id_to_update, is_active, admin_id)
    if success:
        return jsonify({"message": "User status updated successfully."}), 200
    else:
        return jsonify({"error": "Failed to update user status."}), 500

# --- Store Category Management APIs ---

@admin_bp.route('/api/main_categories')
def api_get_main_categories():
    """Provides a simple list of main categories for the filter dropdown."""
    categories = get_all_main_categories()
    return jsonify(categories)

@admin_bp.route('/api/manageable_categories')
def api_get_all_manageable_categories():
    search_term = request.args.get('search', None)
    page = request.args.get('page', 1, type=int)
    per_page = 10 
    category_data = get_structured_paginated_categories(search_term=search_term, page=page, per_page=per_page)
    return jsonify(category_data)

@admin_bp.route('/api/categories/add', methods=['POST'])
def api_add_category():
    data = request.get_json()
    main_category_name = data.get('main_category_name', '').strip()
    sub_category_names = data.get('sub_category_names', [])
    if not main_category_name:
        return jsonify({"error": "Main Category name cannot be empty."}), 400
    success, new_id_or_message = add_new_category(main_category_name, parent_id=None)
    if not success:
        return jsonify({"error": new_id_or_message}), 500
    new_parent_id = new_id_or_message
    if sub_category_names:
        for sub_name in sub_category_names:
            sub_name_clean = sub_name.strip()
            if sub_name_clean:
                add_new_category(sub_name_clean, new_parent_id)
    
    flash("Category was added successfully!", "success")
    
    return jsonify({"message": "Category and its subcategories were added successfully!"}), 201

@admin_bp.route('/api/categories/update_status', methods=['POST'])
def api_update_category_status():
    data = request.get_json()
    active_ids = data.get('active_ids', [])
    if not isinstance(active_ids, list):
        return jsonify({"error": "Invalid data format."}), 400
    success = update_category_activation_status(active_ids)
    if success:
        return jsonify({"message": "Category visibility updated successfully."}), 200
    else:
        return jsonify({"error": "Failed to update category statuses."}), 500

@admin_bp.route('/api/categories/update', methods=['POST'])
def api_update_category():
    data = request.get_json()
    category_id = data.get('category_id')
    new_name = data.get('new_name')
    if not all([category_id, new_name]):
        return jsonify({"error": "Missing required data."}), 400
    success, message = update_category_name(category_id, new_name)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 409

@admin_bp.route('/api/categories/delete', methods=['POST'])
def api_delete_category():
    data = request.get_json()
    category_id = data.get('category_id')
    if not category_id:
        return jsonify({"error": "Missing category ID."}), 400
    success, message = delete_category(category_id)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 409
    
# Dashboard Chart APIs
@admin_bp.route('/api/sales_over_time')
def api_sales_over_time():
    sales_data = get_sales_revenue_over_time()
    return jsonify(sales_data)

@admin_bp.route('/api/top_categories')
def api_top_categories():
    category_data = get_top_performing_categories()
    return jsonify(category_data)



# --- ADD THIS NEW ROUTE FOR THE PAGE ---
@admin_bp.route('/manage_orders')
def admin_manage_orders_page():
    all_categories = get_all_main_categories()
    # This is the NEW, CORRECTED line
    return render_template('all_orders.html', all_categories=all_categories)

# --- ADD THIS NEW API ENDPOINT FOR FETCHING ORDERS ---
@admin_bp.route('/api/orders')
def api_get_all_orders():
    """
    Handles fetching all platform orders with optional filters, search, and pagination.
    """
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', None)
    category_id = request.args.get('category_id', None, type=int)

    order_data = get_paginated_orders_for_admin(
        category_id=category_id,
        search_term=search_term,
        page=page,
        per_page=15 # You can adjust items per page here
    )
    return jsonify(order_data)





# --- ADD THESE THREE NEW API ENDPOINTS FOR DISCOUNTS ---
@admin_bp.route('/api/discounts')
def api_get_discounts():
    """Fetches a paginated list of all discount codes."""
    page = request.args.get('page', 1, type=int)
    discount_data = get_paginated_discounts(page=page, per_page=15)
    return jsonify(discount_data)

@admin_bp.route('/api/discounts/add', methods=['POST'])
def api_add_discount():
    """Handles the creation of a new discount code."""
    admin_id = session.get('user_id')
    data = request.get_json()
    
    # Basic validation
    if not all(k in data for k in ['code', 'discount_type', 'value']):
        return jsonify({"error": "Missing required fields."}), 400

    success, message = create_new_discount(admin_id, data)

    if success:
        return jsonify({"message": message}), 201
    else:
        # 409 Conflict is a good status for "already exists"
        status_code = 409 if "already exists" in message else 500
        return jsonify({"error": message}), status_code

@admin_bp.route('/api/discounts/update_status', methods=['POST'])
def api_update_discount_status():
    """Handles activating or deactivating a discount."""
    data = request.get_json()
    discount_id = data.get('discount_id')
    is_active = data.get('is_active')

    if discount_id is None or is_active is None:
        return jsonify({"error": "Missing required data."}), 400

    success, message = update_discount_status(discount_id, is_active)

    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500
    


# --- ADD THESE TWO NEW ROUTES FOR THE DISCOUNT PAGES ---
@admin_bp.route('/manage_discounts')
def manage_discounts_page():
    return render_template('manage_discounts.html')

@admin_bp.route('/add_discount')
def add_discount_page():
    return render_template('add_discount.html')    



@admin_bp.route('/manage_carousel')
def manage_carousel_page():
    return render_template('manage_carousel.html')





@admin_bp.route('/api/carousel/products')
def api_get_all_products_for_carousel():
    """Provides a simple list of all products for the carousel management page."""
    products = get_all_products_for_carousel_management()
    return jsonify(products)

@admin_bp.route('/api/carousel/update', methods=['POST'])
def api_update_carousel_products():
    """Handles saving the admin's carousel product selections."""
    data = request.get_json()
    product_ids = data.get('product_ids', [])

    if not isinstance(product_ids, list):
        return jsonify({"error": "Invalid data format. Expected a list of product IDs."}), 400

    success, message = update_carousel_products(product_ids)

    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500

# --- END: NEW API ROUTES ---