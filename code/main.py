#!/usr/bin/python
from qrs import qrs
import ConfigParser, os

if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    obj = qrs('2014-10-01', 30, 30, 310900, 'increasing')
    conf_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + "/../db-config.ini"

    conf.read(conf_path)
    obj.connectToDb(
        conf.get('DB', 'host'),
        conf.get('DB', 'user'),
        conf.get('DB', 'password'),
        conf.get('DB', 'name')
    )
    obj.setDbTableName('chomagePE')
  
    query = "SELECT hollande.chomage - sarkozy.chomage FROM ( SELECT bf.nb_chomeur - af.nb_chomeur AS chomage FROM ( SELECT nb_chomeur FROM fact_checking.chomagePE WHERE mois = %s ) AS bf, ( SELECT nb_chomeur FROM fact_checking.chomagePE WHERE mois = %s - INTERVAL %s MONTH ) AS af ) AS hollande, ( SELECT bf.nb_chomeur - af.nb_chomeur AS chomage FROM ( SELECT nb_chomeur FROM fact_checking.chomagePE WHERE mois = %s - INTERVAL %s MONTH ) AS bf, ( SELECT nb_chomeur FROM fact_checking.chomagePE WHERE mois = %s - INTERVAL %s MONTH ) AS af ) AS sarkozy;"
    obj.setQuery(query)

    times = ['2008-01-01', '2015-08-01'] #TODO
    width = [30]
    durations = range(30,36)  # or range(15, 61) TO TEST less than 30
    obj.setParametersInterval(times, widths, durations)
    obj.setNaturalnessLevels([(1,1), (2.71, 60)]) # exponential =~ 2.71
    obj.setSigmaValues(3, 1, 10)
    
    results = obj.executeQuery() #results is a tuple with 4 params

    for result in results:
        t = result[0]
        w = result[1]
        d = result[2]
        r = result[3]
        score_sr = obj.computeSrScore(r)
        score_sp = obj.computeSpScore(w, d, t)
        print("t:", t, "w:", w, "d:", d, "r:", r, "score_sr:", score_sr, "score_sp:", score_sp)

    obj.closeDb()

