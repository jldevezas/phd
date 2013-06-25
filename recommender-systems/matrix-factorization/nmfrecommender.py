#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nmfrecommender.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-14

import csv
import pymf
import numpy as np
import h5py
from collections import OrderedDict

class NmfRecommender:
	def __init__(self, h5filename):
		self.model = None
		self.h5filename = h5filename

	def train(self, path, rank=10, sampleSize=None, delimiter=' '):
		data = {}
		counter = 0
		items = set([])
		with open(path, 'rb') as f:
			reader = csv.reader(f, delimiter=delimiter)
			for user, item, rating in reader:
				if not user in data: data[user] = {}
				data[user][item] = int(rating)
				items.add(item)
				
				if sampleSize is not None:
					counter += 1
					if counter >= sampleSize: break

		users = list(set(data.keys()))
		items = list(items)
		model = h5py.File(self.h5filename)
		model['ratings'] = np.random.random((len(users), len(items)))
		for i in xrange(len(users)):
			for j in xrange(len(items)):
				if items[j] in data[users[i]]:
					model['ratings'][i][j] = data[users[i]][items[j]]
				else:
					model['ratings'][i][j] = 0

		model['W'] = np.random.random((len(users), rank))
		model['H'] = np.random.random((rank, len(items)))
		mfact = pymf.NMF(np.array(matrix), num_bases=rank)
		#mfact.initialization()
		mfact.factorize()
