#!/bin/bash

date >> ${OPENSHIFT_PYTHON_LOG_DIR}/update.log
cd ~/app-root/repo/web-scraper
python3 bin.py >> ${OPENSHIFT_PYTHON_LOG_DIR}/update.log
cp advantages.db ~/app-root/data/
