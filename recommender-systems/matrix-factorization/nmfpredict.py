#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nmfpredict.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-25


import os
import sys
import argparse
from nmfrecommender import NmfRecommender

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
			description='Predict rating for an unrated item of an existing user.')
	parser.add_argument('user',
			help='user identification string, as defined in the training set')
	parser.add_argument('item',
			help='item identification string, as defined in the training set')
	parser.add_argument('model_path',
			help='HDF5 file with the trained model containing the factorized matrices')
	parser.add_argument('-f', '--force-predict', action='store_true',
			help='returns the predicted value even when the original rating is available')
	args = parser.parse_args()
	
	model = NmfRecommender(args.model_path)

	if not args.force_predict:
		# If rating exists, return real rating instead of prediction.
		rating = model.get_rating(args.user, args.item)
		if rating is not None:
			print("User %s rated item %s with %f." % (args.user, args.item, rating))
			sys.exit(0)

	predicted_rating = model.predict(args.user, args.item)
	if predicted_rating is None:
		print("Could not predict rating for user %s and item %s." % (args.user, args.item))
		sys.exit(1)
	
	print("Predicted rating for user %s and item %s is of %f." % (args.user, args.item, predicted_rating))
