from bs4 import BeautifulSoup

from .request_handler import RequestHandler


class WebScraper(object):
    def __init__(self, request_handler=RequestHandler()):
        self.request_handler = request_handler
    
    def hero_names(self):
        content = self.request_handler.get("http://www.dota2.com/heroes/")
        soup = BeautifulSoup(content, "html.parser").find(id="filterName")

        for row in soup.find_all("option"):
            text = row.get_text()
            if(text != "HERO NAME" and text != "All"):
                yield text
