#!/usr/bin/python
from qrs import qrs
import os
import numpy as np

if __name__ == '__main__':
    # Database parameters
    conf_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + "/../db-config.ini"

################################################################################
# Set parameters
    query = """SELECT hollande.chomage - sarkozy.chomage
               FROM (SELECT bf.nb_chomeur - af.nb_chomeur AS chomage
                     FROM (SELECT nb_chomeur FROM chomagePE
                           WHERE mois = <t> ) AS bf,
                          (SELECT nb_chomeur FROM chomagePE
                           WHERE mois = <t> - INTERVAL <w> + 1 MONTH ) AS af ) AS hollande,
                          (SELECT bf.nb_chomeur - af.nb_chomeur AS chomage
                           FROM (SELECT nb_chomeur FROM chomagePE
                                 WHERE mois = <t> - INTERVAL <d> MONTH) AS bf,
                                (SELECT nb_chomeur FROM chomagePE
                                 WHERE mois = <t> - INTERVAL <d> + <w> + 1 MONTH ) AS af ) AS sarkozy;"""
    t0, w0, d0, r0, limit_min = "2014-10-01", 30, 30, 310900, "2000-01-01"
    obj = qrs( query, t0, w0, d0, r0, "increasing", limit_min )

    times = ['2011-01-01', '2015-08-01']
    #widths = range(25,36)
    widths = [30]
    durations = range(20,41)
    obj.initParameters( times, widths, durations )

    levels = [(1,1), (2.71, 60)]
    sigma_w, sigma_t, sigma_d = 5, 1, 10
    obj.initSP( levels, sigma_w, sigma_t, sigma_d  )

################################################################################
# Compute Results
    obj.openDb( conf_path )
    results = obj.execute()
    obj.closeDb()

    obj.fetchTableValues("select mois, nb_chomeur from chomagePE;") # we need for SP and SR

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

    pos_annotations_sr = [(45,10), (45,12), (43,10)]
    pos_annotations_sp = [(45,10), (45,12), (43,10)]
    for w in widths:
        print(obj.displaySr(results, pos_annotations_sr, w))
        print(obj.displaySp(results, pos_annotations_sp, w))

