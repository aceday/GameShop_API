import pytest, os, sys, flask, time
from app import app, mysql
from faker import Faker
os.system('clear' if os.name == 'posix' else 'cls')
print("Make sure edit first the variable HOST at line 55 before test :)")
time.sleep(2)
# Generators
def gen_account():
    return {
        "username": Faker().user_name(),
        "password": Faker().password()
    }

def gen_customer():
    return {
        "customer_code": Faker().random_number(digits=5),
        "customer_name": Faker().name(),
        "customer_other_details": Faker().sentence()
    }

def gen_product():
    items = ["Call of Duty", "FIFA 22", "Minecraft", "Fortnite", "GTA V", "Cyberpunk 2077",
                "Red Dead Redemption 2", "The Witcher 3", "Overwatch", "Apex Legends", "Valorant", 
                "League of Legends", "World of Warcraft", "Dota 2", "Counter Strike: Global Offensive",
                "Rainbow Six Siege", "Rocket League", "Among Us", "Fall Guys", "Minecraft Dungeons", 
                "Halo Infinite", "Forza Horizon 5", "Assassin's Creed Valhalla", "Far Cry 6", 
                "Watch Dogs: Legion", "The Division 2", "Ghost Recon: Breakpoint", "Rainbow Six Extraction", 
                "Just Dance 2022", "Immortals Fenyx Rising", "Prince of Persia: The Sands of Time", 
                "Splinter Cell: Blacklist", "Beyond Good and Evil 2", "Rayman Legends", "Rabbids Invasion", 
                "Mario + Rabbids"]
    return {
        "product_name": Faker().random_element(elements=items),
        "product_code": Faker().random_number(digits=5),
        "price": Faker().random_number(digits=2),
        "product_type": Faker().random_element(elements=["Game Software","Game Software"]),
    }

def gen_customer_order():
    return {
        "date_of_order": Faker().date(),
        "customer_id": Faker().random_number(digits=2),
        "product_id": Faker().random_number(digits=2),
        "other_order_details": Faker().sentence()
    }

def gen_customer_purchase():
    return {
        "date_of_purchase": Faker().date(),
        "customer_id": Faker().random_number(digits=2),
        "product_id": Faker().random_number(digits=2),
        "other_order_purchase_details": Faker().sentence()
    }

# VARIABLES
HOST = "localhost:5000"
DEBUG = True
client = app.test_client()
app.config['TESTING'] = True

username = gen_account()["username"]
password = gen_account()["password"]


with app.app_context():
    cur = mysql.connection.cursor()
    real_token = ""
    cur = mysql.connection.cursor()

# Refresh fetcher
def refresh_customers():
    response = client.get('/customers')
    # Count customers
    try:
        if len(response.json) > 0:
            return response.json
    except:
        return {
            "customer_code" : gen_customer()["customer_code"],
            "customer_name" : gen_customer()["customer_name"],
            "customer_other_details" : gen_customer()["customer_other_details"]
        }

def refresh_products():
    response = client.get('/products')
    # Count products
    try:
        if len(response.json) > 0:
            return response.json
    except:
        return {
            "product_name" : gen_product()["product_name"],
            "product_code" : gen_product()["product_code"],
            "price" : gen_product()["price"],
            "product_type" : gen_product()["product_type"]
        }

def refresh_customer_orders():
    response = client.get('/customer_orders')
    # Count orders
    try:
        if len(response.json) > 0:
            return response.json
    except:
        return {
            "date_of_order" : gen_customer_order()["date_of_order"],
            "customer_id" : gen_customer_order()["customer_id"],
            "product_id" : gen_customer_order()["product_id"],
            "other_order_details" : gen_customer_order()["other_order_details"]
        }

def refresh_customer_purchases():
    response = client.get('/customer_purchases')
    # Count purchases
    try:
        if len(response.json) > 0:
            return response.json
    except:
        return {
            "date_of_purchase" : gen_customer_purchase()["date_of_purchase"],
            "customer_id" : gen_customer_purchase()["customer_id"],
            "product_id" : gen_customer_purchase()["product_id"],
            "other_order_purchase_details" : gen_customer_purchase()["other_order_purchase_details"]
        }

# Tests

@pytest.fixture 
def test_host():
    response = client.get('/')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_home():
    response = client.get('/')
    assert response.status_code == 200

def test_register_first():
    global username, password
    response = client.post('/register', 
                        json={
                            "username": username,
                            "password": password},
                        headers={
                            "Content-Type": "application/json"
                        })
    if DEBUG:
        print(response.status_code, response.data)
    assert response.status_code == 201

def test_register_second():
    global username, password
    response = client.post('/register', 
                        json={
                            "username": username,
                            "password": password},
                        headers={
                            "Content-Type": "application/json"
                        })
    if DEBUG:
        print(response.status_code, response.data)
    assert response.status_code == 409

def test_login_first():
    global username, password
    response = client.post('/login', 
                        json={
                            "username": username,
                            "password": password},
                        headers={
                            "Content-Type": "application/json"
                        })
    if DEBUG:
        print(response.status_code, response.data)

    # Update token
    global real_token
    real_token = response.json["token"]

    assert response.status_code == 200

# CUSTOMERS
def test_customers_get():
    response = client.get('/customers')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_customers_get_id():
    customers = refresh_customers()
    customer_last_id = customers[-1]['customer_id']
    response = client.get(f'/customers/{customer_last_id}')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_customers_post():
    customer = gen_customer()
    response = client.post('/customers',
                            headers={
                                'Content-Type': 'application/json',
                                'Authorization' : f'Bearer {real_token}'
                            },
                            json={
                                'customer_code': customer["customer_code"],
                                'customer_name': customer["customer_name"],
                                'customer_other_details': customer["customer_other_details"]
                            })
    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
    assert response.status_code == 201

def test_customers_put():
    customers = refresh_customers()
    customer_last_id = customers[-1]['customer_id']
    customer = gen_customer()
    # close foreign key check
    response = client.put(f'/customers/{customer_last_id}',
                            headers={
                                'Content-Type': 'application/json',
                                'Authorization' : f'Bearer {real_token}'
                            },
                            json={
                                'customer_code': customer["customer_code"],
                                'customer_name': customer["customer_name"],
                                'customer_other_details': customer["customer_other_details"]
                            })
    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
    assert response.status_code == 200

def test_customers_delete():
    customers = refresh_customers()
    customer_last_id = customers[-1]['customer_id']
    response = client.delete(f'/customers/{customer_last_id}',
                            headers={
                                'Authorization' : f'Bearer {real_token}'
                            })
    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
        print(f"Customer ID: {customer_last_id}")
    assert response.status_code == 200

# Products
def test_products_get():
    response = client.get('/products')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_products_get_id():
    response = client.get('/products')
    products = response.json
    product_last_id = products[-1]['product_id']
    response = client.get(f'/products/{product_last_id}')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_products_post():
    product = gen_product()
    response = client.post('/products',
                            headers={
                                'Content-Type': 'application/json',
                                'Authorization' : f'Bearer {real_token}'
                            },
                            json={
                                'product_name': product["product_name"],
                                'product_code': product["product_code"],
                                'product_type': product["product_type"],
                                'price': product["price"]
                            })
    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
    assert response.status_code == 201

def test_products_put():
    products = refresh_products()
    product_last_id = products[-1]['product_id']
    product = gen_product()
    response = client.put(f'/products/{product_last_id}',
                            headers={
                                'Content-Type': 'application/json',
                                'Authorization' : f'Bearer {real_token}'
                            },
                            json={
                                'product_name': product["product_name"],
                                'product_code': product["product_code"],
                                'product_type': product["product_type"],
                                'price': product["price"]
                            })
    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
    assert response.status_code == 200

def test_products_delete():
    products = refresh_products()
    product_last_id = products[-1]['product_id']
    response = client.delete(f'/products/{product_last_id}',
                            headers={
                                'Authorization' : f'Bearer {real_token}'
                            })
    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
        print(f"Product ID: {product_last_id}")
    assert response.status_code == 200

# Customer Orders
def test_customer_orders_get():
    response = client.get('/customer_orders')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_customer_orders_get_id():
    response = client.get('/customer_orders')
    orders = response.json
    order_last_id = orders[-1]['order_id']
    response = client.get(f'/customer_orders/{order_last_id}')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_customer_orders_post():
    # Check availability customer_id from customers
    customers = refresh_customers()
    customer_id = customers[-1]['customer_id']

    # Check availability product_id from products
    products = refresh_products()
    product_id = products[-1]['product_id']

    order = gen_customer_order()

    response = client.post('/customer_orders',
                            headers={
                                'Content-Type': 'application/json',
                                'Authorization' : f'Bearer {real_token}'
                            },
                            json={
                                'date_of_order': order["date_of_order"],
                                'customer_id': customer_id,
                                'product_id': product_id,
                                'other_order_details': order["other_order_details"]
                            })

    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
    assert response.status_code == 201

def test_customer_orders_put():
    orders = refresh_customer_orders()
    order_last_id = orders[-1]['order_id']

    # Check availability customer_id from customers
    customers = refresh_customers()
    customer_id = customers[-1]['customer_id']

    # Check availability product_id from products
    products = refresh_products()
    product_id = products[-1]['product_id']

    order = gen_customer_order()

    response = client.put(f'/customer_orders/{order_last_id}',
                            headers={
                                'Content-Type': 'application/json',
                                'Authorization' : f'Bearer {real_token}'
                            },
                            json={
                                'date_of_order': order["date_of_order"],
                                'customer_id': customer_id,
                                'product_id': product_id,
                                'other_order_details': order["other_order_details"]
                            })

    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
    assert response.status_code == 200

def test_customer_orders_delete():
    orders = refresh_customer_orders()
    order_last_id = orders[-1]['order_id']
    response = client.delete(f'/customer_orders/{order_last_id}',
                            headers={
                                'Authorization' : f'Bearer {real_token}'
                            })
    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
        print(f"Order ID: {order_last_id}")
    assert response.status_code == 200


# CUSTOMER PURCHASES
def test_customer_purchases_get():
    response = client.get('/customer_purchases')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_customer_purchases_get_id():
    purchases = refresh_customer_purchases()
    purchase_last_id = purchases[-1]['purchase_id']
    response = client.get(f'/customer_purchases/{purchase_last_id}')
    if DEBUG:
        print(response)
    assert response.status_code == 200

def test_customer_purchases_post():
    # Check availability customer_id from customers
    customers = refresh_customers()
    customer_id = customers[-1]['customer_id']

    # Check availability product_id from products
    products = refresh_products()
    product_id = products[-1]['product_id']

    purchase = gen_customer_purchase()

    response = client.post('/customer_purchases',
                            headers={
                                'Content-Type': 'application/json',
                                'Authorization' : f'Bearer {real_token}'
                            },
                            json={
                                'date_of_purchase': purchase["date_of_purchase"],
                                'customer_id': customer_id,
                                'product_id': product_id,
                                'other_order_purchase_details': purchase["other_order_purchase_details"]
                            })

    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
    assert response.status_code == 201

def test_customer_purchases_put():
    purchases = refresh_customer_purchases()
    purchase_last_id = purchases[-1]['purchase_id']

    # Check availability customer_id from customers
    customers = refresh_customers()
    customer_id = customers[-1]['customer_id']

    # Check availability product_id from products
    products = refresh_products()
    product_id = products[-1]['product_id']

    purchase = gen_customer_purchase()

    response = client.put(f'/customer_purchases/{purchase_last_id}',
                            headers={
                                'Content-Type': 'application/json',
                                'Authorization' : f'Bearer {real_token}'
                            },
                            json={
                                'date_of_purchase': purchase["date_of_purchase"],
                                'customer_id': customer_id,
                                'product_id': product_id,
                                'other_order_purchase_details': purchase["other_order_purchase_details"]
                            })

    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
    assert response.status_code == 200

def test_customer_purchases_delete():
    purchases = refresh_customer_purchases()
    purchase_last_id = purchases[-1]['purchase_id']
    response = client.delete(f'/customer_purchases/{purchase_last_id}',
                            headers={
                                'Authorization' : f'Bearer {real_token}'
                            })
    if DEBUG:
        print(f"Error: {response.status_code}, {response.get_data(as_text=True)}")
        print(f"Purchase ID: {purchase_last_id}")
    assert response.status_code == 200


if __name__ == '__main__':
    pytest.main()