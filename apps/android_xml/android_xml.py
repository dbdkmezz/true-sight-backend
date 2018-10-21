from io import BytesIO

import xml.etree.ElementTree as ET

from ..hero_advantages.models import Hero
from ..hero_abilities.models import Ability

# from ..hero_advantages.web_scraper import WebScraper as HeroWebScraper
# from ..hero_abilities.web_scraper import WebScraper as HeroAbillityWebScraper
        # web_scraper = WebScraper(request_handler)
        # for hero in Hero.objects.all():
        #     web_scraper.load_hero_abilities(hero)



class AndroidXml(object):
    request_handler = None
    
    @classmethod
    def generate(cls, update_first=True):
        if update_first:
            Hero.update_from_web(cls.request_handler)
            HeroAbility.update_from_web(cls.request_handler)

        tree = ET.Element('listOfHeroInfo')

        for h in Hero.objects.all():
            hero = ET.SubElement(tree, 'heroInfo')
            name = ET.SubElement(hero, 'name')
            name.text = h.name
            for a in Ability.objects.filter(hero=h):
                ability = ET.SubElement(hero, 'abilities')
                ET.SubElement(ability, 'name').text = a.name
                ET.SubElement(ability, 'cooldown').text = a.cooldown

        f = BytesIO()
        ET.ElementTree(tree).write(f, encoding='utf-8', xml_declaration=True)
        return f.getvalue()

    @classmethod
    def get_heroes(cls, request_handler=None):
        web_scraper = WebScraper(request_handler)
        hero_names = list(web_scraper.get_hero_names())
        print(hero_names)
