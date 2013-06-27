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
		logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
				datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)

		self.model = None
		self.h5filename = h5filename

		# This is why it would be useful to have a separate training class and prediction class.
		self.training_rank = 10
		self.training_sample_size = None
		self.training_csv_delimiter = ','

	def set_training_rank(self, rank):
		self.training_rank = rank

	def set_training_sample_size(self, sample_size):
		self.training_sample_size = sample_size

	def set_training_csv_delimiter(self, delimiter):
		self.training_csv_delimiter = delimiter

	def get_training_rank(self):
		return self.training_rank

	def get_training_sample_size(self):
		return self.training_sample_size

	def get_training_csv_delimiter(self):
		return self.training_csv_delimiter

	def train(self, csv_path):
		if os.path.exists(self.h5filename):
			ans = None
			while ans != 'y' and ans != 'n':
				ans = raw_input("===> HDF5 model already exists at %s. Overwrite? [yn] " % self.h5filename)
			if ans != 'y': return
			os.remove(self.h5filename)

		with h5py.File(self.h5filename) as model, open(csv_path, 'rb') as f_csv:
			logging.info("Loading data from %s" % csv_path)
			if self.training_sample_size is not None:
				logging.info("Using sample size %d" % self.training_sample_size)

			matrix_size = (100, 100)
			
			logging.info("Starting with a %dx%d ratings matrix in HDF5 file" % matrix_size)
			model.create_dataset('ratings', matrix_size, maxshape=(None, None))
			model['ratings'][...] = 0
			users_index = model.create_group('users')
			items_index = model.create_group('items')
			
			row_counter = 0
			user_counter = 0
			item_counter = 0
			
			for user, item, rating in csv.reader(f_csv, delimiter=self.training_csv_delimiter):
				try:
					if not user in users_index:
						users_index[user] = user_counter
						user_counter += 1

					if not item in items_index:
						items_index[item] = item_counter
						item_counter += 1

					if user_counter >= model['ratings'].shape[0]:
						matrix_size = (matrix_size[0] * 2, matrix_size[1])
						logging.info("Increasing ratings matrix in HDF5 file to a %dx%d dimension" % matrix_size)
						model['ratings'].resize(matrix_size)

					if item_counter >= model['ratings'].shape[1]:
						matrix_size = (matrix_size[0], matrix_size[1] * 2)
						logging.info("Increasing ratings matrix in HDF5 file to a %dx%d dimension" % matrix_size)
						model['ratings'].resize(matrix_size)

					row = model['ratings'][users_index[user][()]]
					row[items_index[item][()]] = int(rating)
					model['ratings'][users_index[user][()]] = row
				
					if self.training_sample_size is not None:
						row_counter += 1
						if row_counter >= self.training_sample_size: break
				except Exception:
					logging.warning("Error storing rating for (%s, %s, %s), skipping" % (user, item, rating))

			matrix_size = (user_counter, item_counter)
			logging.info("Reducing ratings matrix in HDF5 file to a %dx%d dimension" % matrix_size)
			model['ratings'].resize(matrix_size)

			logging.info("Running non-negative matrix factorization in disk")
			mfact = pymf.NMF(model['ratings'], num_bases=self.training_rank)
			mfact.factorize()
			logging.info("Storing %dx%d W matrix and %dx%d H matrix in HDF5 file"
					% (user_counter, self.training_rank, self.training_rank, item_counter))

			# Users' latent factors.
			model['W'] = mfact.W
			# Items' latent factors.
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

	def get_rating(self, user_id, item_id):
		with h5py.File(self.h5filename, 'r') as model:
			if not user_id in model['users']:
				logging.error("User %s not in model." % user_id)
				return

			if not item_id in model['items']:
				logging.error("Item %s not in model." % item_id)
				return

			user_index = model['users'][user_id][()]
			item_index = model['items'][item_id][()]

			if model['ratings'][user_index][item_index] != 0:
				return model['ratings'][user_index][item_index]

			return None
