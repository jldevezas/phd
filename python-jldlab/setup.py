#!/usr/bin/python
# -*- coding: utf8 -*-
#
# setup.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-28

import os
from distutils.core import setup

setup(name='jldlab',
		version='dev',
		description='Python Tools for Social Recommender Systems',
		author='José Devezas',
		author_email='joseluisdevezas@gmail.com',
		url='http://www.josedevezas.com/phd/python-jldlab.html',
		packages = ['jldlab', 'jldlab.recsys', 'jldlab.recsys.models', 'jldlab.sna'],
		package_dir = {'jldlab': 'lib/jldlab'},   
		license = 'OSI Approved :: GNU General Public License (GPL)',
		requires=['pymf', 'numpy', 'h5py', 'scipy', 'pymongo'])     
