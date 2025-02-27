from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_httpauth import HTTPBasicAuth
import jwt, datetime, json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pyc import *

# PROGRAM:: REQUIREMENTS 

app = Flask(__name__)

app.config["MYSQL_HOST"] = mysql_host
app.config["MYSQL_USER"] = mysql_user
app.config["MYSQL_PASSWORD"] = mysql_passwd
app.config["MYSQL_DB"] = mysql_db
app.config["SECRET_KEY"] = mysql_sk

mysql = MySQL(app)
auth = HTTPBasicAuth()

# def is_admin(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         username = request.headers.get('username')
        
#         if not username:
#             return jsonify({"message":"Username is missing",
#                             # "username" : username
#                             }), 400
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT role_name FROM users WHERE username = %s", (username,))
#         if_admin = cur.fetchone()
#         print(if_admin)
#         if if_admin and if_admin[0] == 'admin':
#             return f(*args, **kwargs)
#         else:
#             return jsonify({"message": "Admin access required",
#                             # "username" : username,
#                             # "data" : if_admin
#                             }), 403

#     return decorated_function

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return jsonify({"error": "Token is missing or invalid"}), 401 
        token = token.split("Bearer ")[1].strip()   
        try:
            decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            request.username = decoded_token["username"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!, login again!"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": "Invalid token", "details": str(e)}), 401
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

# Test Token
@app.route("/checker", methods=["GET"])
@token_required
def checker_route():
    return jsonify({"message": f"Hello my friend {request.username}!"})


# SECTION: LOGIN DATA
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if not (username and password):
        return jsonify({"success": False, "message": "Username and Password Required"}), 400
    
    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT username, passwd, role_id FROM users WHERE username = %s", (username,))
            user_auth = cur.fetchone()
            
            if user_auth and check_password_hash(user_auth[1], password):
                token = jwt.encode({
                    "username": username,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                }, app.config["SECRET_KEY"], algorithm="HS256")
                
                return jsonify({
                    "success": True,
                    "message": "Logged In Successfully",
                    "token": token
                }), 200
            
            return jsonify({"success": False, "message": "Invalid Username or Password"}), 401
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# SECTION: CREATE AN USER ACCOUNT
@app.route("/register", methods=["POST", "GET"])
def manage_register():
    default_role_id = 1
    if request.method == "POST":
        data = request.get_json()
        username, password = data.get("username"), data.get("password")
        if not (username and password): 
            return jsonify({"success": False, "message": "Username and password are required"}), 401
        try:
            with mysql.connection.cursor() as cur:
                if cur.execute("SELECT 1 FROM users WHERE username = %s", (username,)) and cur.fetchone():
                    return jsonify({"success": False, "message": "Username already exists"}), 409
                cur.execute("INSERT INTO users (username, passwd, role_id)VALUES (%s, %s, %s)", (username, generate_password_hash(password), default_role_id))
                mysql.connection.commit()
                return jsonify({"success": True, "message": "Account created successfully"}), 201
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"success": False, "message": str(e)}), 409
    elif request.method == "GET":
        return jsonify({
            "message": "You want to GET request for register?, use POST.",
            "success": False
        }), 405

# CUSTOMERS
@app.route("/customers", methods=["GET", "POST"])
@app.route("/customers/<int:id>", methods=["GET", "PUT", "DELETE"])
def manage_customers(id=None):
    table_name = "customer"
    
    @token_required
    def modifier():
        if request.method == "POST":
            # Create customer
            data = request.get_json()
            customer_code, customer_name  = data.get("customer_code"), data.get("customer_name")
            customer_other_details = data.get("customer_other_details")
            if not all([customer_code, customer_name, customer_other_details]):
                return jsonify({"success": False, "message": "All information is required"}), 400
            try:
                with mysql.connection.cursor() as cur:
                    cur.execute("INSERT INTO customer (customer_code, customer_name, customer_OtherDetails) VALUES (%s, %s, %s)", 
                                (customer_code, customer_name, customer_other_details))
                    mysql.connection.commit()
                    return jsonify({"success": True, "message": "Customer created successfully"}), 201  
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500
        
        elif request.method == "PUT": 
            # Update customer
            data = request.get_json()
            customer_code = data.get("customer_code")
            customer_name = data.get("customer_name")
            customer_other_details = data.get("customer_other_details")
            update_fields = []
            values = []
            if customer_code:
                update_fields.append("customer_code = %s")
                values.append(customer_code)
            if customer_name:
                update_fields.append("customer_name = %s")
                values.append(customer_name)
            if customer_other_details:
                update_fields.append("customer_OtherDetails = %s")
                values.append(customer_other_details)
            if not update_fields:
                return jsonify({"success": False, "message": "No fields provided"}), 400
            values.append(id)
            query = f"UPDATE {table_name} SET " + ", ".join(update_fields) + " WHERE customer_id = %s"
            try:
                with mysql.connection.cursor() as cur:
                    cur.execute(query, values)
                    mysql.connection.commit()
                    affected_rows = cur.rowcount
                    if affected_rows == 0:
                        return jsonify({"success": False, "message": "Customer not found"}), 404
                    return jsonify({"success": True, "message": "Customer updated successfully"}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500
        
        elif request.method == "DELETE": 
            # Delete customer
            try:
                with mysql.connection.cursor() as cur:
                    cur.execute(f"DELETE FROM {table_name} WHERE customer_id = %s", (id,))
                    mysql.connection.commit()
                    affected_rows = cur.rowcount
                    if affected_rows == 0:
                        return jsonify({"success": False, "message": "Customer not found"}), 404
                    return jsonify({"success": True, "message": "Customer deleted successfully"}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500
    
    if request.method not in ["GET"]: return modifier()
    else:
        try:
            if id:
                cur = mysql.connection.cursor()
                cur.execute(f"SELECT * FROM {table_name} WHERE customer_id = %s", (id,))
                entry = cur.fetchone()
                if not entry: return jsonify({"success": False, "message": "Customer not found"}), 404
                return jsonify(dict(zip([col[0] for col in cur.description], entry))), 200
            else:
                cur = mysql.connection.cursor()
                cur.execute(f"SELECT * FROM {table_name}")
                entries = cur.fetchall()
                if len(entries) > 0:
                    columns = [col[0] for col in cur.description]
                    return jsonify([dict(zip(columns, entry)) for entry in entries]), 200
                else:
                    return jsonify({
                        "message" : f"No {table_name} content",
                    }), 404
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500


# --------------- CUSTOM ORDERS  ---------------

# CUSTOMER ORDERS
@app.route("/customer_orders", methods=["POST", "GET"])
@app.route("/customer_orders/<int:order_id>", methods=["GET", "PUT", "DELETE"])
def manage_customer_orders(order_id=None):
    table_name = "customer_orders"
    product_table = "products"
    customer_table = "customer"
    @token_required
    def modifier():
        if request.method == "POST":
            # Create customer order
            data = request.get_json()
            required_fields = ["date_of_order", "other_order_details", "product_id", "customer_id"]
            if not all(field in data for field in required_fields):
                return jsonify({"success": False, "message": "All fields are required"}), 400

            cur = mysql.connection.cursor()
            cur.execute(f"SELECT product_id FROM {product_table} WHERE product_id = %s", (data["product_id"],))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Product not found"}), 404

            cur.execute(f"SELECT customer_id FROM {customer_table} WHERE customer_id = %s", (data["customer_id"],))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Customer not found"}), 404

            try:
                cur.execute(f"INSERT INTO {table_name} (date_of_order, other_order_details, product_id, customer_id) VALUES (%s, %s, %s, %s)", 
                            (data["date_of_order"], data["other_order_details"], data["product_id"], data["customer_id"]))
                mysql.connection.commit()
                cur.close()
                return jsonify({"success": True, "message": "Customer order created successfully"}), 201
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500

        elif request.method == "PUT":
            # Update customer order
            data = request.get_json()
            required_fields = ["date_of_order", "other_order_details", "product_id", "customer_id"]
            if not all(field in data for field in required_fields):
                return jsonify({"success": False, "message": "All fields are required"}), 400

            cur = mysql.connection.cursor()
            cur.execute(f"SELECT order_id FROM {table_name} WHERE order_id = %s", (order_id,))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Order not found"}), 404

            cur.execute(f"SELECT customer_id FROM {customer_table} WHERE customer_id = %s", (data["customer_id"],))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Customer not found"}), 404

            cur.execute(f"SELECT product_id FROM {product_table} WHERE product_id = %s", (data["product_id"],))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Product not found"}), 404

            try:
                cur.execute(f"UPDATE {table_name} SET date_of_order = %s, other_order_details = %s, product_id = %s, customer_id = %s WHERE order_id = %s",
                            (data["date_of_order"], data["other_order_details"], data["product_id"], data["customer_id"], order_id))
                mysql.connection.commit()
                cur.close()
                return jsonify({"success": True, "message": "Customer order updated successfully"}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500

        elif request.method == "DELETE":
            # Delete customer order
            try:
                cur = mysql.connection.cursor()
                cur.execute(f"SELECT order_id FROM {table_name} WHERE order_id = %s", (order_id,))
                if not cur.fetchone():
                    return jsonify({"success": False, "message": "Order not found"}), 404

                cur.execute(f"DELETE FROM {table_name} WHERE order_id = %s", (order_id,))
                mysql.connection.commit()
                cur.close()
                return jsonify({"success": True, "message": "Customer order deleted successfully"}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)})

    if request.method not in ["GET"]: return modifier()
    else:
        if order_id:
            cur = mysql.connection.cursor()
            cur.execute(f"SELECT * FROM {table_name} WHERE order_id = %s", (order_id,))
            entry = cur.fetchone()
            if not entry: return jsonify({"success": False, "message": "Order not found"}), 404
            columns = [col[0] for col in cur.description]
            return jsonify(dict(zip(columns, entry))), 200
        else:
            cur = mysql.connection.cursor()
            cur.execute(f"SELECT * FROM {table_name}")
            entries = cur.fetchall()
            columns = [col[0] for col in cur.description]
            return jsonify([dict(zip(columns, entry)) for entry in entries]), 200

# --------------- CUSTOM PURCHASES  ---------------

@app.route("/customer_purchases", methods=["GET", "POST"])
@app.route("/customer_purchases/<int:customer_purchase_id>", methods=["GET", "PUT", "DELETE"])
def manage_customer_purchases(customer_purchase_id=None):
    table_name = "customer_purchases"
    customer_table = "customer"

    @token_required
    def modifier():
        if request.method == "POST":
            # Create new customer purchase
            data = request.get_json()
            required_fields = ["customer_id", "product_id", "date_of_purchase"]
            if not all(field in data for field in required_fields):
                return jsonify({"success": False, "message": "Missing required fields"}), 400
            
            # Validate customer ID
            cur = mysql.connection.cursor()
            cur.execute(f"SELECT * FROM {customer_table} WHERE customer_id = %s", (data["customer_id"],))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Customer ID does not exist"}), 400

            query = """
                INSERT INTO customer_purchases (customer_id, product_id, date_of_purchase, other_purchase_details)
                VALUES (%s, %s, %s, %s)
            """
            values = (data["customer_id"], data["product_id"], data["date_of_purchase"], data.get("other_purchase_details"))

            try:
                cur.execute(query, values)
                mysql.connection.commit()
                cur.close()
                return jsonify({"success": True, "message": "Customer purchase added successfully"}), 201
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500

        elif request.method == "PUT":
            # Update customer purchase
            data = request.get_json()
            update_fields = []
            values = []

            if "date_of_purchase" in data:
                update_fields.append("date_of_purchase = %s")
                values.append(data["date_of_purchase"])

            if "other_purchase_details" in data:
                update_fields.append("other_purchase_details = %s")
                values.append(data["other_purchase_details"])

            if not update_fields:
                return jsonify({"success": False, "message": "No fields provided"}), 400

            values.append(customer_purchase_id)

            query = "UPDATE customer_purchases SET " + ", ".join(update_fields) + " WHERE purchase_id = %s"

            try:
                cur = mysql.connection.cursor()
                cur.execute(query, values)
                mysql.connection.commit()
                affected_rows = cur.rowcount
                cur.close()
                if affected_rows == 0:
                    return jsonify({"success": False, "message": "Customer purchase not found"}), 404
                return jsonify({"success": True, "message": "Customer purchase updated successfully"}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500

        elif request.method == "DELETE":
            # Delete customer purchase
            try:
                cur = mysql.connection.cursor()
                cur.execute("DELETE FROM customer_purchases WHERE purchase_id = %s", (customer_purchase_id,))
                mysql.connection.commit()
                affected_rows = cur.rowcount
                cur.close()
                if affected_rows == 0:
                    return jsonify({"success": False, "message": "Customer purchase not found"}), 404
                return jsonify({"success": True, "message": "Customer purchase deleted successfully"}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500

    if request.method not in ["GET"]: 
        return modifier()
    else:
        cur = mysql.connection.cursor()
        if customer_purchase_id:
            cur.execute(f"SELECT * FROM {table_name} WHERE purchase_id = %s", (customer_purchase_id,))
            entry = cur.fetchone()
            cur.close()
            if not entry:
                return jsonify({"success": False, "message": "Customer purchase not found"}), 404
            return jsonify({
                "purchase_id": entry[0],
                "product_id": entry[1],
                "date_of_purchase": entry[2],
                "other_purchase_details": entry[3],
                "customer_id": entry[4]
            }), 200
        else:
            cur.execute(f"SELECT * FROM {table_name}")
            entries = cur.fetchall()
            columns = [col[0] for col in cur.description]
            cur.close()
            return jsonify([dict(zip(columns, entry)) for entry in entries]), 200


# --------------- PRODUCTS --------------- (NORM)
@app.route("/products", methods=["GET", "POST"])
@app.route("/products/<int:product_id>", methods=["GET", "POST", "PUT", "DELETE"])
def products(product_id=None):
    table_name = "products"

    # Use another method what changes of source code from above, so i put it different ~ @aceday
    
    cur = mysql.connection.cursor()

    if request.method == "GET":
        if product_id:
            cur.execute(f"SELECT * FROM {table_name} WHERE product_id = %s", (product_id,))
            product = cur.fetchone()
            if not product:
                return jsonify({"success": False, "message": "Product not found"}), 404

            product_data = {
                "product_id": product[0],
                "product_name": product[1],
                "price": product[2],
                "product_type": product[3],
                "product_code": product[4],
            }
            return jsonify(product_data), 200
        else:
            cur.execute(f"SELECT * FROM {table_name}")
            products = cur.fetchall()

            product_list = []
            for product in products:
                product_list.append(
                    {
                        "product_id": product[0],
                        "product_name": product[1],
                        "price": product[2],
                        "product_type": product[3],
                        "product_code": product[4],
                    }
                )
            return jsonify(product_list), 200

    elif request.method == "POST":
        @token_required
        def create_product():
            data = request.get_json()
            product_name = data.get("product_name")
            price = data.get("price")
            product_type = data.get("product_type")
            product_code = data.get("product_code")

            if not all([product_name, price, product_type, product_code]):
                return jsonify({"success": False, "message": "All fields are required"}), 400

            try:
                cur.execute(f"INSERT INTO {table_name} (product_name, price, product_type, product_code) VALUES (%s, %s, %s, %s)",
                            (product_name, price, product_type, product_code),
                )
                mysql.connection.commit()
                return jsonify({"success": True, "message": "Product created successfully"}), 201
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500
        return create_product()

    elif request.method == "PUT":
        @token_required
        def update_product():
            data = request.get_json()
            product_name = data.get("product_name")
            price = data.get("price")
            product_type = data.get("product_type")
            product_code = data.get("product_code")

            if not all([product_name, price, product_type, product_code]):
                return jsonify({"success": False, "message": "All fields are required"}), 400

            cur.execute(f"SELECT * FROM {table_name} WHERE product_id = %s", (product_id,))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Product not found"}), 404

            try:
                cur.execute(f"UPDATE {table_name} SET product_name = %s, price = %s, product_type = %s, product_code = %s WHERE product_id = %s",
                            (product_name, price, product_type, product_code, product_id),
                )
                mysql.connection.commit()
                return jsonify({"success": True, "message": "Product updated successfully"}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500
        return update_product()

    elif request.method == "DELETE":
        @token_required
        def delete_product():
            cur.execute(f"SELECT * FROM {table_name} WHERE product_id = %s", (product_id,))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Product not found"}), 404

            try:
                cur.execute(f"DELETE FROM {table_name} WHERE product_id = %s", (product_id,))
                mysql.connection.commit()
                return jsonify({"success": True, "message": "Product deleted successfully"}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"success": False, "message": str(e)}), 500
        return delete_product()

    else:
        return jsonify({"success": False, "message": "Method not allowed"}), 405


# ---------------------------------------------------

# Users
@app.route("/users", methods=["GET"])
@token_required
# @is_admin
def get_users():
    table_name = "users"

    decode_token = jwt.decode(request.headers.get("Authorization").split(" ")[1], app.config["SECRET_KEY"], algorithms=["HS256"])
    username = decode_token["username"]

    query = f"SELECT role_name FROM {table_name} WHERE username = '{username}'"
    cur = mysql.connection.cursor()
    cur.execute(query)
    is_admin = cur.fetchone()


    if is_admin[0] != 'admin':
        return jsonify({"message": "Admin access required",
                        "success": False,
                        # "username" : username,
                        }), 403

    cur.execute(f"SELECT * FROM {table_name}")
    entries = cur.fetchall()
    users = []

    for entry in entries:
        user = {
            'user_id': entry[0],
            'username': entry[1],
            'passwd': entry[2],
            # 'token_id': entry[3],     # Security purposes
            'role_id': entry[4]
        }
        users.append(user)

    return jsonify(users), 200

# WAIT
if __name__ == "__main__":
    app.run(debug=True)