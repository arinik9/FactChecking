import ConfigParser, MySQLdb, os
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
	query_start = "DELETE FROM fact_checking.chomagePE WHERE mois = \""
	db_cursor = db.cursor()
	for i in range(24):
		print(query_start + str(date.year) + '-' + str(date.month) + "-01\"" + ";")
		db_cursor.execute(query_start + str(date.year) + '-' + str(date.month) + "-01\"" + ";")
		# Add one month
		date += timedelta(days=32)
		date = date.replace(day=1)
	db.commit()
