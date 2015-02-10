#!/usr/bin/env python
# coding=utf-8

"""
core.models_init
"""

__author__ = 'Rnd495'

import models
from configs import Configs

configs = Configs.instance()


class InitError(Exception):
    """
    InitError
    this exception can be raised when initializing applications
    this exception can carry an inner exception
    """
    def __init__(self, message, inner_exception=None):
        Exception.__init__(self)
        self.message = message
        self.inner_exception = inner_exception

    def __str__(self):
        return self.message

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.message)


def init():
    session = models.get_global_session()
    if session.query(models.User).count() > 0:
        return

    # configs check
    if not configs.init_admin_username or not configs.init_admin_password:
        raise InitError("InitError: admin username or password is not found in config.")

    # create table
    models.Base.metadata.create_all(models.get_engine())

    # create role
    session.add(models.Role(u"站长", 1))
    session.add(models.Role(u"管理员", 2))
    session.add(models.Role(u"会员", 3))
    session.commit()

    # create init admin user
    admin_user = models.User(
        name=configs.init_admin_username,
        pwd=configs.init_admin_password,
        role_id=1)
    session.add(admin_user)
    session.commit()