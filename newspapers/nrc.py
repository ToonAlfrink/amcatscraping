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

from amcat.scraping.scraper import HTTPScraper, DBScraper
from amcat.scraping.document import HTMLDocument
from amcat.scraping import toolkit as stoolkit

from urlparse import urljoin
from urllib import urlencode
from urllib2 import HTTPError
import re

class NRCScraper(HTTPScraper, DBScraper):
    medium_name = "NRC Handelsblad"
    nrc_version = "NH"

    login_url = "https://login.nrc.nl/login"
    index_url = "http://digitaleeditie.nrc.nl/digitaleeditie/{self.nrc_version}/{d.year}/{month_minus}/{d.year}{d.month:02d}{d.day:02d}___/1_01/index.html"
    section_url = "http://digitaleeditie.nrc.nl/digitaleeditie/{self.nrc_version}/{d.year}/{month_minus:02d}/{d.year}{d.month:02d}{d.day:02d}___/section{secnr}.html"

    def _login(self, username, password):

        page = self.getdoc(self.login_url)

        form = stoolkit.parse_form(page)
        form['username'] = username
        form['password'] = password
        self.opener.opener.open(self.login_url, urlencode(form))

    def _get_units(self):
        d = self.options.get('date')
        month_minus = d.month - 1
        index_url = self.index_url.format(**locals())
        sections = self.getdoc(index_url).cssselect('#Sections a.section-link')
        for s in sections:
            #for each linked section from the left panel
            section_url = urljoin(index_url, s.get('href'))
            try:
                section_index = urljoin(section_url, self.getdoc(section_url).cssselect("#Tabs li.text-tab a")[0].get('href'))
            except HTTPError:
                continue
            for div in self.getdoc(section_index).cssselect("#MainContent div.one-preview"):
                #for each page representation in the 'teksten' tab of the section
                pagenumber = div.cssselect("h3 span")[0].text.strip("pagin ")
                for a in div.cssselect("ul.article-links li a"):
                    #for each article link in that div
                    yield (pagenumber, urljoin(section_index, a.get('href')))

    def _scrape_unit(self, pagenr_url):
        pagenumber,  url = pagenr_url
        page = HTMLDocument(date = self.options.get('date'), url = url, pagenumber = pagenumber)
        page.prepare(self)
        article = self._get_article(page)
        if article:
            yield article

    def _get_article(self, page):
        by = page.doc.cssselect("#MainContent p.by")[0]
        if by.cssselect("span.person"):
            page.props.author = by.cssselect("span.person")[0].text_content().strip()
        page.props.text = page.doc.cssselect('.column-left')
        if not page.doc.cssselect('h2')[0].text:
            return
        page.props.headline = page.doc.cssselect("#MainContent h2")[0].text
        intro = page.doc.cssselect("p.leader em.intro") + page.doc.cssselect('p.intro')
        if intro:
            page.props.text = intro + page.props.text
        page.props.section = page.doc.cssselect("div.more-articles h4")[0].text
        p = re.compile("^[A-Z][a-z]+( [A-Z][a-z]+)?\.$")
        strong = page.doc.cssselect("p.intro strong")
        if strong and strong[0].text:
            if p.match(strong[0].text):
                page.props.dateline = strong[0].text
        return page


if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.debug_module("amcat.scraping.scraper")
    amcatlogging.debug_module("amcat.scraping.document")
    cli.run_cli(NRCScraper)
