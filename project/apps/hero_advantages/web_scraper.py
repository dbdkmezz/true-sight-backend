import re
from enum import Enum, unique

from .request_handler import RequestHandler


@unique
class HeroRole(Enum):
    CARRY = 1
    SUPPORT = 2
    OFF_LANE = 3
    JUNGLER = 4
    MID = 5
    ROAMING = 6


@unique
class Lane(Enum):
    MIDDLE = 1
    SAFE = 2
    OFF_LANE = 3
    TOP = 4
    JUNGLE = 5


class WebScraper(object):
    def __init__(self, request_handler=RequestHandler()):
        self.request_handler = request_handler

    def get_hero_names(self):
        soup = self.request_handler.get_soup("http://www.dota2.com/heroes/")
        soup = soup.find(id="filterName")

        for row in soup.find_all("option"):
            text = row.get_text()
            if(text != "HERO NAME" and text != "All"):
                yield text

    def hero_is_role(self, hero, role):
        pass

    def _hero_present_in_lane(self, hero_name, lane, min_presence=30):
        lane_map = {
            Lane.SAFE: "http://www.dotabuff.com/heroes/lanes?lane=safe",
            Lane.MIDDLE: "http://www.dotabuff.com/heroes/lanes?lane=mid",
            Lane.OFF_LANE: "http://www.dotabuff.com/heroes/lanes?lane=off",
            Lane.JUNGLE: "http://www.dotabuff.com/heroes/lanes?lane=jungle",
        }
        soup = self.request_handler.get_soup(lane_map[lane])
        table = soup.find("table", class_="sortable")
        for row in table.find_all("tr"):
            name_cell = row.find("td", class_="cell-xlarge", text=hero_name)
            if name_cell and name_cell.get_text() == hero_name:
                # Find the cell with a "%" character in the string
                presence_cell = row.find(string=re.compile("%"))
                presence = float(presence_cell.replace("%", ""))
                return presence >= min_presence

        return False

    def _teamliquid_hero_is_role(self, hero_name, role):
        role_map = {
            HeroRole.CARRY: "Carry",
            HeroRole.SUPPORT: "Support",
            # OFF_LANE = 3
            # JUNGLER = 4
            # MID = 5
            # ROAMING = 6
        }

        soup = self.request_handler.get_soup(
            "http://wiki.teamliquid.net/dota2/Hero_Roles")
        # The first table with the role name in its table heading ("th")
        table = next((
            t for t in soup.find_all("table")
            if t.find_all("th", text=re.compile(".*{}".format(role_map[role])))
        ))
        return hero_name in (i.get("title") for i in table.find_all("a"))
