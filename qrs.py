import MySQLdb
import math
import Queue

class qrs:
    """Query Response Surface"""
    def __init__(self, t0, w0, d0, r0, claim_type):
        self.t0 = t0
        self.w0 = w0
        self.d0 = d0
        self.r0 = r0
        self.db = None
        self.db_name = None
        self.db_cursor = None
        self.db_table_name = None
        self.q = None
        self.t_interval = None
        self.w_interval = None
        self.d_interval = None
        self.claim_type = claim_type
        self.all_possible_parameters = Queue.Queue()
        self.backup_parameters = Queue.Queue()
        self.sigma_w = None # pour SP_rel
        self.sigma_d = None # pour SP_rel
        self.sigma_t = None # pour SP_rel

    def connectToDb(self, host, username, passwd, dbname):
        self.db_name = dbname
        self.db = MySQLdb.connect(host=host,user=username,passwd=passwd,db=dbname)
        self.db_cursor = self.db.cursor()

    def closeDb(self):
        self.db_cursor.close()
        self.db.close()

    def setDbTableName(self,tablename):
        self.db_table_name = tablename

    def setParametersInterval(self, t, w, d):
        self.t_interval = t
        self.w_interval = w
        self.d_interval = d
        
        for t in self.t_interval:
            for w in self.w_interval:
                for d in self.d_interval:
                    self.all_possible_parameters.put((t,w,d))

    def setQuery(self, q):
        self.q = q

    def getP(self):
        while not self.all_possible_parameters.empty():
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
        values = 0 #juste pour demarer la boucle while
        while True:
            values = self.getP()
            if values == -1:
                break
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
        return results

    def computeSpScore(self, w):
        """ SP = SP_nat * SP_rel 
	    SP_nat = SP_nat_w * SP_nat_d
	    SP_rel = SP_rel_w * SP_rel_d * SP_rel_t """
        #sp_nat = #TODO

        sp_rel_w = math.exp(-((w-self.w0)/self.sigma_w))
        sp_rel_d = math.exp(-((d-self.d0)/self.sigma_d))
        sp_rel_t = math.exp(-((t-self.t0)/self.sigma_t))
        sp_rel = sp_rel_w * sp_rel_d * sp_rel_t
        #return (sp_nat, sp_rel) => TODO 

    def computeSrScore(self, r):
        """ SR = r/r0 - 1 for increasing rate
            SR = r0/r - 1 for decreasing rate"""
        if self.claim_type == "increasing":
            return r/float(self.r0) - 1
        return self.r0/float(r) - 1

