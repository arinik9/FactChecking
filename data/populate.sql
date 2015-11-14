CREATE DATABASE fact_checking CHARACTER SET utf8 COLLATE utf8_general_ci;
CONNECT fact_checking;

/*****************************************************************
***********      INSEE
*****************************************************************/
CREATE TABLE IF NOT EXISTS chomage (
	annee INT NOT NULL,
	trimestre INT NOT NULL,
	millier INT NOT NULL,
	taux FLOAT(3,1)
);
/* /home/nejat/ProjSpec/FactChecking/chomage.csv */
LOAD DATA INFILE '/home/hh/prog/FactChecking/chomage.csv' 
INTO TABLE chomage 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Claim 1
select sum(millier)*1000 from chomage where annee = 2007 and trimestre = 2; /*   2 154 000*/
select sum(millier)*1000 from chomage where annee = 2012 and trimestre = 1; /* - 2 582 000 = 428 000*/

/*****************************************************************
***********      POLE EMPLOI
*****************************************************************/
CREATE TABLE IF NOT EXISTS chomagePE (
	mois DATE NOT NULL,
	nb_chomeur INT NOT NULL
);
/* /home/nejat/ProjSpec/FactChecking/chomagePEcatA.csv */
LOAD DATA INFILE '/home/hh/prog/FactChecking/chomagePEcatA.csv' 
INTO TABLE chomagePE 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

