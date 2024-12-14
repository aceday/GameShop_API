CREATE TABLE drive_types (
product_id INT,
size INT,
other_console_details TEXT,
FOREIGN KEY (product_id) REFERENCES products(product_id)
);
