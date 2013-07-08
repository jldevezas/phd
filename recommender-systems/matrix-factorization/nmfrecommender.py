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
		self.training_normalization = True
		self.training_rank = 1000
		self.training_sample_size = None
		self.training_csv_delimiter = ','

	def enable_training_normalization(self):
		self.training_normalization = True

	def disable_training_normalization(self):
		self.training_normalization = False

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

	def __escape(self, h5key):
		return h5key.replace('/', '_')

	def __unescape(self, h5key):
		return h5key.replace('_', '/')

	def __normalize(self, vector, scale=(0, 1)):
		min_vector = min(vector)
		max_vector = max(vector)
		result = []
		for i in xrange(len(vector)):
			if vector[i] == 0:
				result.append(0) # TODO this should come from behind as None if it works
			else:
				result.append(((scale[1] - scale[0]) * (vector[i] - min_vector)) / (max_vector - min_vector))
		return np.array(result)

	def train(self, csv_path):
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
					if not self.__escape(user) in users_index:
						users_index[self.__escape(user)] = user_counter
						user_counter += 1

					if not self.__escape(item) in items_index:
						items_index[self.__escape(item)] = item_counter
						item_counter += 1

					if user_counter >= model['ratings'].shape[0]:
						matrix_size = (matrix_size[0] * 2, matrix_size[1])
						logging.info("Increasing ratings matrix in HDF5 file to a %dx%d dimension" % matrix_size)
						model['ratings'].resize(matrix_size)

					if item_counter >= model['ratings'].shape[1]:
						matrix_size = (matrix_size[0], matrix_size[1] * 2)
						logging.info("Increasing ratings matrix in HDF5 file to a %dx%d dimension" % matrix_size)
						model['ratings'].resize(matrix_size)

					row = model['ratings'][users_index[self.__escape(user)][()]]
					row[items_index[self.__escape(item)][()]] = int(rating)
					model['ratings'][users_index[self.__escape(user)][()]] = row
				
					if self.training_sample_size is not None:
						row_counter += 1
						if row_counter >= self.training_sample_size: break
				except Exception:
					logging.warning("Error storing rating for (%s, %s, %s), skipping" % (user, item, rating))

			matrix_size = (user_counter, item_counter)
			logging.info("Reducing ratings matrix in HDF5 file to a %dx%d dimension" % matrix_size)
			model['ratings'].resize(matrix_size)

			if self.training_normalization:
				logging.info("Normalizing ratings matrix in HDF5 file")
				for i in xrange(user_counter):
					user_vector = model['ratings'][i][()]
					model['ratings'][i] = self.__normalize(user_vector)

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
			if not self.__escape(user_id) in model['users']:
				logging.error("predict: User %s not in model." % user_id)
				return None

			if not self.__escape(item_id) in model['items']:
				logging.error("predict: Item %s not in model." % item_id)
				return None

			user_index = model['users'][self.__escape(user_id)][()]
			item_index = model['items'][self.__escape(item_id)][()]
			if 'predicted_ratings' in model:
				logging.info("Found precomputed prediction value.")
				return model['predicted_ratings'][user_index, item_index]
			predicted_rating = np.dot(model['W'][user_index, :], model['H'][:, item_index])
			return predicted_rating

	def get_rating(self, user_id, item_id):
		with h5py.File(self.h5filename, 'r') as model:
			if not self.__escape(user_id) in model['users']:
				logging.error("get_rating: User %s not in model." % user_id)
				return None

			if not self.__escape(item_id) in model['items']:
				logging.error("get_rating: Item %s not in model." % item_id)
				return None

			user_index = model['users'][self.__escape(user_id)][()]
			item_index = model['items'][self.__escape(item_id)][()]

			rating = model['ratings'][user_index][item_index][()]

			if rating != 0:
				return rating

			return None

	def precompute_predictions(self):
		results = []
		with h5py.File(self.h5filename) as model:
			matrix_size = model['ratings'].shape

			logging.info("Creating items index in HDF5")
			t_str = h5py.special_dtype(vlen=str)
			items_index = model.create_dataset('items_index', (matrix_size[1], ), dtype=t_str)
			for item_id in model['items']:
				item_index = model['items'][item_id][()]
				items_index[item_index] = item_id

			predicted_ratings = model.create_dataset('predicted_ratings', matrix_size)

			for user_id in model['users']:
				logging.info("Precomputing predictions for user %s and storing in HDF5" % user_id)
				user_index = model['users'][self.__escape(user_id)][()]
				W = model['W'][user_index]
				H = model['H']
				predicted_ratings[user_index] = np.dot(W, H)

		logging.info("Rating predictions precomputed")

	def recommend(self, user_id, limit=None):
		results = []
		with h5py.File(self.h5filename, 'r') as model:
			if not self.__escape(user_id) in model['users']:
				logging.error("predict: User %s not in model." % user_id)
				return results

			user_index = model['users'][self.__escape(user_id)][()]
			
			if 'predicted_ratings' in model:
				user_predicted_ratings = model['predicted_ratings'][user_index, :]
				item_indices = sorted(xrange(len(user_predicted_ratings)),
						key=lambda i: user_predicted_ratings[i], reverse=True)
				counter = 0
				for item_index in item_indices:
					stored_rating = model['ratings'][user_index, item_index]
					if stored_rating == 0:
						results.append((user_predicted_ratings[item_index],
							self.__unescape(model['items_index'][item_index])))
					counter += 1
					if limit is not None and counter % limit == 0: break
				return results
			else:
				for item_id in model['items']:
					item_index = model['items'][item_id][()]
					stored_rating = model['ratings'][user_index, item_index]
					if stored_rating == 0:
						results.append((self.predict(user_id, item_id), self.__unescape(item_id)))
				results = sorted(results, key=lambda tup: tup[0], reverse=True)

			return results
