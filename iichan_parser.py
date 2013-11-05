#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '0.02'
__author__ = 'Andrey Derevyagin'
__copyright__ = 'Copyright © 2013'


import lxml.html
import urllib
import re
import sys
import time
import string
import urlparse
import os
import shutil


class Post(object):
	"""docstring for Post"""
	def __init__(self):
		super(Post, self).__init__()
		self.title = ''
		self.poster = ''
		self.time = 0
		self.post = None
		self.thumb = None
		self.img = None
		self.id = None
		self.lxml_data = None

	def __str__(self):
		return '%s %s %s'%(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(self.time)), self.title.encode('utf-8'), self.img)


class Iichan_parser(object):
	def __init__(self):
		super(Iichan_parser, self).__init__()
		self.doc = None
		self.copy_wakaba3_js = False
		self.posts = None
		self.path = None
		self.suffix = None
		self.use_local = False


	def parse_post_title(self, label, post=None):
		if post==None:
			post = Post()
		text = label.text_content()
		for el in label.iterchildren():
			# check title & poster name
			if 'span' == el.tag:
				for attr in el.items():
					if 'class' == attr[0]:
						if 'filetitle' == attr[1] or 'replytitle' == attr[1]:
							post.title = el.text_content().strip()
						if 'postername' == attr[1] or 'commentpostername' == attr[1]:
							post.poster = el.text_content().strip()
			if 'input' == el.tag:
				pid = None
				c = 0
				for attr in el.items():
					if ('type' == attr[0] and 'checkbox' == attr[1]) or ('name' == attr[0] and 'delete' == attr[1]):
						c += 1
					if 'value' == attr[0] and attr[1].isdigit():
						pid = int(attr[1])
				if c == 2 and pid <> None:
					post.id = pid

			tmp = el.text_content().strip()
			if len(tmp)>0:
				p = text.find(tmp)
				if p == 0:
					text = text[p+len(tmp):].strip()
				elif p > 0:
					text = ('%s%s'%(text[:p-1],text[p+len(tmp):])).strip()
		#print 
		#print text
		srch = re.compile('(\d{2})\s+([^\s]+)\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})').search(text)
		if srch!=None:
			gr = srch.groups()
			month_dict = {
				u'января': 'January',
				u'февраля': 'February',
				u'марта': 'March',
				u'апреля': 'April',
				u'мая': 'May',
				u'июня': 'June',
				u'июля': 'July',
				u'августа': 'August',
				u'сентября': 'September',
				u'октября': 'October',
				u'ноября': 'November',
				u'декабря': 'December',
			}
			if not month_dict.has_key(gr[1]):
				print 'Month name error: %s'%gr[1]
				sys.exit(1)
			post.time = int(time.mktime(time.strptime('%s %s %s %s:%s:%s'%(gr[2], month_dict[gr[1]], gr[0], gr[3], gr[4], gr[5]), '%Y %B %d %H:%M:%S')))# - time.timezone
			#print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(post.time))
		return post

	def parse_post_img(self, a, post=None):
		for el in a.iterchildren():
			if 'img' == el.tag:
				for attr in el.items():
					if 'class' == attr[0] and 'thumb' == attr[1]:
						if post == None:
							post = Post()
						for attr2 in el.items():
							if 'src' == attr2[0]:
								post.thumb = attr2[1]
								break
						for attr2 in a.items():
							if 'href' == attr2[0]:
								post.img = attr2[1]
								break
						break
		return post

	def build_thread_html_filename(self, tid):
		fn = '%s.html'%tid
		if self.suffix <> None:
			fn = '%s_%s.html'%(tid, self.suffix)
		if self.path <> None:
			fn = '%s/%s'%(self.path, fn)
		return fn

	def html_data(self, url, ignore_local=False):
		page = None
		if ignore_local==False and self.use_local:
			tid = self.thread_id_from_url(url)
			fn = self.build_thread_html_filename(tid)
			if os.path.exists(fn):
				page = open(fn, 'r').read()
		if page==None:
			page = urllib.urlopen(url)
			code = page.getcode()
			if code == 200:
				return page.read()
			else:
				return code
		return page
		'''
		fn = url.split('/')[-1]
		f = open(fn, 'w')
		f.write(html_data)
		f.close()

		return open(url.split('/')[-1], 'r').read()
		'''

	def thread_id_from_url(self, url):
		return url.split('/')[-1].split('.')[0]

	def thread_id(self, html_data):
		sign = 'id="thread-'
		idx = html_data.find(sign)
		idx += len(sign)
		i = 0
		while html_data[idx+i] in '0123456789':
			i+=1
		tid = html_data[idx:idx+i]
		return tid

	def stringify_children(self, node):
		rv = lxml.etree.tostring(node, encoding='utf-8', method='html').strip()
		return rv[len('<blockquote>'):-1*len('</blockquote>')].strip()

	def parse_data(self, html_data, tid=None):
		if tid == None:
			tid = self.thread_id(html_data)

		self.doc = lxml.html.document_fromstring(html_data)
		start_post = self.doc.get_element_by_id('thread-%s'%tid, None)
		posts = [Post(), ]
		posts[0].lxml_data = start_post
		for el in start_post.iterchildren():
			if len(posts) == 1:
				if 'label' == el.tag:
					posts[0] = self.parse_post_title(el, posts[0])
				elif 'blockquote' == el.tag:
					posts[0].post = self.stringify_children(el) #el.text_content
				elif 'a' == el.tag:
					posts[0] = self.parse_post_img(el, posts[0])
			if 'table' == el.tag:
				reply = None
				for el2 in el.find_class('reply')[0].iterchildren():
					if 'label' == el2.tag:
						reply = self.parse_post_title(el2, reply)
					elif 'blockquote' == el2.tag:
						if reply == None:
							reply = Post()
						reply.post = self.stringify_children(el.find('.//blockquote')) #el2.text_content
					elif 'a' == el2.tag:
						reply = self.parse_post_img(el2, reply)
				if reply != None:
					reply.lxml_data = el
					posts.append(reply)

		return posts		

	def parse_url(self, url):
		html_data = self.html_data(url)
		if not isinstance(html_data, int):
			return self.parse_data(html_data)

	def url_to_filename(self, url, source_url, files_path):
		expanded_url = url
		if expanded_url[0] == '/':
			parsed_uri = urlparse.urlparse(source_url)
			host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
			expanded_url = host+url
		elif expanded_url[0] == '.':
			path = '/'.join(source_url.split('/')[:-1])
			expanded_url = '%s/%s'%(path, url)
		fn = url.split('/')[-1]
		#fn = '%s/%s'%(files_path, fn)
		return (expanded_url, fn)

	def __replace_href_src(self, tag, old, new):
		for attr in tag.items():
			if ('href' == attr[0] or 'src' == attr[0]) and attr[1] == old:
				tag.attrib[attr[0]] = new
				break
		for t in tag.iterchildren():
			if 'table' <> t.tag:
				self.__replace_href_src(t, old, new)

	def save_local(self, url, path=None, suffix=None):
		self.path = path
		self.suffix = suffix
		html_data = self.html_data(url, True)
		if isinstance(html_data, int):
			return html_data
		tid = self.thread_id(html_data)
		self.posts = self.parse_data(html_data, tid)

		parsed_uri = urlparse.urlparse(url)
		host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

		html_file_prefix = '%s_files/'%tid
		if self.path <> None:
			files_path = '%s/%s'%(self.path, html_file_prefix)
		else:
			files_path = html_file_prefix
		if not os.path.exists(files_path) or not os.path.isdir(files_path):
			os.makedirs(files_path)

		# download css & js
		for l in self.doc.findall(".//link"):
			for attr in l.items():
				if 'href' == attr[0]:
					(ex_url, fn) = self.url_to_filename(attr[1], url, files_path)
					if not os.path.exists(files_path + fn):
						print 'Downloading... %s'%ex_url
						urllib.urlretrieve(ex_url, files_path + fn)
					l.attrib['href'] = html_file_prefix + fn
		for l in self.doc.findall(".//script"):
			for attr in l.items():
				if 'src' == attr[0]:
					(ex_url, fn) = self.url_to_filename(attr[1], url, files_path)
					if not os.path.exists(files_path + fn):
						if fn == 'wakaba3.js' and self.copy_wakaba3_js and os.path.exists(fn):
							print 'Copy... %s'%fn
							shutil.copyfile(fn, files_path + fn)
						else:
							print 'Downloading... %s'%ex_url
							urllib.urlretrieve(ex_url, files_path + fn)
					l.attrib['src'] = html_file_prefix + fn

		html_data = lxml.etree.tostring(self.doc, encoding='utf-8', method='html')
		#html_data = lxml.etree.tostring(self.doc)
		# download images and replace urls in posts
		for p in self.posts:
			if p.thumb <> None:
				(ex_url, fn) = self.url_to_filename(p.thumb, url, files_path)
				if not os.path.exists(files_path + fn):
					print 'Downloading... %s'%ex_url
					urllib.urlretrieve(ex_url, files_path + fn)
				#html_data = html_data.replace('=\"%s\"'%p.thumb, '=\"%s%s\"'%(html_file_prefix, fn))
				self.__replace_href_src(p.lxml_data, p.thumb, '%s%s'%(html_file_prefix, fn))
			if p.img <> None:
				(ex_url, fn) = self.url_to_filename(p.img, url, files_path)
				if not os.path.exists(files_path + fn):
					print 'Downloading... %s'%ex_url
					urllib.urlretrieve(ex_url, files_path + fn)
				#html_data = html_data.replace('=\"%s\"'%p.img, '=\"%s%s\"'%(html_file_prefix, fn))
				self.__replace_href_src(p.lxml_data, p.img, '%s%s'%(html_file_prefix, fn))

		# prepare document
		# delete post form
		post_form = self.doc.get_element_by_id('postform')
		if post_form != None:
			post_form.getparent().remove(post_form)
		for del_form in self.doc.find_class('userdelete'):
			del_form.getparent().remove(del_form)

		# add '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />'
		meta = lxml.etree.Element('meta', content='text/html;charset=utf-8')
		meta.attrib['http-equiv'] = 'Content-Type'
		self.doc.find('head').find('title').addnext(meta)

		fn = self.build_thread_html_filename(tid)
		f = open(fn, 'w')
		f.write(lxml.html.tostring(self.doc, encoding='UTF-8', method="html", pretty_print=False))
		f.close()

		return 0


if __name__=='__main__':
	ip = Iichan_parser()
	ip.copy_wakaba3_js = True
	#ip.save_local('http://iichan.hk/to/res/140802.html', path='to')
	#ip.save_local('http://iichan.hk/b/res/2816200.html', path='b', suffix='cписок_неймфагов')
	#ip.save_local('http://iichan.hk/o/res/19273.html', path='o', suffix='Алиса')
	ip.save_local('http://iichan.hk/to/arch/res/70160.html', path='to', suffix='Рейму_одинокая')

	"""
	### JaTT
	ip.save_local('http://iichan.hk/b/arch/res/1985140.html', suffix='JaTT_01', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/1992801.html', suffix='JaTT_02', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/1997646.html', suffix='JaTT_03', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2003765.html', suffix='JaTT_04', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2011828.html', suffix='JaTT_05', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2020107.html', suffix='JaTT_06', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2027033.html', suffix='JaTT_07', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2037243.html', suffix='JaTT_08', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2045885.html', suffix='JaTT_09', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2056256.html', suffix='JaTT_10', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2063007.html', suffix='JaTT_11', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2067652.html', suffix='JaTT_12', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2073394.html', suffix='JaTT_13', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2079467.html', suffix='JaTT_14', path='b/Just another Touhou thread')
	ip.save_local('http://iichan.hk/b/arch/res/2088750.html', suffix='JaTT_15', path='b/Just another Touhou thread')

	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2093892.html', suffix='JaTT_16', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2105188.html', suffix='JaTT_17', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2115341.html', suffix='JaTT_18', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2131564.html', suffix='JaTT_19', path='b/Just another Touhou thread')

	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2136719.html', suffix='JaTT_20', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2143503.html', suffix='JaTT_21', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2149494.html', suffix='JaTT_22', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2155312.html', suffix='JaTT_23', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2160194.html', suffix='JaTT_24', path='b/Just another Touhou thread')

	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2171945.html', suffix='JaTT_25', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2193149.html', suffix='JaTT_26', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2206373.html', suffix='JaTT_27', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2215979.html', suffix='JaTT_28', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2223862.html', suffix='JaTT_29', path='b/Just another Touhou thread')

	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2228397.html', suffix='JaTT_30', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2238293.html', suffix='JaTT_31', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2248241.html', suffix='JaTT_32', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2279232.html', suffix='JaTT_33', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2300134.html', suffix='JaTT_34', path='b/Just another Touhou thread')

	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2356400.html', suffix='JaTT_35', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2363770.html', suffix='JaTT_36', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2374045.html', suffix='JaTT_37', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2389566.html', suffix='JaTT_38', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2400252.html', suffix='JaTT_39', path='b/Just another Touhou thread')

	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2418761.html', suffix='JaTT_40', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2430713.html', suffix='JaTT_41', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2462521.html', suffix='JaTT_42', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2491116.html', suffix='JaTT_43', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2527969.html', suffix='JaTT_44', path='b/Just another Touhou thread')

	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2550876.html', suffix='JaTT_45', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2583675.html', suffix='JaTT_46', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2608355.html', suffix='JaTT_47', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2639989.html', suffix='JaTT_48', path='b/Just another Touhou thread')
	ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2705302.html', suffix='JaTT_49', path='b/Just another Touhou thread')
	"""
