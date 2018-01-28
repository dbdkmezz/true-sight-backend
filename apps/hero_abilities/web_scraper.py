import re
import logging

from apps.utils.request_handler import RequestHandler


logger = logging.getLogger(__name__)


class WebScraper(object):
    def __init__(self, request_handler=None):
        self.request_handler = request_handler or RequestHandler()

    def load_hero_abilities(self, hero):
        from .models import Ability  # avoid circual dependency, eugh!

        soup = self.request_handler.get_soup(
            'https://dota2.gamepedia.com/{}'.format(
                hero.name.replace(' ', '_')))
        abilities = soup.find_all(style=re.compile('^flex: 0 1 450px;.*'))  # the lhs ability box

        for ability in abilities:
            try:
                header = ability.find(style=re.compile('.*font-size: 110%.*'))
                name = next(header.stripped_strings)
                is_ultimate = bool(  # there must be an easier way
                    header.parent.find(style=re.compile('.*background-color: #414141.*')))
                is_from_talent = bool(
                    header.parent.find(style=re.compile('.*background-color: #BDB76B.*')))
                try:
                    hotkey = header.find(title='Hotkey').text
                except AttributeError:
                    hotkey = ''

                try:
                    cooldowns_including_talent = ability.find(
                        title='Cooldown').parent.parent.get_text(strip=True)
                except AttributeError:
                    cooldown = ''
                else:
                    cooldown = cooldowns_including_talent.split('(')[0]
                Ability.objects.update_or_create(
                    hero=hero,
                    name=name,
                    defaults={
                        'cooldown': cooldown,
                        'hotkey': hotkey,
                        'is_ultimate': is_ultimate,
                        'is_from_talent': is_from_talent,
                    })
            except Exception as e:
                print("{}: {}".format(hero, e))
                logger.exception('Error loading ability for %s', hero)
