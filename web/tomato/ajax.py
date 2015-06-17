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

from lib import wrap_json

@wrap_json
def topology_info(api, id): #@ReservedAssignment
	info = api.topology_info(id, True)
	return info

@wrap_json
def topology_modify(api, id, **attrs): #@ReservedAssignment
	info = api.topology_modify(id, attrs)
	return info

@wrap_json
def topology_action(api, id, action, params={}): #@ReservedAssignment
	res = api.topology_action(id, action, params)
	info = api.topology_info(id)
	return (res, info)

@wrap_json
def topology_remove(api, id): #@ReservedAssignment
	return api.topology_remove(id)

@wrap_json
def topology_permission(api, id, user, permission): #@ReservedAssignment
	return api.topology_permission(id, user, permission)

@wrap_json
def element_create(api, topid, type, parent=None, **attrs): #@ReservedAssignment
	info = api.element_create(topid, type, parent, attrs)
	return info

@wrap_json
def element_info(api, id, fetch=False): #@ReservedAssignment
	info = api.element_info(id, fetch)
	return info

@wrap_json
def element_modify(api, id, **attrs): #@ReservedAssignment
	info = api.element_modify(id, attrs)
	return info

@wrap_json
def element_action(api, id, action, params={}): #@ReservedAssignment
	res = api.element_action(id, action, params)
	info = api.element_info(id)
	return (res, info)

@wrap_json
def element_remove(api, id): #@ReservedAssignment
	res = api.element_remove(id)
	return res

@wrap_json
def connection_create(api, elements, **attrs):
	info = api.connection_create(elements[0], elements[1], attrs)
	return info

@wrap_json
def connection_info(api, id, fetch=False): #@ReservedAssignment
	info = api.connection_info(id, fetch)
	return info

@wrap_json
def connection_modify(api, id, **attrs): #@ReservedAssignment
	info = api.connection_modify(id, attrs)
	return info

@wrap_json
def connection_action(api, id, action, params={}): #@ReservedAssignment
	res = api.connection_action(id, action, params)
	info = api.connection_info(id)
	return (res, info)

@wrap_json
def connection_remove(api, id): #@ReservedAssignment
	res = api.connection_remove(id)
	return res

@wrap_json
def account_info(api, name):
	res = api.account_info(name)
	return res
