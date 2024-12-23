# **GameShop_API**
Game Shop backend runs with python flask, no modern just CLI in 1985


### Framework Used
- **Python Flask**

### Database used
- **MySQL and MariaDB**

---

### Example Usage
#### Customers
- `{hostname}/customers` - Get all customer details.
- `{hostname}/customer/id` - Get customer by specifying id number.

### Products
- `{hostname}/products/` - Gets all products available.
- `{hostname}/products/id` Get product by specifying id number.

### Customer Orders
- `{hostname}/customer_orders` - Gets all order entries by customers.
- `{hostname}/customer_orders` - Get a detail customer order by specifying id number.


### Customer Purchases
- `{hostname}/customer_purchases` - Gets all purchases entries by customers.
- `{hostname}/customer_purchases` - Get a detail customer purchase by specifying id number.

### Register an account and Login
- `{hostname}/register` - Register an account.
- `{hostname}/login` - Login an account, to generate the token.
---

### 

### Modify the entry
- `POST, PUT and DELETE` - Require login, so go to the `/register`.



