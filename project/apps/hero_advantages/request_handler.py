import time
import logging
import requests
from requests.exceptions import ConnectionError

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class RequestHandler(object):
    @classmethod
    def sleeps(self):
        return [1, 5, 15]

    @classmethod
    def get(cls, url, retry=0):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)"
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/39.0.2171.95 Safari/537.36"),
        }
        try:
            r = requests.get(url, headers=headers)
        except ConnectionError:
            if retry == len(cls.sleeps()):
                raise
            sleep_lenght = cls.sleeps()[retry]
            logger.warning(
                "CONNECTION ERROR LOADING %s, retrying after sleep of %s",
                url,
                sleep_lenght,
            )
            time.sleep(sleep_lenght)
            return cls.get(url, retry + 1)
        return r.content

    @classmethod
    def get_soup(cls, url):
        return BeautifulSoup(cls.get(url), "html.parser")
