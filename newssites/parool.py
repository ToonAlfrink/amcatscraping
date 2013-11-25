# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
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

import re
import datetime
from urlparse import urljoin
from urllib2 import HTTPError

from amcat.scraping.scraper import HTTPScraper, DatedScraper
from amcat.scraping.document import HTMLDocument
from amcat.scraping.htmltools import create_cc_cookies

from amcat.tools import toolkit
from amcat.tools.toolkit import readDate

INDEX_URL = "http://www.parool.nl/parool/article/pagedListContent.do?language=nl&navigationItemId=1&page={pagenr}"

class ParoolScraper(HTTPScraper, DatedScraper):
    medium_name = "Parool website"
    def _set_cookies(self):
        for cookie in create_cc_cookies(".parool.nl"):
            self.opener.cookiejar.set_cookie(cookie)

    def _get_units(self):
        self._set_cookies()
        i = 0
        while True:
            index = self.getdoc(INDEX_URL.format(pagenr = i))
            for li in index.cssselect("ul.list_node li"):
                date = readDate(li.cssselect("a")[-1].text.strip(")( ")).date()
                if date == self.options['date']:
                    yield urljoin(index.url, li.cssselect("h3 a")[0].get('href'))
                elif date <= self.options['date']:
                    return
            i += 1
            
    def _scrape_unit(self, url):
        page = HTMLDocument(url = url)
        page.prepare(self)
        page.props.headline = page.doc.cssselect("#art_box2 h1")[0].text_content()
        for h1 in page.doc.cssselect("h1"):
            h1.drop_tree()
        page.props.author = self.getauthor(page.doc)
        page.props.text = page.doc.cssselect("#art_box2 p")
        page.props.date = readDate(page.doc.cssselect("div.time_post")[0].text.split("Bron:")[0])
        page.props.section = re.search("parool/nl/[0-9]+/([A-Z\-]+)/article", page.props.url).group(1).capitalize()
        yield page

    def getauthor(self, doc):
        author = doc.cssselect("div.time_post")[0].text.split(":")[-1].strip()
        if author.endswith(" uur"):
            author = None
        author_re = re.search("\(Door\: ([\w ]+)\)", doc.cssselect("#art_box2")[0].text_content())
        if author_re:
            author = author_re.group(1)
        return author
        

if __name__ == '__main__':
    import sys
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.debug_module("amcat.scraping.scraper")
    amcatlogging.debug_module("amcat.scraping.document")
    cli.run_cli(ParoolScraper)
