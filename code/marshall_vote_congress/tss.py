#!/usr/bin/python
from qrs import qrs
import os
import numpy as np

#TIME SERIES SIMILARITY: JIM MARSHALL'S VOTE CLAIM

if __name__ == '__main__':
    # Database parameters
    conf_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + "/../../db-config.ini"

################################################################################
# Set parameters

    # Times t1 and t2 will be in format of <YY-MM-DD>
    # u and v are 2 entities => e1 and e2 are alse entities which are sql table


# We have 2 types of query

#This query bases on entity1's 'P', '+', '-' votes and find common votes on entity2's votes
#Asymetric comparison
    """query = SELECT c.common/t.total FROM 
            (SELECT count(*) AS total FROM <u> 
                WHERE vote_created >= <a> AND vote_created < <b> AND option_key!='0') AS t,
            
            (SELECT count(*) AS common FROM
                (SELECT a.vote_created AS vote_created, a.vote_number AS vote_number, 
                            a.option_key AS entity1_vote_type, b.option_key AS entity2_vote_type
                    FROM (SELECT vote_number, vote_session, vote_created, option_key, vote_question FROM <u> 
                            WHERE  vote_created >= <a> AND vote_created < <b> AND option_key != '0') AS a
                    LEFT JOIN (SELECT  vote_number, vote_session, vote_created, option_key, vote_question FROM <v> 
                                WHERE  vote_created >= <a> AND vote_created < <b>) AS b
                    ON  a.vote_session = b.vote_session AND a.vote_number = b.vote_number AND a.vote_question=b.vote_question) AS joined_table
                WHERE (entity1_vote_type = 'P' OR  entity1_vote_type = '+' OR entity1_vote_type = '-') 
                        AND entity1_vote_type = entity2_vote_type)  AS c;"""


#This query bases on just common '-' and '+' votes
#Symetric comparison
    query =  """SELECT c.common/t.total FROM (SELECT count(*) AS total FROM <u>
                                            WHERE vote_created >= <a> AND vote_created < <b>) AS t,
                                        (SELECT count(*) AS common FROM 
                                            (SELECT * FROM <u> WHERE  vote_created >= <a> AND vote_created < <b>) AS u,
                                            (SELECT * FROM <v> WHERE  vote_created >= <a> AND vote_created < <b>) AS v
                                WHERE u.vote_session = v.vote_session AND u.vote_number = v.vote_number AND u.vote_question = v.vote_question 
                                            AND (u.option_key = '+' OR u.option_key = '-') AND u.option_key = v.option_key) AS c;"""

    a0, b0, u0, v0, r0, limit_min = "2010-01-01", "2010-10-15", "boehner", "marshall", 0.65, "2007-01-04" # 65% of same vote
    obj = qrs( query, a0, b0, u0, v0, r0, limit_min )

    period = ['2009-01-01', '2010-12-01']
    # Possibilities: bachmann, boehner, clyburn, kaptur, kucinich, oberstar, rangel, rayn, schock, speier 
    #u = ["boehner", "bachmann", "schock", "ryan"]
    u = ["boehner"]
    v = ["marshall"]
    obj.initParameters( u, v, period )

    # e, e, e^(1/2), e^(1/3), e^(1/4), e^(0)
    levels_a = [(2.71,'01-01'), (2.71, '01-15'), (1.4, '02-01'), (1.28, '02-15'),\
            (1, '03-01'), (1, '03-15'), (1, '04-01'), (1, '04-15'), (1, '05-01'),\
            (1, '05-15'), (1, '06-01'), (1, '06-15'), (1, '07-01'), (1, '07-15'),\
            (1, '08-01'), (1, '08-15'), (1, '09-01'), (1, '09-15'), (1, '10-01'),\
            (1, '10-15'), (1, '11-01'), (1, '11-15'), (1, '12-01'), (1, '12-15')]

    # '01-01' has more score because it represents the end of a month at the same time when it is end date
    # for example, begining: '2009-01-01' and end: '2010-01-01' 
    levels_b = [(2.71,'01-01'), (1, '01-15'), (1, '02-01'), (1, '02-15'),\
            (1, '03-01'), (1, '03-15'), (1, '04-01'), (1, '04-15'), (1, '05-01'),\
            (1, '05-15'), (1, '06-01'), (1, '06-15'), (1, '07-01'), (1, '07-15'),\
            (1, '08-01'), (1, '08-15'), (1, '09-01'), (1, '09-15'), (1, '10-01'),\
            (1, '10-15'), (1, '11-01'), (1.28, '11-15'), (1.4, '12-01'), (2.71, '12-15')]
    # e^(0), e^(1/3), e, e^(3/2), e^2, e^(5/2)
    #second index of each tuple is in order of month number
    # (1,0) means the difference of month number between a and b is between 1 and 12 months
    # ('2010-01-01', '2010-04-01') is an exemple
    # (1,12) means the difference of month number between a and b is between 12 and 24 months
    # ('2009-01-01', '2010-04-01') is an exemple
    levels_length = [(1, 0), (1.4, 12), (1.68, 24), (2, 36), (2.4, 48), (2.7, 60)]

    sigma_a, sigma_b = 1000, 1
    obj.initSP(levels_a, levels_b, levels_length, sigma_a, sigma_b)

################################################################################
# Compute Results
    obj.openDb( conf_path )

    
    results = obj.execute()
    obj.closeDb()
    #print results

    #print obj.timelist
    #obj.initMatrix(results)
    #print obj.matrix_sr
    #print obj.matrix_sp
    

    #obj.fetchTableValues("select mois, nb_chomeur from chomagePE;") # we need for SP and SR

    print("\n")

    # it is difficult to find an appropriate threshold for RE and CA
    print("\nCA_po:")
    print( obj.CA_po(5, results) ) # first 5 items

    print("\nRE_po:")
    print( obj.RE_po(5, results) )

    measures = obj.checkClaimQuality(results)
    print "\nfairness: ", measures["fairness"]
    print "robustness: ", measures["robustness"]
    print "uniqueness: ", measures["uniqueness"]

    pos_annotations_sr = [(24,3)]
    pos_annotations_sp = [(24,3)]
    print(obj.displaySr(results, pos_annotations_sr))
    print(obj.displaySp(results, pos_annotations_sp))

