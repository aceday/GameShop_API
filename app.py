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

# Update the customer
@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):

    # curl -X PUT -H "Content-Type: application/json" -d "{\"customer_name\": \"John Doe\"}" http://localhost:5000/customers/1

    data = request.get_json()
    customer_code           = data.get("customer_code")
    customer_name           = data.get("customer_name")
    customer_other_details  = data.get("customer_other_details")

    # Build UPDATE query
    update_fields = []
    values = []

    if customer_code:
        update_fields.append("customer_code = %s")
        values.append(customer_code)

    if customer_name:
        update_fields.append("customer_name = %s")
        values.append(customer_name)

    if customer_other_details:
        update_fields.append("customer_other_details = %s")
        values.append(customer_other_details)

    # Validation
    if not update_fields:
        return jsonify({
            "success": False,
            "message": "No fields provided"
        }), 400

    values.append(customer_id)

    # Generate UPDATE query
    query = "UPDATE customer SET " + ", ".join(update_fields) + " WHERE customer_id = %s"

    try:
        cur = mysql.connection.cursor()
        cur.execute(query, values)
        mysql.connection.commit()
        affected_rows = cur.rowcount
        cur.close()

        if affected_rows == 0:
            return jsonify({
                "success": False,
                "message": "Customer not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Customer updated successfully"
        }), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Delete a customer
@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM customer WHERE customer_id = %s", (customer_id,))
        mysql.connection.commit()
        affected_rows = cur.rowcount
        cur.close()

        if affected_rows == 0:
            return jsonify({
                "success": False,
                "message": "Customer not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Customer deleted successfully"
        }), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# --------------- ACCESSORIES ---------------

# Get data from accessories
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

# Commit to accessories
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

# Update record for accessories
@app.route("/accessories/<int:product_id>", methods=["PUT"])
def update_accessory(product_id):

    # curl -X PUT -H "Content-Type: application/json" -d "{\"accessory_name\": \"Gaming Keyboard\"}" http://localhost:5000/accessories/1

    data = request.get_json()
    accessory_name          = data.get("accessory_name")
    accessory_description   = data.get("accessory_description")
    other_accessory_details = data.get("other_accessory_details")

    # Build UPDATE query
    update_fields = []
    values = []

    if accessory_name:
        update_fields.append("accessory_name = %s")
        values.append(accessory_name)

    if accessory_description:
        update_fields.append("accessory_description = %s")
        values.append(accessory_description)

    if other_accessory_details:
        update_fields.append("other_accessory_details = %s")
        values.append(other_accessory_details)

    # Validation
    if not update_fields:
        return jsonify({
            "success": False,
            "message": "No fields provided"
        }), 400

    values.append(product_id)

    # Generate UPDATE query
    query = "UPDATE accessories SET " + ", ".join(update_fields) + " WHERE product_id = %s"

    try:
        cur = mysql.connection.cursor()
        cur.execute(query, values)
        mysql.connection.commit()
        affected_rows = cur.rowcount
        cur.close()

        if affected_rows == 0:
            return jsonify({
                "success": False,
                "message": "Accessory not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Accessory updated successfully"
        }), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
 
# Delete record from accessories
@app.route("/accessories/<int:product_id>", methods=["DELETE"])
def delete_accessory(product_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM accessories WHERE product_id = %s", (product_id,))
        mysql.connection.commit()
        affected_rows = cur.rowcount
        cur.close()

        if affected_rows == 0:
            return jsonify({
                "success": False,
                "message": "Accessory not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Accessory deleted successfully"
        }), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    

# --------------- CUSTOM ORDERS  ---------------
# 

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

    # curl -X POST -H "Content-Type: application/json" -d "{\"date_of_order\": \"2024-12-16\", \"other_order_details\": \"Urgent delivery\", \"product_id\": 1, \"customer_id\": 1}" http://localhost:5000/customer_orders

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




#  --------------- CUSTOMER PURCHASES  ---------------
@app.route("/customer_purchases", methods=["GET"])
def get_customer_purchases():

    # curl -X GET http://localhost:5000/customer_purchases

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

# Update a record for customer_purchase
@app.route("/customer_purchases/<int:customer_id>/<int:product_id>", methods=["PUT"])
def update_customer_purchase(customer_id, product_id):

    # curl -X PUT -H "Content-Type: application/json" -d "{\"date_of_purchase\": \"2024-12-16\", \"other_purchase_details\": \"Credit card payment\"}" http://localhost:5000/customer_purchases/1/1

    data = request.get_json()
    date_of_purchase = data.get("date_of_purchase")
    other_purchase_details = data.get("other_purchase_details")

    # Build UPDATE query
    update_fields = []
    values = []

    if date_of_purchase:
        update_fields.append("date_of_purchase = %s")
        values.append(date_of_purchase)

    if other_purchase_details:
        update_fields.append("other_purchase_details = %s")
        values.append(other_purchase_details)

    # Validation
    if not update_fields:
        return jsonify({
            "success": False,
            "message": "No fields provided"
        }), 400

    values.append(customer_id)
    values.append(product_id)

    # Generate UPDATE query
    query = "UPDATE customer_purchases SET " + ", ".join(update_fields) + " WHERE customer_id = %s AND product_id = %s"

    try:
        cur = mysql.connection.cursor()
        cur.execute(query, values)
        mysql.connection.commit()
        affected_rows = cur.rowcount
        cur.close()

        if affected_rows == 0:
            return jsonify({
                "success": False,
                "message": "Customer purchase not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Customer purchase updated successfully"
        }), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Delete record customer_purchase
@app.route("/customer_purchases/<int:customer_id>/<int:product_id>", methods=["DELETE"])
def delete_customer_purchase(customer_id, product_id):

    # curl -X DELETE http://localhost:5000/customer_purchases/1/1

    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM customer_purchases WHERE customer_id = %s AND product_id = %s", (customer_id, product_id))
        mysql.connection.commit()
        affected_rows = cur.rowcount
        cur.close()

        if affected_rows == 0:
            return jsonify({
                "success": False,
                "message": "Customer purchase not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Customer purchase deleted successfully"
        }), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# --------------- DRIVE TYPES ---------------

# GET from driver_types
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

# Commit record to driver_types
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

# Update record for drive_types
@app.route("/drive_types/<int:product_id>", methods=["PUT"])
def update_drive_type(product_id):

    # curl -X PUT -H "Content-Type: application/json" -d "{\"size\": \"1TB\", \"other_console_details\": \"HDD\"}" http://localhost:5000/drive_types/1

    data = request.get_json()
    size = data.get("size")
    other_console_details = data.get("other_console_details")

    # Validation
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    if not all([size, other_console_details]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM drive_types WHERE product_id = %s", (product_id,))
        drive_type = cur.fetchone()

        if not drive_type:
            return jsonify({"success": False, "message": "Drive type not found"}), 404

        cur.execute("UPDATE drive_types SET size = %s, other_console_details = %s WHERE product_id = %s", 
                    (size, other_console_details, product_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Drive type updated successfully"}), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    

# Delete record driver_types
@app.route("/drive_types/<int:product_id>", methods=["DELETE"])
def delete_drive_type(product_id):

    # curl -X DELETE http://localhost:5000/drive_types/1

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM drive_types WHERE product_id = %s", (product_id,))
        drive_type = cur.fetchone()

        if not drive_type:
            return jsonify({"success": False, "message": "Drive type not found"}), 404

        cur.execute("DELETE FROM drive_types WHERE product_id = %s", (product_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Drive type deleted successfully"}), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# --------------- GAMES ---------------
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

# Delete entry games
@app.route("/games/<int:product_id>", methods=["DELETE"])
def delete_game(product_id):

    # curl -X DELETE http://localhost:5000/games/1

    try:
        cur = mysql.connection.cursor()
        
        # Check game existence
        cur.execute("SELECT * FROM games WHERE product_id = %s", (product_id,))
        game = cur.fetchone()
        
        if not game:
            return jsonify({"success": False, "message": "Game not found"}), 404
        
        cur.execute("DELETE FROM games WHERE product_id = %s", (product_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Game deleted successfully"}), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500



# --------------- PRODUCTS ---------------
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

# Update a record for product
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):

    # curl -X PUT -H "Content-Type: application/json" -d "{\"product_name\": \"Gaming Laptop Pro\", \"product_description\": \"Upgraded laptop\", \"product_price\": 1299.99, \"product_type_code\": 1}" http://localhost:5000/products/1

    data = request.get_json()
    product_name = data.get("product_name")
    product_description = data.get("product_description")
    product_price = data.get("product_price")
    product_type_code = data.get("product_type_code")  # FOREIGN KEY

    # Validation
    if not all([product_name, product_description, product_price, product_type_code]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    # Check product existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
    if not cur.fetchone():
        return jsonify({"success": False, "message": "Product not found"}), 404

    # Check product type existence
    cur.execute("SELECT product_type_code FROM product_types WHERE product_type_code = %s", (product_type_code,))
    if not cur.fetchone():
        return jsonify({"success": False, "message": "Product type not found"}), 404

    try:
        cur.execute("UPDATE products SET product_name = %s, product_description = %s, product_price = %s, product_type_code = %s WHERE product_id = %s", 
                    (product_name, product_description, product_price, product_type_code, product_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Product updated successfully"}), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# Delete record for product
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):

    # curl -X DELETE http://localhost:5000/products/1curl -X DELETE http://localhost:5000/products/1

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
        product = cur.fetchone()

        if not product:
            return jsonify({"success": False, "message": "Product not found"}), 404

        cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Product deleted successfully"}), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    


# --------------- PRODUCT TYPES ---------------
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

# Update record for product_type
@app.route("/product_types/<int:product_type_code>", methods=["PUT"])
def update_product_type(product_type_code):
    data = request.get_json()
    product_type = data.get("product_type")

    # Validation
    if not product_type:
        return jsonify({"success": False, "message": "Product type is required"}), 400

    # Check product type existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT product_type_code FROM product_types WHERE product_type_code = %s", (product_type_code,))
    if not cur.fetchone():
        return jsonify({"success": False, "message": "Product type not found"}), 404

    try:
        cur.execute("UPDATE product_types SET product_type = %s WHERE product_type_code = %s", (product_type, product_type_code))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Product type updated successfully"}), 200
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    


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


# WAIT
if __name__ == "__main__":
    app.run(debug=True)