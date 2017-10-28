import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup


class RequestHandler(object):
    @classmethod
    def get(cls, url, retries=3):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)"
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/39.0.2171.95 Safari/537.36"),
        }
        try:
            r = requests.get(url, headers=headers)
        except ConnectionError:
            if retries == 0:
                raise
            print("CONNECTION ERROR LOADING {}, retrying".format(url))
            return cls.get(url, retries - 1)
        return r.content

    @classmethod
    def get_soup(cls, url):
        return BeautifulSoup(cls.get(url), "html.parser")
