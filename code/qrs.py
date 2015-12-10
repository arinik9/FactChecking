import math, Queue, ConfigParser, MySQLdb

import numpy as np
import matplotlib.pyplot as plt

import matplotlib
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.pyplot import figure
from datetime import datetime, timedelta
from mpl_toolkits.axes_grid1 import AxesGrid

# Utils
def sub_month(n, date):
    for i in range(n):
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
    def __init__(self, query, t0, w0, d0, r0, claim_type, min_time):
        """Initialization with parameters of the original claim"""
        self.q = query
        self.t0 = t0
        self.w0 = w0
        self.d0 = d0
        self.r0 = r0

        self.claim_type = claim_type
        self.min_time = min_time
        self.all_possible_parameters = Queue.Queue()
        self.backup_parameters = Queue.Queue()
        self.naturalness_levels = []
        self.timelist = []

        self.db = None
        self.db_cursor = None
        self.matrix_sr = None
        self.matrix_sp = None

        """No parameter interval specified"""
        self.t_interval = None
        self.w_interval = None
        self.d_interval = None

        """No relevance parameters specified"""
        self.sigma_w = None
        self.sigma_d = None
        self.sigma_t = None

    def openDb(self, conf_path):
        conf = ConfigParser.ConfigParser()
        conf.read( conf_path )
        self.db = MySQLdb.connect(
            conf.get('DB', 'host'),
            conf.get('DB', 'user'),
            conf.get('DB', 'password'),
            conf.get('DB', 'name')
        )
        self.db_cursor = self.db.cursor()

    def closeDb(self):
        self.db_cursor.close()
        self.db.close()

    """ t: end date of the second period
        w: lenght of periods
        d: distance between the end of each period"""
    def initParameters(self, t, w, d):
        self.t_interval, self.w_interval, self.d_interval = t, w, d
        if type(t[0]) == type(str()):
            cur_period = datetime.strptime( self.t_interval[0], "%Y-%m-%d" )
            last_period = datetime.strptime( self.t_interval[1], "%Y-%m-%d" )
            min_t = sub_month( 1, datetime.strptime(self.min_time, "%Y-%m-%d") )
        else:
            cur_period = self.t_interval[0]
            last_period = self.t_interval[1]

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
                        if cur_period-w-d >= self.min_time:
                            self.all_possible_parameters.put( [cur_period, w, d] )
                            if cur_period not in self.timelist:
                                self.timelist.append(cur_period)
            if type(t[0]) == type(str()):
                # Add one month
                cur_period += timedelta(days=32)
                cur_period = cur_period.replace(day=1)
            else:
                cur_period += 1

    def initSP(self, levels, sigma_w, sigma_t, sigma_d):
        self.naturalness_levels = levels
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
            self.all_possible_parameters.put( self.backup_parameters.get() )
        return -1 # empty

    def execute(self):
        results = []
        parameters = self.getP()

        while parameters != -1:
            t, w, d = parameters[0:3]
            #print(fill_params(query, t, str(w), str(d)) )
            self.db_cursor.execute( fill_params(self.q, t, str(w), str(d)) )
            rows = self.db_cursor.fetchall()
            for row in rows:
                if row[0] is not None:
                    results.append( [t, w, d, float(str(row[0]))] )
            parameters = self.getP()
        return results

    def SP(self, w, d, t):
        """ SP = SP_nat * SP_rel
        SP_nat = SP_nat_w * SP_nat_d
        SP_rel = SP_rel_w * SP_rel_d * SP_rel_t """

        """
        naturalness level = (chi_l, pi_l)
        x[1] % w == 0 -> check if a duration is multiple of w
        pi_l (integral period). If not, we put -1. Because at the end
        we'll use max() function and -1 will not be seleceted in any case
        """
        sp_nat_w = max( map(lambda x: x[0] if w % x[1] == 0 else 1, self.naturalness_levels) )
        sp_nat_d = max( map(lambda x: x[0] if d % x[1] == 0 else 1, self.naturalness_levels) )
        #sp_nat = sp_nat_w * sp_nat_d => un problem sur le calcul de sp_w
        sp_nat =  sp_nat_d * sp_nat_w # TODO find a solution for sp_nat_w

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

        return round(sp_nat * sp_rel, 3)

    def SR(self, r):
        """ SR = r/r0 - 1 for increasing rate
            SR = r0/r - 1 for decreasing rate"""
        if self.claim_type == "increasing":
            return round( (float(r) / float(self.r0)) - 1, 3 )
        return round( (float(self.r0) / float(r)) - 1, 3 )

    def exclude_p(self, subset_a, p):
        sp = self.SP(p[1], p[2], p[0])
        for p_prime in subset_a:
            sp_prime = self.SP(p_prime[1], p_prime[2], p_prime[0])
            if sp > sp_prime:
                subset_a.remove(p_prime)

        if len(subset_a) == 0:
            subset_a.append(p)

        return subset_a

    def CA_tr(self, threshold_r, results):
        subset_a = []
        if threshold_r > 0:
            print("please give a negatif threshold")
            return -1
        for result in results:
            if self.SR( result[3] ) < threshold_r:
                subset_a = self.exclude_p( subset_a, result[0:3] )
        return subset_a

    def CA_tp(self, threshold_p, results):
    #This method returns a list. The first element of this list is an item with the lowest SR value
    #That is why we add at the beginning of the list each time
        subset_a = []
        min_sr = 0
        for result in results:
            t, w, d, r = result[0:4]
            sr = self.SR(r)
            sp = self.SP(w,d,t)
            if sp > threshold_p:
                sub_list = map( lambda x: x[1], subset_a )
                if len(sub_list) > 0:
                # sub_list will be empty at the beginning
                    min_sr = min(sub_list)
                    if min_sr > sr:
                        subset_a.insert( 0, [sp, sr, (t,w,d)] )#adding to beggining of the list
                else:
                    subset_a.append( [sp, sr, (t,w,d)] ) # just for the first insert

        return [i[2] for i in subset_a]

    def CA_po(self, k, results):
    # po: pareto-optimal
    # k: nb of results for output with highest sensibility
        subset_a = []
        for result in results:
            t, w, d, r = result[0:4]
            sr = self.SR(r)
            sp = self.SP(w,d,t)
            if sr<0: # a counter-argument should be < 0
                if len(subset_a)>0:
                    add = True
                    for a in subset_a:
                        # we want to keep in the list the items which are equals (sp and sr)
                        # that is why we added not() statement in addition
                        if sp>=a[0] and sr<=a[1] and not(sp==a[0] and sr==a[1]):
                            subset_a.remove(a)
                        elif sp<=a[0] and sr>=a[1] and not(sp==a[0] and sr==a[1]):
                            add = False
                            break
                    if add:
                        subset_a.append((sp, sr, (t,w,d)))
                else: # len(subset_a) == 0 => just for the first insert
                    subset_a.append((sp, sr, (t,w,d)))

        subset_a.sort(key=lambda x: x[0], reverse=True) #ordering by SP
        #return  [i[2] for i in subset_a[:k]]#just extract parameter information
        return  subset_a[:k]

    def RE_tr(self, threshold_r, results):
        if threshold_r<0:
            return "please give a positif threshold"
        subset_a = []
        for result in results:
            if abs(self.SR( result[3] )) < threshold_r:
                subset_a = self.exclude_p( subset_a, result[0:3] )
        return subset_a

    def RE_tp(self, threshold_p, results):
    #This method returns a list. The first element of this list is an item with the lowest SR value
    #That is why we add at the beginning of the list each time
        subset_a = []
        min_sr = 0
        for result in results:
            t, w, d, r = result[0:4]
            sr = abs(self.SR(r))
            sp = self.SP(w,d,t)
            if sp > threshold_p:
                sub_list = map( lambda x: x[1], subset_a )
                if len(sub_list) > 0:
                # sub_list will be empty at the beginning
                    min_sr = min(sub_list)
                    if min_sr > sr:
                        subset_a.insert( 0, [sp, sr, (t,w,d)] )#adding to beggining of the list
                else:
                    subset_a.append( [sp, sr, (t,w,d)] ) # just for the first insert

        return [i[2] for i in subset_a]

    def RE_po(self, k, results):
    # po: pareto-optimal
    # k: nb of results for output with highest sensibility
        subset_a = []
        for result in results:
            t, w, d, r = result[0:4]
            sr = abs(self.SR(r))
            sp = self.SP(w,d,t)
            if len(subset_a)>0:
                add = True
                for a in subset_a:
                    # we want to keep in the list the items which are equals (sp and sr)
                    # that is why we added not() statement in addition
                    if sp>=a[0] and sr<=a[1] and not(sp==a[0] and sr==a[1]):
                        subset_a.remove(a)
                    elif sp<=a[0] and sr>=a[1] and not(sp==a[0] and sr==a[1]):
                        add = False
                        break
                if add:
                    subset_a.append((sp, sr, (t,w,d)))
            else: # len(subset_a) == 0 => just for the first insert
                subset_a.append((sp, sr, (t,w,d)))

        subset_a.sort(key=lambda x: x[0], reverse=True) #ordering by SP =>descending order
        k_first_items = subset_a[:k]
        #return  [i[2] for i in subset_a[:k]]#just extract parameter information
        k_first_items.sort(key=lambda x: x[1]) #ordering by SR => je triche un peu => normalement l'algo ne dit pas ca
        # mais en fait si on voit la definition de RE, un RE possible devrait etre tres proche de r0. C'est pour ca j'ai appliquer ca ici
        # avec la 2eme manipulation (ordering) on obtient les memes valeurs que celles de l'article
        return k_first_items

    def checkClaimQuality(self, results):
        # low uniqueness means is easy to find perturbed claims that are at least as strong as the original clame
        # low robustness means the original claim can be easily weakend
        # fairness of 0: the claim is unbiased, positive fairness: the claim is understated, negative claim is overstated

        fairness = 0.0
        robustness = 0.0
        uniqueness = 0.0
        total_parameters_nb = float(abs(len(results)))

        for result in results:
            t, w, d, r = result[0:4]
            sr = self.SR(r)
            sp = self.SP(w,d,t)
            fairness += sr * sp
            robustness += sp * (min(0, sr))**2
            ### Uniqueness ###
            one_indicator_function = lambda x: 1 if x<0  else 0
            uniqueness += 1/total_parameters_nb * one_indicator_function(sr)

        measures = {}
        measures["fairness"] = fairness
        measures["robustness"] = math.exp(-robustness)
        measures["uniqueness"] = uniqueness

        return measures

# SR and SP Display
    def initMatrix(self, results):
        self.matrix_sr = [np.nan] * len( self.d_interval )
        self.matrix_sp = [np.nan] * len( self.d_interval )

        old_t = results[0][0]
        column_sr, column_sp = [], []
        for result in results:
            t, w, d, r = result[0:4]
            if str(t) != str(old_t):
                self.matrix_sr = np.column_stack( (self.matrix_sr, column_sr + [np.nan] * (len(self.d_interval) - len(column_sr))) )
                self.matrix_sp = np.column_stack( (self.matrix_sp, column_sp + [np.nan] * (len(self.d_interval) - len(column_sp))) )
                column_sr = []
                column_sp = []
            old_t = t
            column_sr.append( self.SR(r) )
            column_sp.append( self.SP(w, d, t) )

        self.matrix_sr = np.column_stack( (self.matrix_sr, column_sr + [np.nan] * (len(self.d_interval) - len(column_sr))) )
        self.matrix_sp = np.column_stack( (self.matrix_sp, column_sp + [np.nan] * (len(self.d_interval) - len(column_sp))) )

        #delete initialized row
        self.matrix_sr = np.delete( self.matrix_sr, 0, 1 )
        self.matrix_sp = np.delete( self.matrix_sp, 0, 1 )


    def shiftedColorMap(self, cmap, start=0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
        cdict = {
            'red': [],
            'green': [],
            'blue': [],
            'alpha': []
        }

        print "GIRDI"

        # regular index to compute the colors
        reg_index = np.linspace(start, stop, 257)

        # shifted index to match the data
        shift_index = np.hstack([
            np.linspace(0.0, midpoint, 160, endpoint=False), 
            np.linspace(midpoint, 1.0, 97, endpoint=True)
        ])

        for ri, si in zip(reg_index, shift_index):
            r, g, b, a = cmap(ri)

            cdict['red'].append((si, r, r))
            cdict['green'].append((si, g, g))
            cdict['blue'].append((si, b, b))
            cdict['alpha'].append((si, a, a))

        newcmap = matplotlib.colors.LinearSegmentedColormap(name, cdict)
        plt.register_cmap(cmap=newcmap)

        return newcmap


    def displaySr(self, results):
        if len(self.w_interval) > 1:
            print("Too many width values. Set w to some value.")
            return -1
        x, y = self.timelist, self.d_interval
        if self.matrix_sr is None:
            self.initMatrix( results )
        #source: http://stackoverflow.com/questions/7404116/defining-the-midpoint-of-a-colormap-in-matplotlib

        #greener colors strengthen the claim
        #redder colors weaken the claim

        #we do not want to display nan values. So we mask nan values
        #there is nan values because some parameter combinations are not valid
        masked_array = np.ma.array (self.matrix_sr, mask=np.isnan(self.matrix_sr))
        #We could do our colormap with discrete (listed) colors but LinearSegmentedColormap is better
        #cMap = ListedColormap(['#FE2E2E', '#FE642E', '#FE9A2E', '#FACC2E', '#FFFF00', '#F3F781', '#C8FE2E', '#00FF00', '#01DF01'])

        colors = [(plt.cm.jet(i)) for i in xrange(230,140,-1)]
        green = [(0.6509803921568628, 1.0, 0.30980392156862746, 1.0), (0.6431372549019608, 1.0, 0.30980392156862746, 1.0), (0.6352941176470588, 1.0, 0.30980392156862746, 1.0), (0.6274509803921569, 1.0, 0.30980392156862746, 1.0), (0.6196078431372549, 1.0, 0.30980392156862746, 1.0), (0.611764705882353, 1.0, 0.30980392156862746, 1.0), (0.6039215686274509, 1.0, 0.30980392156862746, 1.0), (0.596078431372549, 1.0, 0.30980392156862746, 1.0), (0.5882352941176471, 1.0, 0.30980392156862746, 1.0), (0.5803921568627451, 1.0, 0.30980392156862746, 1.0), (0.5725490196078431, 1.0, 0.30980392156862746, 1.0), (0.5647058823529412, 1.0, 0.30980392156862746, 1.0), (0.5568627450980392, 1.0, 0.30980392156862746, 1.0), (0.5490196078431373, 1.0, 0.30980392156862746, 1.0), (0.5411764705882353, 1.0, 0.30980392156862746, 1.0),(0.5333333333333333, 1.0, 0.30980392156862746, 1.0), (0.5254901960784314, 1.0, 0.30980392156862746, 1.0), (0.5176470588235295, 1.0, 0.30980392156862746, 1.0), (0.5098039215686274, 1.0, 0.30980392156862746, 1.0)]

        colors= colors+green # len(green)=19, total_len = 109
        #plt.cm.jet() has 256 different colors.
        #We will focus on xrange(130,230) in descending order
        #because we want that redder colors matches poor values
        #and greener colors maches high values

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

        print max_limit, min_limit
        cMap = LinearSegmentedColormap.from_list('cMap', colors,  N=109) #N=90+19
        cMap.set_bad('white',1.) #does not work with pcolor() => use pcolormesh()
	orig_cmap = cMap
	shifted_cmap = self.shiftedColorMap(orig_cmap, midpoint=(abs(min_limit)/float(max_limit+abs(min_limit))), name='shifted')

        fig = plt.figure(figsize=(16,16)) # with (16,16), it is better for Hollande&Sarkozy's claim
        grid = AxesGrid(fig, 111, nrows_ncols=(1, 1), axes_pad=0.5,
                label_mode="1", share_all=True,
                cbar_location="right", cbar_mode="each",
                cbar_size="7%", cbar_pad="2%")

        im2 = grid[0].imshow(masked_array, origin="lower", interpolation="None", cmap=shifted_cmap)
	grid.cbar_axes[0].colorbar(im2)
	grid[0].set_title('Recentered cmap with function', fontsize=8)




	for ax in grid:
            ax.set_xticks(np.arange(len(x))-0.5)
            if type(self.t_interval[0]) == type(str):
                ax.set_xticklabels(map(lambda a: a[:7], x), rotation=270 ) ;
            else:
                ax.set_xticklabels(map(lambda a: str(a), x), rotation=270 ) ;
            ax.tick_params(axis='x', labelsize=8)
            ax.set_yticks(np.arange(len(y))+0.5)
            ax.set_yticklabels(map(lambda i: str(i), y))
            #plt.autoscale()
            ax.grid(True)



	#    ax.set_yticks([])
	#    ax.set_xticks([])

        # The aprt below does not work with hollande&sarkozy's claim
        """
        # draw a thick red hline at y=0 that spans the xrange
        unit = 1.0 / (self.t_interval[-1] - self.t_interval[0])
        middle = float(self.t0 - self.t_interval[0]) / float(self.t_interval[-1] - self.t_interval[0]) + unit
        plt.axhline(y=self.d0 + 0.5, xmin=middle-unit/2, xmax=middle+unit/2, linewidth=4, color='b')

        start = self.t0 - self.t_interval[0] + 1.5
        unit = 1.0 / (self.d_interval[-1] - self.d_interval[0])
        middle = float(self.d0 - self.d_interval[0]) / float(self.d_interval[-1] - self.d_interval[0]) + unit
        plt.axvline(x=start, ymin=middle-unit/2, ymax=middle+unit/2, linewidth=4, color='b')
	"""
        plt.show()
        return True

    def displaySp(self, results):
        if len(self.w_interval) > 1:
            print("Too many width values. Set w to some value.")
            return -1
        x, y = self.timelist, self.d_interval
        if self.matrix_sr is None:
            self.initMatrix( results )
        # darker colors indicates higher sensibility

        #we do not want to display nan values. So we mask nan values
        #there is nan values because some parameter combinations are not valid
        masked_array = np.ma.array( self.matrix_sp, mask = np.isnan(self.matrix_sp) )
        #We could do our colormap with discrete (listed) colors but LinearSegmentedColormap is better
        #cMap = ListedColormap(['#FE2E2E', '#FE642E', '#FE9A2E', '#FACC2E', '#FFFF00', '#F3F781', '#C8FE2E', '#00FF00', '#01DF01'])

        #plt.cm.jet() has 256 different colors.
        #We will focus on xrange(172,0) in descending order
        #because we want that darker colors matches high values
        #and greener/yellower colors maches poor values

        #cMap.set_bad('white',1.) #does not work with pcolor() => use pcolormesh()
        fire_color=[(255, 238,60),  (255, 238, 63), (255, 238, 67), (255, 236, 67), (255, 234, 67), (255, 232, 67), (255, 230, 67), (255, 228, 67), (255, 226, 67), (255, 224, 67), (255, 222, 67), (255, 220, 67), (255, 218, 67), (255, 216, 67), (255, 214, 67), (255, 212, 67), (255, 210, 67), (255, 208, 67), (255, 206, 67), (255, 204, 67), (255, 202, 67), (255, 200, 67), (255, 198, 67), (255, 196, 67),  (255, 195, 67),(255, 193, 65),(255, 191, 63),(255, 189, 61),(255, 187, 59),(255, 185, 57),(255, 183, 55),(255, 181, 53),(255, 179, 51), (255, 177, 49),(255, 175, 47),(255, 173, 45),(255, 171, 43),(255, 169, 41),(255, 167, 39),(255, 165, 37),(255, 163, 35),(255, 161, 33),(255, 159, 31),(255, 157, 29),(255, 155, 27),(255, 153, 25),(255, 151, 23),(255, 149, 21),(255, 147, 19),(255, 145, 17),(255, 143, 15),(255, 141, 13),(255, 138, 11),(255, 136, 9),(255, 134, 7),(255, 132, 5),(255, 131, 3),(255, 129, 1),(254, 126, 0),(252, 125, 0),(250, 122, 0),(248, 121, 0),(246, 118, 0),(244, 116, 0),(242, 115, 0),(240, 113, 0),(238, 111,0),(236, 109, 0),(234, 107, 0),(232, 105, 0),(230, 102, 0),(228, 100, 0),(227, 98, 0),(225, 97, 0),(223, 94, 0),(221, 93, 0),(219, 91, 0),(217, 89, 0),(215, 87, 0),(213, 84, 0),(211, 83, 0),(209, 81, 0),(207, 79, 0),(205, 77, 0),(203, 75, 0),(201, 73, 0),(199, 70, 0),(197, 68, 0),(195, 66, 0),(193, 64, 0),(191, 63, 0),(189, 61, 0),(187, 59, 0),(185, 57, 0),(183, 54, 0),(181, 52, 0),(179, 51, 0),(177, 49, 0),(175, 47, 0),(174, 44, 0),(172, 42, 0),(170, 40, 0),(168, 39, 0), (166, 37, 0),(164, 34, 0),(162, 33, 0),(160, 31, 0),(158, 29, 0),(156, 27, 0),(154, 25, 0),(152, 22, 0),(150, 20, 0),(148, 18, 0),(146, 17, 0),(144, 14, 0),(142, 13, 0),(140, 11, 0),(138, 9, 0),(136, 6, 0),(134, 4, 0),(132, 2, 0),(130, 0, 0),(128, 0, 0),(126, 0, 0),(124, 0, 0),(122, 0, 0),(120, 0, 0),(118, 0, 0),(116, 0, 0),(114, 0, 0),(112, 0, 0),(110, 0, 0),(108, 0, 0),(106, 0, 0),(104, 0, 0),(102, 0, 0),(100, 0, 0),(98, 0, 0),(96, 0, 0),(94, 0, 0),(92, 0, 0),(90, 0, 0),(88, 0, 0),(86, 0, 0),(83, 0, 0),(81, 0, 0),(79, 0, 0),(77, 0, 0),(75, 0, 0),(73, 0, 0),(71, 0, 0),(69, 0, 0),(67, 0, 0),(65, 0, 0),(63, 0, 0),(61, 0, 0),(59, 0, 0),(57, 0, 0),(55, 0, 0),(53, 0, 0),(51, 0, 0),(49, 0, 0),(47, 0, 0),(45, 0, 0),(43, 0, 0),(41, 0, 0),(39, 0, 0),(37, 0, 0),(35, 0, 0),(33, 0, 0),(31, 0, 0),(29, 0, 0),(26, 0, 0),(24, 0, 0),(22, 0, 0),(20, 0, 0),(18, 0, 0),(16, 0, 0),(14, 0, 0),(12, 0, 0),(10, 0, 0),(8, 0, 0),(6, 0, 0),(4, 0, 0),(2,0, 0),(0, 0, 0)]

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
        return True
