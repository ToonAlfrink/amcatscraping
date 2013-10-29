#!/bin/bash                                                                                          

DATE=$(date +'%Y-%m-%d')
python $PYTHONPATH/scrapers/tv/teletekst.py $TELETEKST_PROJECT --articleset $TELETEKST_ARTICLESET
wait
DEDUPLICATE='python '$PYTHONPATH'/amcat/scripts/maintenance/deduplicate.py'
$DEDUPLICATE $TELETEKST_ARTICLESET --first_date $DATE --last_date $DATE
wait
kill `ps -ef |grep twitter_statuses_filter|grep -v grep|awk '{print $2}'`
wait
python $PYTHONPATH/scrapers/social/twitter/twitter_statuses_filter.py $DATE
