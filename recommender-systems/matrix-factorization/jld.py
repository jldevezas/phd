#!/usr/bin/python
# -*- coding: utf8 -*-
#
# jld.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-14

import os
import csv
import pymf
import numpy as np
import h5py
import logging
import operator
import random
import math
from tempfile import NamedTemporaryFile
from collections import OrderedDict
from scipy.spatial import distance

class LatentFactorsModel:
	def __init__(self, h5filename=None):
		logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
				datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)

		self.model = None
		self.h5filename = h5filename
		self.normalization = True

		# This is why it would be useful to have a separate training class and prediction class.
		self.training_rank = 1000
		self.training_sample_size = None
		self.training_csv_delimiter = ','

	def enable_normalization(self):
		self.normalization = True

	def disable_normalization(self):
		self.normalization = False

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
		if len(vector) == 0:
			return vector
		min_vector = min(vector)
		max_vector = max(vector)
		if max_vector - min_vector == 0:
			return list(np.zeros(len(vector)))
		result = []
		for i in xrange(len(vector)):
			if vector[i] == 0:
				result.append(0) # TODO this should come from behind as None if it works
			else:
				result.append(((scale[1] - scale[0]) * (vector[i] - min_vector)) / float(max_vector - min_vector))
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

			if self.normalization:
				logging.info("Normalizing ratings matrix in HDF5 file")
				for i in xrange(user_counter):
					user_vector = model['ratings'][i][()]
					model['ratings'][i] = self.__normalize(user_vector)

			#logging.info("Running non-negative matrix factorization in disk")
			#mfact = pymf.NMF(model['ratings'], num_bases=self.training_rank)
			logging.info("Running singular value decomposition in disk")
			mfact = pymf.SVD(model['ratings'])
			mfact.factorize()
			logging.info("Storing %dx%d W matrix and %dx%d H matrix in HDF5 file"
					% (user_counter, self.training_rank, self.training_rank, item_counter))

			# Users' latent factors.
			#model['W'] = mfact.W
			#model['W'] = np.dot(mfact.U, np.sqrt(mfact.S))
			model['U'] = mfact.U
			model['S'] = mfact.S
			# Items' latent factors.
			#model['H'] = mfact.H
			#model['H'] = np.dot(np.sqrt(mfact.S), mfact.V)
			model['V'] = mfact.V
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
			predicted_rating = np.dot(model['U'][user_index, :],
					np.dot(model['S'][:], model['V'][:, item_index]))
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
				U = model['U'][user_index]
				S = model['S']
				V = model['V']
				predicted_ratings[user_index] = np.dot(U, np.dot(S, V))

		logging.info("Rating predictions precomputed")

	def recommend(self, user_id, limit=None, all=False):
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
					if stored_rating == 0 or all:
						results.append((self.__unescape(model['items_index'][item_index]),
							user_predicted_ratings[item_index]))

						counter += 1
						if limit is not None and counter % limit == 0: break
				return results
			else:
				for item_id in model['items']:
					item_index = model['items'][item_id][()]
					stored_rating = model['ratings'][user_index, item_index]
					if stored_rating == 0 or all:
						results.append((self.__unescape(item_id), self.predict(user_id, item_id)))
				results = sorted(results, key=lambda tup: tup[1], reverse=True)

			return results

	def recommend_by_query(self, item_ratings, all=False):
		results = []
		with h5py.File(self.h5filename, 'r') as model:
			user_vector = self.__item_rating_dictionary_to_user_vector(item_ratings)

			# NOTE Projected vector can be appended to U matrix to compute model incrementally.
			projected_user_vector = np.dot(user_vector, np.dot(model['V'][:].T, np.linalg.inv(model['S'])))
			
			predictions = np.dot(projected_user_vector, np.dot(model['S'], model['V']))

			for item_id in model['items']:
				item_index = model['items'][item_id][()]
				stored_rating = user_vector[item_index]
				if stored_rating == 0 or all:
					results.append((self.__unescape(item_id), predictions[item_index]))
			
			return sorted(results, key=lambda tup: tup[1], reverse=True)

	def __item_rating_dictionary_to_user_vector(self, item_ratings):
		if self.normalization:
			ord_item_ratings = OrderedDict(item_ratings)
			items = ord_item_ratings.keys()
			counts = self.__normalize(ord_item_ratings.values())
			for i in xrange(len(items)):
				item_ratings[items[i]] = counts[i]

		with h5py.File(self.h5filename, 'r') as model:
			user_vector = np.zeros(len(model['items']))
			for item_id in model['items']:
				if self.__unescape(item_id) in item_ratings:
					user_vector[model['items'][item_id][()]] = item_ratings[self.__unescape(item_id)]

		return user_vector

	def nearest_neighbors(self, item_ratings, distance=distance.euclidean, limit=5):
		distances = {}
		with h5py.File(self.h5filename, 'r') as model:
			user_vector = self.__item_rating_dictionary_to_user_vector(item_ratings)
			ratings = model['ratings']
			for i in xrange(len(ratings)):
				distances[str(i + 1)] = distance(user_vector, ratings[i])
			
		return sorted(distances.iteritems(), key=operator.itemgetter(1))[:limit]

	def nearest_neighbor(self, item_ratings, distance=distance.euclidean):
		return self.nearest_neighbors(item_ratings, distance, limit=1)[0]

	def __partition(self, lst, n):
		division = len(lst) / float(n)
		return [ lst[int(round(division * i)): int(round(division * (i + 1)))] for i in xrange(n) ]

	# TODO calculate best basis size (number of latent factors?) to predict
	def best_basis_size(self):
		pass

	# This is a batch method that computes MAE for a set of test users
	def mean_absolute_error(self, original_prediction_indices_tuples):
		mae = 0.0
		given = 0
		for original_user_vector, predicted_user_vector, indices in original_prediction_indices_tuples:
			if len(original_user_vector) != len(predicted_user_vector):
				raise Exception("Vector length mistmatch")

			if len(indices) < 1:
				raise Exception("Index vector is empty, nothing to calculate")

			original_user_vector = np.array(original_user_vector)
			predicted_user_vector = np.array(predicted_user_vector)
			indices = np.array(indices)
			given += len(indices)

			original_user_vector = original_user_vector[indices]
			predicted_user_vector = predicted_user_vector[indices]

			mae += np.sum(np.abs(original_user_vector - predicted_user_vector))

		return mae / given

	# This is a batch method that computes RMSE for a set of test users
	def root_mean_squared_error(self, original_prediction_indices_tuples):
		rmse = 0.0
		given = 0
		for original_user_vector, predicted_user_vector, indices in original_prediction_indices_tuples:
			if len(original_user_vector) != len(predicted_user_vector):
				raise Exception("Vector length mistmatch")

			if len(indices) < 1:
				raise Exception("Index vector is empty, nothing to calculate")

			original_user_vector = np.array(original_user_vector)
			predicted_user_vector = np.array(predicted_user_vector)
			indices = np.array(indices)
			given += len(indices)

			original_user_vector = original_user_vector[indices]
			predicted_user_vector = predicted_user_vector[indices]

			rmse += np.sum(np.power(np.abs(original_user_vector - predicted_user_vector), 2))

		return rmse / given

	def k_fold_cross_validation(self, original_csv_path, k=10, given_fraction=0.8,
			feature_sampling=None, max_features=None, output_filename=None):
		self.enable_normalization()

		with open(original_csv_path, 'rb') as f_csv:
			user_set = set([])
			item_set = set([])
			
			# Load all user IDs.
			logging.info("Loading all user IDs from %s" % original_csv_path)
			for user, item, rating in csv.reader(f_csv, delimiter=self.training_csv_delimiter):
				user_set.add(user)
				item_set.add(item)
			user_set = list(user_set)
			
			# Generate k partitions.
			logging.info("Partitioning the user data into %d sets" % k)
			random.shuffle(user_set)
			folds = self.__partition(user_set, k)

			# Create a temporary CVS file for each partition.
			fold_csv_files = []
			fold_csv_writers = []
			for fold in folds:
				tmp_file = NamedTemporaryFile(delete=False)
				fold_csv_files.append(tmp_file)
				fold_csv_writers.append(csv.writer(tmp_file, delimiter=self.training_csv_delimiter))

			# Create user-fold_index dictionary.
			user_fold_index = {}
			has_item = []
			for i in xrange(len(folds)):
				has_item.append(set([]))
				for user in folds[i]:
					user_fold_index[user] = i

			hdf5_filenames = []
			for i in xrange(len(folds)):
				tmpfile = NamedTemporaryFile(delete=False)
				tmpfile.close()
				hdf5_filenames.append(tmpfile.name)

			# Restart reading CSV file and fill CSVs.
			logging.info("Creating training and test sets")
			f_csv.seek(0)
			item_vector = list(item_set)
			for user, item, rating in csv.reader(f_csv, delimiter=self.training_csv_delimiter):
				rating = int(rating)
				for i in xrange(len(fold_csv_writers)):
					if user_fold_index[user] == i:
						# Store test set.
						with h5py.File(hdf5_filenames[i]) as model:
							if not 'test' in model:
								model.create_dataset('test', (len(folds[i]), len(item_vector)), dtype='f')
								model['test'][...] = 0
							model['test'][folds[i].index(user), item_vector.index(item)] = rating
					else:
						# Create training data.
						fold_csv_writers[i].writerow([user, item, rating])
						has_item[i].add(item)

			# Normalize test sets.
			logging.info("Normalizing test sets")
			for i in xrange(len(hdf5_filenames)):
				with h5py.File(hdf5_filenames[i]) as model:
					for i in xrange(model['test'].shape[0]):
						model['test'][i] = self.__normalize(model['test'][i])

			# Add zero values for missing items for a random user
			# (fix to guarantee that all items are included)
			logging.info("Adding reference to missing items")
			for i in xrange(len(has_item)):
				not_i = 0
				if i == 0: not_i = 1
				for item in item_set - has_item[i]:
					fold_csv_writers[i].writerow([folds[not_i][0], item, 0])

			# Create model for each training set.
			logging.info("Training models for each of the %d folds" % k)
			for i in xrange(len(fold_csv_files)):
				model = LatentFactorsModel(hdf5_filenames[i])

				model.set_training_csv_delimiter(self.training_csv_delimiter)
				model.set_training_rank(self.training_rank)
				model.set_training_sample_size(self.training_sample_size)
				
				fold_csv_files[i].close()
				model.train(fold_csv_files[i].name)

			# Predict and evaluate all folds
			logging.info("Using test sets to evaluate models in k=%d folds" % k)
			fold_mae = []
			fold_rmse = []
			n_feature_fold_mae = {}
			n_features = None
			feature_sizes = None

			for i in xrange(len(hdf5_filenames)):
				with h5py.File(hdf5_filenames[i]) as model:
					n_features = model['V'].shape[1]

					n_max_features = n_features
					if max_features is not None:
						n_max_features = max_features

					if feature_sampling is not None:
						#feature_sizes = (range(1, min(n_max_features/feature_sampling, 20))
						#		+ range(n_max_features / feature_sampling,
						#			n_max_features, n_max_features / feature_sampling))
						feature_sizes = sorted(set([int(round(x)) for x in
							np.logspace(0, np.log10(n_max_features), feature_sampling)]))
						logging.info("Calculating MAE for the following number of features: %s"
								% ', '.join([str(s) for s in feature_sizes]))
					
					query_prediction_indices_tuples = []
					n_feature_query_prediction_indices_tuples = {}
					
					for user_vector in model['test']:
						# Randomly set given_fraction of ratings to zero.
						query_user_vector = np.array([rating for rating in user_vector])
						idx_ratings = np.flatnonzero(query_user_vector)
						random.shuffle(idx_ratings)
						idx_ratings = idx_ratings[0:math.ceil(len(idx_ratings) * given_fraction)]
						query_user_vector[idx_ratings] = 0
						
						query_user_vector = list(query_user_vector)
						idx_ratings = list(idx_ratings)

						projected_user_vector = np.dot(query_user_vector,
								np.dot(model['V'][:].T, np.linalg.inv(model['S'])))
						predictions = self.__normalize(
								np.dot(projected_user_vector, np.dot(model['S'], model['V'])))
						
						query_prediction_indices_tuples.append((user_vector, predictions, idx_ratings))

						if feature_sampling is not None:
							for size in feature_sizes:
								projected_user_vector = np.dot(query_user_vector,
										np.dot(model['V'][0:size].T, np.linalg.inv(model['S'][0:size, 0:size])))
								predictions = self.__normalize(np.dot(projected_user_vector,
									np.dot(model['S'][0:size, 0:size], model['V'][0:size])))
								
								if not size in n_feature_query_prediction_indices_tuples:
									n_feature_query_prediction_indices_tuples[size] = []

								n_feature_query_prediction_indices_tuples[size].append(
										(user_vector, predictions, idx_ratings))
					
					fold_mae.append(self.mean_absolute_error(query_prediction_indices_tuples))
					fold_rmse.append(self.root_mean_squared_error(query_prediction_indices_tuples))

					if feature_sampling is not None:
						for size in feature_sizes:
							if not size in n_feature_fold_mae:
								n_feature_fold_mae[size] = []
							n_feature_fold_mae[size].append(
									self.mean_absolute_error(n_feature_query_prediction_indices_tuples[size]))

				
				logging.info("Fold %d done" % (i+1, ))

			out = None
			writer = None
			if output_filename is not None:
				out = open(output_filename, 'wb')
				writer = csv.writer(out, delimiter=self.training_csv_delimiter)

			avg_mae = np.mean(fold_mae)
			std_mae = np.std(fold_mae)
			logging.info("MAE(n_features=%d):  %f +/- %f" % (n_features, avg_mae, std_mae))
			logging.info("RMSE(n_features=%d): %f +/- %f" % (n_features, np.mean(fold_rmse), np.std(fold_rmse)))

			if writer is not None:
				logging.info("Storing evaluation results in %s" % output_filename)
				writer.writerow(["features", "avg.mae", "std.mae"])

			if feature_sampling is not None:
				for size in n_feature_fold_mae:
					avg_mae = np.mean(n_feature_fold_mae[size])
					std_mae = np.std(n_feature_fold_mae[size])
					if writer is None:
						logging.info("MAE(n_features=%d) = %f +/- %f" % (size, avg_mae, std_mae))
					else:
						writer.writerow([size, avg_mae, std_mae])


			if writer is not None:
				writer.writerow([n_features, avg_mae, std_mae])

			if out is not None:
				out.close()

			# Delete temporary files.
			logging.info("Deleting temporary files")
			for fold_csv_file, hdf5_filename in zip(fold_csv_files, hdf5_filenames):
				os.unlink(fold_csv_file.name)
				os.unlink(hdf5_filename)
