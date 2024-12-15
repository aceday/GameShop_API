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

# ACCESSORIES
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

# PRODUCT TYPES
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

if __name__ == "__main__":
    app.run(debug=True)