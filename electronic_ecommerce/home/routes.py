from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request
import decimal

# --- START: MODIFIED IMPORT BLOCK ---
# We will use your existing, correct model functions and add the new one
from ..models.product_model import (
    get_all_active_products, 
    get_all_categories, 
    get_product_by_id,
    search_and_filter_products, 
    get_distinct_brands,
    # get_featured_products, # <-- No longer needed
    get_products_by_category_name,
    get_carousel_products, # <-- Use the new function
    get_related_products
)
# --- END: MODIFIED IMPORT BLOCK ---

home_bp = Blueprint('home_bp', __name__, template_folder='templates')

# -----------------------------------------------------------------------------
# DISPATCHER AND PAGE RENDERING ROUTES
# -----------------------------------------------------------------------------

@home_bp.route("/dashboard_redirect")
def dashboard_redirect():
    """
    This is an intelligent dispatcher route. After login, users are sent here.
    """
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'admin':
            return redirect(url_for('admin_bp.dashboard'))
        elif role == 'seller':
            return redirect(url_for('seller_bp.dashboard'))
        # Default for 'buyer' is the personalized homepage
        return redirect(url_for('home_bp.home_page'))
    
    # If not in session, go to the public landing page
    return redirect(url_for('landing'))


@home_bp.route("/about")
def about_page():
    """Renders the public 'About Us' page."""
    return render_template("about.html")

@home_bp.route("/home")
def home_page():
    """
    Serves the main POST-LOGIN homepage (the storefront).
    This page is PROTECTED and requires a user to be logged in.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    
    try:
        # --- THIS IS THE CORRECTED LINE ---
        carousel_products = get_carousel_products() 
        
        featured_categories = {
            'televisions': get_products_by_category_name('Televisions'),
            'appliances': get_products_by_category_name('Air Conditioners & Coolers'),
        }
    except Exception as e:
        print(f"Error fetching homepage data: {e}")
        carousel_products = []
        featured_categories = {}

    return render_template(
        "home.html", 
        carousel_products=carousel_products,
        featured_categories=featured_categories
    )


@home_bp.route("/product/<int:product_id>")
def product_details_page(product_id):
    """
    Serves the page for a single product's details.
    THIS ROUTE IS NOW PUBLIC and does not require a login.
    """
    product_details = get_product_by_id(product_id)
    if not product_details:
        return "Product not found", 404 
    return render_template("product_details.html", product_details=product_details)


# -----------------------------------------------------------------------------
# API ROUTES & SEARCH PAGE
# -----------------------------------------------------------------------------

@home_bp.route("/api/product/<int:product_id>/json")
def api_get_product_json(product_id):
    """
    API endpoint to provide ALL details for a single product in JSON format.
    """
    product_data = get_product_by_id(product_id)
    if not product_data:
        return jsonify({"error": "Product not found"}), 404
    
    for key, value in product_data['product'].items():
        if isinstance(value, decimal.Decimal):
            product_data['product'][key] = float(value)
            
    return jsonify(product_data)


@home_bp.route("/api/product/<int:product_id>/related")
def api_get_related_products(product_id):
    """
    API endpoint to fetch related products for a given product.
    """
    product_details = get_product_by_id(product_id)
    if not product_details:
        return jsonify({"error": "Original product not found"}), 404
    category_id = product_details['product']['category_id']
    related = get_related_products(category_id, product_id)
    return jsonify(related)

@home_bp.route("/api/products")
def api_get_all_products():
    """
    API endpoint to provide all active and approved products in JSON format.
    """
    products = get_all_active_products()
    return jsonify(products)

@home_bp.route("/api/categories")
def api_get_all_categories():
    """
    API endpoint to provide all main categories for filtering.
    """
    categories = get_all_categories()
    return jsonify(categories)


@home_bp.route("/search")
def search_page():
    """
    Handles product search and filtering with pagination.
    """
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('q', None)
    category_id = request.args.get('category', None, type=int)
    brand = request.args.get('brand', None)
    min_price = request.args.get('min_price', None, type=float)
    max_price = request.args.get('max_price', None, type=float)
    sort_by = request.args.get('sort_by', 'relevance')
    
    results = search_and_filter_products(
        search_term=search_term, category_id=category_id, brand=brand, 
        min_price=min_price, max_price=max_price, sort_by=sort_by, page=page
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            "partials/product_grid.html", 
            products=results['products'],
            pagination=results
        )
        
    all_categories = get_all_categories()
    all_brands = get_distinct_brands()
    
    return render_template(
        "search_results.html", 
        products=results['products'],
        pagination=results,
        search_term=search_term,
        all_categories=all_categories,
        all_brands=all_brands,
        current_filters={
            'category_id': category_id, 'brand': brand, 'min_price': min_price, 
            'max_price': max_price, 'sort_by': sort_by, 'q': search_term
        }
    )