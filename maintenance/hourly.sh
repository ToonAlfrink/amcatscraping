#!/bin/bash                                                                                          

python $PYTHONPATH/scrapers/tv/teletekst.py $TELETEKST_PROJECT --articleset $TELETEKST_ARTICLESET
wait
kill `ps -ef |grep twitter_statuses_filter|grep -v grep|awk '{print $2}'`
wait
python $PYTHONPATH/scrapers/social/twitter/twitter_statuses_filter.py
