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

#useful imports
from urllib import urlencode
from urlparse import urljoin

from amcat.scraping.document import Document, HTMLDocument
from amcat.scraping.scraper import HTTPScraper, DBScraper
from amcat.scraping.toolkit import parse_form
from amcat.tools.toolkit import readDate

class KM4DevScraper(HTTPScraper, DBScraper):
    medium_name = "dgroups.org"
    login_url = "https://dgroups.org/groups/km4dev-l/login"
    page_url = "https://dgroups.org/groups/km4dev-l/discussions?page={pagenr}&nolayout=true"

    def _login(self, username, password):
        post = {
            'email' : username,
            'password' : password,
            }
        self.open(self.login_url, urlencode(post))

    def _get_units(self):
        for x in range(1,100):
            doc = self.getdoc(self.page_url.format(pagenr=x))
            for li in doc.cssselect("li.hentry"):
                headline = li.cssselect("h1.summary")[0].text_content().strip()
                url = urljoin(doc.base_url,li.cssselect("a")[0].get('href'))
                yield headline, url

    def _scrape_unit(self, unit):
        headline, url = unit
        doc = self.getdoc(url)
        _html = doc.cssselect("#messages-list li.hentry")
        parent = self._scrape_li(_html[0])
        parent['headline'], parent['url'] = headline, url
        for li in doc.cssselect("#messages-list li.hentry")[1:]:
            article = self._scrape_li(li)
            article['parent'] = parent
            yield article
        yield parent

    def _scrape_li(self, li):
        lines = [br.text or br.tail or "" for br in li.cssselect("p.entry-summary, p.entry-summary br")]
        text = "\n".join([l for l in lines if not l.startswith(">")])
        return {
            'date' : readDate(li.cssselect("time")[0].get('datetime')),
            'text' : text,
            'author' : li.cssselect("p.owner-name")[0].text_content().strip(),
            'pagenr' : int(li.cssselect("p.message-ordinal")[0].text),
            'children' : [],
            }

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(KM4DevScraper)


