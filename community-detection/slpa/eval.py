#!/usr/bin/python
# -*- coding: utf8 -*-
#
# eval.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-30


from jldlab.sna import CoverEvaluation

ev = CoverEvaluation()
overlapping_modularity = ev.overlapping_modularity()
