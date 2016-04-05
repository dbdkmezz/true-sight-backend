#!/bin/bash

date >> ${OPENSHIFT_PHP_LOG_DIR}/update.log
python3 ~/app-root/repo/web-scraper/bin.py >> ${OPENSHIFT_PHP_LOG_DIR}/update.log
cp ~/app-root/repo/web-scraper/advantages.db ~/app-root/data/
