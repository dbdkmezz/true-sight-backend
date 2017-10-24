import requests
from requests.exceptions import ConnectionError

class RequestHandler(object):
    @staticmethod
    def get(url, retries=3):
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
            }
            try:
                r = requests.get(url, headers=headers)
            except ConnectionError:
                if retires == 0:
                    raise
                print("CONNECTION ERROR LOADING {}, retrying".format(url))
                return load_url(url, retries - 1)
            return r.content

