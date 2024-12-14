create table if not exists games(
	-- game_id int auto_increment primary key,
    game_name varchar(48),
    memory_required int,
    number_of_players int,
    other_game_details text
);