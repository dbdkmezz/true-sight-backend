import re
from enum import Enum, unique

from django.utils.functional import cached_property

from apps.utils.request_handler import RequestHandler


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
    def __init__(self, request_handler=None):
        self.request_handler = request_handler or RequestHandler()

    def get_hero_names(self, min_heroes=115):
        soup = self.request_handler.get_soup("http://www.dota2.com/heroes/")
        soup = soup.find(id="filterName")

        result = []
        for row in soup.find_all("option"):
            text = row.get_text()
            if(text != "HERO NAME" and text != "All"):
                result.append(text)
        if len(result) < min_heroes:
            raise Exception('Got too few hero names from the web, only got %s', len(result))
        return result

    def hero_is_role(self, hero, role):
        ROLE_TEST_MAP = {
            HeroRole.CARRY: lambda h: (
                h in self._carry_heroes
            ),
            HeroRole.SUPPORT: lambda h: (
                h in self._support_heroes
            ),
            HeroRole.JUNGLER: lambda h: (
                h in self._jungle_heroes
            ),
            HeroRole.OFF_LANE: lambda h: (
                h in self._off_lane_heroes
            ),
            HeroRole.MIDDLE: lambda h: (
                h in self._middle_lane_heroes
            ),
            HeroRole.ROAMING: lambda h: (
                h in self._roaming_heroes
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

    @cached_property
    def _middle_lane_heroes(self):
        return self._heroes_present_in_lane(Lane.MIDDLE)

    @cached_property
    def _carry_heroes(self):
        return list(
            set(
                self._heroes_present_in_lane(Lane.SAFE)
            ).intersection(self._teamliquid_heroes_of_role(HeroRole.CARRY)))

    @cached_property
    def _off_lane_heroes(self):
        return self._heroes_present_in_lane(Lane.OFF_LANE)

    @cached_property
    def _jungle_heroes(self):
        return self._heroes_present_in_lane(Lane.JUNGLE)

    @cached_property
    def _roaming_heroes(self):
        return self._heroes_present_in_lane(Lane.ROAMING)

    @cached_property
    def _support_heroes(self):
        return self._teamliquid_heroes_of_role(HeroRole.SUPPORT)

    def _heroes_present_in_lane(self, lane):
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

        result = []
        for row in table.find_all("tr"):
            columns = row.find_all("td")
            if len(columns) == 0:
                continue
            hero_name = columns[1].get_text()
            presence = float(columns[2].get_text().replace("%", ""))
            if presence >= min_presence:
                result.append(hero_name)
        return result

    def _teamliquid_heroes_of_role(self, role):
        ROLE_MAP = {
            HeroRole.CARRY: "Carry",
            HeroRole.SUPPORT: "Support",
            # HeroRole.JUNGLER: "Jungler",
        }

        soup = self.request_handler.get_soup("http://wiki.teamliquid.net/dota2/Hero_Roles")
        # The first table with the role name in its table heading ("th")
        table = next((
            t for t in soup.find_all("table")
            if t.find_all("th", text=re.compile(".*{}".format(ROLE_MAP[role])))
        ))
        return [i.get("title") for i in table.find_all("a")]
