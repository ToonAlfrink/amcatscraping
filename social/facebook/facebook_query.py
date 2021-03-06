# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Affero General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Affero General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

"""
Scrapes any object which matches query, aswell as any post or comment inside any of those objects.
Objects can be people, pages, events, applications, groups, places.
"""


from amcat.scraping.document import Document, HTMLDocument


from urllib import urlencode
#from urlparse import urljoin
from amcat.tools.toolkit import readDate

import json

START_URL = "https://graph.facebook.com/search?q={q}&type={t}"
LOGIN_URL = "https://facebook.com"
OAUTH = "https://graph.facebook.com/oauth/access_token?client_id=518912194794049&client_secret=fbf08cd3b7a6cd23cb4045de03c739fb&grant_type=client_credentials"
COMMENT_URL = "https://graph.facebook.com/{}/comments?acces_token={}"
OBJECT_URL = "https://graph.facebook.com/{}?access_token={}"


TYPES = [
    #"post",
    "page",
    "event",
    "group"
    ]

from django import forms
from amcat.scraping.scraper import HTTPScraper,DBScraper,AuthForm
from datetime import date

class SearchResult(object):
    def __init__(self,data,url,_type):
        self.data = data
        self.url = url
        self.type = _type
    def __str__(self):
        return self.url


class FacebookQueryForm(AuthForm):
    query = forms.CharField()

class FacebookQueryScraper(HTTPScraper, DBScraper):
    options_form = FacebookQueryForm
    medium_name = "Facebook"

    def __init__(self, *args, **kwargs):
        super(FacebookQueryScraper, self).__init__(*args, **kwargs)
        self.options['date'] = date.today()
        self.access_token = self.open(OAUTH).read().split("=")[1]

    def _login(self, username, password):
        self.open(LOGIN_URL) #cookies
        POST_DATA = {
            'email' : username,
            'pass' : password
            }
        result = self.open(LOGIN_URL, urlencode(POST_DATA))

    def _get_units(self):
        for _type in TYPES:
            next_url = START_URL.format(q=self.options['query'],t=_type)
            while True:
                _json = self.open(next_url).read()
                if not _json:
                    break
                data = json.loads(_json)
                for obj in data['data']:
                    yield SearchResult(obj,next_url,_type)
                try:
                    next_url = data['paging']['next']
                except KeyError:
                    break
            
        
    def _scrape_unit(self, result): 

        # (i)page properties: 
        # bytes, page, category, any of the article props

        # article properties: 
        # date, section, pagenr, headline, byline, length (autogenerated),
        # url (already present), text, parent, medium (auto), author

        obj = Document()
        obj.doc = result.data
        obj.props.type = result.type 
        obj.props.fb_id = obj.doc['id']


        _type = result.type
        if _type == "post":
            for post in self.scrape_post(obj):
                yield post
        elif _type == "page":
            for unit in self.scrape_page(obj):
                yield unit
        #...etc... TO DO

        #yield obj
            
    def scrape_post(self,obj):
        obj.props.author = " | ".join(obj.doc['from'].values())
        if 'message' in obj.doc.keys():
            obj.props.text = obj.doc['message']
        else:
            obj.props.text = " "
        obj.props.date = readDate(obj.doc['updated_time'])
        
        if obj.doc['type'] in ["video","photo","link"]:
            obj.props.headline = obj.doc['name']
            if 'link' in obj.doc.keys():
                obj.props.source = obj.doc['link']
        elif obj.doc['type'] != "status":
            
            raise NotImplementedError
            
        yield obj

    def scrape_page(self,obj):
        obj.props.headline = obj.doc['name']
        obj.props.meta = obj.doc
        obj.doc = self.getdoc(OBJECT_URL.format(obj.props.meta['id'],self.access_token))
        yield obj
        # wordt vervolgd


if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.debug_module("amcat.scraping.scraper")
    amcatlogging.debug_module("amcat.scraping.document")
    cli.run_cli(FacebookQueryScraper)

