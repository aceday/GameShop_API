create table if not exists customer_purchases(
	purchase_id int auto_increment primary key,
    date_of_purchase date,
    other_purchase_details text
);