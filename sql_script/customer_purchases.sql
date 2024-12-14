
create table customer_purchases(purchase_id int auto_increment primary key,
date_of_purchase datetime,
other_purchase_details varchar(100));

alter table customer_purchases add column customer_id int,
add column product_id int;

ALTER TABLE customer_purchases
ADD CONSTRAINT fk_customer_id
FOREIGN KEY (customer_id)
REFERENCES customer (customer_id);


alter table customer_purchases add constraint fk_product_id foreign key (product_id) references products(product_id);
