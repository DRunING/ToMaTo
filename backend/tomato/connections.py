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
import threading

from topology import Topology
from auth import Flags
from auth.permissions import Permissions, PermissionMixin, Role
from lib import db, attributes, logging #@UnresolvedImport
from accounting import UsageStatistics
from lib.decorators import *
from host import HostConnection, HostElement, getConnectionCapabilities, getAll as getAllHosts

REMOVE_ACTION = "(remove)"

ST_CREATED = "created"
ST_STARTED = "started"

LOCKS = {}
LOCKS_LOCK = threading.RLock()

def getLock(obj):
	with LOCKS_LOCK:
		if not obj.id in LOCKS:
			LOCKS[obj.id] = threading.RLock()
		return LOCKS[obj.id]
	
def removeLock(obj):
	with LOCKS_LOCK:
		with getLock(obj):
			del LOCKS[obj.id]

class Connection(PermissionMixin, db.ChangesetMixin, attributes.Mixin, models.Model):
	topology = models.ForeignKey(Topology, null=False, related_name="connections")
	state = models.CharField(max_length=20, validators=[db.nameValidator])
	permissions = models.ForeignKey(Permissions, null=False)
	totalUsage = models.OneToOneField(UsageStatistics, null=True, related_name='+')
	attrs = db.JSONField()
	#elements: set of elements.Element
	connection1 = models.ForeignKey(HostConnection, null=True, on_delete=models.SET_NULL, related_name="+")
	connection2 = models.ForeignKey(HostConnection, null=True, on_delete=models.SET_NULL, related_name="+")
	connectionElement1 = models.ForeignKey(HostElement, null=True, on_delete=models.SET_NULL, related_name="+")
	connectionElement2 = models.ForeignKey(HostElement, null=True, on_delete=models.SET_NULL, related_name="+")
	
	DIRECT_ACTIONS = True
	DIRECT_ACTIONS_EXCLUDE = ["start", "stop", "prepare", "destroy"]
	CUSTOM_ACTIONS = {REMOVE_ACTION: [ST_CREATED]}
	
	DIRECT_ATTRS = True
	DIRECT_ATTRS_EXCLUDE = []
	CUSTOM_ATTRS = {}
	
	DEFAULT_ATTRS = {"emulation": True, "bandwidth_to": 10000, "bandwidth_from": 10000}
	
	DOC=""
	
	class Meta:
		pass

	def init(self, topology, el1, el2, attrs={}):
		self.topology = topology
		self.permissions = topology.permissions
		self.attrs = dict(self.DEFAULT_ATTRS)
		self.state = ST_CREATED
		self.totalUsage = UsageStatistics.objects.create()
		self.save()
		self.elements.add(el1)
		self.elements.add(el2)
		self.save()	
		self.modify(attrs)
		
	def _saveAttributes(self):
		pass #disable automatic attribute saving		
		
	@classmethod
	def canConnect(cls, el1, el2):
		return el1.CAP_CONNECTABLE and el2.CAP_CONNECTABLE
		
	def upcast(self):
		return self
	
	def mainConnection(self):
		return self.connection1

	def remoteType(self):
		return self.mainConnection().type if self.mainConnection() else "bridge"

	def _adaptAttrs(self, attrs):
		tmp = {}
		reversed = not self._correctDirection() #@ReservedAssignment
		for key, value in attrs.iteritems():
			if reversed:
				if key.endswith("_from"):
					key = key[:-5] + "_to"
				elif key.endswith("_to"):
					key = key[:-3] + "_from"
			tmp[key] = value
		return tmp

	def _remoteAttrs(self):
		caps = getConnectionCapabilities(self.remoteType())
		allowed = caps["attrs"].keys() if caps else []
		attrs = {}
		reversed = not self._correctDirection() #@ReservedAssignment
		for key, value in self.attrs.iteritems():
			if key in allowed:
				attrs[key] = value
		attrs = self._adaptAttrs(attrs)
		return attrs

	def checkModify(self, attrs):
		"""
		Checks whether the attribute change can succeed before changing the
		attributes.
		If checks whether the attributes are listen in CAP_ATTRS and if the
		current object state is listed in CAP_ATTRS[NAME].
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""
		self.checkRole(Role.manager)
		mcon = self.mainConnection()
		direct = []
		if self.DIRECT_ATTRS:
			if mcon:
				direct = mcon.getAllowedAttributes().keys()
			else:
				caps = getConnectionCapabilities(self.remoteType())
				direct = caps["attrs"].keys() if caps else []
		for key in attrs.keys():
			if key in direct and not key in self.DIRECT_ATTRS_EXCLUDE:
				continue
			if key.startswith("_"):
				continue
			fault.check(key in self.CUSTOM_ATTRS, "Unsuported attribute for: %s", key)
			self.CUSTOM_ATTRS[key].check(self, attrs[key])
		
	def modify(self, attrs):
		"""
		Sets the given attributes to their given values. This method first
		checks if the change can be made using checkModify() and then executes
		the attribute changes by calling modify_KEY(VALUE) for each key/value
		pair in attrs. After calling all these modify_KEY methods, it will save
		the object.
		
		Classes inheriting from this class should only implement the modify_KEY
		methods and not touch this method.  
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""		
		with getLock(self):
			return self._modify(attrs)
			
	def _modify(self, attrs):
		self.checkModify(attrs)
		logging.logMessage("modify", category="connection", id=self.id, attrs=attrs)		
		try:
			directAttrs = {}
			for key, value in attrs.iteritems():
				if key in self.CUSTOM_ATTRS:
					getattr(self, "modify_%s" % key)(value)
				else:
					if key.startswith("_"):
						self.setAttribute(key, value)
					else:
						directAttrs[key] = value
			if directAttrs:
				self.setAttributes(directAttrs)					
				mcon = self.mainConnection()
				if mcon:
					mcon.modify(self._remoteAttrs())
		except Exception, exc:
			self.onError(exc)
			raise
		self.save()
		logging.logMessage("info", category="connection", id=self.id, info=self.info())			
	
	def checkAction(self, action):
		"""
		Checks if the action can be executed. This method checks if the action
		is listed in CAP_ACTIONS and if the current state is listed in 
		CAP_ACTIONS[action].
		
		@param action: Action to check
		@type action: str
		"""
		self.checkRole(Role.manager)
		if self.DIRECT_ACTIONS and not action in self.DIRECT_ACTIONS_EXCLUDE:
			mcon = self.mainConnection()
			if mcon and action in mcon.getAllowedActions():
				return
		fault.check(action in self.CUSTOM_ACTIONS, "Unsuported action: %s", action)
		fault.check(self.state in self.CUSTOM_ACTIONS[action], "Action %s can not be executed in state %s", (action, self.state))
	
	def action(self, action, params):
		"""
		Executes the action with the given parameters. This method first
		checks if the action is possible using checkAction() and then executes
		the action by calling action_ACTION(**params). After calling the action
		method, it will save the object.
		
		Classes inheriting from this class should only implement the 
		action_ACTION method and not touch this method. 
		
		@param action: Name of the action
		@type action: str
		@param params: Parameters for the action
		@type params: dict
		"""
		with getLock(self):
			return self._action(action, params)
			
	def _action(self, action, params):
		self.checkAction(action)
		logging.logMessage("action start", category="connection", id=self.id, action=action, params=params)
		try:
			if action in self.CUSTOM_ACTIONS:
				res = getattr(self, "action_%s" % action)(**params)
			else:
				mcon = self.mainConnection()
				assert mcon
				res = mcon.action(action, params)
				self.setState(mcon.state, True)
		except Exception, exc:
			self.onError(exc)
			raise
		self.save()
		logging.logMessage("action end", category="connection", id=self.id, action=action, params=params, res=res)
		logging.logMessage("info", category="connection", id=self.id, info=self.info())			
		return res

	def setState(self, state, dummy=None):
		self.state = state
		self.save()

	def checkRemove(self):
		self.checkRole(Role.manager)

	def remove(self):
		with getLock(self):
			self._removeLocked()
		removeLock(self)
			
	def _removeLocked(self):
		self.checkRemove()
		logging.logMessage("info", category="topology", id=self.id, info=self.info())
		logging.logMessage("remove", category="topology", id=self.id)		
		self.triggerStop()
		for el in self.getElements():
			el.connection = None
			el.save()
		self.elements.clear() #Important, otherwise elements will be deleted
		#self.totalUsage will be deleted automatically
		#not deleting permissions, the object belongs to the topology
		self.delete()
			
	def getElements(self):
		# sort elements so el1->el2 is from and el2->el1 is to
		return sorted([el.upcast() for el in self.elements.all()], key=lambda el: el.id)
			
	def getHostElements(self):
		return filter(bool, [self.connectionElement1, self.connectionElement2])
			
	def getHostConnections(self):
		return filter(bool, [self.connection1, self.connection2])

	def onError(self, exc):
		pass

	def _correctDirection(self):
		"""
		Find out whether the directions are correct
		"""
		el1 = self.getElements()[0].mainElement()
		fault.check(el1, "Can not check directions on unprepared element")
		id1 = el1.num
		if self.connectionElement1:
			id2 = self.connectionElement1.num
		else:
			el2 = self.getElements()[1].mainElement()
			fault.check(el2, "Can not check directions on unprepared element")
			id2 = el2.num
		return id1 < id2
		
	def _start(self):
		if self.state == ST_STARTED:
			return
		els = self.getElements()
		assert len(els) == 2, "Connection %s has %d connections" % (self, len(els))
		el1, el2 = els
		el1, el2 = el1.mainElement(), el2.mainElement()
		fault.check(el1 and el2, "Can not connect unprepared element")
		# First create connection, then set attributes
		if el1.host == el2.host:
			# simple case: both elements are on same host
			self.connection1 = el1.connectWith(el2, attrs={}, owner=self)
			if self.connection1.state == ST_CREATED:
				self.connection1.action("start")
		else:
			# complex case: helper elements needed to connect elements on different hosts
			self.connectionElement1 = el1.host.createElement("udp_tunnel", owner=self)
			self.connectionElement2 = el2.host.createElement("udp_tunnel", attrs={
				"connect": "%s:%d" % (el1.host.address, self.connectionElement1.attrs["attrs"]["port"])
			}, owner=self)
			self.connection1 = el1.connectWith(self.connectionElement1, attrs={}, owner=self)
			self.connection2 = el2.connectWith(self.connectionElement2, owner=self)
			self.save()
			self.connectionElement1.action("start")
			self.connectionElement2.action("start")
			if self.connection1.state == ST_CREATED:
				self.connection1.action("start")
			if self.connection2.state == ST_CREATED:
				self.connection2.action("start")
		# Find out and set allowed attributes
		allowed = self.connection1.getAllowedAttributes()
		attrs = dict(filter(lambda (k, v): k in allowed, self._remoteAttrs().items()))
		self.connection1.modify(attrs)
		# Unset all disallowed attributes
		for key in self.attrs.keys():
			if not key in allowed:
				del self.attrs[key]
		self.setState(ST_STARTED)
			
	def _stop(self):
		if self.connection1:
			if self.connection1.state == ST_STARTED:
				self.connection1.action("stop")
			self.connection1.remove()
			self.connection1 = None
			self.save()
		if self.connection2:
			if self.connection2.state == ST_STARTED:
				self.connection2.action("stop")
			self.connection2.remove()
			self.connection2 = None
			self.save()
		if self.connectionElement1:
			if self.connectionElement1.state == ST_STARTED:
				self.connectionElement1.action("stop")
			self.connectionElement1.remove()
			self.connectionElement1 = None
			self.save()
		if self.connectionElement2:
			if self.connectionElement2.state == ST_STARTED:
				self.connectionElement2.action("stop")
			self.connectionElement2.remove()
			self.connectionElement2 = None
			self.save()
		self.setState(ST_CREATED)

	def triggerStart(self):
		for el in self.getElements():
			if not el.readyToConnect():
				return
		# This is very important
		# To avoid race conditions where two elements are started at the same time and then trigger
		# the connection start at the same time, a lock is used to guarantee that only one instance
		# of _start runs at the same time.
		# To avoid the case that the second element uses old connection data and runs _start again,
		# the object is fetched freshly from the database. 
		with getLock(self):
			obj = Connection.objects.get(id=self.id)
			obj._start()
		
	def triggerStop(self):
		# This is very important, see the comment on triggerStart 
		with getLock(self):
			try:
				obj = Connection.objects.get(id=self.id)
				obj._stop()
			except Connection.DoesNotExist:
				# Other end of connection deleted the connection, no need to stop it
				pass
		
	@classmethod
	def getCapabilities(cls, type_, host_):
		if not host_:
			host_ = getAllHosts()[0]
		if cls.DIRECT_ATTRS or cls.DIRECT_ACTIONS:
			host_cap = host_.getConnectionCapabilities(type_)
		cap_actions = dict(cls.CUSTOM_ACTIONS)
		if cls.DIRECT_ACTIONS:
			for action, params in host_cap["actions"].iteritems():
				if not action in cls.DIRECT_ACTIONS_EXCLUDE:
					cap_actions[action] = params
		cap_attrs = {}
		for attr, params in cls.CUSTOM_ATTRS.iteritems():
			cap_attrs[attr] = params.info()
		if cls.DIRECT_ATTRS:
			for attr, params in host_cap["attrs"].iteritems():
				if not attr in cls.DIRECT_ATTRS_EXCLUDE:
					cap_attrs[attr] = params
		return {
			"attrs": cap_attrs,
			"actions": cap_actions,
		}
		
	def _getType(self):
		if self.mainConnection():
			return self.mainConnection().type
		for el in self.getElements():
			if el.type == "external_network_endpoint":
				return "fixed_bridge"
		return "bridge"
			
	def info(self):
		if not currentUser().hasFlag(Flags.Debug):
			self.checkRole(Role.user)
		info = {
			"id": self.id,
			"type": self._getType(),
			"state": self.state,
			"attrs": self.attrs.copy(),
			"elements": sorted([el.id for el in self.elements.all()]), #sort elements so that first is from and second is to
			"debug": {
					"host_elements": [(o.host.address, o.num) for o in self.getHostElements()],
					"host_connections": [(o.host.address, o.num) for o in self.getHostConnections()],
			}
		}
		info["attrs"]["host"] = self.connection1.host.address if self.connection1 else None
		info["attrs"]["host_fileserver_port"] = self.connection1.host.hostInfo.get('fileserver_port', None) if self.connection1 else None
		mcon = self.mainConnection()
		if mcon:
			info["attrs"].update(self._adaptAttrs(mcon.attrs["attrs"]))
		return info

		
	def updateUsage(self, now):
		self.totalUsage.updateFrom(now, [el.usageStatistics for el in self.getHostElements()]
								 + [con.usageStatistics for con in self.getHostConnections()])
		
		
def get(id_, **kwargs):
	try:
		con = Connection.objects.get(id=id_, **kwargs)
		return con.upcast()
	except Connection.DoesNotExist:
		return None

def getAll(**kwargs):
	return (con.upcast() for con in Connection.objects.filter(**kwargs))

def create(el1, el2, attrs={}):
	fault.check(el1 != el2, "Cannot connect element with itself")
	fault.check(not el1.connection, "Element #%d is already connected", el1.id)
	fault.check(not el2.connection, "Element #%d is already connected", el2.id)
	fault.check(el1.CAP_CONNECTABLE, "Element #%d can not be connected", el1.id)
	fault.check(el2.CAP_CONNECTABLE, "Element #%d can not be connected", el2.id)
	fault.check(el1.topology == el2.topology, "Can only connect elements from same topology")
	el1.topology.checkRole(Role.manager)	
	con = Connection()
	con.init(el1.topology, el1, el2, attrs)
	con.save()
	con.triggerStart()
	logging.logMessage("create", category="connection", id=con.id)	
	logging.logMessage("info", category="connection", id=con.id, info=con.info())
	return con

from . import fault, currentUser
