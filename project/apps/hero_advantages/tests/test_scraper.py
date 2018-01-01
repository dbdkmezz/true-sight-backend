import py
import unittest

from ..request_handler import RequestHandler
from ..web_scraper import WebScraper, Lane, HeroRole


class MockRequestHandler(RequestHandler):
    url_map = {
        "http://www.dota2.com/heroes/": "Heroes_dota2.com.html",
        "http://wiki.teamliquid.net/dota2/Hero_Roles": "Hero Roles.html",
        "http://www.dotabuff.com/heroes/lanes?lane=mid": "Dotabuff Middle Lane.html",
        "http://www.dotabuff.com/heroes/lanes?lane=roaming": "Dotabuff Roaming.html",
        "http://www.dotabuff.com/heroes/disruptor/matchups": "Disruptor.html",
    }

    @classmethod
    def get(cls, url):
        filename = cls.url_map[url]
        path = str(py.path.local().join(
            "project", "apps", "hero_advantages", "tests", "data", filename))
        with open(path, "r") as f:
            return f.read()


class TestGetHeroNames(unittest.TestCase):
    def setUp(self):
        scraper = WebScraper(request_handler=MockRequestHandler())
        self.result = list(scraper.get_hero_names())

    def test_correct_number_names_loaded(self):
        self.assertEqual(len(self.result), 111)

    def test_contains_disruptor(self):
        self.assertEqual(self.result.count("Disruptor"), 1)


class TestHeroIsRole(unittest.TestCase):
    def test_carry_requires_both(self):
        class MockScraper(WebScraper):
            def __init__(self):
                pass

            def _hero_present_in_lane(self, hero_name, lane):
                return hero_name == "MR CARRY" and lane == Lane.SAFE

            def _teamliquid_hero_is_role(self, hero_name, role):
                return hero_name == "MR CARRY" and role == HeroRole.CARRY

        scraper = MockScraper()
        self.assertTrue(scraper.hero_is_role("MR CARRY", HeroRole.CARRY))
        self.assertFalse(scraper.hero_is_role("SOMEONE", HeroRole.CARRY))
        self.assertFalse(scraper.hero_is_role("MR CARRY", HeroRole.SUPPORT))


class TestDotabuffLane(unittest.TestCase):
    def setUp(self):
        self.scraper = WebScraper(request_handler=MockRequestHandler())

    def test_high_presence(self):
        self.assertTrue(
            self.scraper._hero_present_in_lane("Shadow Fiend", Lane.MIDDLE))

    def test_just_enough_presence(self):
        self.assertTrue(
            self.scraper._hero_present_in_lane("Brewmaster", Lane.MIDDLE))

    def test_low_presence(self):
        self.assertFalse(
            self.scraper._hero_present_in_lane("Drow Ranger", Lane.MIDDLE))

    def test_not_on_page(self):
        self.assertFalse(
            self.scraper._hero_present_in_lane("Anti-Mage", Lane.MIDDLE))

    def test_roaming(self):
        self.assertTrue(
            self.scraper._hero_present_in_lane("Riki", Lane.ROAMING))


class TestTeamLiquidIsRole(unittest.TestCase):
    def setUp(self):
        self.scraper = WebScraper(request_handler=MockRequestHandler())

    def test_carry(self):
        self.assertTrue(
            self.scraper._teamliquid_hero_is_role("Anti-Mage", HeroRole.CARRY))

    def test_not_carry(self):
        self.assertFalse(
            self.scraper._teamliquid_hero_is_role("Disruptor", HeroRole.CARRY))

    def test_sub_string_not_carry(self):
        self.assertFalse(
            self.scraper._teamliquid_hero_is_role("nt", HeroRole.CARRY))

    def test_support(self):
        self.assertTrue(
            self.scraper._teamliquid_hero_is_role(
                "Disruptor", HeroRole.SUPPORT))


class TestScrapingOfAdvantages(unittest.TestCase):
    def setUp(self):
        scraper = WebScraper(request_handler=MockRequestHandler())
        self.result = list(scraper.load_advantages_for_hero("Disruptor"))

    def test_first_name(self):
        self.assertEqual(self.result[0]['enemy_name'], "Axe")

    def test_first_advantage(self):
        self.assertEqual(self.result[0]['advantage'], 1.85)

    def test_last_name(self):
        self.assertEqual(self.result[-1]['enemy_name'], "Io")

    def test_last_advantage(self):
        self.assertEqual(self.result[-1]['advantage'], -2.1)

    def test_right_number_loaded(self):
        self.assertEqual(len(self.result), 110)


# class TestGetNumFromPercent(unittest.TestCase):
#     def test_get_num_from_percent(self):
#         string = "1.8%"
#         self.assertEqual(scraper.AdvantageDataForAHero.get_num_from_percent(string), 1.8)

#     def test_get_num_from_percent_negative(self):
#         string = "-1.8%"
#         self.assertEqual(scraper.AdvantageDataForAHero.get_num_from_percent(string), -1.8)

#     def test_get_num_from_percent_empty(self):
#         string = ""
#         self.assertEqual(scraper.AdvantageDataForAHero.get_num_from_percent(string), 0)


# class TestNameToUrlName(unittest.TestCase):
#     def test_blank(self):
#         self.assertEqual(scraper.AdvantageDataForAHero.name_to_url_name(""), "")

#     def test_one_word(self):
#         self.assertEqual(scraper.AdvantageDataForAHero.name_to_url_name("Disruptor"), "disruptor")

#     def test_four_words(self):
#         self.assertEqual(scraper.AdvantageDataForAHero.name_to_url_name("Keeper of the Light"), "keeper-of-the-light")

#     def test_apstrophe(self):
#         self.assertEqual(scraper.AdvantageDataForAHero.name_to_url_name("Nature's Prophet"), "natures-prophet")


