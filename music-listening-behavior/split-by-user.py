#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
# split-by-user.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-04-05

import os
import sys
import gzip

if len(sys.argv) < 2:
	print("Usage: %s scrobble.tsv[.gz]" % os.path.basename(sys.argv[0]))
	sys.exit(0)

previousUid = None
outfile = None
infile = None

if sys.argv[1].endswith(".gz"):
	infile = gzip.open(sys.argv[1], 'rt')
else:
	infile = open(sys.argv[1])

for line in infile:
	fields = line.split('\t')
	if previousUid != fields[0]:
		print("===> Processing user %s..." % fields[0])
		previousUid = fields[0]
		if outfile != None:
			outfile.close()
		outfile = open("%s.csv" % fields[0], 'w')
	if len(fields) == 6:
		outfile.write(line)

if outfile != None:
	outfile.close()
