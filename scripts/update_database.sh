#!/bin/bash

python3 /home/paul/dota-vision-web-scraper/bin.py 

rhc scp test upload advantages.db app-root/data/
