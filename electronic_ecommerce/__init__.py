# electronic_ecommerce/__init__.py

import os
from flask import Flask, jsonify, redirect, url_for, render_template, session, send_from_directory, request
import requests
from flask_mail import Mail

mail = Mail()

def create_app():
    """
    This is the Application Factory. It creates, configures, and returns the
    Flask application instance.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')

    app = Flask(__name__,
                template_folder=template_folder,
                static_folder=static_folder,
                instance_relative_config=True)

    app.config.from_object('config.Config')
    mail.init_app(app)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # --- Register Blueprints ---
    from .admin.routes import admin_bp
    from .auth.routes import auth_bp
    from .seller.routes import seller_bp
    from .home.routes import home_bp
    from .buyer.routes import buyer_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(buyer_bp)

    # -----------------------------------------------------------------------------
    # TOP-LEVEL PAGE & UTILITY ROUTES
    # -----------------------------------------------------------------------------
    
    @app.route("/")
    def landing():
        if 'user_id' in session:
            return redirect(url_for('home_bp.home_page'))
            
        # This part is already correct
        from .models.product_model import get_carousel_products
        carousel_products = get_carousel_products()
            
        return render_template("landing.html", carousel_products=carousel_products)
    
    @app.route("/product/<int:product_id>")
    def product_details(product_id):
        from .models.product_model import get_product_by_id
        product_data = get_product_by_id(product_id)
        if product_data is None:
            return "Product not found or is not active.", 404
        return render_template("product_details.html", product_details=product_data)

    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # -----------------------------------------------------------------------------
    # GENERAL-PURPOSE & NOTIFICATION API ROUTES
    # -----------------------------------------------------------------------------
    
    from .models.notification_model import get_unread_notifications, mark_notifications_as_read

    @app.route("/api/notifications/unread")
    def api_get_unread_notifications():
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        user_id = session['user_id']
        notifications = get_unread_notifications(user_id)
        return jsonify(notifications)

    @app.route("/api/notifications/mark-read", methods=['POST'])
    def api_mark_notifications_read():
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        user_id = session['user_id']
        data = request.get_json()
        notif_ids = data.get('notification_ids', [])

        if not isinstance(notif_ids, list):
            return jsonify({"error": "Invalid data format."}), 400

        if not notif_ids:
            return jsonify({"message": "No notifications to mark as read."}), 200

        success = mark_notifications_as_read(user_id, notif_ids)
        if success:
            return jsonify({"message": "Notifications marked as read."}), 200
        else:
            return jsonify({"error": "Failed to mark notifications as read."}), 500

    # --- START: CORRECTED CAROUSEL API ROUTE ---
    @app.route("/api/products/carousel") # Renamed from /featured to /carousel
    def api_carousel_products():
        # Correctly imports and calls the new function
        from .models.product_model import get_carousel_products
        products = get_carousel_products()
        return jsonify(products)
    # --- END: CORRECTED CAROUSEL API ROUTE ---

    @app.route("/api/categories")
    def api_categories():
        from .models.product_model import get_all_categories
        categories = get_all_categories()
        return jsonify(categories)

    @app.route("/api/countries")
    def get_countries():
        # This function and the ones below are fine and do not need changes
        url = "https://api.countrystatecity.in/v1/countries"
        headers = {"X-CSCAPI-KEY": app.config["CSC_API_KEY"]}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            countries = [{"name": c["name"], "iso2": c["iso2"]} for c in response.json()]
            return jsonify(countries)
        return jsonify({"error": "Failed to fetch countries"}), 500

    @app.route("/api/states/<country_code>")
    def get_states(country_code):
        url = f"https://api.countrystatecity.in/v1/countries/{country_code}/states"
        headers = {"X-CSCAPI-KEY": app.config["CSC_API_KEY"]}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            states = [{"name": s["name"], "iso2": s["iso2"]} for s in response.json()]
            return jsonify(states)
        return jsonify({"error": "Failed to fetch states"}), 500

    @app.route("/api/cities/<country_code>/<state_code>")
    def get_cities(country_code, state_code):
        url = f"https://api.countrystatecity.in/v1/countries/{country_code}/states/{state_code}/cities"
        headers = {"X-CSCAPI-KEY": app.config["CSC_API_KEY"]}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            cities = [{"name": c["name"]} for c in response.json()]
            return jsonify(cities)
        return jsonify({"error": "Failed to fetch cities"}), 500
    
    with app.app_context():
        from .models.user_model import create_default_admin
        create_default_admin()

    return app