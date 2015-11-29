#!/usr/bin/python
from qrs import qrs
import ConfigParser, os
import numpy as np

if __name__ == '__main__':
################################################################################
# Set configuration
    conf = ConfigParser.ConfigParser()
    obj = qrs(2001, 6, 6, 1.665, "increasing", 1989, 2012)
    conf_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + "/../db-config.ini"

    conf.read(conf_path)
    obj.connectToDb(
        conf.get('DB', 'host'),
        conf.get('DB', 'user'),
        conf.get('DB', 'password'),
        conf.get('DB', 'name')
    )
    obj.setDbName("fact_checking")
    obj.setDbTableName("nyc_adoptions")

################################################################################
# Set parameters
    query = """SELECT af.total / bf.total
               FROM (SELECT SUM(adoptions) AS total FROM fact_checking.nyc_adoptions
                     WHERE year BETWEEN <t> - <w> - <d> + 1 and <t> - <d>) AS bf,
                    (SELECT  SUM(adoptions) AS total FROM fact_checking.nyc_adoptions
                     WHERE year BETWEEN <t> - <w> + 1 AND <t>) AS af;"""
    times = [1995, 2012]
    widths = [6]
    durations = range(1,19)
    naturalness_levels = [(1,1), (2.718, 4), (7.389, 8)]

    obj.setParametersInterval(times, widths, durations)
    obj.setNaturalnessLevels(naturalness_levels)
    obj.setSigmaValues(3, 1, 10)# sigma_w, sigma_t, sigma_d

################################################################################
# Compute Results
    results = obj.executeQuery(query)
    cpt = 0
    line = []
    for i in range(len(results)):
        if i%7 < 1:
            print(line)
            line = []
        else:
            line.append(results[i])
            line.append(round(obj.computeSrScore(results[i][3]),2))
    #print(line)

    matrix_sr=[np.nan]*len(durations)
    matrix_sp=[np.nan]*len(durations)
    #we  construct our matrix column by column

    print("\n\n")

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
    #print(matrix_sr)

    threshold_r = -0.2
    print("\nCA_tr with the threshold: "+str(threshold_r))
    print(obj.CA_tr(threshold_r, results)) #results obtained by executeQuery()

    threshold_p = 0.2
    print("\nCA_tp with the threshold: "+str(threshold_p))
    print(obj.CA_tp(threshold_p, results)) #results obtained by executeQuery()
    #if threshold_r == -0.7, the result would be [[2010, 6, 8]]
    #if threshold_r == -0.2, the result would be [[2001, 6, 4]]
    obj.closeDb()

    #obj.displaySr(obj.timelist, obj.d_interval, matrix_sr)
    #obj.displaySp(obj.timelist, obj.d_interval, matrix_sp)
