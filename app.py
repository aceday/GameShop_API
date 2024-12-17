from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_httpauth import HTTPBasicAuth
import jwt, datetime , json
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
            return jsonify({"error": "Token has expired!, login again!"}), 401
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

    # curl -X POST localhost:5000/login -H "Content-Type: application/json" -d "{\"username\":\"your_username\",\"password\":\"your_password\"}"

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

@app.route("/protected", methods=["GET"])
@token_required
def protected_route():
    return jsonify({"message": f"Hello, {request.username}!"})


# SECTION: CREATE AN USER ACCOUNT

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return jsonify({"message": "You need to query it :P"})

    elif request.method == "POST":
        data = request.json
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 401

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT username FROM users WHERE username = %s", (username,))
            
            if cur.fetchone():
                return jsonify({"success": False, "message": "Username already exists"}), 409

            role_id = 1  # Default role_id
            password_enc = generate_password_hash(password)
            
            cur.execute("INSERT INTO users (username, passwd, role_id) VALUES (%s, %s, %s)", (username, password_enc, role_id))
            mysql.connection.commit()
            
            return jsonify({"success": True, "message": "Account created successfully"}), 201
        
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"success": False, "message": str(e)}), 409
        finally:
            cur.close()

# CUSTOMERS
@app.route("/customers", methods=["GET"])
def get_customers():

    # curl -X GET localhost:5000/register

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
@token_required
def post_customer():

    # curl -X POST localhost:5000/customers -H "Authorization: Bearer your_token" -H "Content-Type: application/json" -d "{\"customer_code\":\"your_code\",\"customer_name\":\"Your Name\",\"customer_other_details\":\"Additional Details\"}"

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
        cur.execute("INSERT INTO customer (customer_code, customer_name, customer_OtherDetails) VALUES (%s, %s, %s)", 
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
@token_required
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
@token_required
def delete_customer(customer_id):

    # curl -X DELETE "localhost:5000/customers/your_id" -H "Authorization: Bearer your_token"

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


# --------------- CUSTOM ORDERS  ---------------
# 

# CUSTOMER ORDERS
@app.route("/customer_orders", methods=["GET"])
def get_customer_orders():

    # curl -X GET localhost:5000/customer_orders

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
@token_required
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

# Update record customer_order
@app.route("/customer_orders/<int:order_id>", methods=["PUT"])
@token_required
def put_customer_order(order_id):

    # curl -X PUT "localhost:5000/customer_orders/1" -H "Authorization: Bearer your_token" -H "Content-Type: application/json" -d "{\"date_of_order\": \"2024-12-17\", \"other_order_details\": \"Urgent delivery\", \"product_id\": 1, \"customer_id\": 1}"

    data = request.get_json()
    date_of_order = data.get("date_of_order")
    other_order_details = data.get("other_order_details")
    product_id = data.get("product_id")
    customer_id = data.get("customer_id")

    # Validation
    if not all([date_of_order, other_order_details, product_id, customer_id]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    # Check order existence
    cur = mysql.connection.cursor()
    cur.execute("SELECT order_id FROM customer_orders WHERE order_id = %s", (order_id,))
    if not cur.fetchone():
        return jsonify({"success": False, "message": "Order not found"}), 404

    # Check product and customer existence
    cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
    if not cur.fetchone():
        return jsonify({"success": False, "message": "Product not found"}), 404

    cur.execute("SELECT customer_id FROM customer WHERE customer_id = %s", (customer_id,))
    if not cur.fetchone():
        return jsonify({"success": False, "message": "Customer not found"}), 404

    try:
        cur.execute("UPDATE customer_orders SET date_of_order = %s, other_order_details = %s, product_id = %s, customer_id = %s WHERE order_id = %s",
                    (date_of_order, other_order_details, product_id, customer_id, order_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Customer order updated successfully"}), 200
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# Delete record customer_orders
@app.route("/customer_orders/<int:order_id>", methods=["DELETE"])
@token_required
def delete_customer_order(order_id):

    # curl -X DELETE "localhost:5000/customer_orders/1" -H "Authorization: Bearer your_token"
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT order_id FROM customer_orders WHERE order_id = %s", (order_id,))
        if not cur.fetchone():
            return jsonify({"success": False, "message": "Order not found"}), 404

        cur.execute("DELETE FROM customer_orders WHERE order_id = %s", (order_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Customer order deleted successfully"}), 200
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    


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

# Commit customer_purchase
@app.route("/customer_purchases", methods=["POST"])
@token_required
def post_customer_purchase():

    # curl -X POST -H "Content-Type: application/json" -d "{\"customer_id\": 1, \"product_id\": 1, \"date_of_purchase\": \"2024-12-16\", \"other_purchase_details\": \"Credit card payment\"}" http://localhost:5000/customer_purchases
    
    data = request.get_json()
    
    # Extract fields from the request
    customer_id = data.get("customer_id")
    product_id = data.get("product_id")
    date_of_purchase = data.get("date_of_purchase")
    other_purchase_details = data.get("other_purchase_details")

    # Validate required fields
    if not all([customer_id, product_id, date_of_purchase]):
        return jsonify({
            "success": False,
            "message": "Missing required fields: customer_id, product_id, or date_of_purchase"
        }), 400

    # SQL INSERT query
    query = """
        INSERT INTO customer_purchases (customer_id, product_id, date_of_purchase, other_purchase_details)
        VALUES (%s, %s, %s, %s)
    """
    values = (customer_id, product_id, date_of_purchase, other_purchase_details)

    try:
        cur = mysql.connection.cursor()
        cur.execute(query, values)
        mysql.connection.commit()
        cur.close()

        return jsonify({
            "success": True,
            "message": "Customer purchase added successfully"
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Update a record for customer_purchase
@app.route("/customer_purchases/<int:customer_id>/<int:product_id>", methods=["PUT"])
@token_required
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
@token_required
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

# --------------- PRODUCTS --------------- (NORM)
@app.route("/products", methods=["GET", "POST"])
@app.route("/products/<int:product_id>", methods=["GET", "POST", "PUT", "DELETE"])
def products(product_id=None):
    table_name = "products_norm"

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
                cur.execute(
                    f"INSERT INTO {table_name} (product_name, price, product_type, product_code) VALUES (%s, %s, %s, %s)",
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
                cur.execute(
                    f"UPDATE {table_name} SET product_name = %s, price = %s, product_type = %s, product_code = %s WHERE product_id = %s",
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
def get_users():
    table_name = "users"
    query = f"SELECT * FROM {table_name}"

    cur = mysql.connection.cursor()

    cur.execute(query)
    entries = cur.fetchall()

    users = []

    for entry in entries:
        user = {
            'user_id': entry[0],
            'username': entry[1],
            'passwd': entry[2],
            'token_id': entry[3],
            'role_id': entry[4]
        }
        users.append(user)

    return jsonify(users), 200

# WAIT
if __name__ == "__main__":
    app.run(debug=True)