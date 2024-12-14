CREATE TABLE accessories (
product_id INT,
accessory_name VARCHAR(255),
accessory_description TEXT,
other_accessory_details TEXT,
FOREIGN KEY (product_id) REFERENCES products(product_id)
);
