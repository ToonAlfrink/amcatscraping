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
from amcat.scraping.toolkit import parse_form
from amcat.tools.toolkit import readDate

class BoerderijScraper(HTTPScraper, DatedScraper):
    medium_name = "boerderij.nl"
    index_url = "http://www.boerderij.nl"
    page_url = "http://www.boerderij.nl/Archief/?articleType=News&page={pagenr}"

    def _get_units(self):
        pagenr = 1
        while True:
            page_url = self.page_url.format(**locals())
            page_doc = self.getdoc(page_url)
            for li in page_doc.cssselect("#content ul.media-list li"):
                date = readDate(li.cssselect("div.meta time")[0].get('datetime'))
                url = urljoin(page_url, li.cssselect("a")[0].get('href'))
                if date.date() == self.options['date']:
                    yield (date, url)
                elif date.date() < self.options['date']:
                    return
            pagenr += 1

    def _scrape_unit(self, bits):
        date, url = bits
        article = HTMLDocument(date = date, url = url)
        article.prepare(self)
        content = article.doc.cssselect("#content")[0]
        article.props.section = content.cssselect("div.info-block p.meta a.label")[0].text
        article.props.headline = content.cssselect("div.title h1")[0].text
        article.props.externalid = url.split("-")[-1].strip("W/")
        article.props.text = content.cssselect("div.article")
        article.props.author = content.cssselect("p.meta span.user a.label")[0].text.strip()
        article.props.tags = set([a.text for a in content.cssselect("ul.taglist li a")])
        article.props.view_count = int(content.cssselect("div.info-block span.view-count")[0].text)
        yield article
        self.clearcookies()

    def clearcookies(self):
        """Clear cookies so the site won't interrupt us after 3 articles"""
        self.opener.cookiejar._cookies = {}

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(BoerderijScraper)


