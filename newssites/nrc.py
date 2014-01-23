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
from urllib import quote_plus
import json
from lxml import html

from amcat.scraping.scraper import HTTPScraper,DatedScraper
from amcat.tools.toolkit import readDate
from amcat.scraping.document import HTMLDocument

class WebNRCScraper(HTTPScraper, DatedScraper):
    medium_name = "NRC - website"
    index_url = "http://www.nrc.nl/nieuws/overzicht/{self.options[date].year:04d}/{self.options[date].month:02d}/{self.options[date].day:02d}/"

    def _get_units(self):
        index_doc = self.getdoc(self.index_url.format(**locals()))
        for div in index_doc.cssselect("div.article"):
            #item contains multiple anchors of which we want the one without class
            href = div.cssselect("a:not([class])")[0].get('href')
            section = div.cssselect("a.sectie") and div.cssselect("a.sectie")[0].text or None
            yield (urljoin(index_doc.url, href), section)
        
    def _scrape_unit(self, unit): 
        url, section = unit
        if not section:
            section = url.split("/")[3]
        doc = self.getdoc(url)

        try:
            headline = doc.cssselect("#artikel h1")[0].text_content()
        except IndexError:
            return #no headline, no article

        article_dict = {
            'url' : url,
            'text' : doc.cssselect("#broodtekst")[0],
            'headline' : headline,
            'section' : section,
            'author' : doc.cssselect("div.author") and doc.cssselect("div.author a")[0].text or None,
            'date' : readDate(doc.cssselect("#midden time")[0].get('datetime')),
            'children' : []
            }

        article = HTMLDocument(**article_dict)
        article.props.html = html.tostring(doc)
        yield article
        
        for c in self.get_comments(article):
            c.is_comment = True
            c.parent = article
            yield c

    comment_url = "http://disqus.com/embed/comments/?disqus_version=b755cbf6&f=nrcnl&t_u={url}"

    def get_comments(self, article):
        disqus_url = self.comment_url.format(url = quote_plus(article.props.url))
        doc = self.getdoc(disqus_url)
        data = json.loads(doc.cssselect("#disqus-threadData")[0].text)
        comments = [HTMLDocument(**self.get_comment(post)) for post in data['response']['posts']]
        comments = {comment.props.externalid : comment for comment in comments}
        for _id, comment in comments.items():
            if comment.props.parent:
                comment.props.parent = comments[str(comment.props.parent)]
            yield comment

    def get_comment(self, post):
        return {
            'author' : post['author']['name'],
            'date' : readDate(post['createdAt']),
            'text' : post['message'],
            'votes' : {
                'likes' : post['likes'],
                'dislikes' : post['dislikes']},
            'externalid' : post['id'],
            'parent' : post['parent']
            }
                
if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scraping")
    cli.run_cli(WebNRCScraper)


