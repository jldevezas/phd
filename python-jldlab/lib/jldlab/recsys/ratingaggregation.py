#!/usr/bin/python
# -*- coding: utf8 -*-
#
# ratingaggregation.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-28

def group_weighted_mean_by_user_activity(group_vectors):
	weights = np.array([np.count_nonzero(group_vector) for group_vector in group_vectors])
	weights = normalize(1 - weights / float(np.max(weights)), scale=(0.3, 0.7))
	return np.sum([weight * np.array(group_vector)
		for group_vector, weight in zip(group_vectors, weights)], axis=0)

def group_mean(group_vectors):
	return np.mean(group_vectors, axis=0)
