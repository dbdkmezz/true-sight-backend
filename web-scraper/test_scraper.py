from bs4 import BeautifulSoup

import scraper
import unittest

# Example of use:
# python3 -m unittest test_scraper.TestHelperFunctions

class TestScrapingOfAdvantages(unittest.TestCase):
    def setUp(self):
        file_string = scraper.load_file("samples/Disruptor.html")
        self.list = scraper.AdvantageDataForAHero.get_advantages_from_string(file_string)

    def test_first_name(self):
        self.assertEqual(self.list[0].name, "Axe")

    def test_first_advantage(self):
        self.assertEqual(self.list[0].advantage, 1.85)

    def test_last_name(self):
        self.assertEqual(self.list[-1].name, "Io")

    def test_last_advantage(self):
        self.assertEqual(self.list[-1].advantage, -2.1)

    def test_right_number_loaded(self):
        self.assertEqual(len(self.list), 110)


class TestScrapingOfCarryAndSupport(unittest.TestCase):
    def setUp(self):
        self.file_string = scraper.load_file("samples/Hero Roles.html")

    def test_get_role_column_carry(self):
        soup = BeautifulSoup(self.file_string, "html.parser")
        self.assertEqual(scraper.AdvantageDataForAHero.get_role_column(soup, "Carry"), 1)

    def test_get_role_column_support(self):
        soup = BeautifulSoup(self.file_string, "html.parser")
        self.assertEqual(scraper.AdvantageDataForAHero.get_role_column(soup, scraper.AdvantageDataForAHero.SUPPORT_STRING), 5)

    def test_carry(self):
        soup = BeautifulSoup(self.file_string, "html.parser")
        self.assertEqual(scraper.AdvantageDataForAHero.is_role_from_teamliquid(soup, "Antimage", scraper.AdvantageDataForAHero.CARRY_STRING), 1)

    def test_not_carry(self):
        soup = BeautifulSoup(self.file_string, "html.parser")
        self.assertEqual(scraper.AdvantageDataForAHero.is_role_from_teamliquid(soup, "Disruptor", scraper.AdvantageDataForAHero.CARRY_STRING), 0)

    def test_sub_string_not_carry(self):
        soup = BeautifulSoup(self.file_string, "html.parser")
        self.assertEqual(scraper.AdvantageDataForAHero.is_role_from_teamliquid(soup, "nt", scraper.AdvantageDataForAHero.CARRY_STRING), 0)

class TestScrapingOfMid(unittest.TestCase):
    def setUp(self):
        file_string = scraper.load_file("samples/Dotabuff Middle Lane.html")
        self.soup = BeautifulSoup(file_string, "html.parser")

    def test_high_presence(self):
        self.assertEqual(scraper.AdvantageDataForAHero.is_role_from_dotabuff(self.soup, "Shadow Fiend"), 1)

    def test_just_enough_presence(self):
        self.assertEqual(scraper.AdvantageDataForAHero.is_role_from_dotabuff(self.soup, "Brewmaster"), 1)

    def test_low_presence(self):
        self.assertEqual(scraper.AdvantageDataForAHero.is_role_from_dotabuff(self.soup, "Drow Ranger"), 0)

    def test_not_on_page(self):
        self.assertEqual(scraper.AdvantageDataForAHero.is_role_from_dotabuff(self.soup, "Anti-Mage"), 0)


class TestRoaming(unittest.TestCase):
    def test_in_list(self):
        self.assertEqual(scraper.AdvantageDataForAHero.is_roaming_hero("Crystal Maiden"), 1)

    def test_not_in_list(self):
        self.assertEqual(scraper.AdvantageDataForAHero.is_roaming_hero("Gabe Newell"), 0)


class TestGetHeroNames(unittest.TestCase):
    def setUp(self):
        file_string = scraper.load_file("samples/Heroes_dota2.com.html")
        self.list = scraper.get_hero_names_from_string(file_string)

    def test_correct_number_names_loaded(self):
        self.assertEqual(len(self.list), 111)

    def test_contains_disruptor(self):
        self.assertEqual(self.list.count("Disruptor"), 1)


class TestGetNumFromPercent(unittest.TestCase):
    def test_get_num_from_percent(self):
        string = "1.8%"
        self.assertEqual(scraper.AdvantageDataForAHero.get_num_from_percent(string), 1.8)

    def test_get_num_from_percent_negative(self):
        string = "-1.8%"
        self.assertEqual(scraper.AdvantageDataForAHero.get_num_from_percent(string), -1.8)

    def test_get_num_from_percent_empty(self):
        string = ""
        self.assertEqual(scraper.AdvantageDataForAHero.get_num_from_percent(string), 0)


class TestNameToUrlName(unittest.TestCase):
    def test_blank(self):
        self.assertEqual(scraper.AdvantageDataForAHero.name_to_url_name(""), "")

    def test_one_word(self):
        self.assertEqual(scraper.AdvantageDataForAHero.name_to_url_name("Disruptor"), "disruptor")

    def test_four_words(self):
        self.assertEqual(scraper.AdvantageDataForAHero.name_to_url_name("Keeper of the Light"), "keeper-of-the-light")

    def test_apstrophe(self):
        self.assertEqual(scraper.AdvantageDataForAHero.name_to_url_name("Nature's Prophet"), "natures-prophet")



if __name__ == "__main__":
    unittest.main()
