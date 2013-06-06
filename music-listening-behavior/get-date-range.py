#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
# get-date-range.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-04-18

import re
import os
import sys
import gzip
import datetime

if len(sys.argv) < 2:
	print("Usage: %s scrobble.tsv[.gz]" % os.path.basename(sys.argv[0]))
	sys.exit(0)

infile = None

if sys.argv[1].endswith(".gz"):
	infile = gzip.open(sys.argv[1], 'rt')
else:
	infile = open(sys.argv[1])

count = 0
minDate = datetime.datetime.max
maxDate = datetime.datetime.min
for line in infile:
	columns = line.split('\t')
	dateParts = tuple([int(e) for e in re.split(r'[-T:]', columns[1][0:-1])])
	date = datetime.datetime(*dateParts)

	if date < minDate:
		minDate = date

	if date > maxDate:
		maxDate = date

	count += 1
	if count % 100000 == 0:
		sys.stdout.write('.')
		sys.stdout.flush()

print()
print("Dates range from %s to %s" % (minDate, maxDate))
