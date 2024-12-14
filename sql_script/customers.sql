create table if not exists customer(
	customer_id int auto_increment primary key,
    customer_code varchar(9),
    customer_name varchar(48),
    customer_address varchar(64),
    customer_OtherDetails text
);