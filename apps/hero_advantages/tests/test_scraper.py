import py
import unittest

from ...utils.request_handler import MockRequestHandler
from ..web_scraper import WebScraper, Lane, HeroRole


mock_request_handler = MockRequestHandler(
    url_map={
        "http://www.dota2.com/heroes/": "Heroes_dota2.com.html",
        "http://wiki.teamliquid.net/dota2/Hero_Roles": "Hero Roles.html",
        "http://www.dotabuff.com/heroes/lanes?lane=mid": "Dotabuff Middle Lane.html",
        "http://www.dotabuff.com/heroes/lanes?lane=roaming": "Dotabuff Roaming.html",
        "http://www.dotabuff.com/heroes/disruptor/matchups": "Disruptor.html",
    },
    files_path=py.path.local().join("apps", "hero_advantages", "tests", "data"),
)


class TestGetHeroNames(unittest.TestCase):
    def setUp(self):
        scraper = WebScraper(request_handler=mock_request_handler)
        self.result = list(scraper.get_hero_names(min_heroes=111))

    def test_correct_number_names_loaded(self):
        self.assertEqual(len(self.result), 111)

    def test_contains_disruptor(self):
        self.assertEqual(self.result.count("Disruptor"), 1)


class TestHeroIsRole(unittest.TestCase):
    def test_carry_requires_both(self):
        class MockScraper(WebScraper):
            def __init__(self):
                pass

            def _heroes_present_in_lane(self, lane):
                return ["MR CARRY"] if lane == Lane.SAFE else []

            def _teamliquid_heroes_of_role(self, role):
                return ["MR CARRY"] if role == HeroRole.CARRY else []

        scraper = MockScraper()
        self.assertTrue(scraper.hero_is_role("MR CARRY", HeroRole.CARRY))
        self.assertFalse(scraper.hero_is_role("SOMEONE", HeroRole.CARRY))
        self.assertFalse(scraper.hero_is_role("MR CARRY", HeroRole.SUPPORT))


class TestDotabuffLane(unittest.TestCase):
    def setUp(self):
        self.scraper = WebScraper(request_handler=mock_request_handler)

    def test_high_presence(self):
        self.assertTrue(
            self.scraper.hero_is_role("Shadow Fiend", HeroRole.MIDDLE))

    def test_just_enough_presence(self):
        self.assertTrue(
            self.scraper.hero_is_role("Brewmaster", HeroRole.MIDDLE))

    def test_low_presence(self):
        self.assertFalse(
            self.scraper.hero_is_role("Drow Ranger", HeroRole.MIDDLE))

    def test_not_on_page(self):
        self.assertFalse(
            self.scraper.hero_is_role("Anti-Mage", HeroRole.MIDDLE))

    def test_roaming(self):
        self.assertTrue(
            self.scraper.hero_is_role("Riki", HeroRole.ROAMING))


class TestTeamLiquidIsRole(unittest.TestCase):
    def setUp(self):
        self.scraper = WebScraper(request_handler=mock_request_handler)

    def test_carry(self):
        self.assertIn(
            "Anti-Mage",
            self.scraper._teamliquid_heroes_of_role(HeroRole.CARRY))

    def test_not_carry(self):
        self.assertNotIn(
            "Disruptor",
            self.scraper._teamliquid_heroes_of_role(HeroRole.CARRY))

    def test_sub_string_not_carry(self):
        self.assertNotIn(
            "nt",
            self.scraper._teamliquid_heroes_of_role(HeroRole.CARRY))

    def test_support(self):
        self.assertIn(
            "Disruptor",
            self.scraper._teamliquid_heroes_of_role(HeroRole.SUPPORT)
        )


class TestScrapingOfAdvantages(unittest.TestCase):
    def setUp(self):
        scraper = WebScraper(request_handler=mock_request_handler)
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


