#!/usr/bin/env python
# coding = utf-8

"""
core.models
"""

__author__ = 'Rnd495'

import datetime
import hashlib

from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from configs import Configs


class _Base(object):
    """
    Declarative base
    """
    DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'

    def to_dict(self):
        fields = {}
        for field in dir(self):
            # those are not field
            if field.startswith('_') or field in ['metadata', 'DATETIME_FORMAT']:
                continue
            val = self.__getattribute__(field)
            # dirty way to remove functions
            if callable(val):
                continue
            # format datetime to text
            if isinstance(val, datetime.datetime):
                val = val.strftime(self.DATETIME_FORMAT)
            # format children metadata
            elif isinstance(val, Base):
                val = val.to_dict()
            fields[field] = val
        return fields


configs = Configs.instance()
meta = MetaData()
Base = declarative_base(cls=_Base)

_engine = None
_session_maker = None
_session = None


def get_engine():
    global _engine
    if not _engine:
        _engine = create_engine(
            configs.database_url,
            encoding=configs.database_encoding,
            echo=False)
        Base.metadata.create_all(_engine)
    return _engine


def get_session_maker():
    global _session_maker
    if not _session_maker:
        _session_maker = sessionmaker(bind=get_engine())
    return _session_maker


def get_global_session():
    global _session
    if not _session:
        _session = get_session_maker()()
    return _session


def get_new_session():
    return get_session_maker()()


class User(Base):
    __table__ = Table("t_user", meta, autoload=True, autoload_with=get_engine())

    def __init__(self, name, pwd,
                 user_id=None, role_id=3, header_url=None):
        self.user_name = name
        self.user_pass = User.password_hash(pwd)
        self.user_register_time = datetime.datetime.now()
        self.user_role_id = role_id
        self.user_header_url = header_url
        if user_id is not None:
            self.user_id = user_id

    def get_is_same_password(self, password):
        return User.password_hash(password) == self.user_pass

    def set_password(self, password):
        self.user_pass = User.password_hash(password)

    @staticmethod
    def password_hash(text):
        return hashlib.sha256(text + configs.user_password_hash_salt).hexdigest()


class Role(Base):
    __table__ = Table("t_role", meta, autoload=True, autoload_with=get_engine())

    def __init__(self, name, role_id=None):
        self.role_name = name
        if role_id is not None:
            self.role_id = role_id


class UserHasMonster(Base):
    __table__ = Table("t_user_has_monster", meta, autoload=True, autoload_with=get_engine())


class Skill(Base):
    __table__ = Table("t_skill", meta, autoload=True, autoload_with=get_engine())


class SkillType(Base):
    __table__ = Table("t_skill_type", meta, autoload=True, autoload_with=get_engine())


class SkillTargetType(Base):
    __table__ = Table("t_skill_target_type", meta, autoload=True, autoload_with=get_engine())


class SPSkill(Base):
    __table__ = Table("t_sp_skill", meta, autoload=True, autoload_with=get_engine())


class Monster(Base):
    __table__ = Table("t_monster", meta, autoload=True, autoload_with=get_engine())


class MonsterType(Base):
    __table__ = Table("t_monster_type", meta, autoload=True, autoload_with=get_engine())


class MonsterHasEquipment(Base):
    __table__ = Table("t_monster_has_equipment", meta, autoload=True, autoload_with=get_engine())


class MonsterHasSkill(Base):
    __table__ = Table("t_monster_has_skill", meta, autoload=True, autoload_with=get_engine())


class MonsterHasSPSkill(Base):
    __table__ = Table("t_monster_has_sp_skill", meta, autoload=True, autoload_with=get_engine())


class Element(Base):
    __table__ = Table("t_element", meta, autoload=True, autoload_with=get_engine())

    def __init__(self, name, element_id=None):
        self.element_name = name
        if element_id is not None:
            self.element_id = element_id


class ElementVSElement(Base):
    __table__ = Table("t_element_vs_element", meta, autoload=True, autoload_with=get_engine())

    def __init__(self, atk_element_id, def_element_id, effect=1.0):
        self.atk_element_id = atk_element_id
        self.def_element_id = def_element_id
        self.effect = effect


class Equipment(Base):
    __table__ = Table("t_element", meta, autoload=True, autoload_with=get_engine())