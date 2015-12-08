#!/usr/bin/python
from qrs import qrs
import os
import numpy as np

if __name__ == '__main__':
    # Database parameters
    conf_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + "/../db-config.ini"

################################################################################
# Set parameters
    query = """SELECT af.total / bf.total
               FROM (SELECT SUM(adoptions) AS total FROM nyc_adoptions
                     WHERE year BETWEEN <t> - <w> - <d> + 1 and <t> - <d>) AS bf,
                    (SELECT  SUM(adoptions) AS total FROM nyc_adoptions
                     WHERE year BETWEEN <t> - <w> + 1 AND <t>) AS af;"""
    t0, w0, d0, r0, limit_min = 2001, 6, 6, 1.665, 1988
    obj = qrs( query, t0, w0, d0, r0, "increasing", limit_min)

    times = [1995, 2012]
    #widths = [1,2,3,4,5,6,7,8,9]
    widths = [6]
    durations = range(1,19)
    obj.initParameters( times, widths, durations )

    levels = [(1,1), (2.718, 4), (7.389, 8)]
    sigma_w, sigma_t, sigma_d = 3, 1, 10
    obj.initSP( levels, sigma_w, sigma_t, sigma_d  )

################################################################################
# Compute Results
    obj.openDb( conf_path )
    results = obj.execute()
    obj.closeDb()
    print("\n")
    print("I changed the width values. Now: ", widths)

    # it is difficult to find an appropriate threshold for RE and CA
    print("\nCA_po:")
    print( obj.CA_po(5, results) ) # first 5 items

    print("\nRE_po:")
    print( obj.RE_po(5, results) )

    measures = obj.checkClaimQuality(results)
    print "\nfairness: ", measures["fairness"]
    print "robustness: ", measures["robustness"]
    print "uniqueness: ", measures["uniqueness"]

    print(obj.displaySr(results))
    #print(obj.displaySp(results))
