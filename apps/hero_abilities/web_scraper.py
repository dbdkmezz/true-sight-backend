import re
import logging

from apps.utils.request_handler import RequestHandler

from .models import Ability, SpellImmunity, DamageType

logger = logging.getLogger(__name__)


class WebScraper(object):
    def __init__(self, request_handler=None):
        self.request_handler = request_handler or RequestHandler()

    def load_hero_abilities(self, hero):
        soup = self.request_handler.get_soup(
            'https://dota2.gamepedia.com/{}'.format(
                hero.name.replace(' ', '_')))
        abilities = soup.find_all(style=re.compile('^flex: 0 1 450px;.*'))  # the lhs ability box
        hotkeys_loaded = []
        for ability in abilities:
            try:
                header = ability.find(style=re.compile('.*font-size: 110%.*'))
                name = next(header.stripped_strings)
                description = ability.find(
                    style=re.compile('vertical-align: top;.*border-top.*')
                ).text.replace('\n', '')
                if description == '':
                    raise Exception("Could not load description")

                header_background_colour = re.match(
                    r'.*background-color: (.*?);.*',
                    header['style']
                ).group(1)
                if header_background_colour == '#2277AA':
                    continue  # Ability of controlled unit
                if header_background_colour == '#BDB76B':
                    continue  # Talent ability
                if header_background_colour == '#5B388F':
                    continue  # Ability from aghanims
                is_ultimate = (header_background_colour == '#414141')
                if not is_ultimate:
                    assert header_background_colour == '#B44335'

                spell_immunity = self._get_spell_immunity(header)
                spell_immunity_detail = self._get_spell_immunity_detail(ability)

                damage_type, aghanims_damage_type = self._get_damage_type(ability)

                hotkey = self._get_hotkey(hero, header)
                if hotkey and hotkey in hotkeys_loaded:
                    continue
                hotkeys_loaded += hotkey

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
                        'description': description,
                        'cooldown': cooldown,
                        'hotkey': hotkey,
                        'is_ultimate': is_ultimate,
                        # 'is_from_talent': is_from_talent,
                        # 'is_from_aghanims': is_from_aghanims,
                        'spell_immunity': spell_immunity,
                        'spell_immunity_detail': spell_immunity_detail,
                        'damage_type': damage_type,
                        'aghanims_damage_type': aghanims_damage_type,
                    })
            except Exception as e:
                print("{}: {} {}".format(hero, type(e), e))
                logger.exception('Error loading ability for %s', hero)

    _spell_immunity_map = {
        'Does not pierce spell immunity.': SpellImmunity.DOES_NOT_PIERCE,
        'Partially pierces spell immunity.': SpellImmunity.PARTIALLY_PIERCES,
        'Pierces spell immunity.': SpellImmunity.PIERCES,
    }

    @classmethod
    def _get_spell_immunity(cls, header):
        for img in header.find_all('img'):
            if img['alt'] in cls._spell_immunity_map.keys():
                return cls._spell_immunity_map[img['alt']]

    @staticmethod
    def _get_spell_immunity_detail(ability):
        spell_immunity_images = ability.find_all(title=re.compile('.*spell immunity.*'))
        if len(spell_immunity_images) == 2:
            return spell_immunity_images[1].parent.parent.get_text(strip=True)
        elif len(spell_immunity_images) > 2:
            raise Exception("Unexpected number of spell immunity images")
        return ''

    _damage_type_map = {
        'Magical': DamageType.MAGICAL,
        'Physical': DamageType.PHYSICAL,
        'Pure': DamageType.PURE,
        # Spectre has this, no one else, probably just a bug on the wiki
        'HP Removal': DamageType.PURE,
    }

    @classmethod
    def _get_damage_type(cls, ability):
        try:
            damage_header = next(b for b in ability.find_all('b') if b.text == 'Damage')
        except StopIteration:
            return None, None

        damage_info = damage_header.find_next_siblings('a')
        damage_type = cls._damage_type_map[damage_info[0].text]
        if len(damage_info) == 1 or damage_info[1].get('title') in ("Damage types", "Talent"):
            return damage_type, None

        assert damage_info[1].get('title') == "Upgradable by Aghanim's Scepter."
        aghanims_damage_type = cls._damage_type_map[damage_info[2].text]
        return damage_type, aghanims_damage_type

    @staticmethod
    def _get_hotkey(hero, header):
        try:
            hotkey = header.find(title='Hotkey').text
        except AttributeError:
            return ''
        if hero.name == 'Invoker' and len(hotkey) > 1:
            return ''
        return hotkey
