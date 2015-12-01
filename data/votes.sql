CONNECT fact_checking;
CREATE TABLE IF NOT EXISTS bachmann (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS boehner (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS clyburn (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS kaptur (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS kucinich (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS marshall (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS oberstar (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS rangel (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS rayn (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS schock (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

CREATE TABLE IF NOT EXISTS speier (
	vote_session INT NOT NULL,
	vote_number INT NOT NULL,
	person_id INT NOT NULL,
	person_firstname VARCHAR(50) NOT NULL,
	person_lastname VARCHAR(50) NOT NULL,
	option_key VARCHAR(1) NOT NULL,
	vote_created DATE,
	vote_question VARCHAR(200) NOT NULL,
	PRIMARY KEY (vote_session,vote_number)
);

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_bachmann_2007-octobre2010.csv' 
INTO TABLE bachmann 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_boehner_2007-octobre2010.csv' 
INTO TABLE boehner 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_clyburn_2007-octobre2010.csv' 
INTO TABLE clyburn 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_kaptur_2007-octobre2010.csv' 
INTO TABLE kaptur 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_kucinich_2007-octobre2010.csv' 
INTO TABLE kucinich 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_marshall_2007-octobre2010.csv' 
INTO TABLE marshall 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_oberstar_2007-octobre2010.csv' 
INTO TABLE oberstar 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_rangel_2007-octobre2010.csv' 
INTO TABLE rangel 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_rayn_2007-octobre2010.csv' 
INTO TABLE rayn 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_schock_2007-octobre2010.csv' 
INTO TABLE schock 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/home/nejat/us_congress_votes/csv/votes_speier_2007-octobre2010.csv' 
INTO TABLE speier 
FIELDS TERMINATED BY ',' 
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
