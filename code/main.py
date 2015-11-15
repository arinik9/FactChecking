#!/usr/bin/python
from qrs import qrs
import ConfigParser, os
import numpy as np

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

    times = ['2008-01-01', '2015-08-01']
    widths = [30]
    durations = range(30,36)  # or range(15, 61) TO TEST less than 30
    obj.setParametersInterval(times, widths, durations)
    obj.setNaturalnessLevels([(1,1), (2.71, 60)]) # exponential =~ 2.71
    obj.setSigmaValues(3, 1, 10)
    
    results = obj.executeQuery() #results is a tuple with 4 params
    matrix_sr=[np.nan]*len(durations)  #init
    matrix_sp=[np.nan]*len(durations)  #init
    #we  construct our matrix column by column
    

    old_t = results[0][0]
    column_sr = []
    column_sp = []
    for result in results:
        t = result[0]
        w = result[1]
        d = result[2]
        r = result[3]
        if str(t) != str(old_t):
            matrix_sr = np.column_stack((matrix_sr,column_sr+[np.nan]*(len(durations)-len(column_sr))))
            matrix_sp = np.column_stack((matrix_sp,column_sp+[np.nan]*(len(durations)-len(column_sp))))
            column_sr = []
            column_sp = []
        old_t = t
        score_sr = obj.computeSrScore(r)
        column_sr.append(score_sr)
        score_sp = obj.computeSpScore(w, d, t)
        column_sp.append(score_sp)

        #print("t:", t, "w:", w, "d:", d, "r:", r, "score_sr:", score_sr, "score_sp:", score_sp)
    matrix_sr = np.column_stack((matrix_sr,column_sr+[np.nan]*(len(durations)-len(column_sr))))
    matrix_sp = np.column_stack((matrix_sp,column_sp+[np.nan]*(len(durations)-len(column_sp))))
    matrix_sr = np.delete(matrix_sr, 0, 1) #we delete initialized row
    matrix_sp = np.delete(matrix_sp, 0, 1) # we delete initialized row

    obj.closeDb()
    
    obj.displaySr(obj.timelist, obj.d_interval, matrix_sr)
    #obj.displaySp(obj.timelist, obj.d_interval, matrix_sp)

