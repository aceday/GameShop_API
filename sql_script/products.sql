create table if not exists products(
	product_id int auto_increment primary key,
    product_description text,
    product_name varchar(48),
    product_price real
);