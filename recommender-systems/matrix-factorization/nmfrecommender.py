#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nmfrecommender.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-14

import csv
import pymf
import numpy as np
from collections import OrderedDict

class NMFRecommender:
	def __init__(self):
		self.model = None

	def train(self, path, sampleSize=None):
		data = {}
		counter = 0
		items = set([])
		with open(path, 'rb') as f:
			reader = csv.reader(f, delimiter=' ')
			for user, item, rating in reader:
				if not user in data: data[user] = {}
				data[user][item] = int(rating)
				items.add(item)
				
				if not sampleSize is None:
					counter += 1
					if counter >= sampleSize: break

		users = list(set(data.keys()))
		items = list(items)
		matrix = []
		for i in xrange(len(users)):
			matrix.append(np.zeros(len(items)))
			for j in xrange(len(items)):
				if items[j] in data[users[i]]:
					matrix[i][j] = data[users[i]][items[j]]
				else:
					matrix[i][j] = 0
		mfact = pymf.NMF(np.array(matrix), num_bases=2)
		#mfact.initialization()
		mfact.factorize()
		print(mfact.U)

	def storeModel(self, path):
		pass

	def loadModel(self, path):
		pass
