#!/usr/bin/python
# -*- coding: utf8 -*-
#
# cross_validation.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-07-16

import os
import sys
import string
import argparse
from jld import LatentFactorsModel

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
			description="Do k-fold cross-validation by creating k training CSVs from the original.")
	parser.add_argument('ratings_path',
			help="a CSV file with no header and three columns: user_id, item_id, rating number")
	parser.add_argument('-d', '--delimiter', type=str,
			help="the CSV column delimiter character (DEFAULT=',')")
	parser.add_argument('-r', '--rank', type=int,
			help="the number of latent factors (DEFAULT=1000)")
	parser.add_argument('-k', '--folds', type=int,
			help="the number of folds to use in cross-validation (DEFAULT=10)")
	parser.add_argument('-n', '--feature-sampling-interval', type=int,
			help="the sampling interval of the number of features to use in cross-validation")
	parser.add_argument('-o', '--output', type=str,
			help="output CSV filename, to store validation scores (MAE)")
	args = parser.parse_args()

	if not os.access(args.ratings_path, os.R_OK):
		print("'%s' is not readable." % args.ratings_path)
		sys.exit(0)

	model = LatentFactorsModel()

	if args.delimiter is not None:
		model.set_training_csv_delimiter(args.delimiter)

	if args.rank is not None:
		model.set_training_rank(args.rank)

	k = 10
	if args.folds is not None:
		k = args.folds

	feature_sampling = None
	if args.feature_sampling_interval is not None:
		feature_sampling_interval = args.feature_sampling_interval

	output_filename = None
	if args.output is not None:
		output_filename = args.output

	model.k_fold_cross_validation(
			args.ratings_path,
			k=k,
			feature_sampling=feature_sampling_interval,
			output_filename=output_filename)
