CREATE DATABASE fact_checking CHARACTER SET utf8 COLLATE utf8_general_ci;
CONNECT fact_checking;
CREATE TABLE IF NOT EXISTS chomage (
	ZE2010 INT NOT NULL,
	LIBZE2010 VARCHAR(255) NOT NULL,
	T2_2007 FLOAT(3,1),
	T3_2007 FLOAT(3,1),
	T4_2007 FLOAT(3,1),

	T1_2008 FLOAT(3,1),
	T2_2008 FLOAT(3,1),
	T3_2008 FLOAT(3,1),
	T4_2008 FLOAT(3,1),

	T1_2009 FLOAT(3,1),
	T2_2009 FLOAT(3,1),
	T3_2009 FLOAT(3,1),
	T4_2009 FLOAT(3,1),

	T1_2010 FLOAT(3,1),
	T2_2010 FLOAT(3,1),
	T3_2010 FLOAT(3,1),
	T4_2010 FLOAT(3,1),

	T1_2011 FLOAT(3,1),
	T2_2011 FLOAT(3,1),
	T3_2011 FLOAT(3,1),
	T4_2011 FLOAT(3,1),

	T1_2012 FLOAT(3,1)
);

LOAD DATA INFILE '/home/nejat/ProjSpec/FactChecking/chomageParZoneEmploi_trimestrielle_France.csv' 
INTO TABLE chomage 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

CREATE TABLE IF NOT EXISTS population (
	annee INT NOT NULL,
	population_active INT NOT NULL
);
LOAD DATA INFILE '/home/hh/prog/FactChecking/population-active.csv' 
INTO TABLE population
FIELDS TERMINATED BY ';' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Pour créer un vue afin de l'utiliser l'operation 'join' sur la table chomage et population

CREATE VIEW chomageByYear AS
SELECT ROUND(ZE2010/100) as "regioncode", LIBZE2010 as "ville", sum(T2_2007+T3_2007+T4_2007)/3 as "2007",
 sum(T1_2008+T2_2008+T3_2008+T4_2008)/4 as "2008",
sum(T1_2009+T2_2009+T3_2009+T4_2009)/4 as "2009",
sum(T1_2010+T2_2010+T3_2010+T4_2010)/4 as "2010",
sum(T1_2011+T2_2011+T3_2011+T4_2011)/4 as "2011",
T1_2012 as "2012"
from chomage
group by ZE2010;

Select * from chomageByYear; 
