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

from urlparse import urljoin
from datetime import datetime

from amcat.scraping.scraper import HTTPScraper
from amcat.models.medium import Medium


UNIT_FILE = open('maroc_units.txt', 'a+')
START_AT=('wie-schrijft-blijft',2)

class MarocScraper(HTTPScraper):
    medium_name = "marokko.nl"
    index_url = "http://www.maroc.nl/forums/forum.php"

    def _get_units(self):
        self.medium = Medium.get_or_create(self.medium_name)
        """        doc = self.getdoc(self.index_url)
        skip = True
        for li in doc.cssselect("ol.childforum li.forumbit_post"):
            forum_url = urljoin(doc.base_url,li.cssselect("h2.forumtitle a")[0].get('href'))
            if START_AT[0] in forum_url:
                skip = False
            if skip:
                continue
            for page in self.__get_pages(forum_url):
                for li in page.cssselect("#threads li.threadbit"):
                    try:
                        unit = li.cssselect("h3.threadtitle a")[0].get('href')
                    except IndexError as e:
                        print(e)
                    else:
                        print(unit, file=UNIT_FILE)
                        yield unit"""
        units = set(map(str.strip, UNIT_FILE.readlines()))
        for unit in units:
            yield unit

    def __get_pages(self, url):
        firsturl = url + "?daysprune=-1"
        doc = self.getdoc(firsturl)
        yield doc
        n_subjects = int(doc.cssselect("#threadpagestats")[0].text.strip().split()[-1])
        n_pages = n_subjects / 20 + 1
        startpage = 2
        if START_AT[0] in url:
            startpage = START_AT[1]
        for pagenr in range(startpage,n_pages + 1):
            yield self.getdoc(url + "index{}.html?daysprune=-1".format(pagenr))

    def _scrape_unit(self, thread_url):
        pages = list(self.__get_thread_pages(thread_url))
        op = self.__get_op(pages[0])
        for page in pages[1:]:
            op['children'].extend(list(self.__get_posts(page)))
        yield op

    def __get_posts(self, doc):
        for li in doc.cssselect("#posts li.postcontainer"):
            post = {
                'date' : self.__get_date(li.cssselect("span.date")[0].text_content()),
                'headline' : li.cssselect("h2.title")[0].text_content(),
                'externalid' : int(li.cssselect("a.postcounter")[0].get('name').split("post")[1]),
                'text' : li.cssselect("blockquote.postcontent")[0].text_content(),
                'author' : li.cssselect("a.username strong")[0].text,
                'children' : [],
                'medium' : self.medium,
                'project' : self.options['project']
                }
            yield post

    def __get_op(self, doc):
        posts = list(self.__get_posts(doc))
        op = posts[0]
        op['children'] = posts[1:]
        op['section'] = doc.base_url.split("/")[4]
        op['url'] = doc.base_url
        return op

    def __get_date(self, string):
        today = datetime.today()
        if "Gisteren" in string:
            yesterday = today - timedelta(days = 1)
            year, month, day = yesterday.year, yesterday.month, yesterday.day
        elif "Vandaag" in string:
            year, month, day = today.year, today.month, today.day
        else:
            day, month, year = map(int, string.split(",")[0].split("-"))
            year += 2000
        hour, minute = map(int, string.split(",")[1].split(":"))
        return datetime(year, month, day, hour, minute)

    def __get_thread_pages(self, url):
        doc = self.getdoc(url)
        yield doc
        n_subjects = int(doc.cssselect("#postpagestats_above")[0].text.strip().split()[-1])
        n_pages = n_subjects / 10 + 1
        for pagenr in range(2,n_pages + 1):
            page_url = url.split(".html")[0] + "-{}".format(pagenr) + ".html"
            yield self.getdoc(page_url)

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(MarocScraper)


