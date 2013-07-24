#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '0.01'
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

	def __str__(self):
		return '%s %s %s'%(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(self.time)), self.title.encode('utf-8'), self.img)


"""
first post:
<form id="delform" action="/cgi-bin/wakaba.pl/b/" method="post">
  <div id="thread-2524447">
    <span class="filesize">Файл: <a target="_blank" href="/b/src/1351873989666.jpg">1351873989666.jpg</a>  - (<em>54 KB, 401x600</em>)</span>
    &nbsp;<br /> 
    <a target="_blank" href="/b/src/1351873989666.jpg"> <img src="/b/thumb/1351873989666s.jpg" width="133" height="200" alt="54 KB" class="thumb" /></a>
    <a name="2524447"></a>
    <label>
      <input type="checkbox" name="delete" value="2524447" />
      <span class="filetitle">Stranger story</span>
      <span class="postername">Сырно</span>
         Пт 02 ноября 2012 20:33:09
    </label>
    <span class="reflink">
      <a href="javascript:insert('&gt;&gt;2524447')">&#x2116;2524447</a>
    </span>&nbsp;
    <blockquote> <p>Ветер. Резкий&#44; холодный&#44; неприветливый. ... <p><em>2. Ну этих людей. Тем более уже поздно&#44; могут и не так понять меня. Уж лучше пойду в парк&#44; а с утра найду себе новый дом.</em></p>
    </blockquote>

reply:
<table><tbody>
  <tr>
    <td class="doubledash">&gt;&gt;</td>
    <td class="reply" id="reply2524474">
      <a name="2524474"></a>
      <label><input type="checkbox" name="delete" value="2524474" /><span class="replytitle"></span> <span class="commentpostername">Сырно</span>   Пт 02 ноября 2012 20:57:33</label>
      <span class="reflink">  <a href="javascript:insert('&gt;&gt;2524474')">&#x2116;2524474</a> </span>
      &nbsp;  <br /> 
      <span class="filesize">Файл: <a target="_blank" href="/b/src/1351875453692.jpg">1351875453692.jpg</a>  - (<em>80 KB, 599x358</em>)</span>
      &nbsp;<br />
      <a target="_blank" href="/b/src/1351875453692.jpg"> <img src="/b/thumb/1351875453692s.jpg" width="200" height="119" alt="80 KB" class="thumb" /></a>
      <blockquote> <blockquote class="unkfunc">&gt;rpg<br />&gt;gensokyo<br />&gt;гг=imbalanced magi</blockquote>  </blockquote>
    </td>
  </tr></tbody>
</table>
"""

class Iichan_parser(object):
	def __init__(self):
		super(Iichan_parser, self).__init__()
		self.doc = None


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

	def html_data(self, url):
		page = urllib.urlopen(url)
		return page.read()
		'''
		fn = url.split('/')[-1]
		f = open(fn, 'w')
		f.write(html_data)
		f.close()

		return open(url.split('/')[-1], 'r').read()
		'''

	def thread_id(self, html_data):
		#tid = url.split('/')[-1].split('.')[0]
		sign = 'id="thread-'
		idx = html_data.find(sign)
		idx += len(sign)
		i = 0
		while html_data[idx+i] in '0123456789':
			i+=1
		tid = html_data[idx:idx+i]
		return tid


	def parse_data(self, html_data, tid=None):
		if tid == None:
			tid = self.thread_id(html_data)

		self.doc = lxml.html.document_fromstring(html_data)
		start_post = self.doc.get_element_by_id('thread-%s'%tid, None)
		posts = [Post(), ]
		for el in start_post.iterchildren():
			if 'label' == el.tag:
				posts[0] = self.parse_post_title(el, posts[0])
			elif 'blockquote' == el.tag:
				posts[0].post = el.text_content
			elif 'a' == el.tag:
				posts[0] = self.parse_post_img(el, posts[0])
			elif 'table' == el.tag:
				reply = None
				for el2 in el.find_class('reply')[0].iterchildren():
					if 'label' == el2.tag:
						reply = self.parse_post_title(el2, reply)
					elif 'blockquote' == el2.tag:
						if reply == None:
							reply = Post()
						reply.post = el2.text_content
					elif 'a' == el2.tag:
						reply = self.parse_post_img(el2, reply)
				if reply != None:
					posts.append(reply)

		return posts		

	def parse_url(self, url):
		html_data = self.html_data(url)
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

	def save_local(self, url, path=None, suffix=None):
		html_data = self.html_data(url)
		tid = self.thread_id(html_data)
		posts = self.parse_data(html_data, tid)

		parsed_uri = urlparse.urlparse(url)
		host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

		html_file_prefix = '%s_files/'%tid
		if path <> None:
			files_path = '%s/%s'%(path, html_file_prefix)
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
			print l.items()
		print tid
		for l in self.doc.findall(".//script"):
			for attr in l.items():
				if 'src' == attr[0]:
					(ex_url, fn) = self.url_to_filename(attr[1], url, files_path)
					if not os.path.exists(files_path + fn):
						print 'Downloading... %s'%ex_url
						urllib.urlretrieve(ex_url, files_path + fn)
					l.attrib['src'] = html_file_prefix + fn
			print l.items()

		html_data = lxml.etree.tostring(self.doc)
		# download images and replace urls in posts
		for p in posts:
			if p.thumb <> None:
				(ex_url, fn) = self.url_to_filename(p.thumb, url, files_path)
				if not os.path.exists(files_path + fn):
					print 'Downloading... %s'%ex_url
					urllib.urlretrieve(ex_url, files_path + fn)
				html_data = html_data.replace('=\"%s\"'%p.thumb, '=\"%s%s\"'%(html_file_prefix, fn))
			if p.img <> None:
				(ex_url, fn) = self.url_to_filename(p.img, url, files_path)
				if not os.path.exists(files_path + fn):
					print 'Downloading... %s'%ex_url
					urllib.urlretrieve(ex_url, files_path + fn)
				html_data = html_data.replace('=\"%s\"'%p.img, '=\"%s%s\"'%(html_file_prefix, fn))

		fn = '%s.html'%tid
		if suffix <> None:
			fn = '%s_%s.html'%(tid, suffix)
		if path <> None:
			fn = '%s/%s'%(path, fn)
		f = open(fn, 'w')
		f.write(html_data)
		f.close()



if __name__=='__main__':
	ip = Iichan_parser()
	#ip.save_local('http://gensokyo.4otaku.org/arch/b/res/2524447.html')
	#ip.save_local('http://iichan.hk/b/res/2716929.html')
	#ip.save_local('http://iichan.hk/b/res/2811895.html')

	#ip.save_local('http://iichan.hk/to/res/148288.html', path='to')
	ip.save_local('http://iichan.hk/b/res/2814234.html', path='b', suffix='научно-фантастические_мысли')

