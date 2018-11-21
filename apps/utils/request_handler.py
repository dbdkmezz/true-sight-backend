import io
import time
import logging
import requests
from requests.exceptions import ConnectionError

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class RequestHandler(object):
    @property
    def sleeps(self):
        return [1, 5, 15]

    def get(self, url, retry=0):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)"
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/39.0.2171.95 Safari/537.36"),
        }
        try:
            r = requests.get(url, headers=headers)
        except ConnectionError:
            if retry == len(self.sleeps):
                raise
            sleep_lenght = self.sleeps[retry]
            logger.warning(
                "CONNECTION ERROR LOADING %s, retrying after sleep of %s",
                url,
                sleep_lenght,
            )
            time.sleep(sleep_lenght)
            return cls.get(url, retry + 1)
        return r.content

    def get_soup(self, url):
        return BeautifulSoup(self.get(url), "html.parser")


class MockRequestHandler(RequestHandler):
    def __init__(self, url_map, files_path):
        self.url_map = url_map
        self.files_path = files_path

    def get(self, url):
        filename = self.url_map[url]
        path = str(self.files_path.join(filename))
        with io.open(path, mode='r', encoding='utf8') as f:
            return f.read()
