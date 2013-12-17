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
from html2text import html2text
from datetime import date

from amcat.scraping.document import Document, HTMLDocument
from amcat.scraping.scraper import HTTPScraper, DatedScraper
from amcat.tools.toolkit import readDate

class WakkerDierScraper(HTTPScraper, DatedScraper):
    medium_name = "scraping template"
    newsfeeds = ["http://www.wakkerdier.nl/campagnes/in-de-media", "http://www.wakkerdier.nl/dierennieuws", "http://www.wakkerdier.nl/wakker-dier-persberichten"]

    def _get_units(self):
        shorts = {}
        for index_url in self.newsfeeds:
            doc = self.getdoc(index_url)
            for article in doc.cssselect("div.column_main_wrapper article"):                
                date = self._read_date(article.cssselect("p.date")[0].text_content())
                headline = article.cssselect("h2.orange")[0].text_content().strip()
                if date == self.options['date']:
                    shorts[headline] = (index_url, article)
                elif date < self.options['date']:
                    break

        fulls = set()
        for headline, (index_url, short) in shorts.items():
            last_anchor = short.cssselect("a")[-1]
            if last_anchor.text.strip().lower() == "lees meer":
                fulls.add(tuple({'type' : 'full', 'url' : urljoin(index_url, last_anchor.get('href'))}.items()))
            else:
                article = {'type' : 'short', 'url' : index_url}
                article['text'] = "\n\n".join([html2text(p) for p in short.cssselect("p")])
                article['headline'] = headline
                yield article
        for full in fulls:
            yield dict(full)
                
    def _read_date(self, text):
        months = [('jan','januari'),('feb','februari'),('mar','maart'),('apr','april'),('mei','mei'),('jun','juni'),('jul','juli'),('aug','augustus'),('sep','september'),('okt','oktober'),('nov','november'),('dec','december')]
        day,month,year = text.strip().split()
        for i,t in enumerate(months):
            if month in t:
                month = i + 1
        return date(int(year), month, int(day))

    def _scrape_unit(self, props):
        props['date'] = self.options['date']
        if props['type'] == 'short':
            yield Document(**props)
        elif props['type'] == 'full':
            article = HTMLDocument(**props)
            article.prepare(self)
            
            article.props.section = " > ".join([li.text_content().strip("|") for li in article.doc.cssselect("#a-breadcrumb-component li.a-nav-item")])
            article.props.headline = article.doc.cssselect("div.column_main_wrapper h1.blue")[0].text
            article.props.text = article.doc.cssselect("div.column_main_wrapper div")[0]
            yield article

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(WakkerDierScraper)


