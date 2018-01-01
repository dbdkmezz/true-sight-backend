import re
from enum import Enum, unique

from .request_handler import RequestHandler


@unique
class HeroRole(Enum):
    CARRY = 1
    SUPPORT = 2
    OFF_LANE = 3
    JUNGLER = 4
    MIDDLE = 5
    ROAMING = 6


@unique
class Lane(Enum):
    MIDDLE = 1
    SAFE = 2
    OFF_LANE = 3
    JUNGLE = 4
    ROAMING = 5


class WebScraper(object):
    def __init__(self, request_handler=RequestHandler()):
        self.request_handler = request_handler

    def reset_cache(self):
        self.request_handler.reset_cache()

    def get_hero_names(self):
        soup = self.request_handler.get_soup("http://www.dota2.com/heroes/")
        soup = soup.find(id="filterName")

        for row in soup.find_all("option"):
            text = row.get_text()
            if(text != "HERO NAME" and text != "All"):
                yield text

    def hero_is_role(self, hero, role):
        ROLE_TEST_MAP = {
            HeroRole.CARRY: lambda h: (
                self._hero_present_in_lane(h, Lane.SAFE) and
                self._teamliquid_hero_is_role(h, HeroRole.CARRY)
            ),
            HeroRole.SUPPORT: lambda h: (
                self._teamliquid_hero_is_role(h, HeroRole.SUPPORT)
            ),
            HeroRole.JUNGLER: lambda h: (
                self._hero_present_in_lane(h, Lane.JUNGLE)
            ),
            HeroRole.OFF_LANE: lambda h: (
                self._hero_present_in_lane(h, Lane.OFF_LANE)
            ),
            HeroRole.MIDDLE: lambda h: (
                self._hero_present_in_lane(h, Lane.MIDDLE)
            ),
            HeroRole.ROAMING: lambda h: (
                self._hero_present_in_lane(h, Lane.ROAMING)
            ),
        }
        return ROLE_TEST_MAP[role](hero)

    def load_advantages_for_hero(self, hero):
        """Gets the advantages hero has over the other heroes in the game.

        Yields dictionaries of the format:
        {
            'enemy_name': ENEMY_NAME,
            'advantage': ADVANTAGE_FLOAT,
        }
        """
        soup = self.request_handler.get_soup(
            "http://www.dotabuff.com/heroes/{}/matchups".format(
                hero.replace(' ', '-').replace("'", "").lower()
            ))
        soup = soup.find("table", class_="sortable")

        for row in soup.find_all(lambda tag: tag.has_attr("data-link-to")):
            enemy_name = row.find(class_="cell-xlarge").get_text()
            advantage_cell = row.find(string=re.compile("[0-9]*%"))
            advantage = advantage_cell.replace("%", "")
            yield {
                'enemy_name': enemy_name,
                'advantage': float(advantage),
            }

    def _hero_present_in_lane(self, hero, lane):
        LANE_MAP = {
            Lane.SAFE: "http://www.dotabuff.com/heroes/lanes?lane=safe",
            Lane.MIDDLE: "http://www.dotabuff.com/heroes/lanes?lane=mid",
            Lane.OFF_LANE: "http://www.dotabuff.com/heroes/lanes?lane=off",
            Lane.JUNGLE: "http://www.dotabuff.com/heroes/lanes?lane=jungle",
            Lane.ROAMING: "http://www.dotabuff.com/heroes/lanes?lane=roaming",
        }
        min_presence = 30 if lane != Lane.ROAMING else 5
        soup = self.request_handler.get_soup(LANE_MAP[lane])
        table = soup.find("table", class_="sortable")
        for row in table.find_all("tr"):
            name_cell = row.find("td", class_="cell-xlarge", text=hero)
            if name_cell and name_cell.get_text() == hero:
                # Find the cell with a "%" character in the string
                presence_cell = row.find(string=re.compile("%"))
                presence = float(presence_cell.replace("%", ""))
                return presence >= min_presence

        return False

    def _teamliquid_hero_is_role(self, hero, role):
        ROLE_MAP = {
            HeroRole.CARRY: "Carry",
            HeroRole.SUPPORT: "Support",
            HeroRole.JUNGLER: "Jungler",
        }

        soup = self.request_handler.get_soup(
            "http://wiki.teamliquid.net/dota2/Hero_Roles")
        # The first table with the role name in its table heading ("th")
        table = next((
            t for t in soup.find_all("table")
            if t.find_all("th", text=re.compile(".*{}".format(ROLE_MAP[role])))
        ))
        return hero in (i.get("title") for i in table.find_all("a"))
