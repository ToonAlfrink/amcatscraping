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

class MilieuDefensieScraper(HTTPScraper, DatedScraper):
    medium_name = "milieudefensie.nl"
    page_url = "https://www.milieudefensie.nl/nieuwopmilieudefensienl?b_start:int={offset}"

    def _get_units(self):
        for div in self.get_divs():
            a = div.cssselect("a")[0]
            yield urljoin(a.base_url, a.get('href'))

    def get_divs(self):
        offset = 0
        while True:
            page = self.getdoc(self.page_url.format(**locals()))
            for div in page.cssselect("#Content div.tileItem"):
                try:
                    date_str = div.cssselect(".description")[0].text.split("-")[0].split(",")[-1]
                    date = readDate(date_str).date()
                except (IndexError, ValueError):
                    print("date parsing failed")
                    continue
                if date == self.options['date']:
                    yield div
                elif date < self.options['date']:
                    return
            offset += 20
                
    def _scrape_unit(self, url):
        article = HTMLDocument(url = url)
        article.prepare(self)
        article.props.date = self.options['date']
        article.props.section = " > ".join([
                a.text for a in article.doc.cssselect("#SubHeaderBreadcrumbs a")])
        article.props.headline = article.doc.cssselect("title")[0].text.split("—")[0].strip()
        article.props.text = article.doc.cssselect(
            "#parent-fieldname-description") + article.doc.cssselect("#parent-fieldname-text")
        yield article

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(MilieuDefensieScraper)
