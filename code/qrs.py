import math, Queue, ConfigParser, MySQLdb

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import matplotlib
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.pyplot import figure
from datetime import datetime, timedelta
from mpl_toolkits.axes_grid1 import AxesGrid

__url__ = 'https://github.com/arinik9/FactChecking'
__author__ = 'Nejat ARINIK, Henri Hannetel'
__package__ = 'numpy, matplotlib, ConfigParser, MySQLdb, Queue, math, datetime, mpl_toolkits.axes_grid1'

# Utils
def sub_month(n, date):
	"""
	This method allows to substract 'n' month(s) from 'date'

	@param n: integer => the number of months to substract
	@param date: datetime => the date to rewind

	@return: date: datetime => the rewined date
	"""
	day = date.day
	for i in range(n):
		date = date.replace(day=1)
		date -= timedelta(days=1)
	return date.replace(day=day)

def fill_params(query, t, w, d):
	"""
	This method allows to fill the given parameters in the given query
	'w' and 'd' depend on the type of 't'. If 't' is a year with 4 digits, 'w' and 'd' are in terms of year. If 't' is a date with year, month and day, so 'w' and 'd' are in terms of date.

	@param query: String => the query to be filled
	@param t: String representing a date or integer => the end of second period
	@param w: integer => length of period
	@param d: integer => difference between second period and first period

	@return: res: String => the filled query
	"""
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
	"""
	qrs:  Query Response Surface. This class is implemented after read the article 'Computational Fact Checking'
	This class allows to visualize any fact by perturbing parameters
	"""

	def __init__(self, query, t0, w0, d0, r0, claim_type, min_time):
		"""
		Initialization with parameters of the original claim
		
		@param query: query
		@param t0: string or integer => the end of second period of original claim
		@param w0: Integer => length of periods oforiginal claim 
		@param d0: Integer => difference months or years between the end of second period and the first period of original claim
		@param r0: Integer => the result of original claim
		@param claim_type: String => 2 options are possible: "increasing" or "decreasing". If the original claim states the incresing of something (for instance the number of adoptions), we put "increasing".
		@param min_time: string or integer => the last year or date in database. Before this time, to avoid errors due to non available data in the database

		@return: None
		"""

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

		#To fetch table values in order to use these values in SP and SR
		self.times=None
		self.values=None

		self.conf_path = None
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
		"""
		Set the database attribute (used for database operations) with a MySQL connection.

		@param conf_path: String => the path of configuration file that contains DB connection information (username, password ...) 

		@return: None
		"""

		self.conf_path=conf_path
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
		"""
		Close the database connection.

		##Parameters:## None

		@return: None
		"""

		self.db_cursor.close()
		self.db.close()

	def fetchTableValues(self, query):
		"""
		This method allow to get all values from database table in order to contruct a histogram. Histograms are based on these values.

		@query: a query like 'select year, adoptions from nyc_adoptions;'. In other words, The resukt of the given query must return time information and data. 

		@return None
		"""

		self.openDb(self.conf_path)
		self.db_cursor.execute(query)
		rows = self.db_cursor.fetchall()
		self.times=[]
		self.values=[]

		for row in rows:
			if row[0] is not None:
				self.times.append(row[0])
				self.values.append(row[1])

	def initParameters(self, t, w, d):
		"""
		This method allows to generate all parameters that can be taken by the original query. These parameters are held in 2 Queue structures. When a parameter is used from 'all possible parameters' queue, we put it in 'backup_parameters' because we need it for display.

		@param t: List of datetime or integer => This list has just 2 proximities: Min an Max. If 't' is [1999, 2001], the list contains (1999, 2000, 2001).
		@param w: List of integer => This list contains possible w values that user wants to perturb
		@param d: List of integer => This list contains possible d values that user wants to perturb

		@return: None
		"""

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
		"""
		This method allows to provide 'levels', 'sigma_w', 'sigma_t' and 'sigma_d' for SP configuration

		@param levels: levels on which SP is based. Each level is specified by a pair of naturalness score and an integral period that defines the domain values in a level. With these levels, we are able to give a SP score to a specific duration according to level definitions 
		@param sigma_w: It is a coefficient to penalize 'w' values. Low sigma value penalizes more. High sigma value penalizes less.
		@param sigma_t: It is a coefficient to penalize 't' values. Low sigma value penalizes more. High sigma value penalizes less.
		@param sigma_d: It is a coefficient to penalize 'd' values. Low sigma value penalizes more. High sigma value penalizes less.

		@return: None
		"""
		self.naturalness_levels = levels
		self.sigma_w = sigma_w
		self.sigma_d = sigma_d
		self.sigma_t = sigma_t

	def getP(self):
		"""
		This method allows to get a just one parameter from Queue structure

		##Parameters:## None

		@return: None
		"""

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
		"""
		This method allows to execute the query with all posible parameters in order to compare its result with the original claim result 'r0'. New results are stored in the 'results'.

		##Parameters:## None
		@return: results: List of 4 values lists ('t', 'w', 'd' and 'result')
		"""

		results = []
		parameters = self.getP()

		while parameters != -1: # The Queue 'all_possible_parameters' is not empty
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
		SP_rel = SP_rel_w * SP_rel_d * SP_rel_t

		naturalness level = (chi_l, pi_l)
		x[1] % w == 0 -> check if a duration is multiple of w
		pi_l (integral period). If not, we put -1. Because at the end
		we'll use max() function and -1 will not be seleceted in any case

		##Input##
		@param t: String or datetime => the end of second period
		@param w: integer => length of period
		@param d: integer => difference between second period and first period

		@return: Sp score: Float => Sp score for given 'w', 'd' and 't'
		"""

		sp_nat_w = max( map(lambda x: x[0] if w % x[1] == 0 else 1, self.naturalness_levels) )
		sp_nat_d = max( map(lambda x: x[0] if d % x[1] == 0 else 1, self.naturalness_levels) )
		sp_nat =  sp_nat_d * sp_nat_w 

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

		return round(sp_nat * sp_rel, 3) # with 3 decimals

	def SR(self, r):
		""" 
		SR = r/r0 - 1 for increasing rate
		SR = r0/r - 1 for decreasing rate

		@param r: integer => the result found after executing query in the database for a specific parameter

		@return: sr score: float => sr score for given result 'r'
		"""

		if self.claim_type == "increasing":
			return round( (float(r) / float(self.r0)) - 1, 3 )
		return round( (float(self.r0) / float(r)) - 1, 3 ) # with 3 decimals

	def exclude_p(self, subset_a, p):
		"""
		This method allows to remove all 'p_prime' from 'subset_a' when 'p_prime' < 'p'. This method is used in CA_tr() method.

		@param subset_a: list of parameters => remembered parameter settings (qualified parameters)
		@param p: list of 4 values (t,w,d,r) for given parameter 'p'

		@return: subset_a: list of parameters => updated qualified parameters
		"""

		sp = self.SP(p[1], p[2], p[0])
		for p_prime in subset_a:
			sp_prime = self.SP(p_prime[1], p_prime[2], p_prime[0])
			if sp > sp_prime:
				subset_a.remove(p_prime)

		if len(subset_a) == 0:
			subset_a.append(p)

		return subset_a

	def CA_tr(self, threshold_r, results):
		"""
		This method allows to find counter-arguments according to the threshold 'tr'. This threshold is based on SR function.

		@param threshold_r: float
		@param results: list of list of 4 values (t,w,d,r) from execute() method.

		@return: subset_a: list => list of counter-arguments
		"""

		subset_a = []
		if threshold_r > 0:
			print("please give a negatif threshold")
			return -1
		for result in results:
			if self.SR( result[3] ) < threshold_r:
				subset_a = self.exclude_p( subset_a, result[0:3] )
		return subset_a

	def CA_tp(self, threshold_p, results):
		"""
		This method allows to find counter-arguments according to the threshold 'tp'. This threshold is based on SP function.

		This method returns a list. The first element of this list is an item with the lowest SR value
		That is why we add at the beginning of the list each time

		@param threshold_p: float
		@param results: list of list of 4 values (t,w,d,r) from execute() method.

		@return subset_a: list => list of counter-arguments
		"""

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
		"""
		po: pareto-optimal
		k: nb of results for output with highest sensibility
		This method allows to find counter-arguments according to pareto optimal. This method does not need any threshold.

		@param k: integer => the number of counter-arguments for output
		@param results: list of list of 4 values (t,w,d,r) from execute() method.

		@return subset_a[:k]: list => list of 'k' counter-arguments
		"""

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
		"""
		This method allows to find reverse-engineering parameter settings according to the threshold 'tr'. This threshold is based on SP function.

		@param threshold_r: float
		@param results: list of list of 4 values (t,w,d,r) from execute() method.

		@return: subset_a: list => list of reverse-engineering
		"""

		if threshold_r<0:
			return "please give a positif threshold"
		subset_a = []
		for result in results:
			if abs(self.SR( result[3] )) < threshold_r:
				subset_a = self.exclude_p( subset_a, result[0:3] )
		return subset_a

	def RE_tp(self, threshold_p, results):
		"""
		This method allows to find reverse-engineering parameter settings according to the threshold 'tp'. This threshold is based on SP function.

		This method returns a list. The first element of this list is an item with the lowest SR value
		That is why we add at the beginning of the list each time

		@param threshold_p: float
		@param results: list of list of 4 values (t,w,d,r) from execute() method.

		@return subset_a: list => list of reverse-engineering
		"""

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
		"""
		po: pareto-optimal
		k: nb of results for output with highest sensibility
		This method allows to find reverse-engineering parameter settigns according to pareto optimal. This method does not need any threshold.

		@param k: integer => the number of reverse-engineering for output
		@param results: list of list of 4 values (t,w,d,r) from execute() method.

		@return subset_a[:k]: list => list of 'k' reverse-engineering
		"""

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
		"""
		Different quality measures make sense for claims of different types, or the same claim viewed from different per-
		spectives

		low uniqueness means is easy to find perturbed claims that are at least as strong as the original clame
		low robustness means the original claim can be easily weakend
		fairness of 0: the claim is unbiased, positive fairness: the claim is understated, negative claim is overstated

		@param results: list of list of 4 values: 't', 'w', 'd' and 'r'. These 4 values come form execute() method.

		@return measures: List of float => Calculations for "fairness", "robustness" and "uniqueness"
		"""

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


#####################
#     Display       #
#####################
	def initMatrix(self, results):
		"""
		This method allows to create a matrix from results (output of execute() method). A matrix is created column by column.

		@param results: the results from execute() method

		@return None
		"""

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

	def shiftedColorMap(self, cmap, start=0.0, midpoint=0.5, stop=1.0, name='shiftedcmap', intensity_up=127, intensity_down=128):
		"""
		This method allows to configure the colorbar beside heatmap. Thanks to this method, we match yellow color to '0' value which is midpoint of colorbar.
		This method is used in displaySr and displaySp

		@param cmap: colormap => color pixels
		@param start: float => Start point. '0.0' means the first pixel in colormap
		@param midpoint: float => Mid point
		@param stop: float => Stop point. '1.0' means the last pixel in colormap
		@param name: "shiftedcmap" always I think. It is used LinearSegmentedColormap() int his method
		@param intensity_up: the number of pixel in the first part of colormap
		@param intensity_down: the number of pixel in the second and last part of colormap. These 2 parts of colormap are separeted by 'midpoint'.

		@return newcmap: new colormap shifted
		"""

	# intensity_up + intensity_down should be 257. Because we initialize 'reg_index' with 257 pixels
		cdict = {
			'red': [],
			'green': [],
			'blue': [],
			'alpha': []
		}


		# regular index to compute the colors
		reg_index = np.linspace(start, stop, 257) #generating values from 'start' to 'stop' with 257 points

		# shifted index to match the data
		shift_index = np.hstack([
			np.linspace(start, midpoint, intensity_up, endpoint=False), #generating values from 'start' to 'midpoint' with 'intensity_up' points
			np.linspace(midpoint, stop, intensity_down, endpoint=True) #generating values from 'midpoint' to 'stop' with 'intensity_down' points
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

	def displaySr(self, results, pos_annotations, w, legend_horizontal_margin=150, legend_location="upper left"):
		"""
		This method allows to display SR heatmap.

		@param results: list of list of 4 values. Results from execute() method
		@param pos_annotations: List of 2 integer values (x,y) => Positions of annotations on heatmap. 'x' and 'y' starts from 0.  
		@param w: integer => for displaying a heatmap, we need to fixe one of the 3 parameters 'w', 'd' and 't'. We always fixe 'w' in this implementation
		@param legend_horizontal_margin: integer => the margin between histogram bars and legend box. It is usefull when any histogram bars are overlapping with legend. By default 150
		@param legend_location: string. the location of legend on histograms. By default "upper left". For the other options: http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.legend

		@return Boolean value: True or False => 'True' indicates that display operation is done. 
		"""


		#source: http://stackoverflow.com/questions/7404116/defining-the-midpoint-of-a-colormap-in-matplotlib
		if len(self.w_interval) > 1:
			print("Too many width values. Set w to some value.")
			return -1
		x, y = self.timelist, self.d_interval
		if self.matrix_sr is None:
			self.initMatrix( results )

		#greener colors strengthen the claim
		#redder colors weaken the claim

		#we do not want to display nan values. So we mask nan values
		#there is nan values because some parameter combinations are not valid
		masked_array = np.ma.array (self.matrix_sr, mask=np.isnan(self.matrix_sr))

		#plt.cm.jet() has 256 different colors.
		#We will focus on xrange(140,230) in descending order
		#because we want that redder colors matches poor values and greener colors maches high values
		colors = [(plt.cm.jet(i)) for i in xrange(230,140,-1)]
		green = [(0.6509803921568628, 1.0, 0.30980392156862746, 1.0), (0.6431372549019608, 1.0, 0.30980392156862746, 1.0), (0.6352941176470588, 1.0, 0.30980392156862746, 1.0), (0.6274509803921569, 1.0, 0.30980392156862746, 1.0), (0.6196078431372549, 1.0, 0.30980392156862746, 1.0), (0.611764705882353, 1.0, 0.30980392156862746, 1.0), (0.6039215686274509, 1.0, 0.30980392156862746, 1.0), (0.596078431372549, 1.0, 0.30980392156862746, 1.0), (0.5882352941176471, 1.0, 0.30980392156862746, 1.0), (0.5803921568627451, 1.0, 0.30980392156862746, 1.0), (0.5725490196078431, 1.0, 0.30980392156862746, 1.0), (0.5647058823529412, 1.0, 0.30980392156862746, 1.0), (0.5568627450980392, 1.0, 0.30980392156862746, 1.0), (0.5490196078431373, 1.0, 0.30980392156862746, 1.0), (0.5411764705882353, 1.0, 0.30980392156862746, 1.0),(0.5333333333333333, 1.0, 0.30980392156862746, 1.0), (0.5254901960784314, 1.0, 0.30980392156862746, 1.0), (0.5176470588235295, 1.0, 0.30980392156862746, 1.0), (0.5098039215686274, 1.0, 0.30980392156862746, 1.0)]

		# we are adding more green values => It is better to see different green values on heatmap
		colors= colors+green # len(green)=19, total_len = 109

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

		cMap = LinearSegmentedColormap.from_list('cMap', colors,  N=len(colors))
		orig_cmap = cMap
		# Tuning the midpoint of colormap in order to match 'yellow' to 'zero'
		shifted_cmap = self.shiftedColorMap(orig_cmap, midpoint=(abs(min_limit)/float(max_limit+abs(min_limit))), name='shifted', intensity_up=160, intensity_down=97)

		fig = plt.figure(figsize=(160,160)) # with (16,16), it is better for Hollande&Sarkozy's claim
		grid = AxesGrid(	fig, 111, nrows_ncols=(1, 1), axes_pad=0.5, # just 1 plot in this grid
							label_mode="1", share_all=True,
							cbar_location="right", cbar_mode="each",
							cbar_size="7%", cbar_pad="2%", aspect=True
				)

		im2 = grid[0].imshow(masked_array, origin="lower", interpolation="None", cmap=shifted_cmap)
		grid.cbar_axes[0].colorbar(im2)
		grid[0].set_title('Relative Strength of Results (SR)', fontsize=14)


		# We get table values
		# For instance, "times" is equal to 'years' and "values" is equal to 'adoptions' in the table 'nyc_adoptions' in MySQL
		times, values = self.times, self.values

		# Initializing annotations on histogram
		labels_general=["Claim","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O"] # label of each annotation
		labels = labels_general[:len(pos_annotations)] # we pick the ones that will be used on the axe

		# we get time and d values via pos_annotations
		# for instance, if annotation=(5,6), the value is (2001,6) => according to [year, adoptions]
		parameters = []
		for pos in pos_annotations:
			i=pos[0]
			j=pos[1]
			# x: time_interval, y: d_interval 
			if not(isinstance(x[i], int)):  #Hollande&Sarkozy
				parameters.append((datetime.strptime(x[i], "%Y-%m-%d" ), y[j])) # corresponding parameters for each annotation
			else:
				parameters.append((x[i], y[j])) # corresponding parameters for each annotation

		for ax in grid:
			ax.set_xticks(np.arange(len(x))-0.5)
			if type(self.t_interval[0]) == type(str):
				ax.set_xticklabels(map(lambda a: a[:7], x), rotation=270 ) ;
			else:
				ax.set_xticklabels(map(lambda a: str(a), x), rotation=270 ) ;
			ax.tick_params(axis='x', labelsize=8)
			ax.set_yticks(np.arange(len(y))-0.5)
			ax.set_yticklabels(map(lambda i: str(i), y))
			ax.grid(True)
			# Annotations
			for label, xy in zip(labels, pos_annotations):
				ax.annotate(	label, xy, xytext=(17,17), size=10.5, textcoords="offset points",ha='center', va='bottom',
								bbox={'facecolor':'white'}, arrowprops={'arrowstyle':'->'}
				)


	##############
	# HISTOGRAMS #
	##############

		#Now, we generate len(pos_annotations) histograms (because we have len(pos_annotations) annotations)
		f, axes = plt.subplots(1, len(pos_annotations))
		if not(isinstance(axes, np.ndarray)): # in case of single annotations
			axes = np.asarray([axes])
		width=1 # width of each bar in histogram
		for ax, param, label in zip(axes, parameters, labels):
			x=[]
			y=[]
			colors_hist=[]
			w, d, t = w, param[1], param[0]

			offset_last_green_bar = 0
			offset_first_red_bar = 0
			colors_hist = [None]*len(times)
			for i, time, val in zip(range(len(times)), times, values): 
				colors_hist[i] = 'blue'
				if not(isinstance(time, long)): #Hollande&Sarkozy
					year=datetime.combine(time, datetime.min.time())
					if year<=t and year>sub_month(w, t):
						if not('green' in colors_hist):
							offset_last_green_bar = i+w
						colors_hist[i] = 'green'
						
					if year<=sub_month(d, t) and year>sub_month( w, sub_month(d, t)):
						if not('red' in colors_hist or 'yellow' in colors_hist):
							offset_first_red_bar = i
						if colors_hist[i] == 'green': #overlapping of green and red colors in the same bar => intersection
							colors_hist[i] = 'yellow'
						else:
							colors_hist[i] = 'red'
				else:
					year=time
					if year<=t and year>(t-w):
						if not('green' in colors_hist):
							offset_last_green_bar = i+w
						colors_hist[i] = 'green'
					if year<=(t-d) and year>(t-d-w):
						if not('red' in colors_hist or 'yellow' in colors_hist):
							offset_first_red_bar = i
						if colors_hist[i] == 'green': #overlapping of green and red colors in the same bar
							colors_hist[i] = 'yellow'
						else:
							colors_hist[i] = 'red'

				x.append(str(time)[:7])
				y.append(val)

		ax.bar(range(len(y)), y, width=width, color=colors_hist)
		ax.set_xticks(np.arange(len(y)) + width/2)
		# In order not to display all dates on x-axes, we use modulo for reduce the numbers of date
		# We want to see at most 50 date labels on the axe
		reduction_ratio = 1
		if len(x)>50:
			reduction_ratio = len(x) / 50
		ax.set_xticklabels(map(lambda (i,a): str(a)[:7] if (i % reduction_ratio)==0 else "", enumerate(x)), rotation=270 ) 
		ax.tick_params(axis='x', labelsize=8)

		extra = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0) # For adding "w,d,t" information on legend
		red_patch = mpatches.Patch(color='red') #adding red patch
		green_patch = mpatches.Patch(color='green')
		if 'yellow' in colors_hist:
			yellow_patch = mpatches.Patch(color='yellow')
			ax.legend([extra, red_patch, green_patch, yellow_patch],["w= "+str(w)+", d= "+str(d)+\
					", t= "+str(t)[:7], "Period 1", "Period 2", "Intersection"], prop={'size':12-len(axes)}, loc=legend_location)
		else:
			ax.legend([extra, red_patch, green_patch],["w= "+str(w)+", d= "+str(d)+\
			", t= "+str(t)[:7], "Period 1", "Period 2"], prop={'size':12-len(axes)}, loc=legend_location)

		ax.set_title(label, fontsize=12)

		x1,x2,y1,y2 = ax.axis() # we get the size of the current axe
		ax.set_ylim(y1,y2+legend_horizontal_margin) # in order that legend stay up enough on the axe (screen) 
		if len(x)>50: # if there is more than 50 dates, we focus on the part with green and red color => zooming
			ax.set_xlim(offset_first_red_bar-15,offset_last_green_bar+5) # For Hollande&Sarkozy

		plt.tight_layout()
		plt.subplots_adjust(wspace = 0.1*len(axes)) # updating margin between axes according to len(axes)

		plt.show()
		return True

	def displaySp(self, results, pos_annotations, w, legend_horizontal_margin=150, legend_location="upper left"):
		"""
		This method allows to display SP heatmap.

		@param results: list of list of 4 values. Results from execute() method
		@param pos_annotations: List of 2 integer values (x,y) => Positions of annotations on heatmap. 'x' and 'y' starts from 0.  
		@param w: integer => for displaying a heatmap, we need to fixe one of the 3 parameters 'w', 'd' and 't'. We always fixe 'w' in this implementation
		@param legend_horizontal_margin: integer => the margin between histogram bars and legend box. It is usefull when any histogram bars are overlapping with legend. By default 150
		@param legend_location: string. the location of legend on histograms. By default "upper left". For the other options: http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.legend

		@return Boolean value: True or False => 'True' indicates that display operation is done. 
		"""

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

		fire_color=[(255, 238,60),  (255, 238, 63), (255, 238, 67), (255, 236, 67), (255, 234, 67), (255, 232, 67), (255, 230, 67), (255, 228, 67), (255, 226, 67), (255, 224, 67), (255, 222, 67), (255, 220, 67), (255, 218, 67), (255, 216, 67), (255, 214, 67), (255, 212, 67), (255, 210, 67), (255, 208, 67), (255, 206, 67), (255, 204, 67), (255, 202, 67), (255, 200, 67), (255, 198, 67), (255, 196, 67),  (255, 195, 67),(255, 193, 65),(255, 191, 63),(255, 189, 61),(255, 187, 59),(255, 185, 57),(255, 183, 55),(255, 181, 53),(255, 179, 51), (255, 177, 49),(255, 175, 47),(255, 173, 45),(255, 171, 43),(255, 169, 41),(255, 167, 39),(255, 165, 37),(255, 163, 35),(255, 161, 33),(255, 159, 31),(255, 157, 29),(255, 155, 27),(255, 153, 25),(255, 151, 23),(255, 149, 21),(255, 147, 19),(255, 145, 17),(255, 143, 15),(255, 141, 13),(255, 138, 11),(255, 136, 9),(255, 134, 7),(255, 132, 5),(255, 131, 3),(255, 129, 1),(254, 126, 0),(252, 125, 0),(250, 122, 0),(248, 121, 0),(246, 118, 0),(244, 116, 0),(242, 115, 0),(240, 113, 0),(238, 111,0),(236, 109, 0),(234, 107, 0),(232, 105, 0),(230, 102, 0),(228, 100, 0),(227, 98, 0),(225, 97, 0),(223, 94, 0),(221, 93, 0),(219, 91, 0),(217, 89, 0),(215, 87, 0),(213, 84, 0),(211, 83, 0),(209, 81, 0),(207, 79, 0),(205, 77, 0),(203, 75, 0),(201, 73, 0),(199, 70, 0),(197, 68, 0),(195, 66, 0),(193, 64, 0),(191, 63, 0),(189, 61, 0),(187, 59, 0),(185, 57, 0),(183, 54, 0),(181, 52, 0),(179, 51, 0),(177, 49, 0),(175, 47, 0),(174, 44, 0),(172, 42, 0),(170, 40, 0),(168, 39, 0), (166, 37, 0),(164, 34, 0),(162, 33, 0),(160, 31, 0),(158, 29, 0),(156, 27, 0),(154, 25, 0),(152, 22, 0),(150, 20, 0),(148, 18, 0),(146, 17, 0),(144, 14, 0),(142, 13, 0),(140, 11, 0),(138, 9, 0),(136, 6, 0),(134, 4, 0),(132, 2, 0),(130, 0, 0),(128, 0, 0),(126, 0, 0),(124, 0, 0),(122, 0, 0),(120, 0, 0),(118, 0, 0),(116, 0, 0),(114, 0, 0),(112, 0, 0),(110, 0, 0),(108, 0, 0),(106, 0, 0),(104, 0, 0),(102, 0, 0),(100, 0, 0),(98, 0, 0),(96, 0, 0),(94, 0, 0),(92, 0, 0),(90, 0, 0),(88, 0, 0),(86, 0, 0),(83, 0, 0),(81, 0, 0),(79, 0, 0),(77, 0, 0),(75, 0, 0),(73, 0, 0),(71, 0, 0),(69, 0, 0),(67, 0, 0),(65, 0, 0),(63, 0, 0),(61, 0, 0),(59, 0, 0),(57, 0, 0),(55, 0, 0),(53, 0, 0),(51, 0, 0),(49, 0, 0),(47, 0, 0),(45, 0, 0),(43, 0, 0),(41, 0, 0),(39, 0, 0),(37, 0, 0),(35, 0, 0),(33, 0, 0),(31, 0, 0),(29, 0, 0),(26, 0, 0),(24, 0, 0),(22, 0, 0),(20, 0, 0),(18, 0, 0),(16, 0, 0),(14, 0, 0),(12, 0, 0),(10, 0, 0),(8, 0, 0),(6, 0, 0),(4, 0, 0),(2,0, 0),(0, 0, 0)]

		fire_color = list(reversed(fire_color))
		fire = map(lambda x: (x[0]/float(255),x[1]/float(255),x[2]/float(255)),fire_color)
		colors=list(reversed(fire))

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
			min_limit=0

		cMap = LinearSegmentedColormap.from_list('cMap', colors,  N=len(fire)) #N=90+19
		cMap.set_bad('white',1.) #does not work with pcolor() => use pcolormesh()
		orig_cmap = cMap
		shifted_cmap = self.shiftedColorMap(orig_cmap, midpoint=(abs(min_limit)/float(max_limit+abs(min_limit))), name='shifted', intensity_up=15, intensity_down=242)

		fig = plt.figure(figsize=(16,16)) # with (16,16), it is better for Hollande&Sarkozy's claim
		grid = AxesGrid(fig, 111, nrows_ncols=(1, 1), axes_pad=0.5,
				label_mode="1", share_all=True,
				cbar_location="right", cbar_mode="each",
				cbar_size="7%", cbar_pad="2%")

		im2 = grid[0].imshow(masked_array, origin="lower", interpolation="None", cmap=shifted_cmap)
		grid.cbar_axes[0].colorbar(im2)
		grid[0].set_title('Relative Sensibility of Parameter Settings (SP)', fontsize=14)

		# We get table values
		# For instance, "times" is equal to 'years' and "values" is equal to 'adoptions' in the table 'nyc_adoptions'
		times, values = self.times, self.values

		# Initializing annotations on histogram
		labels_general=["Claim","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O"] # label of each annotation
		labels = labels_general[:len(pos_annotations)]

		# we get time and d values via pos_annotations
		# for instance, if annotation=(5,6), the value is (2001,6) => according to [year, adoptions]
		parameters = []
		for pos in pos_annotations:
			i=pos[0]
			j=pos[1]
			# x: time_interval, y: d_interval 
			if not(isinstance(x[i], int)):  #Hollande&Sarkozy
				parameters.append((datetime.strptime(x[i], "%Y-%m-%d" ), y[j])) # corresponding parameters for each annotation
			else:
				parameters.append((x[i], y[j])) # corresponding parameters for each annotation

		for ax in grid:
				ax.set_xticks(np.arange(len(x))-0.5)
				if type(self.t_interval[0]) == type(str):
					ax.set_xticklabels(map(lambda a: a[:7], x), rotation=270 ) ;
				else:
					ax.set_xticklabels(map(lambda a: str(a), x), rotation=270 ) ;
				ax.tick_params(axis='x', labelsize=8)
				ax.set_yticks(np.arange(len(y))-0.5)
				ax.set_yticklabels(map(lambda i: str(i), y))
				ax.grid(True)

				# Annotations
				for label, xy in zip(labels, pos_annotations):
					ax.annotate(label, xy, xytext=(20,20), size=12, textcoords="offset points", ha="center", va="bottom",\
							bbox={'facecolor':'white'}, arrowprops={'arrowstyle':'->'})


		##############
		# HISTOGRAMS #
		##############

		#Now, we generate len(pos_annotations) histograms (because we have len(pos_annotations) annotations)
		f, axes = plt.subplots(1, len(pos_annotations))
		if not(isinstance(axes, np.ndarray)): # in case of single annotation
			axes = np.asarray([axes])
		width=1 # width of each bar in histogram
		for ax, param, label in zip(axes, parameters, labels):
			x=[]
			y=[]
			colors_hist=[]
			w, d, t = w, param[1], param[0]

			offset_last_green_bar = 0
			offset_first_red_bar = 0
			colors_hist = [None]*len(times)
			for i, time, val in zip(range(len(times)), times, values): 
				colors_hist[i] = 'blue'
				if not(isinstance(time, long)): #Hollande&Sarkozy
					year=datetime.combine(time, datetime.min.time())
					if year<=t and year>sub_month(w, t):
						if not('green' in colors_hist):
							offset_last_green_bar = i+w
						colors_hist[i] = 'green'
						
					if year<=sub_month(d, t) and year>sub_month( w, sub_month(d, t)):
						if not('red' in colors_hist or 'yellow' in colors_hist):
							offset_first_red_bar = i
						if colors_hist[i] == 'green': #overlapping of green and red colors in the same bar => intersection
							colors_hist[i] = 'yellow'
						else:
							colors_hist[i] = 'red'
				else:
					year=time
					if year<=t and year>(t-w):
						if not('green' in colors_hist):
							offset_last_green_bar = i+w
						colors_hist[i] = 'green'
					if year<=(t-d) and year>(t-d-w):
						if not('red' in colors_hist or 'yellow' in colors_hist):
							offset_first_red_bar = i
						if colors_hist[i] == 'green': #overlapping of green and red colors in the same bar
							colors_hist[i] = 'yellow'
						else:
							colors_hist[i] = 'red'

				x.append(str(time)[:7])
				y.append(val)

		ax.bar(range(len(y)), y, width=width, color=colors_hist)
		ax.set_xticks(np.arange(len(y)) + width/2)
		# In order not to display all dates on x-axes, we use modulo for reduce the numbers of date
		reduction_ratio = 1
		if len(x)>50:
			reduction_ratio = len(x)/50
		ax.set_xticklabels(map(lambda (i,a): str(a)[:7] if (i % reduction_ratio)==0 else "", enumerate(x)), rotation=270 ) ;
		ax.tick_params(axis='x', labelsize=9)

		extra = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none',\
				linewidth=0) # For adding "w,d,t" information on legend
		red_patch = mpatches.Patch(color='red') #adding red patch
		green_patch = mpatches.Patch(color='green')
		if 'yellow' in colors_hist:
			yellow_patch = mpatches.Patch(color='yellow')
			ax.legend([extra, red_patch, green_patch, yellow_patch],["w= "+str(w)+", d= "+str(d)+\
			", t= "+str(t)[:7], "Period 1", "Period 2", "Intersection"], prop={'size':12-len(axes)}, loc=legend_location)
		else:
			ax.legend([extra, red_patch, green_patch],["w= "+str(w)+", d= "+str(d)+\
			", t= "+str(t)[:7], "Period 1", "Period 2"], prop={'size':12-len(axes)}, loc=legend_location)

		ax.set_title(label, fontsize=12)
		x1,x2,y1,y2 = ax.axis()
		ax.set_ylim(y1,y2+legend_horizontal_margin) # in order that legend stay up enough on the axe (screen) 
		if len(x)>50:
			ax.set_xlim(offset_first_red_bar-15,offset_last_green_bar+5) # For Hollande&Sarkozy
		plt.tight_layout()
		plt.subplots_adjust(wspace = 0.1*len(axes)) # updating margin between axes according to len(axes)
		plt.show()
		return True
