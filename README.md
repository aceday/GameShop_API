# GameShop API

This is a Flask-based API for managing a game shop. It includes endpoints for user authentication, customer management, product management, and customer orders.

## Requirements

- Python 3.x
- Flask
- Flask-MySQLdb
- Flask-HTTPAuth
- PyJWT
- Faker

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/GameShop_API.git
    cd GameShop_API
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up your MySQL database and update the configuration in [app.py](http://_vscodecontentref_/1):
    ```python
    app.config["MYSQL_HOST"] = "your_mysql_host"
    app.config["MYSQL_USER"] = "your_mysql_user"
    app.config["MYSQL_PASSWORD"] = "your_mysql_password"
    app.config["MYSQL_DB"] = "your_mysql_db"
    app.config["SECRET_KEY"] = "your_secret_key"
    ```

## Running the Application

1. Start the Flask application:
    ```sh
    python app.py
    ```

2. The API will be available at `http://127.0.0.1:5000`.

## API Endpoints

### Authentication

- **Login**
    - `POST /login`
    - Request body: `{ "username": "your_username", "password": "your_password" }`
    - Response: `{ "success": True, "message": "Logged In Successfully", "token": "your_jwt_token" }`

- **Register**
    - `POST /register`
    - Request body: `{ "username": "your_username", "password": "your_password" }`
    - Response: `{ "success": True, "message": "Account created successfully" }`

### Customers

- **Get all customers**
    - `GET /customers`
    - Response: List of customers

- **Get customer by ID**
    - `GET /customers/<int:id>`
    - Response: Customer details

- **Create customer**
    - `POST /customers`
    - Request body: `{ "customer_code": "code", "customer_name": "name", "customer_other_details": "details" }`
    - Response: `{ "success": True, "message": "Customer created successfully" }`

- **Update customer**
    - `PUT /customers/<int:id>`
    - Request body: `{ "customer_code": "code", "customer_name": "name", "customer_other_details": "details" }`
    - Response: `{ "success": True, "message": "Customer updated successfully" }`

- **Delete customer**
    - `DELETE /customers/<int:id>`
    - Response: `{ "success": True, "message": "Customer deleted successfully" }`

### Products

- **Get all products**
    - `GET /products`
    - Response: List of products

- **Get product by ID**
    - `GET /products/<int:product_id>`
    - Response: Product details

- **Create product**
    - `POST /products`
    - Request body: `{ "product_name": "name", "price": "price", "product_type": "type", "product_code": "code" }`
    - Response: `{ "success": True, "message": "Product created successfully" }`

- **Update product**
    - `PUT /products/<int:product_id>`
    - Request body: `{ "product_name": "name", "price": "price", "product_type": "type", "product_code": "code" }`
    - Response: `{ "success": True, "message": "Product updated successfully" }`

- **Delete product**
    - `DELETE /products/<int:product_id>`
    - Response: `{ "success": True, "message": "Product deleted successfully" }`

### Customer Orders

- **Get all customer orders**
    - `GET /customer_orders`
    - Response: List of customer orders

- **Get customer order by ID**
    - `GET /customer_orders/<int:order_id>`
    - Response: Customer order details

- **Create customer order**
    - `POST /customer_orders`
    - Request body: `{ "date_of_order": "date", "other_order_details": "details", "product_id": "product_id", "customer_id": "customer_id" }`
    - Response: `{ "success": True, "message": "Customer order created successfully" }`

- **Update customer order**
    - `PUT /customer_orders/<int:order_id>`
    - Request body: `{ "date_of_order": "date", "other_order_details": "details", "product_id": "product_id", "customer_id": "customer_id" }`
    - Response: `{ "success": True, "message": "Customer order updated successfully" }`

- **Delete customer order**
    - `DELETE /customer_orders/<int:order_id>`
    - Response: `{ "success": True, "message": "Customer order deleted successfully" }`

### Customer Purchases

- **Get all customer purchases**
    - `GET /customer_purchases`
    - Response: List of customer purchases

- **Get customer purchase by ID**
    - `GET /customer_purchases/<int:customer_purchase_id>`
    - Response: Customer purchase details

- **Create customer purchase**
    - `POST /customer_purchases`
    - Request body: `{ "customer_id": "customer_id", "product_id": "product_id", "date_of_purchase": "date", "other_purchase_details": "details" }`
    - Response: `{ "success": True, "message": "Customer purchase added successfully" }`

- **Update customer purchase**
    - `PUT /customer_purchases/<int:customer_purchase_id>`
    - Request body: `{ "date_of_purchase": "date", "other_purchase_details": "details" }`
    - Response: `{ "success": True, "message": "Customer purchase updated successfully" }`

- **Delete customer purchase**
    - `DELETE /customer_purchases/<int:customer_purchase_id>`
    - Response: `{ "success": True, "message": "Customer purchase deleted successfully" }`
