"""
	Copyright: (c) 2013 William Forde (willforde+xbmc@gmail.com)
	License: GPLv3, see LICENSE for more details
	
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.
	
	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.
	
	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Call Necessary Imports
import HTMLParser
from xbmcutil import listitem, plugin

class VideosParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.sciencefriday.com/topics/space.html#page/bytopic/1
	"""
	def parse(self, html, contentType):
		""" Parses SourceCode and Scrape Categorys """

		# Class Vars
		self.contentVideo = "video" in contentType
		self.contentType = contentType
		self.divcount = None
		self.section = 0
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		if self.contentVideo: self.item.urlParams["action"] = "PlayVideo"
		else: self.item.urlParams["action"] = "PlayAudio"
		self.item.setQualityIcon(True)
		self.item.setAudioInfo()
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif tag == u"div":
			# Increment div counter when within show-block
			if self.divcount: self.divcount +=1
			else:
				# Convert Attributes to a Dictionary
				attrs = dict(attrs)
				
				# Check for required section
				if u"id" in attrs and attrs[u"id"] == self.contentType: self.divcount = 1
			
		# Fetch video info Block
		elif self.divcount == 3:
			# Check for Title, Plot and Date
			if tag == "h4": self.section = 101
			elif tag == "a":
				# Convert Attributes to a Dictionary
				attrs = dict(attrs)
				# Check for url and title
				if self.section == 102 and u"href" in attrs:
					self.item.urlParams["url"] = attrs[u"href"]
					self.section = 103
		
		# Fetch Image Block
		elif self.divcount == 5 and tag == "img":
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			# Fetch video Image
			if "data-lazysrc" in attrs:
				self.item.setThumbnailImage(attrs["data-lazysrc"])
	
	def handle_data(self, data):
		# When within selected section fetch Time
		if self.section == 101: # Date
			self.item.setDateInfo(data, "%b. %d, %Y")
			self.section = 102
		elif self.section == 103: # Title
			self.item.setLabel(data)
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == u"div" and self.divcount:
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 1:
				self.append(self.item.getListitemTuple(True))
				self.reset_lists()

class RecentParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.sciencefriday.com/video/index.html#page/full-width-list/1
	"""
	def parse(self, html):
		""" Parses SourceCode and Scrape Categorys """

		# Class Vars
		self.divcount = None
		self.section = 0
		self.contentVideo = plugin["type"] == "video"
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		if self.contentVideo: self.item.urlParams["action"] = "PlayVideo"
		else: self.item.urlParams["action"] = "PlayAudio"
		self.item.setQualityIcon(True)
		self.item.setAudioInfo()
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif tag == u"div":
			# Increment div counter when within show-block
			if self.divcount: self.divcount +=1
			else:
				# Convert Attributes to a Dictionary
				attrs = dict(attrs)
				
				# Check for required section
				if u"id" in attrs and attrs[u"id"] == u"full-width-list": self.divcount = 1
			
		# Fetch video info Block
		elif self.divcount == 4:
			# Check for Title, Plot and Date
			if tag == "h4": self.section = 101
			elif tag == "p": self.section = 102
			elif tag == "a":
				# Convert Attributes to a Dictionary
				attrs = dict(attrs)
				# Check for url and title
				if u"href" in attrs:
					self.item.urlParams["url"] = attrs[u"href"]
					self.section = 103
		
		# Fetch Image Block
		elif self.divcount == 5 and tag == "img":
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			# Fetch video Image
			if "data-lazysrc" in attrs:
				self.item.setThumbnailImage(attrs["data-lazysrc"])
	
	def handle_data(self, data):
		# When within selected section fetch Time
		if self.section == 101: # Date
			self.item.setDateInfo(data, "%b. %d, %Y")
			self.section = 0
		elif self.section == 102: # Plot
			self.item.infoLabels["plot"] = data.strip()
			self.section = 0
		elif self.section == 103: # Title
			self.item.setLabel(data)
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == u"div" and self.divcount:
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 1:
				self.append(self.item.getListitemTuple(True))
				self.reset_lists()
