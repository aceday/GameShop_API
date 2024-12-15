from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_httpauth import HTTPBasicAuth
import jwt
import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# PROGRAM:: REQUIREMENTS 

app = Flask(__name__)

app.config["MYSQL_HOST"] = "192.168.1.139"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "gameshop"
app.config["SECRET_KEY"] = "marc123"

mysql = MySQL(app)
auth = HTTPBasicAuth()

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            request.username = decoded_token["username"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return wrapper

@app.errorhandler(404)
def page_not_found(e):
    return "NOT FOUND :P", 404


# Homepage
@app.route("/", methods=["GET"])
def hello_world():
    with open("index.html", "r") as f:
        return f.read()

# SECTION: LOGIN DATA
@app.route("/login", methods=["POST"])
def login_post():
    data = request.json

    # Fetch username and password
    # Validate input
    username = data.get("username")
    password = data.get("password")

    # Validate input
    if not username or not password:
        return jsonify({"success": False, "message": "Username and Password Required"}), 400

    # Query user data
    cur = mysql.connection.cursor()
    cur.execute("""SELECT 
                        username,
                        passwd,
                        role_id
                    FROM users 
                    WHERE username = %s""",
                    (username,))

    user_auth = cur.fetchone()

    # Check authentication
    if user_auth and check_password_hash(user_auth[1], password):
        
        token = jwt.encode({
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config["SECRET_KEY"], algorithm="HS256")
        
        cur.execute("""UPDATE users
                    SET token_id = %s
                    WHERE username = %s""",
                    (token, username))
        
        mysql.connection.commit()

        return jsonify({
            "success": True,
            "message": "Logged In Successfully",
            "token": token,
            "data": user_auth
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "Invalid Username or Password"
        }), 401


# SECTION: CREATE AN USER ACCOUNT

@app.route("/register", methods=["GET"])
def register_get():
    return "Query it if you need register..."

@app.route("/register", methods=["POST"])
def register_post():

    data = request.json
    username = data.get("username")
    password = data.get("password")

    if (not username) or (not password):
        return jsonify({
            "success": False,
            "message": "Username and password are required"
            }), 401

    try:

        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE username = %s", (username,))
        
        # if cur.fetchone():
        #     return jsonify({"success": False, "message": "Username already exists"}, 409)

        role_id         = 1         # Default role_id
        password_enc    = generate_password_hash(password)
        
        # Commit a user credential
        cur.execute("INSERT INTO users (username, passwd, role_id) VALUES (%s, %s, %s)", (username, password_enc, role_id))
        mysql.connection.commit()
        
        return jsonify({
            "success": True,
            "message": "Account created successfully"
            }), 201
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False,
                        "message": str(e)
                        }), 409
    finally:
        cur.close()

# CUSTOMERS
@app.route("/customers", methods=["GET"])
# @token_required
def get_customers():
    table_name = "customer"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200

@app.route("/customers", methods=["POST"])
def post_customer():
    data = request.get_json()
    customer_code           = data.get("customer_code")
    customer_name           = data.get("customer_name")
    customer_other_details  = data.get("customer_other_details")

    # Validate data
    if not all([customer_code, customer_name, customer_other_details]):
        return jsonify({
            "success": False,
            "message": "All information is required"
        }), 400

    try:

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO customers (customer_code, customer_name, customer_other_details) VALUES (%s, %s, %s)", 
                    (customer_code, customer_name, customer_other_details))
        mysql.connection.commit()
        cur.close()

        return jsonify({
            "success": True,
            "message": "Customer created successfully"
        }), 201
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500




# ACCESSORIES
@app.route("/accessories", methods=["GET"])
def get_accessories():
    table_name = "accessories"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200

@app.route("/accessories", methods=["POST"])
def post_accessory():

    # curl -X POST -H "Content-Type: application/json" -d "{\"product_id\": 1, \"accessory_name\": \"Gaming Mouse\", \"accessory_description\": \"Wireless gaming mouse\", \"other_accessory_details\": \"Ergonomic design\"}" http://localhost:5000/accessories

    data = request.get_json()
    product_id              = data.get("product_id") 
    accessory_name          = data.get("accessory_name")
    accessory_description   = data.get("accessory_description")
    other_accessory_details = data.get("other_accessory_details")

    # Validation
    if not all([product_id, accessory_name, accessory_description, other_accessory_details]):
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    # Check product existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
    if not cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    try:
        cur.execute("INSERT INTO accessories (product_id, accessory_name, accessory_description, other_accessory_details) VALUES (%s, %s, %s, %s)", 
                    (product_id, accessory_name, accessory_description, other_accessory_details))
        mysql.connection.commit()
        cur.close()
        return jsonify({
            "success": True,
            "message": "Accessory created successfully"
        }), 201
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    

# Add POST for customer_purchase, drive_types, games, products, product_types

# CUSTOMER ORDERS
@app.route("/customer_orders", methods=["GET"])
def get_customer_orders():
    table_name = "customer_orders"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200


@app.route("/customer_orders", methods=["POST"])
def post_customer_orders():
    data = request.get_json()
    date_of_order = data.get("date_of_order")
    other_order_details = data.get("other_order_details")
    product_id = data.get("product_id")
    customer_id = data.get("customer_id")

    # Validation
    if not all([date_of_order, other_order_details, product_id, customer_id]):
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    # Check product and customer existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
    if not cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    cur.execute("SELECT customer_id FROM customer WHERE customer_id = %s", (customer_id,))
    if not cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Customer not found"
        }), 404

    try:
        cur.execute("INSERT INTO customer_orders (date_of_order, other_order_details, product_id, customer_id) VALUES (%s, %s, %s, %s)", 
                    (date_of_order, other_order_details, product_id, customer_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({
            "success": True,
            "message": "Customer order created successfully"
        }), 201
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# CUSTOMER PURCHASES
@app.route("/customer_purchases", methods=["GET"])
def get_customer_purchases():
    table_name = "customer_purchases"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200

@app.route("/customer_purchases", methods=["POST"])
def post_customer_purchases():

    # curl -X POST -H "Content-Type: application/json" -d "{\"date_of_purchase\": \"2024-12-15\", \"other_purchase_details\": \"Cash payment\", \"customer_id\": 1, \"product_id\": 1}" http://localhost:5000/customer_purchases

    data = request.get_json()
    date_of_purchase = data.get("date_of_purchase")
    other_purchase_details = data.get("other_purchase_details")
    customer_id = data.get("customer_id")  # FOREIGN KEY
    product_id = data.get("product_id")  # FOREIGN KEY

    # Validation
    if not all([date_of_purchase, other_purchase_details, customer_id, product_id]):
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    # Check customer and product existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT customer_id FROM customer WHERE customer_id = %s", (customer_id,))
    if not cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Customer not found"
        }), 404

    cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
    if not cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    try:
        cur.execute("INSERT INTO customer_purchases (date_of_purchase, other_purchase_details, customer_id, product_id) VALUES (%s, %s, %s, %s)", 
                    (date_of_purchase, other_purchase_details, customer_id, product_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({
            "success": True,
            "message": "Customer purchase created successfully"
        }), 201
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500



# DRIVE TYPES
@app.route("/drive_types", methods=["GET"])
def get_drive_types():
    table_name = "drive_types"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200

@app.route("/drive_types", methods=["POST"])
def post_drive_types():

    # curl -X POST -H "Content-Type: application/json" -d '{"product_id": 1, "size": "1TB", "other_console_details": "SSD"}' http://localhost:5000/drive_types

    data = request.get_json()
    product_id = data.get("product_id")  # FOREIGN KEY
    size = data.get("size")
    other_console_details = data.get("other_console_details")

    # Validation
    if not all([product_id, size, other_console_details]):
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    # Check product existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
    if not cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    try:
        cur.execute("INSERT INTO drive_types (product_id, size, other_console_details) VALUES (%s, %s, %s)", 
                    (product_id, size, other_console_details))
        mysql.connection.commit()
        cur.close()
        return jsonify({
            "success": True,
            "message": "Drive type created successfully"
        }), 201
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# GAMES
@app.route("/games", methods=["GET"])
def get_games():
    table_name = "games"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200


@app.route("/games", methods=["POST"])
def post_games():

    # curl -X POST -H "Content-Type: application/json" -d "{\"product_id\": 1, \"game_name\": \"Fortnite\", \"memory_required\": \"8GB\", \"number_of_players\": 4, \"other_game_details\": \"Multiplayer\"}" http://localhost:5000/games

    data = request.get_json()
    product_id = data.get("product_id")  # FOREIGN KEY
    game_name = data.get("game_name")
    memory_required = data.get("memory_required")
    number_of_players = data.get("number_of_players")
    other_game_details = data.get("other_game_details")

    # Validation
    if not all([product_id, game_name, memory_required, number_of_players, other_game_details]):
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    # Check product existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
    if not cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    try:
        cur.execute("INSERT INTO games (product_id, game_name, memory_required, number_of_players, other_game_details) VALUES (%s, %s, %s, %s, %s)", 
                    (product_id, game_name, memory_required, number_of_players, other_game_details))
        mysql.connection.commit()
        cur.close()
        return jsonify({
            "success": True,
            "message": "Game created successfully"
        }), 201
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500



# PRODUCTS
@app.route("/products", methods=["GET"])
def get_products():
    table_name = "products"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200

@app.route("/products", methods=["POST"])
def post_products():

    # curl -X POST -H "Content-Type: application/json" -d "{\"product_name\": \"Gaming Laptop\", \"product_description\": \"High-performance laptop\", \"product_price\": 999.99, \"product_type_code\": 1}" http://localhost:5000/products
    
    data = request.get_json()
    product_name = data.get("product_name")
    product_description = data.get("product_description")
    product_price = data.get("product_price")
    product_type_code = data.get("product_type_code")  # FOREIGN KEY

    # Validation
    if not all([product_name, product_description, product_price, product_type_code]):
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    # Check product type existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT product_type_code FROM product_types WHERE product_type_code = %s", (product_type_code,))
    if not cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Product type not found"
        }), 404

    try:
        cur.execute("INSERT INTO products (product_name, product_description, product_price, product_type_code) VALUES (%s, %s, %s, %s)", 
                    (product_name, product_description, product_price, product_type_code))
        mysql.connection.commit()
        cur.close()
        return jsonify({
            "success": True,
            "message": "Product created successfully"
        }), 201
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    


# PRODUCT TYPES
@app.route("/product_types", methods=["GET"])
def get_product_types():
    table_name = "product_types"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200

@app.route("/product_types", methods=["POST"])
def post_product_types():

    # curl -X POST -H "Content-Type: application/json" -d "{\"product_type\": \"Gaming Laptop\"}" http://localhost:5000/product_types

    data = request.get_json()
    product_type = data.get("product_type")

    # Validation
    if not product_type:
        return jsonify({
            "success": False,
            "message": "Product type is required"
        }), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO product_types (product_type) VALUES (%s)", (product_type,))
        mysql.connection.commit()
        product_type_code = cur.lastrowid
        cur.close()
        return jsonify({
            "success": True,
            "message": "Product type created successfully",
            "product_type_code": product_type_code
        }), 201
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    

# Users
@app.route("/users", methods=["GET"])
def get_users():
    table_name = "users"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}'")
    columns = [col[0] for col in cur.fetchall()]

    cur.close()

    # Merge column and entry
    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200

@app.route("/users", methods=["POST"])
def get_users():

# WAIT
if __name__ == "__main__":
    app.run(debug=True)