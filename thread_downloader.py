#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '0.01'
__author__ = 'Andrey Derevyagin'
__copyright__ = 'Copyright © 2013'


import sys
import os
import json
from iichan_parser import Post, Iichan_parser

if __name__=='__main__':
	script_path = os.path.dirname(os.path.realpath(__file__))
	os.chdir(script_path)

	try:
		settings = __import__('settings')
	except ImportError:
		print 'Error import module "settings", see settings.py.template'
		sys.exit(1)
	threads = getattr(settings, 'threads')

	status_fn = 'status'
	status = {}
	if os.path.exists(status_fn):
		status = json.loads(open(status_fn, 'r').read())
	
	symbols = (u"абвгдеёзийклмнопрстуфхцчъыьэАБВГДЕЁЗИЙКЛМНОПРСТУФХЦЧЪЫЬЭ",
    	       u"abvgdeezijklmnoprstufhc4'y'eABVGDEEZIJKLMNOPRSTUFHC4'Y'E")
	tr = {ord(a):ord(b) for a, b in zip(*symbols)}

	parser_param_names = ['url', 'path', 'suffix']
	ip = Iichan_parser()
	ip.copy_wakaba3_js = True
	for th in threads:
		status_key = th['url']
		print status_key
		st = 'active'
		frequency = 0
		if status.has_key(status_key):
		 	if status[status_key].has_key('status'):
				st = status[status_key]['status']
		 	if status[status_key].has_key('frequency'):
				frequency = status[status_key]['frequency']
		else:
			status[status_key] = {}

		if th.has_key('suffix'):
			status[status_key]['suffix'] = unicode(th['suffix'], 'utf-8').translate(tr)

		if th.has_key('path') and not os.path.exists(th['path']):
			os.makedirs(th['path'])

		if st.lower() == 'active':
			if frequency < 1:
				prms = {}
				for key in parser_param_names:
					if th.has_key(key):
						prms[key] = th[key]
				code = ip.save_local(**prms)
				if code <> 0:
					status[status_key]['status'] = 'code %d'%code
				else:
					posts_count = len(ip.posts)
					if status[status_key].has_key('posts') and status[status_key]['posts'] == posts_count:
						pass
					else:
						# changed post count from last check event
						status[status_key]['posts'] = posts_count
				frequency = 1
				if th.has_key('frequency'):
					frequency = th['frequency']
				status[status_key]['frequency'] = frequency-1
			else:
				frequency -= 1
				status[status_key]['frequency'] = frequency

	status_str = json.dumps(status, sort_keys=True, indent=4, separators=(',', ': '))
	f = open(status_fn, 'w')
	f.write(status_str.encode('utf-8'))
	f.close()


