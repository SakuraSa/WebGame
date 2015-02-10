#!/usr/bin/env python
# coding = utf-8

"""
SocketPage
"""

__author__ = 'Rnd495'

import tornado.websocket

import core.models
from core.configs import Configs
from UI.Manager import mapping

configs = Configs.instance()