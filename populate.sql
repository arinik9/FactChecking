CREATE DATABASE fact_checking CHARACTER SET utf8 COLLATE utf8_general_ci;
CONNECT fact_checking;

/*******************************************************************************
**********     CHOMAGE
*******************************************************************************/
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

CREATE VIEW Vchomage AS SELECT
SUM(T1_2008 + T2_2008 + T3_2008 + T4_2008) A2008,
SUM(T1_2009 + T2_2009 + T3_2009 + T4_2009) A2009,
SUM(T1_2010 + T2_2010 + T3_2010 + T4_2010) A2010,
SUM(T1_2011 + T2_2011 + T3_2011 + T4_2011) A2011
FROM chomage;

/*******************************************************************************
**********     POPULATION
*******************************************************************************/
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

