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

class YouthFoodMovementScraper(HTTPScraper, DatedScraper):
    medium_name = "youthfoodmovement.nl"
    index_url = "http://youthfoodmovement.nl/nieuws/index/page/{pagenr}"

    def _get_units(self):
        pagenr = 0
        while True:
            pagenr += 1
            page_url = self.index_url.format(**locals())
            for article_url in self._getarticles(page_url):
                if article_url:
                    yield article_url
                else:
                    break
            if not article_url:
                break
                
    def _getarticles(self, url):
        doc = self.getdoc(url)
        for div in doc.cssselect("#content div.item"):
            date_str = div.cssselect("h2.date-big")[0].text.strip()
            if date_str == "VANDAAG":
                date = datetime.now()
            else:
                date = readDate(date_str)
            article_url = urljoin("http://youthfoodmovement.nl", div.cssselect("a")[0].get('href'))
            if date.date() == self.options['date']:
                yield article_url
            elif date.date() < self.options['date']:
                yield False

    def _scrape_unit(self, url):
        article = HTMLDocument(url = url)
        article.prepare(self)
        firstitem = article.doc.cssselect("#content div.left_div div.item")[0]
        article.props.text = firstitem.cssselect("p, div")
        article.props.date = readDate(firstitem.cssselect("span.date")[0].text)
        article.props.section = "nieuws"
        article.props.headline = firstitem.cssselect("h3")[0].text
        article.props.externalid = url.split("/")[-1]
        em = firstitem.cssselect("em")
        if em:
            article.props.author = "".join(em[0].text.split("Door ")[1:])
        yield article
        

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(YouthFoodMovementScraper)


