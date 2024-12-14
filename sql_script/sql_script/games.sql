-- LATEST
CREATE TABLE games (
product_id INT,
game_name VARCHAR(255),
memory_required INT,
number_of_players INT,
other_game_details TEXT,
FOREIGN KEY (product_id) REFERENCES products(product_id)
);
