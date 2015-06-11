from ..db import *
from ..lib import logging, error
import time
from . import HostObject

class HostElement(HostObject):
	"""
	:type connection: ..connection.HostConnection
	"""
	connection = ReferenceField('HostConnection') #reverse_delete_rule=NULLIFY defined at bottom of connection.py
	parent = ReferenceField('self', reverse_delete_rule=DENY)
	meta = {
		'collection': 'host_element',
		'indexes': [
			('host', 'num')
		]
	}

	@property
	def children(self):
		return HostElement.objects(parent=self)

	def createChild(self, type_, attrs=None, ownerConnection=None, ownerElement=None):
		if not attrs: attrs = {}
		return self.host.createElement(type_, self, attrs, ownerConnection=ownerConnection, ownerElement=ownerElement)

	def connectWith(self, hel, type_=None, attrs=None, ownerConnection=None, ownerElement=None):
		if not attrs: attrs = {}
		return self.host.createConnection(self, hel, type_, attrs, ownerConnection=ownerConnection,
										  ownerElement=ownerElement)

	def modify(self, attrs):
		logging.logMessage("element_modify", category="host", host=self.host.name, id=self.num, attrs=attrs)
		try:
			self.objectInfo = self.host.getProxy().element_modify(self.num, attrs)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing element", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code == error.UserError.INVALID_STATE:
				self.updateInfo()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("element_info", category="host", host=self.host.name, id=self.num, info=self.objectInfo)
		self.save()

	def action(self, action, params=None):
		if not params: params = {}
		logging.logMessage("element_action begin", category="host", host=self.host.name, id=self.num, action=action,
						   params=params)
		try:
			res = self.host.getProxy().element_action(self.num, action, params)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing element", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code == error.UserError.INVALID_STATE:
				self.updateInfo()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("element_action end", category="host", host=self.host.name, id=self.num, action=action,
						   params=params, result=res)
		self.updateInfo()
		return res

	def remove(self):
		try:
			logging.logMessage("element_remove", category="host", host=self.host.name, id=self.num)
			self.host.getProxy().element_remove(self.num)
		except error.UserError, err:
			if err.code != error.UserError.ENTITY_DOES_NOT_EXIST:
				self.host.incrementErrors()
		except:
			self.host.incrementErrors()
		self.delete()
		self.usageStatistics.delete()

	def getConnection(self):
		return self.connection

	def updateInfo(self):
		try:
			self.objectInfo = self.host.getProxy().element_info(self.num)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing element", category="host", host=self.host.name, id=self.num)
				self.remove()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("element_info", category="host", host=self.host.name, id=self.num, info=self.objectInfo)
		self.save()

	def info(self):
		return self.objectInfo

	def getAttrs(self):
		return self.objectInfo["attrs"]

	def getAllowedActions(self):
		try:
			caps = self.host.getElementCapabilities(self.type)["actions"]
			res = []
			for key, states in caps.iteritems():
				if self.state in states:
					res.append(key)
			return res
		except:
			self.host.incrementErrors()
			logging.logException(host=self.host.name)
			return []

	def getAllowedAttributes(self):
		caps = self.host.getElementCapabilities(self.type)["attrs"]
		ret = dict(filter(lambda attr: not "states" in attr[1] or self.state in attr[1]["states"], caps.iteritems()))
		return ret

	def updateAccountingData(self, data):
		self.usageStatistics.importRecords(data)
		self.usageStatistics.removeOld()

	def synchronize(self):
		try:
			if not self.topologyElement and not self.topologyConnection:
				self.remove()
				return
			self.modify({"timeout": time.time() + 14 * 24 * 60 * 60})
		except error.UserError, err:
			if err.code != error.UserError.UNSUPPORTED_ATTRIBUTE:
				raise
		except:
			logging.logException(host=self.host.address)
