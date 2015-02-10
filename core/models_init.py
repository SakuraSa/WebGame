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
        session.close()
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

    # create element
    element_list = [
        u'普', u'爆（火）', u'河（水）', u'花（草）', u'磁（电）',
        u'冰', u'斗', u'毒', u'地', u'天（飞）',
        u'超', u'虫', u'山（岩）', u'鬼', u'龙',
        u'恶', u'钢', u'月（妖）'
    ]
    for i, name in enumerate(element_list):
        session.add(models.Element(name=name, element_id=i + 1))
    session.commit()

    # create element vs element
    effective_list = {
        (u'爆（火）', u'花（草）'), (u'爆（火）', u'冰'), (u'爆（火）', u'虫'), (u'爆（火）', u'钢'),
        (u'河（水）', u'爆（火）'), (u'河（水）', u'地'), (u'河（水）', u'山（岩）'),
        (u'花（草）', u'河（水）'), (u'花（草）', u'地'), (u'花（草）', u'山（岩）'),
        (u'磁（电）', u'河（水）'), (u'磁（电）', u'天（飞）'),
        (u'冰', u'花（草）'), (u'冰', u'地'), (u'冰', u'天（飞）'), (u'冰', u'龙'),
        (u'斗', u'普'), (u'斗', u'冰'), (u'斗', u'山（岩）'), (u'斗', u'恶'), (u'斗', u'钢'),
        (u'毒', u'花（草）'), (u'毒', u'月（妖）'),
        (u'地', u'爆（火）'), (u'地', u'磁（电）'), (u'地', u'毒）'), (u'地', u'山（岩）'), (u'地', u'钢'),
        (u'天（飞）', u'花（草）'), (u'天（飞）', u'斗'), (u'天（飞）', u'虫'),
        (u'超', u'斗'), (u'超', u'毒'),
        (u'虫', u'花（草）'), (u'虫', u'超'), (u'虫', u'恶'),
        (u'山（岩）', u'爆（火）'), (u'山（岩）', u'冰'), (u'山（岩）', u'天（飞）'), (u'山（岩）', u'虫'),
        (u'鬼', u'超'), (u'鬼', u'鬼'),
        (u'龙', u'龙'),
        (u'恶', u'超'), (u'恶', u'鬼'),
        (u'钢', u'冰'), (u'钢', u'山（岩）'), (u'钢', u'月（妖）'),
        (u'月（妖）', u'斗'), (u'月（妖）', u'龙'), (u'月（妖）', u'恶'),
    }
    not_effective_list = {
        (u'普', u'山（岩）'), (u'普', u'钢'),
        (u'爆（火）', u'爆（火）'), (u'爆（火）', u'河（水）'), (u'爆（火）', u'山（岩）'), (u'爆（火）', u'龙'),
        (u'河（水）', u'河（水）'), (u'河（水）', u'花（草）'), (u'河（水）', u'龙'),
        (u'花（草）', u'爆（火）'), (u'花（草）', u'花（草）'), (u'花（草）', u'毒'),
        (u'花（草）', u'天（飞）'), (u'花（草）', u'虫'), (u'花（草）', u'龙'), (u'花（草）', u'钢'),
        (u'磁（电）', u'花（草）'), (u'磁（电）', u'磁（电）'), (u'磁（电）', u'龙'),
        (u'冰', u'爆（火）'), (u'冰', u'河（水）'), (u'冰', u'冰'), (u'冰', u'钢'),
        (u'斗', u'毒'), (u'斗', u'天（飞）'), (u'斗', u'超'), (u'斗', u'虫'), (u'斗', u'钢'),
        (u'毒', u'毒'), (u'毒', u'地'), (u'毒', u'山（岩）'), (u'毒', u'鬼'),
        (u'地', u'花（草）'), (u'地', u'虫'),
        (u'天（飞）', u'磁（电）'), (u'天（飞）', u'山（岩）'), (u'天（飞）', u'钢'),
        (u'超', u'超'), (u'超', u'钢'),
        (u'虫', u'爆（火）'), (u'虫', u'斗'), (u'虫', u'毒'), (u'虫', u'天（飞）'),
        (u'虫', u'鬼'), (u'虫', u'钢'), (u'虫', u'月（妖）'),
        (u'山（岩）', u'斗'), (u'山（岩）', u'地'), (u'山（岩）', u'钢'),
        (u'鬼', u'恶'),
        (u'龙', u'钢'),
        (u'恶', u'斗'), (u'恶', u'恶'), (u'恶', u'月（妖）'),
        (u'钢', u'爆（火）'), (u'钢', u'河（水）'), (u'钢', u'磁（电）'), (u'钢', u'钢'),
        (u'月（妖）', u'爆（火）'), (u'月（妖）', u'毒'), (u'月（妖）', u'钢'),
    }
    no_effect_list = {
        (u'普', u'鬼'),
        (u'磁（电）', u'地'),
        (u'斗', u'鬼'),
        (u'毒', u'钢'),
        (u'地', u'天（飞）'),
        (u'超', u'恶'),
        (u'鬼', u'普'),
        (u'龙', u'月（妖）'),
    }
    for i, atk_element_name in enumerate(element_list):
        atk_element_id = i + 1
        for j, def_element_name in enumerate(element_list):
            def_element_id = j + 1
            name_pair = (atk_element_name, def_element_name)
            if name_pair in effective_list:
                # double effect
                session.add(models.ElementVSElement(atk_element_id, def_element_id, 2.0))
            elif name_pair in not_effective_list:
                # half effect
                session.add(models.ElementVSElement(atk_element_id, def_element_id, 0.5))
            elif name_pair in no_effect_list:
                # no effect
                session.add(models.ElementVSElement(atk_element_id, def_element_id, 0.0))
            else:
                # normal effect
                session.add(models.ElementVSElement(atk_element_id, def_element_id, 1.0))
    session.commit()

    session.close()