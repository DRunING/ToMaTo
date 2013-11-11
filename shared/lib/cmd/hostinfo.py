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

from . import run, CommandError, getDpkgVersionStr 
import platform, os, time
from ... import config

_cache = {}
def cached(fn):
	def call(*args, **kwargs):
		if fn.__name__ in _cache:
			return _cache[fn.__name__]
		res = fn(*args, **kwargs)
		_cache[fn.__name__] = res
		return res
	call.__name__ = fn.__name__
	call.__doc__ = fn.__doc__
	call.__dict__.update(fn.__dict__)
	return call

@cached
def cpuinfo():
	with open("/proc/cpuinfo", "r") as fp:
		bogomips = []
		models = []
		for line in fp:
			if line.startswith("bogomips"):
				bogomips.append(float(line.split()[2]))
			if line.startswith("model name"):
				models.append(line.split(":")[1].strip())
	return {"count": len(models), "bogomips_avg": sum(bogomips)/len(bogomips), "model": models[0]}

def meminfo():
	with open("/proc/meminfo", "r") as fp:
		data = {}
		for line in fp:
			key, value = line.split(":")
			data[key.lower()] = int(value.strip().split()[0])
		return {"total": data["memtotal"], "used": (data["memtotal"]-data["memfree"]-data["cached"]-data["buffers"])}
	
def loadavg():
	with open("/proc/loadavg", "r") as fp:
		return map(float, fp.readline().split()[:3])
	
def uptime():
	with open("/proc/uptime", "r") as fp:
		return float(fp.readline().split()[0])

@cached
def hostmanagerVersion():
	return getDpkgVersionStr("tomato-hostmanager")

@cached
def system():
	pve_ver = getDpkgVersionStr("pve-manager")
	return {
		"kernel": platform.release(),
		"distribution": ("proxmox", pve_ver, "") if pve_ver else platform.dist(),
		"python": platform.python_version(),
		"processor": platform.machine()
	}

def diskinfo(path):
	out = run(["df", path])
	data = out.splitlines()[1].split()
	return {"total": data[1], "used": data[2], "free": data[3]}

def problems():
	problems = []
	for disk in [config.DATA_DIR]:
		probs = diskproblems(disk)  
		if probs:
			problems.append("Disk: %s on %s" % (probs, disk))
	return problems

def diskproblems(path):
	testFile = os.path.join(path, ".test")
	testData = str(time.time())
	match = False
	try:
		with open(testFile, "w") as fp:
			fp.write(testData)
	except:
		return "Failed to write"
	try:
		with open(testFile, "r") as fp:
			match = fp.read() == testData
	except:
		return "Failed to read"
	try:
		os.unlink(testFile)
	except:
		return "Failed to delete"
	if not match:
		return "Read wrong data"
	return None