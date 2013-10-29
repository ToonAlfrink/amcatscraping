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

import re

from urllib import urlencode
from urlparse import urljoin

from amcat.scraping.document import HTMLDocument
from amcat.scraping.scraper import HTTPScraper, DBScraper
from amcat.scraping.toolkit import parse_form
from amcat.tools.toolkit import readDate

class NRCArchiefScraper(HTTPScraper, DBScraper):
    medium_name = "scraping template"
    base_url = "http://archief.nrc.nl"
    login_url = "https://login.nrc.nl/login?"
    index_url = "http://archief.nrc.nl/index.php/{d.year}/{month}/{d.day}/"

    def _login(self, username, password):
        self.open(self.base_url)
        form = parse_form(self.getdoc(self.login_url).cssselect("form#command")[0])
        form['username'] = username; form['password'] = password
        self.open(self.login_url, urlencode(form))

    months = ["Januari","Februari","Maart",
              "April","Mei","Juni",
              "Juli","Augustus","September",
              "Oktober","November","December"]

    def _get_units(self):
        d = self.options['date']
        month = self.months[d.month - 1]
        index_doc = self.getdoc(self.index_url.format(**locals()))
        for li in index_doc.cssselect("div.main_content ul.list li"):
            page_doc = self.getdoc(urljoin(index_doc.url, li.cssselect("a")[0].get('href')))
            for a in page_doc.cssselect("div.main_content ul.list li a"):
                print(a.get('href'))
                yield urljoin(page_doc.url, a.get('href'))

    def _scrape_unit(self, url):
        article = HTMLDocument(url = url)
        article.prepare(self)
        info = article.doc.cssselect("#article-info")[0].text_content()
        for string in info.split("|"):
            if re.match("[A-Z][a-z]+ ([0-9]{2}\-){2}[0-9]{4}", string.strip()):
                article.props.date = readDate(string.split()[1])
            elif string.strip().startswith("Sectie"):
                article.props.section = string.strip().split(":")[1].strip()
            elif string.strip().startswith("Pagina"):
                article.props.page_str = string.strip().split(":")[1].strip()
        article.props.headline = article.doc.cssselect("#article h1")[0].text_content().strip()
        article.props.text = article.doc.cssselect("#article h3, #article p:not(#article-info):not(#metadata)")
        if article.props.text[-1].text_content().strip().startswith("Op dit artikel rust auteursrecht"):
            article.props.text.pop(-1)
        article.props.tags = [a.text for a in article.doc.cssselect("#metadata a")]
        yield article

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(NRCArchiefScraper)


