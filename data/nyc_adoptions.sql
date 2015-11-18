CONNECT fact_checking;
CREATE TABLE IF NOT EXISTS nyc_adoptions (
	year INT NOT NULL,
	adoptions INT NOT NULL
);

LOAD DATA LOCAL INFILE '/home/nejat/nyc_adoptions.csv' 
INTO TABLE nyc_adoptions 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
