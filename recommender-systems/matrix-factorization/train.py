#!/usr/bin/python
# -*- coding: utf8 -*-
#
# train.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-14

import os
import sys
import string
import argparse
from jld import LatentFactorsModel

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
			description="Train model based on NMF for user-item rating prediction.")
	parser.add_argument('ratings_path',
			help="a CSV file with no header and three columns: user_id, item_id, rating number")
	parser.add_argument('model_path',
			help="HDF5 file to store the trained model containing the factorized matrices")
	parser.add_argument('-d', '--delimiter', type=str,
			help="the CSV column delimiter character (DEFAULT=',')")
	parser.add_argument('-r', '--rank', type=int,
			help="the number of latent factors (DEFAULT=1000)")
	parser.add_argument('-s', '--size', type=int,
			help="the size of the sample to take from the ratings CSV (DEFAULT=None)")
	parser.add_argument('--precompute', action='store_true',
			help="precompute and store prediction values in HDF5 (DEFAULT=False)")
	args = parser.parse_args()

	if not os.access(args.ratings_path, os.R_OK):
		print("'%s' is not readable." % args.ratings_path)
		sys.exit(0)

	if os.path.exists(args.model_path):
		ans = None
		while ans != 'y' and ans != 'n':
			ans = raw_input("===> HDF5 model already exists at %s. Overwrite? [yn] " % args.model_path)
		if ans != 'y': sys.exit(0)
		os.remove(args.model_path)

	model = LatentFactorsModel(args.model_path)

	if args.delimiter is not None:
		model.set_training_csv_delimiter(args.delimiter)

	if args.rank is not None:
		model.set_training_rank(args.rank)

	if args.size is not None:
		model.set_training_sample_size(args.size)

	model.train(args.ratings_path)

	if args.precompute:
		model.precompute_predictions()
