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

from amcat.scraping.document import HTMLDocument
from amcat.scraping.scraper import HTTPScraper, DatedScraper
from amcat.tools.toolkit import readDate

class FoodLogScraper(HTTPScraper, DatedScraper):
    medium_name = "foodlog.nl"
    index_url = "http://foodlog.nl"
    section_url = "{section_url}P{offset}"

    def _get_units(self):
        section_urls = ["http://foodlog.nl/short-news/"]
        section_urls.extend(list(self._getsections()))
        for section_url in section_urls:
            offset = 0
            url = self.section_url.format(**locals())
            doc =  self.getdoc(url)
        
            for url in self._extract(doc): #first page
                if not url: #date < given date
                    break
                yield url

            if doc.cssselect("div.paging"):
                #iterate through pages, 25 articles/page
                while True:
                    br = False
                    offset += 25
                    doc = self.getdoc(self.section_url.format(**locals()))
                    #if offset is out of bounds, page returns first page which we don't want
                    page = doc.cssselect("div.paging div.holder strong")
                    if page and page[0].text == "1":
                        break
                    for url in self._extract(doc):
                        if not url:
                            break
                        yield url
                    if not url:
                        break

    def _getsections(self):
        #get sections from whole webpage, crawler-style
        urls = set([self.index_url])
        for x in range(1):
            for url in list(urls):
                urls.update(self._getlinks(url))
        for url in urls:
            if "/artikel/overzicht/meer/" in url:
                yield url

    def _getlinks(self, url):
        #get anchors from one html doc
        try:
            doc = self.getdoc(url)
        except Exception:
            return
        links = [a.get('href') for a in doc.cssselect("a")]
        print("found {n} links in {url}".format(n = len(links), **locals()))
        for link in links:
            if link:
                yield urljoin(url, link)

    def _extract(self, doc):
        #get articles from section page. return False if out of date bounds
        for li in doc.cssselect("#content ul li"):
            if "short-news" in doc.url:
                url = li.cssselect("div.text-holder a")[0].get('href')
                date = readDate(self.getdoc(url).cssselect("#content em.date a")[0].text)
            else:
                url = li.cssselect("div.heading a")[0].get('href')
                date = readDate(li.cssselect("em.date a")[0].text)
            if date.date() < self.options['date']:
                yield False
            if date.date() == self.options['date']:
                yield url

    def _scrape_unit(self, url):
        article = HTMLDocument(url = url)
        article.prepare(self)
        if "short-news" in url:
            container = "#main"
        else:
            container = "#content"

        article.props.text = article.doc.cssselect("{container} ul.post div.block-content".format(**locals()))[0]
        article.props.date = readDate(article.doc.cssselect("#content div.block-post em.date")[0].text_content())
        article.props.section = article.doc.cssselect("#content a h2")[0].text
        article.props.headline = article.doc.cssselect("#content div.heading h2")[0].text_content().strip()
        try:
            article.props.author = article.doc.cssselect("#content div.block-main div.title a")[0].text
        except Exception:
            pass
        article.props.tags = [a.text for a in article.doc.cssselect("#content div.tags a")]
        yield article


if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(FoodLogScraper)


