#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nmfrecommender.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-14

import os
import csv
import pymf
import numpy as np
import h5py
import logging
from collections import OrderedDict

class NmfRecommender:
	def __init__(self, h5filename):
		self.model = None
		self.h5filename = h5filename
		logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
				datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)

	def train(self, path, rank=10, sample_size=None, delimiter=' '):
		logging.info("Loading data from %s" % path)
		if sample_size is not None:
			logging.info("Using sample size %d" % sample_size)

		data = {}
		counter = 0
		items = set([])
		with open(path, 'rb') as f:
			reader = csv.reader(f, delimiter=delimiter)
			for user, item, rating in reader:
				if not user in data: data[user] = {}
				data[user][item] = int(rating)
				items.add(item)
				
				if sample_size is not None:
					counter += 1
					if counter >= sample_size: break

		users = list(set(data.keys()))
		items = list(items)

		logging.info("Preparing %dx%d ratings matrix in HDF5 file" % (len(users), len(items)))
		if os.path.exists(self.h5filename):
			ans = None
			while ans != 'y' and ans != 'n':
				ans = raw_input("===> HDF5 model already exists at %s. Overwrite? [yn] " % self.h5filename)
			if ans != 'y': return
			os.remove(self.h5filename)

		with h5py.File(self.h5filename) as model:
			model['ratings'] = np.zeros((len(users), len(items)))
			users_index = model.create_group('users')
			items_index = model.create_group('items')

			logging.info("Loading data into ratings matrix")
			for i in xrange(len(users)):
				if not users[i] in users_index:
					users_index[users[i]] = i

				for j in xrange(len(items)):
					if not items[j] in items_index:
						items_index[items[j]] = j

					if items[j] in data[users[i]]:
						row = model['ratings'][i]
						row[j] = data[users[i]][items[j]]
						model['ratings'][i] = row
					else:
						model['ratings'][i][j] = 0

			logging.info("Running non-negative matrix factorization in disk")
			mfact = pymf.NMF(model['ratings'], num_bases=rank)
			mfact.factorize()
			logging.info("Storing %dx%d W matrix and %dx%d H matrix in HDF5 file"
					% (len(users), rank, rank, len(items)))
			model['W'] = mfact.W
			model['H'] = mfact.H
			logging.info("Training completed")
	
	def predict(self, user_id, item_id):
		with h5py.File(self.h5filename, 'r') as model:
			if not user_id in model['users']:
				logging.error("User %s not in model." % user_id)
				return

			if not item_id in model['items']:
				logging.error("Item %s not in model." % item_id)
				return

			user_index = model['users'][user_id][()]
			item_index = model['items'][item_id][()]
			return np.dot(model['W'][:][user_index], model['H'][:].T[item_index])
