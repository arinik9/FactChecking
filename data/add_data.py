import ConfigParser, MySQLdb, os, sys
from datetime import datetime, timedelta

if __name__ == '__main__':
	# Database parameters
	conf_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + "/../db-config.ini"
	conf = ConfigParser.ConfigParser()
	conf.read( conf_path )
	db = MySQLdb.connect(
		conf.get('DB', 'host'),
		conf.get('DB', 'user'),
		conf.get('DB', 'password'),
		conf.get('DB', 'name')
	)
	date = datetime.strptime( "2015-09-01", "%Y-%m-%d" )
	query_start = "INSERT INTO fact_checking.chomagePE (mois, nb_chomeur) VALUES(\""
	nb_chomeur = 3591600
	db_cursor = db.cursor()
	for i in range(24):
		print(query_start + str(date.year) + '-' + str(date.month) + "-01\", " + str(nb_chomeur) + ");")
		db_cursor.execute(query_start + str(date.year) + '-' + str(date.month) + "-01\", " + str(nb_chomeur) + ");")
		print(len(sys.argv))
		if len(sys.argv) > 1:
			if sys.argv[1] == "up":
				nb_chomeur += 20000
			else:
				nb_chomeur -= 20000
		# Add one month
		date += timedelta(days=32)
		date = date.replace(day=1)
	db.commit()
