#!/bin/bash

DATE=$(date -d 'yesterday' +'%Y-%m-%d')
python $PYTHONPATH/amcat/scripts/maintenance/daily.py $DATE
wait
python $PYTHONPATH/amcat/scripts/maintenance/scraping_check.py $DATE $SCRAPING_CHECK_MAIL