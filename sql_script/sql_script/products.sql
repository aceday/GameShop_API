CREATE TABLE products (
  product_id INT PRIMARY KEY,
  product_description VARCHAR(50),
  product_name CHAR(50),
  product_price REAL,
  product_type_code INT,
  FOREIGN KEY (product_type_code) REFERENCES product_types(product_type_code)
);
