import re
import logging

from django.utils.functional import cached_property

from apps.hero_advantages.models import Hero, Advantage
from apps.hero_advantages.roles import HeroRole
from apps.hero_abilities.models import Ability

from .exceptions import DoNotUnderstandQuestion


logger = logging.getLogger(__name__)


class QuestionParser(object):
    def __init__(self, question_text):
        self.text = question_text.lower()

    @cached_property
    def abilities(self):
        """Returns a list of all abilities found in the question.

        Does not include the names of abilities found whose name is a substring of another ability
        whose name is in the question.
        E.g. if 'Chemical Rage' is in the question then this will not return the ability 'Rage'.
        """
        abilities_found = [
            a for a in Ability.objects.all()
            if a.name.lower() in self.text
        ]
        result = []
        for ability in abilities_found:
            other_ability_names = [a.name for a in abilities_found if a != ability]
            if not any((ability.name in n) for n in other_ability_names):
                result.append(ability)
        return result

    @cached_property
    def heroes(self):
        return [
            h for h in Hero.objects.all()
            if self.contains_any_word(h.aliases)
        ]

    @cached_property
    def role(self):
        role_words_map = (
            (('carry', ), HeroRole.CARRY),
            (('support', ), HeroRole.SUPPORT),
            (('off', ), HeroRole.OFF_LANE),
            (('jungle', 'jungling', 'jungler'), HeroRole.JUNGLER),
            (('mid', 'middle'), HeroRole.MIDDLE),
            (('roaming', 'roamer'), HeroRole.ROAMING),
        )
        matching_role = None
        for words, role in role_words_map:
            if self.contains_any_word(words):
                if matching_role:
                    return None
                matching_role = role
        return matching_role

    @cached_property
    def words(self):
        return self.text.strip('?').split(' ')

    @cached_property
    def ability_hotkey(self):
        if len(self.heroes) == 1:
            hotkeys = [
                a.hotkey
                for a in Ability.objects.filter(hero=self.heroes[0])
            ]
            hotkeys_in_question = [
                hotkey for hotkey in hotkeys
                if hotkey.lower() in self.words
            ]
            print(hotkeys_in_question)
            if len(hotkeys_in_question) == 1:
                return hotkeys_in_question[0]
        return None

    def contains_any_word(self, words):
        """Whether any of the words in words feature in the question text"""
        return any((word.lower() in self.text) for word in words)

    def get_responder(self):
        if SingleEnemyAdvantageResponse.matches_question(self):
            return SingleEnemyAdvantageResponse(self)
        if AbilityCooldownResponse.matches_question(self):
            return AbilityCooldownResponse(self)
        if AbilityUltimateResponse.matches_question(self):
            return AbilityUltimateResponse(self)
        if AbilityListResponse.matches_question(self):
            return AbilityListResponse(self)
        if AbilityHotkeyResponse.matches_question(self):
            return AbilityHotkeyResponse(self)

        logger.warning("Unable to parse question. %s", self)
        raise DoNotUnderstandQuestion

    def __str__(self):
        return "Question: '{}'. Abilities: {}, heroes: {}, role: {}.".format(
            self.text, self.abilities, self.heroes, self.role)


class PassiveAbilityError(BaseException):
    pass


class Response(object):
    def __init__(self):
        raise NotImplemented

    @staticmethod
    def matches_question(question):
        raise NotImplemented

    def generate_response(self):
        raise NotImplemented

    @staticmethod
    def comma_separate_with_final_and(words):
        """Returns a string with a ',' between each word, and an 'and' at the end
        For example, given the words ['hat', 'bag', 'cat'] this will return: 'hat, bag, and cat'
        """
        if len(words) == 2:  # no need for a comma
            return ' and '.join(words)
        return re.sub(
            r'^(.*), (.*?)$',
            r'\1, and \2',
            ', '.join(words))

    @staticmethod
    def parse_cooldown(ability):
        if not ability.cooldown:
            raise PassiveAbilityError
        return ability.cooldown.replace('/', ', ')


class AbilityListResponse(Response):
    def __init__(self, question):
        self.hero = question.heroes[0]

    @staticmethod
    def matches_question(question):
        return 'abilities' in question.text and len(question.heroes) == 1

    @staticmethod
    def order_abilities(abilities):
        """Orders the abilities by the posistion of the hotkey on the keyboard"""
        ordered_abilities = []
        for letter in 'qwerty':
            try:
                ordered_abilities.append(
                    next((a for a in abilities if a.hotkey == letter)))
            except StopIteration:
                pass
        ordered_abilities += [a for a in abilities if a not in ordered_abilities]
        return ordered_abilities

    def generate_response(self):
        abilities = Ability.objects.filter(hero=self.hero)
        names = [a.name for a in self.order_abilities(abilities)]
        return "{}'s abilities are {}".format(
            self.hero.name,
            self.comma_separate_with_final_and(names)
        )


class AbilityUltimateResponse(Response):
    def __init__(self, question):
        self.ability = Ability.objects.get(hero=question.heroes[0], is_ultimate=True)

    def matches_question(question):
        return 'ultimate' in question.text and len(question.heroes) == 1

    def generate_response(self):
        try:
            return "{}'s ultimate is {}, it's cooldown is {} seconds".format(
                self.ability.hero.name,
                self.ability.name,
                self.parse_cooldown(self.ability),
            )
        except PassiveAbilityError:
            return "{}'s ultimate is {}"


class AbilityHotkeyResponse(Response):
    def __init__(self, question):
        self.hero = question.heroes[0]
        self.ability = Ability.objects.get(hero=self.hero, hotkey=question.ability_hotkey)

    def matches_question(question):
        return len(question.heroes) == 1 and question.ability_hotkey is not None

    def generate_response(self):
        return "{}'s {} is {}".format(
            self.hero.name,
            self.ability.hotkey,
            self.ability.name,
        )


class AbilityCooldownResponse(Response):
    def __init__(self, question):
        self.ability = question.abilities[0]

    @staticmethod
    def matches_question(question):
        return (
            question.contains_any_word(('cool down' 'cooldown'))
            and len(question.abilities) == 1
        )

    def generate_response(self):
        try:
            return "The cooldown of {} is {} seconds".format(
                self.ability.name,
                self.parse_cooldown(self.ability),
            )
        except PassiveAbilityError:
            return "{} is a passive ability, with no cooldown".format(
                self.ability.name,
            )


class SingleEnemyAdvantageResponse(Response):
    def __init__(self, question):
        self.enemy = question.heroes[0]
        self.role = question.role

    @staticmethod
    def matches_question(question):
        return (
            question.contains_any_word(('strong', 'against', 'counter', 'counters'))
            and len(question.heroes) == 1
        )

    @classmethod
    def _advantage_hero_list(cls, heroes):
        names = [h.hero.name for h in heroes]
        result = cls.comma_separate_with_final_and(names)
        if len(names) == 1:
            result += ' is'
        else:
            result += ' are'
        return result

    @staticmethod
    def _filter_by_role(counters, role):
        if not role:
            return counters

        if role == HeroRole.CARRY:
            heroes = Hero.objects.filter(is_carry=True)
        elif role == HeroRole.MIDDLE:
            heroes = Hero.objects.filter(is_mid=True)
        elif role == HeroRole.SUPPORT:
            heroes = Hero.objects.filter(is_support=True)
        elif role == HeroRole.OFF_LANE:
            heroes = Hero.objects.filter(is_off_lane=True)
        elif role == HeroRole.JUNGLER:
            heroes = Hero.objects.filter(is_jungler=True)
        elif role == HeroRole.ROAMING:
            heroes = Hero.objects.filter(is_roaming=True)
        return counters.filter(hero__in=heroes)

    def generate_response(self):
        counters = Advantage.objects.filter(
            enemy=self.enemy, advantage__gte=0).order_by('-advantage')
        counters = self._filter_by_role(counters, self.role)
        hard_counters = counters.filter(advantage__gte=2)
        soft_counters = (c for c in counters[:8] if c not in hard_counters)
        response = None
        if hard_counters:
            response = '{} very strong against {}'.format(
                self._advantage_hero_list(hard_counters),
                self.enemy.name)
        if soft_counters:
            if response:
                response += '. {} also good'.format(self._advantage_hero_list(soft_counters))
            else:
                response = '{} good against {}'.format(
                    self._advantage_hero_list(soft_counters),
                    self.enemy.name)
        print(response)
        return response
