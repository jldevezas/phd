#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nmfpredict.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-25


import os
import sys
from nmfrecommender import NmfRecommender

if __name__ == "__main__":
	if len(sys.argv) < 4:
		print("%s <user-id> <item-id> <model.h5>" % os.path.basename(sys.argv[0]))
		sys.exit(0)

	model = NmfRecommender(sys.argv[3])
	predicted_rating = model.predict(sys.argv[1], sys.argv[2])
	if predicted_rating is None:
		print("Could not predict rating for user %s and item %s." % (sys.argv[1], sys.argv[2]))
		sys.exit(1)
	
	print("Predicted rating for user %s and item %s is of %f." % (sys.argv[1], sys.argv[2], predicted_rating))
