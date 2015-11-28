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
    def __init__(self, t0, w0, d0, r0, claim_type, min_time, max_time):
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
        self.min_time = min_time
        self.max_time = max_time
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
        d: distance between the end of each period"""
    def setParametersInterval(self, t, w, d):
        self.t_interval = t
        self.w_interval = w
        self.d_interval = d
        if type(t[0]) == type(str()):
            cur_period = datetime.strptime(self.t_interval[0], "%Y-%m-%d")
            last_period = datetime.strptime(self.t_interval[1], "%Y-%m-%d")
            min_t = sub_month( 1, datetime.strptime(self.min_time, "%Y-%m-%d") )
        else:
            cur_period = self.t_interval[0]
            last_period = self.t_interval[1]

        #sarkozy_beginning_time = datetime.strptime("2007-05-01", "%Y-%m-%d")

        while cur_period <= last_period:
            for w in self.w_interval:
                for d in self.d_interval:
                    # limit = sub_month( d, sub_month(w, cur_period) )
                    # if limit > sarkozy_beginning_time:
                    if type(t[0]) == type(str()):
                        if sub_month( w, sub_month(d, cur_period) ) >= min_t:
                            self.all_possible_parameters.put( [str(cur_period)[:10], w, d] )
                            if str(cur_period)[:10] not in self.timelist:
                                self.timelist.append(str(cur_period)[:10])
                    else:
                        # Constraint t-w-d >= min_time
                        if cur_period-w-d >= self.min_time - 1:
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
        x[1] % w == 0 -> check if a duration is multiple of w
        pi_l (integral period). If not, we put -1. Because at the end
        we'll use max() function and -1 will not be seleceted in any case
        """
        sp_nat_w = max( map(lambda x: x[0] if x[1] % w == 0 else -1, self.naturalness_levels) )
        sp_nat_d = max( map(lambda x: x[0] if x[1] % d == 0 else -1, self.naturalness_levels) )
        #sp_nat = sp_nat_w * sp_nat_d => un problem sur le calcul de sp_w
        sp_nat =  sp_nat_d * 1 # TODO find a solution for print sp_nat_w

        if type(self.t0) == type(str()):
            # t1 and self.t0 are type of datetime like (2013-07-16)
            t1 = t.split("-")
            t2 = self.t0.split("-")
            # substract 2 date (only year and month part)
            diff = (int(t2[0]) - int(t1[0]))*12 + (int(t2[1]) - int(t1[1]))
        else:
            diff = t - self.t0
        sp_rel_t = math.exp( -1 * (diff / float(self.sigma_t))**2 )
        sp_rel_w = math.exp( -1 * (float(w - self.w0) / float(self.sigma_w))**2 )
        sp_rel_d = math.exp( -1 * (float(d - self.d0) / float(self.sigma_d))**2 )
        sp_rel = sp_rel_w * sp_rel_d * sp_rel_t

        return sp_nat * sp_rel

    def computeSrScore(self, r):
        """ SR = r/r0 - 1 for increasing rate
            SR = r0/r - 1 for decreasing rate"""
        if self.claim_type == "increasing":
            return float(r) / float(self.r0) - 1
        return float(self.r0) / float(r) - 1

    def exclude_p(self, subset_a, p):
        sp = self.computeSpScore(p[1], p[2], p[0])
        for p_prime in subset_a:
            sp_prime = self.computeSpScore(p_prime[1], p_prime[2], p_prime[0])
            if sp > sp_prime:
                subset_a.remove(p_prime)

        if len(subset_a) == 0:
            subset_a.append(p)

        return subset_a

    def CA_tr(self, tr, query):
        results = []
        parameters = self.getP()
        while parameters != -1:
            t = parameters[0]
            w = parameters[1]
            d = parameters[2]
            #print(fill_params(query, t, str(w), str(d)) )
            self.db_cursor.execute( fill_params(query, t, str(w), str(d)) )
            rows = self.db_cursor.fetchall()
            for row in rows:
                if row[0] is not None:
                    if self.computeSrScore(row[0]) < tr:
                        results = self.exclude_p(results, parameters)
            parameters = self.getP()
        return results

    def CA_tp(self, tp):
    # TODO
        results = []
        parameters = self.getP()
        while parameters != -1:
            t = parameters[0]
            w = parameters[1]
            d = parameters[2]
            #print(fill_params(query, t, str(w), str(d)) )
            self.db_cursor.execute( fill_params(query, t, str(w), str(d)) )
            rows = self.db_cursor.fetchall()
            for row in rows:
                if row[0] is not None:
                   # if self.computeSpScore(row[0]) > tp:
                        results.append(parameters)
            parameters = self.getP()
        return results

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

        colors = [(plt.cm.jet(i)) for i in xrange(230,140,-1)]
	orange=[(1.0, 0.3176470588235294, 0.0, 1.0), (1.0, 0.3254901960784314, 0.0, 1.0), (1.0, 0.3333333333333333, 0.0, 1.0), (1.0, 0.3411764705882353, 0.0, 1.0), (1.0, 0.34901960784313724, 0.0, 1.0), (1.0, 0.3568627450980392, 0.0, 1.0), (1.0, 0.36470588235294116, 0.0, 1.0), (1.0, 0.37254901960784315, 0.0, 1.0), (1.0, 0.3803921568627451, 0.0, 1.0), (1.0, 0.38823529411764707, 0.0, 1.0), (1.0, 0.396078431372549, 0.0, 1.0), (1.0, 0.403921568627451, 0.0, 1.0), (1.0, 0.4117647058823529, 0.0, 1.0), (1.0, 0.4196078431372549, 0.0, 1.0), (1.0, 0.42745098039215684, 0.0, 1.0), (1.0, 0.43529411764705883, 0.0, 1.0), (1.0, 0.44313725490196076, 0.0, 1.0), (1.0, 0.45098039215686275, 0.0, 1.0), (1.0, 0.4588235294117647, 0.0, 1.0), (1.0, 0.4666666666666667, 0.0, 1.0), (1.0, 0.4745098039215686, 0.0, 1.0), (1.0, 0.4823529411764706, 0.0, 1.0), (1.0, 0.49019607843137253, 0.0, 1.0), (1.0, 0.4980392156862745, 0.0, 1.0), (1.0, 0.5058823529411764, 0.0, 1.0), (1.0, 0.5137254901960784, 0.0, 1.0), (1.0, 0.5215686274509804, 0.0, 1.0), (1.0, 0.5294117647058824, 0.0, 1.0), (1.0, 0.5372549019607843, 0.0, 1.0), (1.0, 0.5450980392156862, 0.0, 1.0), (1.0, 0.5529411764705883, 0.0, 1.0), (1.0, 0.5607843137254902, 0.0, 1.0), (1.0, 0.5686274509803921, 0.0, 1.0), (1.0, 0.5764705882352941, 0.0, 1.0), (1.0, 0.5843137254901961, 0.0, 1.0), (1.0, 0.592156862745098, 0.0, 1.0), (1.0, 0.6, 0.0, 1.0), (1.0, 0.6078431372549019, 0.0, 1.0), (1.0, 0.615686274509804, 0.0, 1.0), (1.0, 0.6235294117647059, 0.0, 1.0), (1.0, 0.6313725490196078, 0.0, 1.0), (1.0, 0.6392156862745098, 0.0, 1.0), (1.0, 0.6470588235294118, 0.0, 1.0), (1.0, 0.6549019607843137, 0.0, 1.0), (1.0, 0.6627450980392157, 0.0, 1.0), (1.0, 0.6705882352941176, 0.0, 1.0), (1.0, 0.6784313725490196, 0.0, 1.0), (1.0, 0.6862745098039216, 0.0, 1.0), (1.0, 0.6941176470588235, 0.0, 1.0), (1.0, 0.7019607843137254, 0.0, 1.0), (1.0, 0.7098039215686275, 0.0, 1.0), (1.0, 0.7176470588235294, 0.0, 1.0)]

	green = [(0.6509803921568628, 1.0, 0.30980392156862746, 1.0), (0.6431372549019608, 1.0, 0.30980392156862746, 1.0), (0.6352941176470588, 1.0, 0.30980392156862746, 1.0), (0.6274509803921569, 1.0, 0.30980392156862746, 1.0), (0.6196078431372549, 1.0, 0.30980392156862746, 1.0), (0.611764705882353, 1.0, 0.30980392156862746, 1.0), (0.6039215686274509, 1.0, 0.30980392156862746, 1.0), (0.596078431372549, 1.0, 0.30980392156862746, 1.0), (0.5882352941176471, 1.0, 0.30980392156862746, 1.0), (0.5803921568627451, 1.0, 0.30980392156862746, 1.0), (0.5725490196078431, 1.0, 0.30980392156862746, 1.0), (0.5647058823529412, 1.0, 0.30980392156862746, 1.0), (0.5568627450980392, 1.0, 0.30980392156862746, 1.0), (0.5490196078431373, 1.0, 0.30980392156862746, 1.0), (0.5411764705882353, 1.0, 0.30980392156862746, 1.0),(0.5333333333333333, 1.0, 0.30980392156862746, 1.0), (0.5254901960784314, 1.0, 0.30980392156862746, 1.0), (0.5176470588235295, 1.0, 0.30980392156862746, 1.0), (0.5098039215686274, 1.0, 0.30980392156862746, 1.0)]# , (0.5019607843137255, 1.0, 0.30980392156862746, 1.0), (0.49411764705882355, 1.0, 0.30980392156862746, 1.0), (0.48627450980392156, 1.0, 0.30980392156862746, 1.0), (0.47843137254901963, 1.0, 0.30980392156862746, 1.0), (0.47058823529411764, 1.0, 0.30980392156862746, 1.0), (0.4627450980392157, 1.0, 0.30980392156862746, 1.0), (0.4549019607843137, 1.0, 0.30980392156862746, 1.0), (0.4470588235294118, 1.0, 0.30980392156862746, 1.0), (0.4392156862745098, 1.0, 0.30980392156862746, 1.0), (0.43137254901960786, 1.0, 0.30980392156862746, 1.0), (0.4235294117647059, 1.0, 0.30980392156862746, 1.0), (0.41568627450980394, 1.0, 0.30980392156862746, 1.0), (0.40784313725490196, 1.0, 0.30980392156862746, 1.0), (0.4, 1.0, 0.30980392156862746, 1.0)

        colors= colors[:20]+orange+colors[49:]+green # len(green)=19, len(orange)=52
        #plt.cm.jet() has 256 different colors.
        #We will focus on xrange(130,230) in descending order
        #because we want that redder colors matches poor values
        #and greener colors maches high values


        #cMap.set_bad('white',1.) #does not work with pcolor() => use pcolormesh()
        cMap = LinearSegmentedColormap.from_list('cMap', colors,  N=184) #N=20+52+41+19
        cMap.set_bad('white',1.) #does not work with pcolor() => use pcolormesh()
        fig, ax = plt.subplots()
        #fig, ax = plt.subplots(1,1, figsize=(6,6))
        #heatmap = ax.pcolor(masked_array, cmap=cMap)
        heatmap = ax.pcolormesh(masked_array, cmap=cMap)
        ax.set_xticks(range(len(x)))
        if type(self.t_interval[0]) == type(str):
            ax.set_xticklabels(map(lambda a: a[:7], x), rotation=270 ) ;
        else:
            ax.set_xticklabels(map(lambda a: str(a), x), rotation=270 ) ;
        ax.tick_params(axis='x', labelsize=8)
        ax.set_yticks(range(len(y)))
        ax.set_yticklabels(map(lambda i: str(i), y))
        plt.autoscale()
        ax.grid(True)

        fig.suptitle('Strength Result')

        #we limit colormap values. we force max_limit to 0.4 in case of no existence of positive values
        #because positive values should match greener colors
        max_limit=0
        min_limit=0
        for i in xrange(len(masked_array)):
            for j in xrange(len(masked_array[i])):
                if masked_array[i][j] > max_limit:
                    max_limit=masked_array[i][j]
                if masked_array[i][j] < min_limit:
                    min_limit=masked_array[i][j]
	print max_limit
	print min_limit
	np.set_printoptions(threshold='nan')
	print masked_array
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

        #cMap.set_bad('white',1.) #does not work with pcolor() => use pcolormesh()
        fire_color=[(255, 238, 112),(255, 237, 110),(255, 235, 108),(255, 233, 106),(255, 231, 104),(255, 229, 102),(255, 227, 100),(255, 225, 98),(255, 223, 96),(255, 221, 94),(255, 219, 92),(255, 217, 90),(255, 215, 88),(255, 213, 86),(255, 211, 84),(255, 209, 81),(255, 207, 79),(255, 205, 77),(255, 203, 75),(255, 201, 73),(255, 199, 71),(255, 197, 69),(255, 195, 67),(255, 193, 65),(255, 191, 63),(255, 189, 61),(255, 187, 59),(255, 185, 57),(255, 183, 55),(255, 181, 53),(255, 179, 51), (255, 177, 49),(255, 175, 47),(255, 173, 45),(255, 171, 43),(255, 169, 41),(255, 167, 39),(255, 165, 37),(255, 163, 35),(255, 161, 33),(255, 159, 31),(255, 157, 29),(255, 155, 27),(255, 153, 25),(255, 151, 23),(255, 149, 21),(255, 147, 19),(255, 145, 17),(255, 143, 15),(255, 141, 13),(255, 138, 11),(255, 136, 9),(255, 134, 7),(255, 132, 5),(255, 131, 3),(255, 129, 1),(254, 126, 0),(252, 125, 0),(250, 122, 0),(248, 121, 0),(246, 118, 0),(244, 116, 0),(242, 115, 0),(240, 113, 0),(238, 111,0),(236, 109, 0),(234, 107, 0),(232, 105, 0),(230, 102, 0),(228, 100, 0),(227, 98, 0),(225, 97, 0),(223, 94, 0),(221, 93, 0),(219, 91, 0),(217, 89, 0),(215, 87, 0),(213, 84, 0),(211, 83, 0),(209, 81, 0),(207, 79, 0),(205, 77, 0),(203, 75, 0),(201, 73, 0),(199, 70, 0),(197, 68, 0),(195, 66, 0),(193, 64, 0),(191, 63, 0),(189, 61, 0),(187, 59, 0),(185, 57, 0),(183, 54, 0),(181, 52, 0),(179, 51, 0),(177, 49, 0),(175, 47, 0),(174, 44, 0),(172, 42, 0),(170, 40, 0),(168, 39, 0), (166, 37, 0),(164, 34, 0),(162, 33, 0),(160, 31, 0),(158, 29, 0),(156, 27, 0),(154, 25, 0),(152, 22, 0),(150, 20, 0),(148, 18, 0),(146, 17, 0),(144, 14, 0),(142, 13, 0),(140, 11, 0),(138, 9, 0),(136, 6, 0),(134, 4, 0),(132, 2, 0),(130, 0, 0),(128, 0, 0),(126, 0, 0),(124, 0, 0),(122, 0, 0),(120, 0, 0),(118, 0, 0),(116, 0, 0),(114, 0, 0),(112, 0, 0),(110, 0, 0),(108, 0, 0),(106, 0, 0),(104, 0, 0),(102, 0, 0),(100, 0, 0),(98, 0, 0),(96, 0, 0),(94, 0, 0),(92, 0, 0),(90, 0, 0),(88, 0, 0),(86, 0, 0),(83, 0, 0),(81, 0, 0),(79, 0, 0),(77, 0, 0),(75, 0, 0),(73, 0, 0),(71, 0, 0),(69, 0, 0),(67, 0, 0),(65, 0, 0),(63, 0, 0),(61, 0, 0),(59, 0, 0),(57, 0, 0),(55, 0, 0),(53, 0, 0),(51, 0, 0),(49, 0, 0),(47, 0, 0),(45, 0, 0),(43, 0, 0),(41, 0, 0),(39, 0, 0),(37, 0, 0),(35, 0, 0),(33, 0, 0),(31, 0, 0),(29, 0, 0),(26, 0, 0),(24, 0, 0),(22, 0, 0),(20, 0, 0),(18, 0, 0),(16, 0, 0),(14, 0, 0),(12, 0, 0),(10, 0, 0),(8, 0, 0),(6, 0, 0),(4, 0, 0),(2,0, 0),(0, 0, 0)]

        fire_color = list(reversed(fire_color))
        fire = map(lambda x: (x[0]/float(255),x[1]/float(255),x[2]/float(255)),fire_color)
        fire=list(reversed(fire))
        cMap = LinearSegmentedColormap.from_list('cMap', fire, N=len(fire))
        fig, ax = plt.subplots()
        #fig, ax = plt.subplots(1,1, figsize=(6,6))
        #heatmap = ax.pcolor(masked_array, cmap=cMap)
        #heatmap = ax.pcolormesh(masked_array, cmap=plt.get_cmap("afmhot"))
        heatmap = ax.pcolormesh(masked_array, cmap=cMap)
        ax.set_xticks(range(len(x)))
        if type(self.t_interval[0]) == type(str):
            ax.set_xticklabels(map(lambda a: a[:7], x), rotation=270 ) ;
        else:
            ax.set_xticklabels(map(lambda a: str(a), x), rotation=270 ) ;
        ax.tick_params(axis='x', labelsize=8)
        ax.set_yticks(np.arange(len(y)))
        ax.set_yticklabels(map(lambda i: str(i), y))
        #plt.autoscale()
        ax.grid(True)

        fig.suptitle('Parameter of Sensibility')

        #we limit colormap values. we force min_limit to -1 in case of no existence of negative values
        #because positive values should match greener colors
        max_limit=0
        min_limit=0
        for i in xrange(len(masked_array)):
            for j in xrange(len(masked_array[i])):
                if masked_array[i][j] > max_limit:
                    max_limit=masked_array[i][j]
                if masked_array[i][j] < min_limit:
                    min_limit=masked_array[i][j]
        if max_limit <0:
            max_limit=0.40
        if min_limit >0:
            min_limit=-1
        heatmap.set_clim(vmin=min_limit, vmax=max_limit)
        plt.colorbar(heatmap)
        plt.show()
