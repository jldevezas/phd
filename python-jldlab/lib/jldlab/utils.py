#!/usr/bin/python
# -*- coding: utf8 -*-
#
# utils.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-28

import numpy as np

def normalize(vector, scale=(0, 1), keep_zeros=True):
	if len(vector) == 0:
		return vector
	min_vector = min(vector)
	max_vector = max(vector)
	if max_vector - min_vector == 0:
		return list(np.zeros(len(vector)))
	result = []
	for i in xrange(len(vector)):
		if vector[i] == 0 and keep_zeros:
			result.append(0) # TODO this should come from behind as None if it works
		else:
			result.append(((scale[1] - scale[0]) * (vector[i] - min_vector))
					/ float(max_vector - min_vector) + scale[0])
	return np.array(result)
