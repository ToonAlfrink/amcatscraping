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

from urllib import urlencode
from urlparse import urljoin
import json, re

from amcat.scraping.scraper import HTTPScraper, DBScraper
from amcat.scraping.toolkit import parse_form

from amcat.models.medium import Medium

class TelegraafScraper(HTTPScraper, DBScraper):
    medium_name = "De Telegraaf"
    week_url = "http://www.telegraaf.nl/telegraaf-i/week"

    def _login(self, username, password):
        login_url = "http://www.telegraaf.nl/wuz/loginbox/epaper?nocache"
        self.open(self.week_url)
        form = parse_form(self.getdoc(login_url).cssselect("#user-login")[0])
        form['name'], form['pass'] = username, password
        form['rhash'] = "f8ac71adde5cdb382ab5e485a8c3447210a6b69b"
        form['redir'] = self.week_url
        self.opener.opener.addheaders += [("Host" , "www.telegraaf.nl"), ("Referer", login_url)]
        res = self.open(login_url, urlencode(form))
        if not "user_name" in str(self.opener.cookiejar):
            raise ValueError("wrong user/pass")

    def _get_units(self):
        self.medium = Medium.get_or_create(self.medium_name)
        d = self.options['date']
        data = json.loads(self.open("http://www.telegraaf.nl/telegraaf-i/newspapers").read())
        self.paperdata = [i for i in data if i['date'] == "{}-{:02d}-{:02d}".format(d.year,d.month,d.day)][0]
        articles = []
        for page in self.paperdata['pages']:
            articles += page['articles']
        for article_id in articles:
            yield article_id

    def _scrape_unit(self, article_id):
        url = "http://www.telegraaf.nl/telegraaf-i/article/{}".format(article_id)
        article = {'url' : url, 'metastring' : {},'children' : [], 'medium' : self.medium, 'date':self.options['date'],
                   'project': self.options['project']}
        data = json.loads(self.open(url).read())
        lead, text = "", ""
        for d in data['body']:
            for k, v in d.items():
                if k == 'lead':
                    lead += v + "\n\n"
                    if re.match('[A-Z ]+, [a-z]+', v):
                        article['metastring']['dateline'] = v
                elif k == 'headline':
                    article['headline'] = v
                elif k == 'paragraph':
                    text += v + "\n\n"

        article['text'] = lead + "\n\n" + text
        for page in self.paperdata['pages']:
            if article_id in page['articles']:
                article['pagenr'] = int(page['page_number'])
                
        for section in self.paperdata['sections']:
            if article['pagenr'] in map(int, section['pages']):
                article['section'] = section['title']
        article['byline'] = "\n".join(data['byline'])

        if not article['section'] == "Advertentie":
            yield article

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    cli.run_cli(TelegraafScraper)
