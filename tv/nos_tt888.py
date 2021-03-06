 #!/usr/bin/python
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

from __future__ import unicode_literals, print_function, absolute_import

from urlparse import urljoin
from cStringIO import StringIO
import ftplib, datetime, threading
from contextlib import contextmanager
    
import logging
log = logging.getLogger(__name__)

from amcat.scraping.scraper import DBScraper
from amcat.scraping.document import HTMLDocument
from amcat.models.article import Article
from amcat.tools.stl import STLtoText
from amcat.scraping.toolkit import todate
from amcat.models.medium import Medium

mediadict = {'buitenhof': 'Buitenhof',
             'de wereld draait door': 'De Wereld Draait Door',
             'eenvandaag': 'Een Vandaag',
             'eva jinek op zondag': 'Eva Jinek',
             'knevel & van den brink': 'Knevel &amp; Van Den Brink',
             'nieuwsuur': 'Nieuwsuur',
             'nos journaal 20:00': 'NOS 20:00',
             'nos journaal op 3': 'journaal op 3',
             'pauw & witteman': 'Pauw en Witteman',
             'vandaag de dag': 'Vandaag de dag',
             'vandaag de vrijdag': 'Vandaag de vrijdag',
             'zembla': 'Zembla'}

HOST = "ftp.tt888.nl"

def getDate(title):
    """Parses date (datetime object) from title of tt-888 .stl files. If hour > 24 (the date of nighttime broadcasts to a certain hour are attributed to former day), the true date of the broadcast is used. (hour minus 24, and day plus 1)"""
    datestring = title.split('-')[0:4]
    year, month, day, hour, minute = int(datestring[0]), int(datestring[1]), int(datestring[2]), int(datestring[3].split(',')[0]), int(datestring[3].split(',')[1])
    if hour > 23:
        hour = hour - 24
        date = datetime.datetime(year,month,day,hour,minute)
        return date + datetime.timedelta(1)
    else:
        return datetime.datetime(year,month,day,hour,minute)

def getUrlsFromSet(setid, check_back=30):
    """Returns list with all URLS of articles in the articleset for the last [check_back] days"""
    fromdate = (datetime.date.today() - datetime.timedelta(days = check_back))
    articles = (Article.objects.filter(date__gt = fromdate)
                .filter(articlesets_set = setid).only("url"))
    urls = set(a.url.split('/')[-1] for a in articles if a.url)
    return urls
            
class tt888Scraper(DBScraper):

    def _get_units(self):
        self._ftp = ftplib.FTP(HOST)  
        self._ftp.login(self.options['username'], self.options['password'])
        existing_files = getUrlsFromSet(setid=self.articleset, check_back=30)
        files = self._ftp.nlst()
        for fn in files:
            fn = fn.decode("latin-1")
            title = fn.split('/')[-1]                
            if title.count('-') > 9:
                continue # Filter out reruns (marked by double dates)
            if title in existing_files:
                print("Already in articleset: %s" % title)
                continue # Skip if already in database
            yield fn

    def _scrape_unit(self, fn):
        dest = StringIO()
        self._ftp.retrbinary(b'RETR %s' % (fn.encode('latin-1')) , dest.write)
        body = STLtoText(dest.getvalue())
        body = body.decode('latin-1','ignore').strip().lstrip('888').strip()
        title = fn.split('/')[-1]
        medium = title.split('-')[-1].split('.stl')[0].strip().lower()
        date = getDate(title)

        if medium == 'nos journaal' and int(format(date, '%H')) == 20 and int(format(date, '%M')) == 0: medium = 'nos journaal 20:00'
        if medium in mediadict.keys():
            medium = mediadict[medium]
        med = Medium.get_or_create(medium)
        art = Article(headline=medium, text=body,
                      medium = med, date=date, url = fn)
        yield art

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.debug_module("amcat.scraping.scraper")
    amcatlogging.debug_module("amcat.scraping.document")
    cli.run_cli(tt888Scraper)


