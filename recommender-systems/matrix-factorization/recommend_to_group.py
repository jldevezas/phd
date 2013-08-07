#!/usr/bin/python
# -*- coding: utf8 -*-
#
# recommend_to_group.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-06

import os
import sys
import csv
import argparse
import jld
from jld import LatentFactorsModel

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
			description="Use group preferences to recommend new items.")
	parser.add_argument('model_path',
			help="HDF5 file with the trained model containing the factorized matrices")
	parser.add_argument('preferences_csv_path',
			help="HDF5 file with the trained model containing the factorized matrices")
	parser.add_argument('-c', '--group-combine', choices=['mean', 'usage-wmean'], default='mean',
			help='selects the method to combine the user profiles into a single group profile (DEFAULT: mean)')
	args = parser.parse_args()
	
	model = LatentFactorsModel(args.model_path)

	tastes = {}
	with open(args.preferences_csv_path, 'rb') as f:
		for user_id, item_id, normalized_rating in csv.reader(f):
			if not user_id in tastes:
				tastes[user_id] = {}
			tastes[user_id][item_id] = float(normalized_rating)

	group_combine = jld.group_mean
	if args.group_combine == 'usage-wmean':
		group_combine = jld.group_weighted_mean_by_user_activity

	rank = 1
	for item_id, rating in model.recommend_to_group_by_query(tastes, group_combine=group_combine)[0:20]:
		print "%d\t%.10f\t%s" % (rank, rating, item_id)
		rank += 1
