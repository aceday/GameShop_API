create table customer_orders(order_id int primary key auto_increment,
date_of_order datetime,
other_order_details varchar(100));


alter table customer_orders add column product_id int;


ALTER TABLE customer_orders 
ADD CONSTRAINT fk_product_id 
FOREIGN KEY (product_id) 
REFERENCES products (product_id);


ALTER TABLE customer_orders
ADD COLUMN customer_id INT;

ALTER TABLE customer_orders
ADD CONSTRAINT fk_customer_id
FOREIGN KEY (customer_id)
REFERENCES customer(customer_id);
