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
from datetime import datetime, time
from hashlib import md5

from amcat.scraping.scraper import HTTPScraper, DBScraper
from amcat.models.medium import Medium

class MarokkoScraper(HTTPScraper,DBScraper):
    medium_name = "marokko.nl"
    forum_url = "http://forums.marokko.nl/forumdisplay.php?f={}&page={}"
    login_url = "http://forums.marokko.nl/login.php?do=login"

    def _login(self, username, password):
        post = {
            'do' : 'login',
            'securitytoken' : 'guest',
            'cookieuser' : 1,
            'vb_login_md5password' : md5(password).hexdigest(),
            'vb_login_username' : username,
            }
        response = self.open(self.login_url, urlencode(post))
        if "foutieve gebruikersnaam of wachtwoord" in response.read():
            raise ValueError("login fail")

    def _get_units(self):
        self.medium = Medium.get_or_create(self.medium_name)
        print("Getting forums...")
        forums = list(self.__getforums())
        forums = [(fid,_) for fid,_ in forums if fid not in []]
        for _, doc in forums:
            for pdoc in self.__getpages(doc):
                for li in pdoc.cssselect("li.threadbit"):
                    url = urljoin("http://forums.marokko.nl",li.cssselect("a.title")[0].get('href'))
                    yield url
        for member_url in self.__get_members():
            yield member_url

    def __getforums(self):
        for i in range(100):
            url = self.forum_url.format(i,1)
            try:
                doc = self.getdoc(url)
            except Exception as e:
                print(e)
            else:
                if doc and doc.cssselect("#threadlist"):
                    yield i,doc

    def __getpages(self,doc):
        yield doc
        url = doc.base_url + "&page={}"
        try:
            n_pages = int(doc.cssselect("span > a.popupctrl")[0].text_content().split()[-1])
        except IndexError:
            return
        else:
            for x in range(2,n_pages + 1):
                yield self.getdoc(url.format(x))

    def _scrape_unit(self, url):
        if 'showthread' in url:
            yield self.__scrape_thread(url)
        elif 'member' in url:
            yield self.__scrape_profile(url)


    def __scrape_thread(self, url):
        doc1 = self.getdoc(url)
        op = self.__get_op(doc1)
        n_pages = int(doc1.cssselect("span > a.popupctrl")[0].text_content().split()[-1])
        for i in range(2,n_pages+1):
            doc = self.getdoc(url + "&page={}".format(i))
            for li in [l for l in doc.cssselect("li") if l.get('id').startswith("post_")]:
                article = self.__get_post(li)
                op['children'].append(article)
        return op

    def __get_post(self, li):
        yield {
            'date' : self.__parse_date(li.cssselect("span.date")[0].text_content()),
            'author' : li.cssselect("a.username")[0].text_content().strip(),
            'text' : li.cssselect("blockquote.postcontent")[0],
            'metastring' : {'number' : li.cssselect("a.postcounter")[0].text_content().strip("#")},
            'children' : [],
            'medium' : self.medium,
            'project' : self.options['project']
            }

    def __get_op(self, doc):
        """Get first post, the parent of all replies"""
        firstli = doc.csssselect("#posts li")[0]
        article = self.__get_post(firstli)
        article['section'] = " > ".join([li.text_content().strip() 
                                         for li in doc.cssselect("#breadcrumb li.navbit")[1:-1]])
        article['headline'] = doc.cssselect("span.threadtitle")[0].text_content().strip()
        article['url'] = doc.base_url
        
    def __parse_date(self,string):
        date,time = string.split()
        if date == 'Vandaag':
            today = datetime.today()
            day, month, year = today.day, today.month, today.year
        else:
            day, month, year = map(int,date.split("-"))
        hour,minute = map(int,time.split(":"))
        return datetime(year, month, day, hour, minute)
        
    member_url = "http://forums.marokko.nl/memberlist.php"

    def __get_members(self):
        first = self.getdoc(self.member_url)
        for doc in self.__getpages(first):
            for a in doc.cssselect("#memberlist_table a.username"):
                yield urljoin(doc.base_url, a.get('href'))

    def __scrape_profile(self, url):
        first = self.getdoc(url)
        data = first.cssselect("dl.stats > dt,dl.stats > dd")
        data = zip(data[0::2],data[1::2])
        parent_meta = {dt.text : dd.text for dt,dd in data}
            
        parent = {
            'section' : 'members',
            'headline' : first.cssselect("#userinfo span.member_username")[0].text_content(),
            'byline' : first.cssselect("#userinfo span.usertitle")[0].text_content(),
            'metastring' : parent_meta,
            'children' : [],
            'text' : "This article represents a member of the marokko.nl forum\nConsult it's children to see his/her 'krabbels'.",
            'medium' : self.medium,
            'project' : self.options['project'],
            'date' : datetime(2000,1,1)
            }
        for doc in self.__getpages(first):
            for li in doc.cssselect("#message_list"):
                parent['children'].append({
                        'author' : li.cssselect("a.username")[0].text_content(),
                        'date' : self.__parse_date(li.cssselect("span.postdate")[0].text_content()),
                        'text' : li.cssselect("blockquote")[0],
                        'children' : [],
                        'medium' : self.medium,
                        'project' : self.options['project']
                        })
        return parent
                                   
                    

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(MarokkoScraper)


