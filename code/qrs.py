import MySQLdb
import math
import Queue
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt

def sub_month(month, date):
    for i in range(month):
        date -= timedelta(days=1)
        date = date.replace(day=1)
    return date
# QRS stands for Query Response Surface modelize a claim and is consituted by a parametrized database query
# a set of para
class qrs:
    """Query Response Surface"""
    def __init__(self, t0, w0, d0, r0, claim_type):
        self.db = None
        self.db_name = None
        self.db_cursor = None
        self.db_table_name = None

        """No parameter interval specified"""
        self.t_interval = None
        self.w_interval = None
        self.d_interval = None

        """No relevance parameters specified"""
        self.sigma_w = None # for SP_rel
        self.sigma_d = None # for SP_rel
        self.sigma_t = None # for SP_rel

        """Initialization with parameters of the original claim"""
        self.t0 = t0
        self.w0 = w0
        self.d0 = d0
        self.r0 = r0

        """No query specified"""
        self.q = None

        self.claim_type = claim_type
        self.all_possible_parameters = Queue.Queue()
        self.backup_parameters = Queue.Queue()

        """No naturalness levels specified"""
        self.naturalness_levels = []
        self.timelist = []

    def connectToDb(self, host, username, passwd, dbname):
        self.db_name = dbname
        self.db = MySQLdb.connect(host=host,user=username,passwd=passwd,db=dbname)
        self.db_cursor = self.db.cursor()

    def closeDb(self):
        self.db_cursor.close()
        self.db.close()

    def setDbTableName(self,tablename):
        self.db_table_name = tablename

    """ t: end date of the second period
        w: lenght of periods
        t: distance between the end of each period"""
    def setParametersInterval(self, t, w, d):
        self.t_interval = t
        self.w_interval = w
        self.d_interval = d
        cur_period = datetime.strptime(self.t_interval[0], "%Y-%m-%d")
        last_period = datetime.strptime(self.t_interval[1], "%Y-%m-%d")
        sarkozy_beginning_time = datetime.strptime("2007-05-01", "%Y-%m-%d")

        while cur_period <= last_period:
            for w in self.w_interval:
                for d in self.d_interval:
                    # we have a constraint: t-w-d > 2007 may [sarkozy's beginning period]
                    limit = sub_month( d, sub_month(w, cur_period) )
                    if limit > sarkozy_beginning_time:
                        self.all_possible_parameters.put((str(cur_period),w,d))
                        if str(cur_period) not in self.timelist:
                            self.timelist.append(str(cur_period))
            cur_period += timedelta(days=32)
            cur_period = cur_period.replace(day=1)


    def setQuery(self, q):
        self.q = q

    def setNaturalnessLevels(self, levels):
        self.naturalness_levels = levels

    def setSigmaValues(self, sigma_w, sigma_t, sigma_d):
        self.sigma_w = sigma_w
        self.sigma_d = sigma_d
        self.sigma_t = sigma_t

    def getP(self):
        if not self.all_possible_parameters.empty():
            param = self.all_possible_parameters.get()
            self.backup_parameters.put(param)
            return param

        # pour que les parametres soient pretes a la prochaine requete
        # on recharge la queue self.all_possible_parameters
        while not self.backup_parameters.empty():
            self.all_possible_parameters.put(self.backup_parameters.get())
        return -1 # empty

    def executeQuery(self):
        results = []
        values = self.getP()
        while values != -1:
            t = values[0]
            w = values[1]
            d = values[2]
            """self.db_cursor.execute(self.q, (self.db_name+'.'+self.db_table_name, t, 
                self.db_name+'.'+self.db_table_name, t, str(w+1), 
                self.db_name+'.'+self.db_table_name, t, str(d), 
                self.db_name+'.'+self.db_table_name, t, str(d+w+1)))"""
            self.db_cursor.execute(self.q, (t, t, str(w+1),  t, str(d), t, str(d+w+1)))
            rows = self.db_cursor.fetchall()
            for row in rows:
                results.append((t, w, d, row[0]))
            values = self.getP()
        return results

    def computeSpScore(self, w, d, t):
        """ SP = SP_nat * SP_rel 
        SP_nat = SP_nat_w * SP_nat_d
        SP_rel = SP_rel_w * SP_rel_d * SP_rel_t """

        """ 
        naturalness level = (chi_l, pi_l)
        x[1] % w == 0 => for checking if a duration can divide 
        pi_l (integral period). If not, we put -1. Because at the end
        we'll use max() function and -1 will not be seleceted in any case
        """ 
        sp_nat_w = max(map(lambda x: x[0] if x[1] % w == 0 else -1, self.naturalness_levels))
        sp_nat_d = max(map(lambda x: x[0] if x[1] % d == 0 else -1, self.naturalness_levels))
        sp_nat = sp_nat_w * sp_nat_d

        sp_rel_w = math.exp(-math.pow(((int(w)-int(self.w0))/float(self.sigma_w)),2))
        sp_rel_d = math.exp(-math.pow(((int(d)-int(self.d0))/float(self.sigma_d)), 2))

        diff = 0
        if "-" in t and "-" in self.t0:
            # t1 and self.t0 are type of datetime like (2013-07-16)
            t1=t.split("-")
            t2=self.t0.split("-")
            # substract 2 date (only year and month part)
            diff = diff + (int(t2[0])-int(t1[0]))
            diff = diff + (int(t2[1])-int(t1[1]))/float(12) #conversion from month to year
        else:
            diff = int(t)-int(self.t0)
        sp_rel_t = math.exp(-math.pow((diff)/float(self.sigma_t), 2))
        sp_rel = sp_rel_w * sp_rel_d * sp_rel_t

        return sp_nat * sp_rel 

    def computeSrScore(self, r):
        """ SR = r/r0 - 1 for increasing rate
            SR = r0/r - 1 for decreasing rate"""
        if self.claim_type == "increasing":
            return r/float(self.r0) - 1
        return self.r0/float(r) - 1

    def displaySr(self, x, matrix_sr):
        #greener colors strengthen the claim
        #redder colors weaken the claim
        #print(matrix_sr)
        plt.imshow(matrix_sr, interpolation='none',
                aspect=matrix_sr.shape[1]/matrix_sr.shape[0])

        plt.xticks(range(len(x)), x)
        plt.jet()
        plt.colorbar()

        plt.show()

    def displaySp(self, x, matrix_sp):
        # darker colors indicates higher sensibility
        #print(matrix_sp)
        plt.imshow(matrix_sp, interpolation='none',
                aspect=matrix_sp.shape[1]/matrix_sp.shape[0])

        plt.xticks(range(len(x)), x)
        plt.jet()
        plt.colorbar()

        plt.show()
        #
