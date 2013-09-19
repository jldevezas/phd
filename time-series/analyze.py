#!/usr/bin/python
# -*- coding: utf8 -*-
#
# analyze.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-09-17

import pandas as pd
import pandas.io.sql as pd_sql
import sqlite3 as sql
from datetime import datetime
#import matplotlib.pyplot as plt

def analyze(sqlite_path):
	con = sql.connect(sqlite_path)
	df = pd_sql.read_frame(
			"SELECT user_id, artist, timestamp FROM tracks LIMIT 1000",
			con, index_col='timestamp')
	df.index = pd.to_datetime(df.index.values * 1e9)
	uac_df = df.groupby(['user_id', 'artist']).resample('M', how='count')
	#uac_df.reindex(pd.date_range(min(uac_df.index), max(uac_df.index)))
	print uac_df.head(10)
	#uac_df.to_csv('/Users/jldevezas/Desktop/out.csv', encoding='utf-8')

analyze('/Users/jldevezas/Desktop/lastfm-dump-SNAPSHOT-20130918T1023.db')
