#!/usr/bin/python
# -*- coding: utf8 -*-
#
# coverevaluation.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-30

import logging
import numpy as np
from scipy.misc import comb
from pymongo import MongoClient

class CoverEvaluation:
	def __init__(self, host=None, db='jldlabgraph', nodes_collection='nodes', edges_collection='edges'):
		logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
				datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

		self.db = db
		self.nodes_collection = nodes_collection
		self.edges_collection = edges_collection

		con = MongoClient(host)
		self.nodes = con[db][nodes_collection]
		self.edges = con[db][edges_collection]

	def _summary(self, clusters):
		print "===================== Summary ====================="
		print "Number of communities\t\t{0}".format(len(clusters))
		
		community_sizes = [len(cluster['node_ids']) for cluster in clusters]
		print "Community size mean\t\t{0}".format(np.mean(community_sizes))
		print "Community size std. dev.\t{0}".format(np.std(community_sizes))
		print "===================================================\n"

	def overlapping_modularity(self, summary=True):
		"""
		Computes the overlapping modularity as described in "Modularity measure of networks with
		overlapping communities" by Lázár et al. (2010). This process is not optimized as it's not
		critical (maybe in the future, if I have some time).
		"""

		clusters = self.nodes.aggregate([
			{ '$project': { 'communities': 1 } },
			{ '$unwind': '$communities' },
			{ '$group': { '_id': '$communities', 'node_ids': { '$push': '$_id' } } }
		])['result']

		if summary: self._summary(clusters)

		logging.info("Calculating modularity overlapping for {0} database using {1} and {2} collections".format(
			self.db, self.nodes_collection, self.edges_collection))

		overlapping_modularity = 0
		processed_communities = 0
		for cluster in clusters:
			cluster_accumulator = 0

			ncr = len(cluster['node_ids'])
			if ncr < 2: continue

			edges = [node['edges'] for node in self.nodes.find({ '_id': { '$in': cluster['node_ids'] } })]
			necr = len(set([edge for edge_list in edges for edge in edge_list]))

			for node_id in cluster['node_ids']:
				intra_community_connections = self.nodes.find({ '$and': [
					{ '_id': { '$in': list(set(cluster['node_ids']).difference([node_id])) } },
					{ 'neighbors': node_id }
				]}).count()

				inter_community_connections = self.nodes.find({ '$and': [
					{ '_id': { '$nin': cluster['node_ids'] } },
					{ 'neighbors': node_id }
				]}).count()

				node = self.nodes.find_one({ '_id': node_id })
				if node is None: raise Exception("Unexpected error: {0} node not found".format(node_id))

				nr_communities = len(node['communities'])	#si
				degree = len(node['neighbors'])				#di

				cluster_accumulator += ((inter_community_connections - intra_community_connections)
						/ float(nr_communities * degree))

			overlapping_modularity += (cluster_accumulator / ncr) * (necr / float(comb(ncr, 2))) 

			processed_communities += 1
			if processed_communities % 50 == 0:
				logging.info("{0} communities processed so far".format(processed_communities))

		overlapping_modularity /= float(len(clusters))
		logging.info("Overlapping modularity has a value of {0} for {1}".format(overlapping_modularity, self.db))

		return overlapping_modularity


