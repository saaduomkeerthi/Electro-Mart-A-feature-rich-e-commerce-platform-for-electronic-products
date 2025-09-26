import os
from flask import (Blueprint, render_template, session, redirect, url_for, 
                   jsonify, request, current_app)
from werkzeug.utils import secure_filename
from ..models.notification_model import create_notification
from ..models.user_model import get_all_admins

# --- START: MODIFIED IMPORT BLOCK ---
# Import all necessary model functions
from ..models.buyer_model import (
    get_buyer_dashboard_stats, get_buyer_recent_orders, get_buyer_profile, 
    update_buyer_profile, update_buyer_password,
    get_spending_by_category, get_monthly_spending,
    # --- ADDED NEW IMPORTS FOR CHARTS ---
    get_order_status_distribution, get_top_brands_by_spending
)
# --- END: MODIFIED IMPORT BLOCK ---

from ..models.cart_model import (
    add_to_cart, get_cart_items, update_cart_item_quantity, 
    remove_from_cart, get_cart_item_count, get_cart_status_for_products,
    validate_and_get_coupon
)
from ..models.wishlist_model import (
    add_to_wishlist, remove_from_wishlist, get_wishlist_items, 
    get_wishlist_status_for_products
)
from ..models.address_model import (
    get_buyer_addresses, add_new_address, delete_address
)
from ..models.order_model import (
    create_order_from_cart, get_order_details_for_buyer, create_cancellation_request,
    get_paginated_orders_for_buyer
)

# Blueprint setup
buyer_bp = Blueprint('buyer_bp', __name__, url_prefix='/buyer', template_folder='templates')

@buyer_bp.before_request
def check_buyer():
    """Redirects non-buyers to the login page."""
    if session.get('user_role') != 'buyer':
        return redirect(url_for('auth_bp.login'))

# -----------------------------------------------------------------------------
# PAGE RENDERING ROUTES
# -----------------------------------------------------------------------------

@buyer_bp.route('/dashboard')
def dashboard():
    return render_template('buyer_dashboard.html')

@buyer_bp.route('/profile')
def profile():
    return render_template('buyer_profile.html')

@buyer_bp.route('/order_history')
def order_history():
    return render_template('order_history.html')

@buyer_bp.route('/cart')
def cart_page():
    return render_template('cart.html')

@buyer_bp.route('/checkout')
def checkout_page():
    return render_template('checkout.html')

@buyer_bp.route('/order/<int:order_id>')
def order_details_page(order_id):
    order_data = get_order_details_for_buyer(session['user_id'], order_id)
    if not order_data:
        return "Order not found or you do not have permission to view it.", 404
    return render_template('order_details.html', order_data=order_data)

@buyer_bp.route('/wishlist')
def wishlist_page():
    return render_template('wishlist.html')

# -----------------------------------------------------------------------------
# API ROUTES
# -----------------------------------------------------------------------------

# --- Dashboard APIs ---
@buyer_bp.route('/api/stats')
def api_stats():
    stats = get_buyer_dashboard_stats(session['user_id'])
    return jsonify(stats)

@buyer_bp.route('/api/recent_orders')
def api_recent_orders():
    orders = get_buyer_recent_orders(session['user_id'])
    return jsonify(orders)

@buyer_bp.route('/api/order_history')
def api_order_history_data():
    buyer_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', None)
    status = request.args.get('status', None)
    order_data = get_paginated_orders_for_buyer(
        buyer_id=buyer_id, status=status, search_term=search_term, page=page, per_page=10
    )
    return jsonify(order_data)

@buyer_bp.route('/api/spending_by_category')
def api_spending_by_category():
    data = get_spending_by_category(session['user_id'])
    return jsonify(data)

@buyer_bp.route('/api/monthly_spending')
def api_monthly_spending():
    data = get_monthly_spending(session['user_id'])
    return jsonify(data)

# --- START: NEW API ROUTES FOR CHARTS ---
@buyer_bp.route('/api/order_status_distribution')
def api_order_status_distribution():
    """Provides data for the order status pie chart."""
    data = get_order_status_distribution(session['user_id'])
    return jsonify(data)

@buyer_bp.route('/api/top_brands')
def api_top_brands():
    """Provides data for the top 5 brands horizontal bar chart."""
    data = get_top_brands_by_spending(session['user_id'])
    return jsonify(data)
# --- END: NEW API ROUTES ---

# --- Profile API ---
@buyer_bp.route('/api/profile', methods=['GET', 'POST'])
def api_profile_handler():
    buyer_id = session.get('user_id')
    if request.method == 'POST':
        profile_data = request.form.to_dict()
        profile_image_file = request.files.get('profile_image')
        image_db_path = None
        if profile_image_file and profile_image_file.filename != '':
            unique_filename = secure_filename(f"profile_{buyer_id}_{profile_image_file.filename}")
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            image_db_path = os.path.join(current_app.config['UPLOAD_URL_PATH'], unique_filename).replace("\\", "/")
            profile_image_file.save(save_path)
        success, message, old_image_path = update_buyer_profile(buyer_id, profile_data, image_db_path)
        if success:
            if 'full_name' in profile_data and profile_data['full_name']:
                session['full_name'] = profile_data['full_name']
            if old_image_path:
                try:
                    old_file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(old_image_path))
                    if os.path.exists(old_file_full_path):
                        os.remove(old_file_full_path)
                except Exception as e:
                    print(f"Error cleaning up old buyer profile image: {e}")
            return jsonify({"message": message}), 200
        else:
            if image_db_path:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(image_db_path)))
            return jsonify({"error": message}), 500
    profile_data = get_buyer_profile(buyer_id)
    if profile_data:
        if profile_data.get('profile_image'):
            profile_data['profile_image_url'] = url_for('serve_upload', filename=os.path.basename(profile_data['profile_image']))
        else:
            profile_data['profile_image_url'] = None
        return jsonify(profile_data)
    return jsonify({"error": "Profile not found"}), 404

@buyer_bp.route('/api/password/update', methods=['POST'])
def api_update_password():
    data = request.get_json()
    success, message = update_buyer_password(
        session['user_id'], data.get('old_password'), data.get('new_password')
    )
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400

# --- Shopping Cart & Wishlist APIs ---
@buyer_bp.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    data = request.get_json()
    success, message = add_to_cart(session['user_id'], data.get('product_id'), data.get('quantity', 1))
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"error": message}), 500

@buyer_bp.route('/api/cart', methods=['GET'])
def api_get_cart():
    items = get_cart_items(session['user_id'])
    total = sum(item['subtotal'] for item in items)
    return jsonify({"items": items, "total": total})

@buyer_bp.route('/api/cart/update', methods=['POST'])
def api_update_cart():
    data = request.get_json()
    success = update_cart_item_quantity(session['user_id'], data.get('product_id'), int(data.get('quantity')))
    if success:
        return jsonify({"message": "Cart updated."}), 200
    return jsonify({"error": "Failed to update cart."}), 500

@buyer_bp.route('/api/cart/remove', methods=['POST'])
def api_remove_from_cart():
    data = request.get_json()
    success = remove_from_cart(session['user_id'], data.get('product_id'))
    if success:
        return jsonify({"message": "Item removed from cart."}), 200
    return jsonify({"error": "Failed to remove item."}), 500

@buyer_bp.route('/api/cart/count', methods=['GET'])
def api_get_cart_count():
    count = get_cart_item_count(session['user_id'])
    return jsonify({"item_count": count})

@buyer_bp.route('/api/wishlist', methods=['GET'])
def api_get_wishlist():
    items = get_wishlist_items(session['user_id'])
    return jsonify(items)

@buyer_bp.route('/api/wishlist/toggle', methods=['POST'])
def api_toggle_wishlist():
    product_id = request.json.get('product_id')
    status = get_wishlist_status_for_products(session['user_id'], [product_id])
    is_in_wishlist = status.get(product_id, False)
    if is_in_wishlist:
        success, message = remove_from_wishlist(session['user_id'], product_id)
    else:
        success, message = add_to_wishlist(session['user_id'], product_id)
    if success:
        return jsonify({"message": message, "status": not is_in_wishlist}), 200
    return jsonify({"error": message}), 500

@buyer_bp.route('/api/wishlist/status', methods=['POST'])
def api_get_wishlist_status():
    product_ids = request.json.get('product_ids', [])
    status = get_wishlist_status_for_products(session['user_id'], product_ids)
    return jsonify(status)

# --- Address, Checkout & Coupon APIs ---
@buyer_bp.route('/api/addresses', methods=['GET'])
def api_get_addresses():
    addresses = get_buyer_addresses(session['user_id'])
    return jsonify(addresses)

@buyer_bp.route('/api/addresses/add', methods=['POST'])
def api_add_address():
    success, message = add_new_address(session['user_id'], request.json)
    if success:
        return jsonify({"message": message}), 201
    return jsonify({"error": message}), 500

@buyer_bp.route('/api/addresses/delete', methods=['POST'])
def api_delete_address():
    success = delete_address(session['user_id'], request.json.get('address_id'))
    if success:
        return jsonify({"message": "Address deleted successfully."}), 200
    return jsonify({"error": "Failed to delete address."}), 500

@buyer_bp.route('/api/place_order', methods=['POST'])
def api_place_order():
    data = request.get_json()
    success, message, order_numbers = create_order_from_cart(
        session['user_id'], data.get('address_id'), data.get('payment_method')
    )
    if success:
        return jsonify({
            "message": message, "order_numbers": order_numbers,
            "redirect_url": url_for('buyer_bp.dashboard')
        }), 200
    return jsonify({"error": message}), 500

@buyer_bp.route('/api/cart/status', methods=['POST'])
def api_get_cart_status():
    buyer_id = session.get('user_id')
    data = request.get_json()
    product_ids = data.get('product_ids')
    if not product_ids or not isinstance(product_ids, list):
        return jsonify({"error": "A list of product IDs is required."}), 400
    status = get_cart_status_for_products(buyer_id, product_ids)
    return jsonify(status)

@buyer_bp.route('/api/cart/apply_coupon', methods=['POST'])
def api_apply_coupon():
    data = request.get_json()
    coupon_code = data.get('coupon_code')
    if not coupon_code:
        return jsonify({"error": "Coupon code is required."}), 400
    cart_items = get_cart_items(session['user_id'])
    cart_total = sum(item['subtotal'] for item in cart_items)
    if cart_total == 0:
        return jsonify({"error": "Your cart is empty."}), 400
    coupon, message = validate_and_get_coupon(coupon_code, cart_total)
    if not coupon:
        return jsonify({"error": message}), 400
    discount_amount = 0
    if coupon['discount_type'] == 'percentage':
        discount_amount = (cart_total * float(coupon['value'])) / 100
    elif coupon['discount_type'] == 'fixed':
        discount_amount = float(coupon['value'])
    discount_amount = min(discount_amount, cart_total)
    session['applied_coupon'] = {
        'discount_id': coupon['discount_id'], 'code': coupon['code'],
        'discount_amount': float(discount_amount)
    }
    session.modified = True
    return jsonify({
        "message": message, "discount_amount": float(discount_amount),
        "new_total": float(cart_total - discount_amount)
    })

@buyer_bp.route('/api/cart/remove_coupon', methods=['POST'])
def api_remove_coupon():
    if 'applied_coupon' in session:
        session.pop('applied_coupon', None)
        session.modified = True
    return jsonify({"message": "Coupon removed."}), 200

# --- Order Cancellation API ---
@buyer_bp.route('/api/order/request_cancellation', methods=['POST'])
def api_request_cancellation():
    buyer_id = session.get('user_id')
    data = request.get_json()
    order_id, seller_id, reason, comments = data.get('order_id'), data.get('seller_id'), data.get('reason'), data.get('comments')
    if not all([order_id, seller_id, reason]):
        return jsonify({"error": "Missing required data."}), 400
    order_data = get_order_details_for_buyer(buyer_id, order_id)
    if not order_data:
        return jsonify({"error": "Order not found."}), 404
    order_number = order_data['details']['order_number']
    success, message = create_cancellation_request(order_id, buyer_id, seller_id, reason, comments)
    if success:
        seller_notif_message = f"Buyer {session['full_name']} has requested to cancel Order #{order_number}."
        seller_link = url_for('seller_bp.seller_manage_orders_page')
        create_notification(seller_id, seller_notif_message, seller_link)
        admins = get_all_admins()
        admin_notif_message = f"New cancellation request for Order #{order_number} from {session['full_name']}."
        admin_link = url_for('admin_bp.manage_cancellations_page')
        for admin in admins:
            create_notification(admin['user_id'], admin_notif_message, admin_link)
        return jsonify({"message": message}), 201
    else:
        status_code = 409 if "already exists" in message else 500
        return jsonify({"error": message}), status_code