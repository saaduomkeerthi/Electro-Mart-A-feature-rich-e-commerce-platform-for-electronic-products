# # electronic_ecommerce/models/product_model.py

# import math
# from .db import get_db_connection

# def get_featured_products():
#     """
#     Fetches featured products from the database to display on the landing page.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []

#     try:
#         cursor = conn.cursor(dictionary=True)
#         # Fetch up to 8 featured products that are active, approved, and have stock
#         query = """
#             SELECT
#                 p.product_id,
#                 p.name,
#                 p.short_description,
#                 p.price,
#                 pi.image_url
#             FROM products p
#             LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#             WHERE p.is_featured = TRUE AND p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
#             LIMIT 8;
#         """
#         cursor.execute(query)
#         products = cursor.fetchall()
#         # Convert decimal prices to float for JSON compatibility
#         for product in products:
#             if 'price' in product:
#                 product['price'] = float(product['price'])
#         return products
#     except Exception as e:
#         print(f"Error fetching featured products: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_all_categories():
#     """
#     Fetches all main (level 1) categories from the database.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []

#     try:
#         cursor = conn.cursor(dictionary=True)
#         # Fetch only top-level categories that are active
#         query = "SELECT category_id, name FROM categories WHERE is_active = TRUE AND parent_category_id IS NULL ORDER BY name;"
#         cursor.execute(query)
#         categories = cursor.fetchall()
#         return categories
#     except Exception as e:
#         print(f"Error fetching categories: {e}")
#         return []
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_product_by_id(product_id):
#     """
#     Fetches a single product and its related details (images, specs) by its ID.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return None

#     product_details = {}

#     try:
#         cursor = conn.cursor(dictionary=True)

#         # 1. Fetch main product data
#         product_query = """
#             SELECT p.*, c.name as category_name
#             FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#             WHERE p.product_id = %s AND p.is_active = TRUE;
#         """
#         cursor.execute(product_query, (product_id,))
#         product = cursor.fetchone()

#         if not product:
#             return None # Product not found or is inactive

#         product_details['product'] = product

#         # 2. Fetch all product images
#         images_query = "SELECT image_url, alt_text FROM product_images WHERE product_id = %s ORDER BY is_primary DESC, display_order ASC;"
#         cursor.execute(images_query, (product_id,))
#         product_details['images'] = cursor.fetchall()

#         # 3. Fetch all product specifications
#         specs_query = "SELECT spec_name, spec_value FROM product_specifications WHERE product_id = %s ORDER BY display_order;"
#         cursor.execute(specs_query, (product_id,))
#         product_details['specifications'] = cursor.fetchall()

#         return product_details

#     except Exception as e:
#         print(f"Error fetching product by ID: {e}")
#         return None
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_all_active_products():
#     """
#     Fetches all active and approved products with their primary image to display on the main storefront.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []

#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT 
#                 p.product_id, 
#                 p.name, 
#                 p.short_description, 
#                 p.price, 
#                 p.category_id,
#                 c.name as category_name,
#                 pi.image_url
#             FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#             LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#             WHERE p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
#             ORDER BY p.created_at DESC;
#         """
#         cursor.execute(query)
#         products = cursor.fetchall()
#         return products
#     except Exception as e:
#         print(f"Error fetching all active products: {e}")
#         return []
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_distinct_brands():
#     """Fetches a list of all distinct, non-null brand names from active products."""
#     conn = get_db_connection()
#     if not conn:
#         return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT DISTINCT brand 
#             FROM products 
#             WHERE brand IS NOT NULL AND brand != '' AND is_active = TRUE AND is_approved = TRUE
#             ORDER BY brand ASC;
#         """
#         cursor.execute(query)
#         brands = [row['brand'] for row in cursor.fetchall()]
#         return brands
#     except Exception as e:
#         print(f"Error fetching distinct brands: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# # --- START: PAGINATION LOGIC INTEGRATED ---
# def search_and_filter_products(search_term=None, category_id=None, brand=None, 
#                                min_price=None, max_price=None, sort_by='relevance',
#                                page=1, per_page=12):
#     """
#     Searches and filters products with pagination.
#     Returns a dictionary with products for the current page and pagination info.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return {'products': [], 'total_count': 0, 'total_pages': 0}

#     try:
#         cursor = conn.cursor(dictionary=True)

#         base_query = """
#             FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#         """
        
#         where_clauses = ["p.is_active = TRUE", "p.is_approved = TRUE", "p.stock_quantity > 0"]
#         params = []

#         if search_term:
#             where_clauses.append("(p.name LIKE %s OR p.short_description LIKE %s OR p.brand LIKE %s OR c.name LIKE %s)")
#             for _ in range(4):
#                 params.append(f"%{search_term}%")
#         if category_id:
#             # This handles filtering by main category and all its subcategories
#             where_clauses.append("(p.category_id = %s OR c.parent_category_id = %s)")
#             params.extend([category_id, category_id])
#         if brand:
#             where_clauses.append("p.brand = %s")
#             params.append(brand)
#         if min_price is not None:
#             where_clauses.append("p.price >= %s")
#             params.append(min_price)
#         if max_price is not None:
#             where_clauses.append("p.price <= %s")
#             params.append(max_price)
        
#         where_sql = " WHERE " + " AND ".join(where_clauses)

#         count_query = f"SELECT COUNT(p.product_id) AS total_count {base_query} {where_sql}"
#         cursor.execute(count_query, tuple(params))
#         total_count = cursor.fetchone()['total_count']
#         total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0

#         product_query = f"""
#             SELECT 
#                 p.product_id, p.name, p.short_description, p.price, p.brand,
#                 c.name as category_name,
#                 pi.image_url
#             {base_query}
#             LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#             {where_sql}
#         """

#         if sort_by == 'price_asc':
#             product_query += " ORDER BY p.price ASC"
#         elif sort_by == 'price_desc':
#             product_query += " ORDER BY p.price DESC"
#         elif sort_by == 'newest':
#             product_query += " ORDER BY p.created_at DESC"
#         else:
#             product_query += " ORDER BY p.name ASC"

#         offset = (page - 1) * per_page
#         product_query += " LIMIT %s OFFSET %s"
#         params.extend([per_page, offset])

#         cursor.execute(product_query, tuple(params))
#         products = cursor.fetchall()
        
#         # Convert decimal prices to float for JSON compatibility
#         for product in products:
#             if 'price' in product:
#                 product['price'] = float(product['price'])

#         return {
#             'products': products,
#             'total_count': total_count,
#             'total_pages': total_pages,
#             'current_page': page
#         }

#     except Exception as e:
#         print(f"Error searching/filtering products: {e}")
#         return {'products': [], 'total_count': 0, 'total_pages': 0}
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()
# # --- END: PAGINATION LOGIC INTEGRATED ---


# # --- START: ADD THIS NEW FUNCTION AT THE END OF THE FILE ---
# def get_products_by_category_name(category_name, limit=8):
#     """
#     Fetches a limited number of active, approved products for a specific category name.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT
#                 p.product_id, p.name, p.price, pi.image_url
#             FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#             LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#             WHERE c.name = %s 
#               AND p.is_active = TRUE 
#               AND p.is_approved = TRUE 
#               AND p.stock_quantity > 0
#             ORDER BY p.sold_count DESC, p.created_at DESC
#             LIMIT %s;
#         """
#         cursor.execute(query, (category_name, limit))
#         products = cursor.fetchall()
#         for product in products:
#             if 'price' in product:
#                 product['price'] = float(product['price'])
#         return products
#     except Exception as e:
#         print(f"Error fetching products by category name '{category_name}': {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# # --- ADD THIS NEW FUNCTION AT THE END OF product_model.py ---

# def get_products_grouped_by_seller(max_sellers=5, products_per_seller=4):
#     """
#     Fetches a list of active sellers and a specified number of their top products.
#     Returns a list of dictionaries, where each dictionary contains seller info
#     and a list of their products.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []

#     try:
#         cursor = conn.cursor(dictionary=True)

#         # This complex query uses window functions to efficiently get the top 4 products for each seller in a single database call.
#         # It's much faster than running a separate query for each seller.
#         query = """
#             WITH RankedProducts AS (
#                 SELECT
#                     p.product_id,
#                     p.name,
#                     p.price,
#                     p.seller_id,
#                     s.business_name,
#                     pi.image_url,
#                     -- This function assigns a rank to each product within its seller's group, ordered by sold_count.
#                     ROW_NUMBER() OVER(PARTITION BY p.seller_id ORDER BY p.sold_count DESC, p.created_at DESC) as rn
#                 FROM products p
#                 JOIN sellers s ON p.seller_id = s.seller_id
#                 LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#                 WHERE
#                     p.is_active = TRUE
#                     AND p.is_approved = TRUE
#                     AND p.stock_quantity > 0
#                     AND s.verification_status = 'approved'
#             )
#             SELECT
#                 product_id,
#                 name,
#                 price,
#                 seller_id,
#                 business_name,
#                 image_url
#             FROM RankedProducts
#             WHERE rn <= %s AND seller_id IN (
#                 -- Subquery to select a limited number of distinct, active sellers
#                 SELECT DISTINCT seller_id FROM RankedProducts ORDER BY seller_id LIMIT %s
#             );
#         """
#         cursor.execute(query, (products_per_seller, max_sellers))
#         products_list = cursor.fetchall()

#         # Now, structure the flat list of products into the desired grouped format.
#         sellers_dict = {}
#         for product in products_list:
#             seller_id = product['seller_id']
#             if seller_id not in sellers_dict:
#                 sellers_dict[seller_id] = {
#                     'seller_id': seller_id,
#                     'business_name': product['business_name'],
#                     'products': []
#                 }
            
#             # Convert decimal price to float for JSON compatibility
#             if 'price' in product:
#                 product['price'] = float(product['price'])

#             sellers_dict[seller_id]['products'].append(product)

#         return list(sellers_dict.values())

#     except Exception as e:
#         print(f"Error fetching products grouped by seller: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()            







        

# import math
# from .db import get_db_connection

# def get_featured_products():
#     """
#     Fetches featured products from the database to display on the landing page.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT p.product_id, p.name, p.short_description, p.price, pi.image_url
#             FROM products p
#             LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#             WHERE p.is_featured = TRUE AND p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
#             LIMIT 8;
#         """
#         cursor.execute(query)
#         products = cursor.fetchall()
#         for product in products:
#             if 'price' in product:
#                 product['price'] = float(product['price'])
#         return products
#     except Exception as e:
#         print(f"Error fetching featured products: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_all_categories():
#     """
#     Fetches all main (level 1) categories from the database.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = "SELECT category_id, name FROM categories WHERE is_active = TRUE AND parent_category_id IS NULL ORDER BY name;"
#         cursor.execute(query)
#         categories = cursor.fetchall()
#         return categories
#     except Exception as e:
#         print(f"Error fetching categories: {e}")
#         return []
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_product_by_id(product_id):
#     """
#     Fetches a single product and its related details (images, specs) by its ID.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return None
#     product_details = {}
#     try:
#         cursor = conn.cursor(dictionary=True)
#         product_query = """
#             SELECT p.*, c.name as category_name
#             FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#             WHERE p.product_id = %s AND p.is_active = TRUE;
#         """
#         cursor.execute(product_query, (product_id,))
#         product = cursor.fetchone()
#         if not product:
#             return None
#         product_details['product'] = product
#         images_query = "SELECT image_url, alt_text FROM product_images WHERE product_id = %s ORDER BY is_primary DESC, display_order ASC;"
#         cursor.execute(images_query, (product_id,))
#         product_details['images'] = cursor.fetchall()
#         specs_query = "SELECT spec_name, spec_value FROM product_specifications WHERE product_id = %s ORDER BY display_order;"
#         cursor.execute(specs_query, (product_id,))
#         product_details['specifications'] = cursor.fetchall()
#         return product_details
#     except Exception as e:
#         print(f"Error fetching product by ID: {e}")
#         return None
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_all_active_products():
#     """
#     Fetches all active and approved products.
#     THIS FUNCTION IS NOW CORRECTED to include the parent category ID.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         # --- THIS QUERY IS NOW FIXED ---
#         query = """
#             SELECT 
#                 p.product_id, 
#                 p.name, 
#                 p.short_description, 
#                 p.price, 
#                 p.category_id,
#                 c.name as category_name,
#                 pi.image_url,
#                 c.parent_category_id  -- <-- THIS IS THE CRITICAL LINE THAT WAS ADDED
#             FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#             LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#             WHERE p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
#             ORDER BY p.created_at DESC;
#         """
#         # --- END OF FIX ---
#         cursor.execute(query)
#         products = cursor.fetchall()
#         return products
#     except Exception as e:
#         print(f"Error fetching all active products: {e}")
#         return []
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_distinct_brands():
#     """Fetches a list of all distinct, non-null brand names from active products."""
#     conn = get_db_connection()
#     if not conn:
#         return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = "SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand != '' AND is_active = TRUE AND is_approved = TRUE ORDER BY brand ASC;"
#         cursor.execute(query)
#         brands = [row['brand'] for row in cursor.fetchall()]
#         return brands
#     except Exception as e:
#         print(f"Error fetching distinct brands: {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# def search_and_filter_products(search_term=None, category_id=None, brand=None, 
#                                min_price=None, max_price=None, sort_by='relevance',
#                                page=1, per_page=12):
#     """
#     Searches and filters products with pagination.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return {'products': [], 'total_count': 0, 'total_pages': 0}
#     try:
#         cursor = conn.cursor(dictionary=True)
#         base_query = "FROM products p JOIN categories c ON p.category_id = c.category_id"
#         where_clauses = ["p.is_active = TRUE", "p.is_approved = TRUE", "p.stock_quantity > 0"]
#         params = []
#         if search_term:
#             where_clauses.append("(p.name LIKE %s OR p.short_description LIKE %s OR p.brand LIKE %s OR c.name LIKE %s)")
#             for _ in range(4): params.append(f"%{search_term}%")
#         if category_id:
#             where_clauses.append("(p.category_id = %s OR c.parent_category_id = %s)")
#             params.extend([category_id, category_id])
#         # ... (rest of the function is correct and unchanged)
#         if brand:
#             where_clauses.append("p.brand = %s")
#             params.append(brand)
#         if min_price is not None:
#             where_clauses.append("p.price >= %s")
#             params.append(min_price)
#         if max_price is not None:
#             where_clauses.append("p.price <= %s")
#             params.append(max_price)
        
#         where_sql = " WHERE " + " AND ".join(where_clauses)
#         count_query = f"SELECT COUNT(p.product_id) AS total_count {base_query} {where_sql}"
#         cursor.execute(count_query, tuple(params))
#         total_count = cursor.fetchone()['total_count']
#         total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
#         product_query = f"""
#             SELECT p.product_id, p.name, p.short_description, p.price, p.brand,
#                    c.name as category_name, pi.image_url
#             {base_query}
#             LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#             {where_sql}
#         """
#         if sort_by == 'price_asc': product_query += " ORDER BY p.price ASC"
#         elif sort_by == 'price_desc': product_query += " ORDER BY p.price DESC"
#         elif sort_by == 'newest': product_query += " ORDER BY p.created_at DESC"
#         else: product_query += " ORDER BY p.name ASC"
#         offset = (page - 1) * per_page
#         product_query += " LIMIT %s OFFSET %s"
#         params.extend([per_page, offset])
#         cursor.execute(product_query, tuple(params))
#         products = cursor.fetchall()
#         for p in products:
#             if 'price' in p: p['price'] = float(p['price'])
#         return {'products': products, 'total_count': total_count, 'total_pages': total_pages, 'current_page': page}
#     except Exception as e:
#         print(f"Error searching/filtering products: {e}")
#         return {'products': [], 'total_count': 0, 'total_pages': 0}
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def get_products_by_category_name(category_name, limit=8):
#     """
#     Fetches a limited number of active, approved products for a specific category name.
#     """
#     conn = get_db_connection()
#     if not conn:
#         return []
#     try:
#         cursor = conn.cursor(dictionary=True)
#         query = """
#             SELECT p.product_id, p.name, p.price, pi.image_url
#             FROM products p
#             JOIN categories c ON p.category_id = c.category_id
#             LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
#             WHERE c.name = %s AND p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
#             ORDER BY p.sold_count DESC, p.created_at DESC
#             LIMIT %s;
#         """
#         cursor.execute(query, (category_name, limit))
#         products = cursor.fetchall()
#         for p in products:
#             if 'price' in p: p['price'] = float(p['price'])
#         return products
#     except Exception as e:
#         print(f"Error fetching products by category name '{category_name}': {e}")
#         return []
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()






























































# electronic_ecommerce/models/product_model.py
import math
from .db import get_db_connection

# In electronic_ecommerce/models/product_model.py

# ... (other functions in the file)

# --- START: Find and REPLACE the entire 'get_featured_products' function with this new version ---

def get_carousel_products():
    """
    Fetches products marked for the homepage carousel from the database.
    It now selects products where `is_carousel` is TRUE.
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        # The only change is the WHERE clause: from p.is_featured to p.is_carousel
        query = """
            SELECT
                p.product_id,
                p.name,
                p.short_description,
                p.price,
                pi.image_url
            FROM products p
            LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
            WHERE p.is_carousel = TRUE AND p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
            LIMIT 8;
        """
        cursor.execute(query)
        products = cursor.fetchall()
        for product in products:
            if 'price' in product:
                product['price'] = float(product['price'])
        return products
    except Exception as e:
        print(f"Error fetching carousel products: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- END: Replacement block ---

# ... (rest of the functions in the file)

def get_all_categories():
    """
    Fetches all main (level 1) categories from the database.
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT category_id, name FROM categories WHERE is_active = TRUE AND parent_category_id IS NULL ORDER BY name;"
        cursor.execute(query)
        categories = cursor.fetchall()
        return categories
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- START: MODIFIED FUNCTION ---
def get_product_by_id(product_id):
    """
    Fetches a single product and its related details, NOW INCLUDING SELLER INFO.
    """
    conn = get_db_connection()
    if not conn:
        return None

    product_details = {}

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch main product data AND seller data
        # We've added a JOIN to the 'sellers' table to get the business_name and logo_url
        product_query = """
            SELECT 
                p.*, 
                c.name as category_name,
                s.business_name, 
                s.logo_url
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            JOIN sellers s ON p.seller_id = s.seller_id
            WHERE p.product_id = %s AND p.is_active = TRUE AND p.is_approved = TRUE;
        """
        cursor.execute(product_query, (product_id,))
        product = cursor.fetchone()

        if not product:
            return None

        product_details['product'] = product

        # 2. Fetch all product images (this part is unchanged)
        images_query = "SELECT image_url, alt_text FROM product_images WHERE product_id = %s ORDER BY is_primary DESC, display_order ASC;"
        cursor.execute(images_query, (product_id,))
        product_details['images'] = cursor.fetchall()

        # 3. Fetch all product specifications (this part is unchanged)
        specs_query = "SELECT spec_name, spec_value FROM product_specifications WHERE product_id = %s ORDER BY display_order;"
        cursor.execute(specs_query, (product_id,))
        product_details['specifications'] = cursor.fetchall()

        return product_details

    except Exception as e:
        print(f"Error fetching product by ID: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
# --- END: MODIFIED FUNCTION ---

def get_all_active_products():
    """
    Fetches all active and approved products.
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                p.product_id, 
                p.name, 
                p.short_description, 
                p.price, 
                p.category_id,
                c.name as category_name,
                pi.image_url,
                c.parent_category_id
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
            WHERE p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
            ORDER BY p.created_at DESC;
        """
        cursor.execute(query)
        products = cursor.fetchall()
        return products
    except Exception as e:
        print(f"Error fetching all active products: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_distinct_brands():
    """Fetches a list of all distinct, non-null brand names from active products."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT DISTINCT brand 
            FROM products 
            WHERE brand IS NOT NULL AND brand != '' AND is_active = TRUE AND is_approved = TRUE
            ORDER BY brand ASC;
        """
        cursor.execute(query)
        brands = [row['brand'] for row in cursor.fetchall()]
        return brands
    except Exception as e:
        print(f"Error fetching distinct brands: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def search_and_filter_products(search_term=None, category_id=None, brand=None, 
                               min_price=None, max_price=None, sort_by='relevance',
                               page=1, per_page=12):
    """
    Searches and filters products with pagination.
    """
    conn = get_db_connection()
    if not conn:
        return {'products': [], 'total_count': 0, 'total_pages': 0}

    try:
        cursor = conn.cursor(dictionary=True)

        base_query = "FROM products p JOIN categories c ON p.category_id = c.category_id"
        where_clauses = ["p.is_active = TRUE", "p.is_approved = TRUE", "p.stock_quantity > 0"]
        params = []

        if search_term:
            where_clauses.append("(p.name LIKE %s OR p.short_description LIKE %s OR p.brand LIKE %s OR c.name LIKE %s)")
            for _ in range(4):
                params.append(f"%{search_term}%")
        if category_id:
            where_clauses.append("(p.category_id = %s OR c.parent_category_id = %s)")
            params.extend([category_id, category_id])
        if brand:
            where_clauses.append("p.brand = %s")
            params.append(brand)
        if min_price is not None:
            where_clauses.append("p.price >= %s")
            params.append(min_price)
        if max_price is not None:
            where_clauses.append("p.price <= %s")
            params.append(max_price)
        
        where_sql = " WHERE " + " AND ".join(where_clauses)

        count_query = f"SELECT COUNT(p.product_id) AS total_count {base_query} {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total_count']
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0

        product_query = f"""
            SELECT p.product_id, p.name, p.short_description, p.price, p.brand, c.name as category_name, pi.image_url
            {base_query}
            LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
            {where_sql}
        """

        if sort_by == 'price_asc':
            product_query += " ORDER BY p.price ASC"
        elif sort_by == 'price_desc':
            product_query += " ORDER BY p.price DESC"
        elif sort_by == 'newest':
            product_query += " ORDER BY p.created_at DESC"
        else:
            product_query += " ORDER BY p.name ASC"

        offset = (page - 1) * per_page
        product_query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(product_query, tuple(params))
        products = cursor.fetchall()
        
        for product in products:
            if 'price' in product:
                product['price'] = float(product['price'])

        return {
            'products': products,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        }

    except Exception as e:
        print(f"Error searching/filtering products: {e}")
        return {'products': [], 'total_count': 0, 'total_pages': 0}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_products_by_category_name(category_name, limit=8):
    """
    Fetches a limited number of active, approved products for a specific category name.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.product_id, p.name, p.price, pi.image_url
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
            WHERE c.name = %s AND p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
            ORDER BY p.sold_count DESC, p.created_at DESC
            LIMIT %s;
        """
        cursor.execute(query, (category_name, limit))
        products = cursor.fetchall()
        for product in products:
            if 'price' in product:
                product['price'] = float(product['price'])
        return products
    except Exception as e:
        print(f"Error fetching products by category name '{category_name}': {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_products_grouped_by_seller(max_sellers=5, products_per_seller=4):
    """
    Fetches a list of active sellers and a specified number of their top products.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            WITH RankedProducts AS (
                SELECT p.product_id, p.name, p.price, p.seller_id, s.business_name, pi.image_url,
                       ROW_NUMBER() OVER(PARTITION BY p.seller_id ORDER BY p.sold_count DESC, p.created_at DESC) as rn
                FROM products p
                JOIN sellers s ON p.seller_id = s.seller_id
                LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
                WHERE p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0 AND s.verification_status = 'approved'
            )
            SELECT product_id, name, price, seller_id, business_name, image_url
            FROM RankedProducts
            WHERE rn <= %s AND seller_id IN (SELECT DISTINCT seller_id FROM RankedProducts ORDER BY seller_id LIMIT %s);
        """
        cursor.execute(query, (products_per_seller, max_sellers))
        products_list = cursor.fetchall()
        sellers_dict = {}
        for product in products_list:
            seller_id = product['seller_id']
            if seller_id not in sellers_dict:
                sellers_dict[seller_id] = {'seller_id': seller_id, 'business_name': product['business_name'], 'products': []}
            if 'price' in product:
                product['price'] = float(product['price'])
            sellers_dict[seller_id]['products'].append(product)
        return list(sellers_dict.values())
    except Exception as e:
        print(f"Error fetching products grouped by seller: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_related_products(category_id, current_product_id, limit=4):
    """
    Fetches a few related products from the same category, excluding the current one.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.product_id, p.name, p.price, pi.image_url
            FROM products p
            LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = TRUE
            WHERE p.category_id = %s AND p.product_id != %s AND p.is_active = TRUE AND p.is_approved = TRUE AND p.stock_quantity > 0
            ORDER BY RAND()
            LIMIT %s;
        """
        cursor.execute(query, (category_id, current_product_id, limit))
        products = cursor.fetchall()
        for product in products:
            if 'price' in product:
                product['price'] = float(product['price'])
        return products
    except Exception as e:
        print(f"Error fetching related products for category {category_id}: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()