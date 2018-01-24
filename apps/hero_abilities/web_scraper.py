import re

from apps.utils.request_handler import RequestHandler


class WebScraper(object):
    def __init__(self, request_handler=RequestHandler()):
        self.request_handler = request_handler

    def load_hero_abilities(self, hero):
        from .models import Ability  # avoid circual dependency, eugh!

        soup = self.request_handler.get_soup("https://dota2.gamepedia.com/{}".format(hero.name))
        abilities = soup.find_all(style=re.compile('^flex: 0 1 450px;.*'))  # the lhs ability box

        for ability in abilities:
            header = ability.find(style=re.compile('.*font-size: 110%.*'))
            header_text = list(header.stripped_strings)
            is_ultimate = bool(  # there must be an easier way
                header.parent.find(style=re.compile('.*background-color: #414141.*')))
            name = header_text[0]
            hotkey = header_text[2]  # this has a tooltip with a useful title
            cooldowns_including_talent = ability.find(
                title='Cooldown').parent.parent.get_text(strip=True)
            cooldown = cooldowns_including_talent.split('(')[0]
            Ability.objects.update_or_create(
                hero=hero,
                name=name,
                defaults={
                    'cooldown': cooldown,
                    'hotkey': hotkey,
                    'is_ultimate': is_ultimate,
                })
