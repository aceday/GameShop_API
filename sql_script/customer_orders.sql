create table if not exists customer_orders(
	order_id int auto_increment primary key,
    date_of_order date,
    other_order_details text
);