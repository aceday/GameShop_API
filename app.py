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
app.config["MYSQL_DB"] = "event_reservations"
app.config["SECRET_KEY"] = "kyle123"

mysql = MySQL(app)
auth = HTTPBasicAuth()

@app.errorhandler(404)
def page_not_found(e):
    return "NOT FOUND :P", 404


# Homepage
@app.route("/", methods=["GET"])
def hello_world():
    with open("index.html", "r") as f:
        return f.read()


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
        return jsonify({"success": False, "message": "Username and password are required"}, 400)

    try:

        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE username = %s", (username,))
        
        if cur.fetchone():
            return jsonify({"success": False, "message": "Username already exists"}, 400)

        role_id         = 1         # Default role_id
        password_enc    = generate_password_hash(password)
        
        # Commit a user credential
        cur.execute("INSERT INTO users (username, passwd, role_id) VALUES (%s, %s, %s)", (username, password_enc, role_id))
        mysql.connection.commit()
        
        return jsonify({"success": True, "message": "Account created successfully"}, 201)
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False,
                        "message": str(e)
                        },409)
    finally:
        cur.close()




if __name__ == "__main__":
    app.run(debug=True)