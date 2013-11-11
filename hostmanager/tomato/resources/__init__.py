# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.db import models
import random, sys

from .. import fault
from ..lib import db, attributes, util, logging #@UnresolvedImport
from ..lib.decorators import *

TYPES = {}

def give(type_, num, owner):
    logging.logMessage("instance_return", category="resource", type=type_, num=num, owner=(owner.__class__.__name__.lower(), owner.id))
    if isinstance(owner, Element):
        instance = ResourceInstance.objects.get(type=type_, num=num, ownerElement=owner)
    elif isinstance(owner, Connection):
        instance = ResourceInstance.objects.get(type=type_, num=num, ownerConnection=owner)
    else:
        fault.raise_("Owner must either be Element or Connection, was %s" % owner.__class__.__name__, fault.INTERNAL_ERROR)
    instance.delete()

def take(type_, owner):
    res = getByType(type_)
    fault.check(res, "Multiple or none resources of type %s found", type_, fault.INTERNAL_ERROR)
    range_ = res.getInstanceRange()
    for try_ in xrange(0, 100): 
        num = random.choice(range_)
        try:
            ResourceInstance.objects.get(type=type_, num=num)
            continue
        except ResourceInstance.DoesNotExist:
            pass
        try:
            instance = ResourceInstance()
            instance.init(type_, num, owner)
            logging.logMessage("instance_take", category="resource", type=type_, num=num, owner=(owner.__class__.__name__.lower(), owner.id))
            return num
        except:
            pass
    fault.raise_("Failed to obtain resource of type %s after %d tries" % (type_, try_), code=fault.INTERNAL_ERROR)

from ..elements import Element
from ..connections import Connection

class Resource(db.ChangesetMixin, attributes.Mixin, models.Model):
    type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES]) #@ReservedAssignment
    attrs = db.JSONField()
    numStart = attributes.attribute("num_start", int)
    numCount = attributes.attribute("num_count", int)
    
    class Meta:
        pass

    def init(self, attrs={}):
        self.attrs = {}
        self.save()
        self.modify(attrs)
        
    def getInstanceRange(self):
        fault.check(self.numStart and self.numCount, "This resource can not have any instances", code=fault.INTERNAL_ERROR)
        return xrange(self.numStart, self.numStart + self.numCount)
        
    def upcast(self):
        if not self.type in TYPES:
            return self
        try:
            return getattr(self, self.type)
        except:
            import traceback
            traceback.print_exc()
        fault.raise_("Failed to cast resource #%d to type %s" % (self.id, self.type), code=fault.INTERNAL_ERROR)
    
    def modify(self, attrs):
        logging.logMessage("modify", category="resource", type=self.type, id=self.id, attrs=attrs)
        for key, value in attrs.iteritems():
            if hasattr(self, "modify_%s" % key):
                getattr(self, "modify_%s" % key)(value)
            else:
                self.attrs[key] = value
        logging.logMessage("info", category="resource", type=self.type, id=self.id, info=self.info())
        self.save()
    
    def modify_num_start(self, val):
        self.numStart = val
    
    def modify_num_count(self, val):
        self.numCount = val

    def remove(self):
        logging.logMessage("info", category="resource", type=self.type, id=self.id, info=self.info())
        logging.logMessage("remove", category="resource", type=self.type, id=self.id)
        self.delete()    
    
    def info(self):
        return {
            "id": self.id,
            "type": self.type,
            "attrs": self.attrs.copy(),
        }
    
class ResourceInstance(db.ChangesetMixin, attributes.Mixin, models.Model):
    type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES]) #@ReservedAssignment
    num = models.IntegerField()
    ownerElement = models.ForeignKey(Element, null=True)
    ownerConnection = models.ForeignKey(Connection, null=True)
    attrs = db.JSONField()
    
    class Meta:
        unique_together = (("num", "type"),)

    def init(self, type, num, owner, attrs={}): #@ReservedAssignment
        self.type = type
        self.num = num
        if isinstance(owner, Element):
            self.ownerElement = owner
        elif isinstance(owner, Connection):
            self.ownerConnection = owner
        else:
            fault.raise_("Owner must either be Element or Connection, was %s" % owner.__class__.__name__, fault.INTERNAL_ERROR)
        self.attrs = attrs
        self.save()


def get(id_, **kwargs):
    try:
        el = Resource.objects.get(id=id_, **kwargs)
        try:
            return el.upcast()
        except:
            return el
    except:
        return None

def getByType(type_, **kwargs):
    try:
        el = Resource.objects.get(type=type_, **kwargs)
        return el.upcast()
    except:
        return None

def getAll(**kwargs):
    return (res.upcast() for res in Resource.objects.filter(**kwargs))

def _addResourceRange(type_, start, count):
    return create(type_, {"num_start": start, "num_count": count})

def create(type_, attrs={}):
    if type_ in TYPES:
        res = TYPES[type_]()
    else:
        res = Resource(type=type_)
    res.init(attrs)
    res.save()
    logging.logMessage("create", category="resource", type=res.type, id=res.id, attrs=attrs)
    logging.logMessage("info", category="resource", type=res.type, id=res.id, info=res.info())
    return res

def init():
    if not getByType("vmid"):
        print >>sys.stderr, "Adding default resource entry for vmid"
        _addResourceRange("vmid", 1000, 1000)
    if not getByType("port"):
        print >>sys.stderr, "Adding default resource entry for port"
        _addResourceRange("port", 6000, 1000)
    