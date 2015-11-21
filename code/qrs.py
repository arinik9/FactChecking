import MySQLdb
import math
import Queue
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.pyplot import figure

def sub_month(month, date):
    for i in range(month):
        date -= timedelta(days=1)
        date = date.replace(day=1)
    return date

def fill_params(query, t, w, d):
    res = """"""
    i = 0
    while i < len(query):
        if query[i] == '<':
            if query[i+1] == 't':
                if type(t) == type(str()):
                    res += '"' + t + '"'
                else:
                    res += str(t)
            elif query[i+1] == 'w':
                res += w
            elif query[i+1] == 'd':
                res += d
            i += 3
        else:
            res += query[i]
            i += 1
    return res
# QRS stands for Query Response Surface modelize a claim and is consituted by a parametrized database query
# a set of para
class qrs:
    """Query Response Surface"""
    def __init__(self, t0, w0, d0, r0, claim_type):
        self.db = None
        self.db_name = None
        self.db_cursor = None
        self.db_table_name = None
        self.db_name = None

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

    def setDbName(self,db_name):
        self.db_name = db_name

    """ t: end date of the second period
        w: lenght of periods
        t: distance between the end of each period"""
    def setParametersInterval(self, t, w, d):
        self.t_interval = t
        self.w_interval = w
        self.d_interval = d
        if type(t[0]) == type(str()):
            cur_period = datetime.strptime(self.t_interval[0], "%Y-%m-%d")
            last_period = datetime.strptime(self.t_interval[1], "%Y-%m-%d")
        else:
            cur_period = self.t_interval[0]
            last_period = self.t_interval[1]
            
        #sarkozy_beginning_time = datetime.strptime("2007-05-01", "%Y-%m-%d")

        while cur_period <= last_period:
            for w in self.w_interval:
                for d in self.d_interval:
                    # we have a constraint: t-w-d > 2007 may [sarkozy's beginning period]
                    # limit = sub_month( d, sub_month(w, cur_period) )
                    # if limit > sarkozy_beginning_time:
                    if type(t[0]) == type(str()):
                        self.all_possible_parameters.put( [str(cur_period)[:10], w, d] )
                        if str(cur_period)[:10] not in self.timelist:
                            self.timelist.append(str(cur_period)[:10])
                    else:
                        self.all_possible_parameters.put( [cur_period, w, d] )
                        if cur_period not in self.timelist:
                            self.timelist.append(cur_period)
            if type(t[0]) == type(str()):
                # Add one month
                cur_period += timedelta(days=32)
                cur_period = cur_period.replace(day=1)
            else:
                cur_period += 1

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

    def executeQuery(self, query):
        results = []
        values = self.getP()

        while values != -1:
            t = values[0]
            w = values[1]
            d = values[2]
            #print(fill_params(query, t, str(w), str(d)) )
            self.db_cursor.execute( fill_params(query, t, str(w), str(d)) )
            rows = self.db_cursor.fetchall()
            for row in rows:
                if row[0] is not None:
                    results.append((t, w, d, float(str(row[0]))))
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
        if type(self.t0) == type(str()):
            # t1 and self.t0 are type of datetime like (2013-07-16)
            t1=t.split("-")
            t2=self.t0.split("-")
            # substract 2 date (only year and month part)
            diff = diff + (int(t2[0])-int(t1[0]))
            diff = diff + (int(t2[1])-int(t1[1]))/float(12) #conversion from month to year
        else:
            diff = t - self.t0
        sp_rel_t = math.exp(-math.pow((diff)/float(self.sigma_t), 2))
        sp_rel = sp_rel_w * sp_rel_d * sp_rel_t

        return sp_nat * sp_rel 

    def computeSrScore(self, r):
        """ SR = r/r0 - 1 for increasing rate
            SR = r0/r - 1 for decreasing rate"""
        if self.claim_type == "increasing":
            return float(r)/float(self.r0) - 1
        return float(self.r0)/float(r) - 1


    def displaySr(self, x, y, matrix_sr):
        #interesting source: http://stackoverflow.com/questions/15908371/matplotlib-colorbars-and-its-text-labels
        #same: http://stackoverflow.com/questions/14336138/python-matplotlib-change-color-of-specified-value-in-contourf-plot-using-colorma
        #same: http://stackoverflow.com/questions/14391959/heatmap-in-matplotlib-with-pcolor
        
        #greener colors strengthen the claim
        #redder colors weaken the claim

        #we do not want to display nan values. So we mask nan values
        #there is nan values because some parameter combinations are not valid
        masked_array = np.ma.array (matrix_sr, mask=np.isnan(matrix_sr))
        #We could do our colormap with discrete (listed) colors but LinearSegmentedColormap is better 
        #cMap = ListedColormap(['#FE2E2E', '#FE642E', '#FE9A2E', '#FACC2E', '#FFFF00', '#F3F781', '#C8FE2E', '#00FF00', '#01DF01'])

        colors = [(plt.cm.jet(i)) for i in xrange(230,130,-1)]
        #plt.cm.jet() has 256 different colors. 
        #We will focus on xrange(130,230) in descending order
        #because we want that redder colors matches poor values
        #and greener colors maches high values

        cMap = LinearSegmentedColormap.from_list('cMap', colors,
                N=101) #N=230-130+1=101
        cMap.set_bad('white',1.) #does not work with pcolor() => use pcolormesh()
        fig, ax = plt.subplots()
        #fig, ax = plt.subplots(1,1, figsize=(6,6))
        #heatmap = ax.pcolor(masked_array, cmap=cMap)
        heatmap = ax.pcolormesh(masked_array, cmap=cMap)
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels(map(lambda a: a[:7], x), rotation=270 ) ;
        ax.tick_params(axis='x', labelsize=8)
        ax.set_yticks(range(len(y)))
        ax.set_yticklabels(map(lambda i: str(i), y))
        plt.autoscale()
        ax.grid(False)

        fig.suptitle('Strength Result')

        #we limit colormap values. we force max_limit to 0.4 in case of no existence of positive values
        #because positive values should match greener colors
        max_limit = max(map(lambda i: max(i), masked_array))
        min_limit = min(map(lambda i: min(i), masked_array))
        if max_limit <0:
            max_limit=0.40
        heatmap.set_clim(vmin=min_limit, vmax=max_limit)
        plt.colorbar(heatmap)
        plt.show()

    def displaySp(self, x, y, matrix_sp):
        # darker colors indicates higher sensibility

        #we do not want to display nan values. So we mask nan values
        #there is nan values because some parameter combinations are not valid
        masked_array = np.ma.array (matrix_sp, mask=np.isnan(matrix_sp))
        #We could do our colormap with discrete (listed) colors but LinearSegmentedColormap is better 
        #cMap = ListedColormap(['#FE2E2E', '#FE642E', '#FE9A2E', '#FACC2E', '#FFFF00', '#F3F781', '#C8FE2E', '#00FF00', '#01DF01'])

        colors = [(plt.cm.jet(i)) for i in xrange(172,0,-1)]
        #plt.cm.jet() has 256 different colors. 
        #We will focus on xrange(172,0) in descending order
        #because we want that darker colors matches high values
        #and greener/yellower colors maches poor values

        cMap = LinearSegmentedColormap.from_list('cMap', colors,
                N=173) #N=172-0+1=173
        cMap.set_bad('white',1.) #does not work with pcolor() => use pcolormesh()
        fig, ax = plt.subplots()
        #fig, ax = plt.subplots(1,1, figsize=(6,6))
        #heatmap = ax.pcolor(masked_array, cmap=cMap)
        heatmap = ax.pcolormesh(masked_array, cmap=cMap)
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels(map(lambda a: a[:7], x), rotation=270 ) ;
        ax.tick_params(axis='x', labelsize=8)
        ax.set_yticks(range(len(y)))
        ax.set_yticklabels(map(lambda i: str(i), y))
        plt.autoscale()
        ax.grid(False)

        fig.suptitle('Parameter of Sensibility')

        #we limit colormap values. we force min_limit to -1 in case of no existence of negative values
        #because positive values should match greener colors
        max_limit = max(map(lambda i: max(i), masked_array))
        min_limit = min(map(lambda i: min(i), masked_array))
        if max_limit <0:
            max_limit=0.40
        if min_limit >0:
            min_limit=-1
        heatmap.set_clim(vmin=min_limit, vmax=max_limit)
        plt.colorbar(heatmap)
        plt.show()
