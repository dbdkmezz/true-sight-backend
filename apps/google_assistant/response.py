import re
import logging

from django.utils.functional import cached_property

from apps.hero_advantages.models import Hero, Advantage
from apps.hero_advantages.roles import HeroRole
from apps.hero_abilities.models import Ability, SpellImmunity

from .exceptions import DoNotUnderstandQuestion


logger = logging.getLogger(__name__)


class ResponseGenerator(object):
    @staticmethod
    def respond(question_text):
        question = QuestionParser(question_text)

        if len(question.abilities) == 1:
            if question.contains_any_word(('cool down', 'cooldown')):
                return AbilityCooldownResponse.respond(question)
            if question.contains_any_word(('spell immunity', 'black king', 'king bar', 'bkb')):
                return AbilitySpellImmunityResponse.respond(question)

        if len(question.heroes) == 1:
            if question.contains_any_word(('strong', 'against', 'counter', 'counters')):
                return SingleEnemyAdvantageResponse.respond(question)
            if question.contains_any_word(('ultimate', )):
                return AbilityUltimateResponse.respond(question)
            if question.contains_any_word(('abilities', )):
                return AbilityListResponse.respond(question)
            if question.ability_hotkey:
                return AbilityHotkeyResponse.respond(question)

        logger.warning("Unable to parse question. %s", question)
        raise DoNotUnderstandQuestion


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
                if a.hotkey
            ]
            hotkeys_in_question = [
                hotkey for hotkey in hotkeys
                if hotkey.lower() in self.words
            ]
            if len(hotkeys_in_question) == 1:
                return hotkeys_in_question[0]
        return None

    def contains_any_word(self, words):
        """Whether any of the words in words feature in the question text"""
        return any((word.lower() in self.text) for word in words)

    def __str__(self):
        return "Question: '{}'. Abilities: {}, heroes: {}, role: {}.".format(
            self.text, self.abilities, self.heroes, self.role)


class PassiveAbilityError(BaseException):
    pass


class Response(object):
    def __init__(self):
        raise NotImplemented

    @classmethod
    def respond(cls, question):
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


class AbilityResponse(Response):
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

    @staticmethod
    def parse_cooldown(ability):
        if not ability.cooldown:
            raise PassiveAbilityError
        return ability.cooldown.replace('/', ', ')

    @staticmethod
    def append_description_to_response(response, ability, only_if_short):
        if not ability.description or (only_if_short and len(ability.description) > 120):
            return response
        return "{}. {}".format(response, ability.description)

    @classmethod
    def append_cooldown_to_response(cls, response, ability):
        try:
            return "{}, it's cooldown is {} seconds".format(
                response,
                cls.parse_cooldown(ability),
            )
        except PassiveAbilityError:
            return response


class AbilityListResponse(AbilityResponse):
    @classmethod
    def respond(cls, question):
        hero = question.heroes[0]
        abilities = Ability.standard_objects.filter(hero=hero)
        names = [a.name for a in cls.order_abilities(abilities)]
        return "{}'s abilities are {}".format(
            hero.name,
            cls.comma_separate_with_final_and(names)
        )


class AbilityUltimateResponse(AbilityResponse):
    @classmethod
    def respond(cls, question):
        ability = Ability.objects.get(hero=question.heroes[0], is_ultimate=True)
        response = "{}'s ultimate is {}".format(
                ability.hero.name,
                ability.name,
            )
        response = cls.append_cooldown_to_response(response, ability)
        return cls.append_description_to_response(response, ability, True)


class AbilityHotkeyResponse(AbilityResponse):
    @classmethod
    def respond(cls, question):
        hero = question.heroes[0]
        ability = Ability.objects.get(hero=hero, hotkey=question.ability_hotkey)
        response = "{}'s {} is {}".format(
            hero.name,
            ability.hotkey,
            ability.name,
        )
        return cls.append_description_to_response(response, ability, True)


class AbilityCooldownResponse(AbilityResponse):
    @classmethod
    def respond(cls, question):
        ability = question.abilities[0]
        try:
            return "The cooldown of {} is {} seconds".format(
                ability.name,
                cls.parse_cooldown(ability),
            )
        except PassiveAbilityError:
            return "{} is a passive ability, with no cooldown".format(
                ability.name,
            )


class AbilitySpellImmunityResponse(AbilityResponse):
    @classmethod
    def respond(cls, question):
        ability = question.abilities[0]
        spell_immunity_map = {
            SpellImmunity.PIERCES: 'does pierce spell immunity',
            SpellImmunity.PARTIALLY_PIERCES: 'partially pierces spell immunity',
            SpellImmunity.DOES_NOT_PIERCE: 'does not pierce spell immunity',
        }
        response = "{} {}".format(
            ability.name,
            spell_immunity_map[ability.spell_immunity],
        )
        return cls.append_spell_immunity_detail_to_response(response, ability)

    @staticmethod
    def append_spell_immunity_detail_to_response(response, ability):
        if not ability.spell_immunity_detail:
            return response
        return "{}. {}".format(response, ability.spell_immunity_detail)


class SingleEnemyAdvantageResponse(Response):
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

    @classmethod
    def respond(cls, question):
        enemy = question.heroes[0]
        role = question.role
        counters = Advantage.objects.filter(
            enemy=enemy, advantage__gte=0).order_by('-advantage')
        counters = cls._filter_by_role(counters, role)
        hard_counters = counters.filter(advantage__gte=2)
        soft_counters = (c for c in counters[:8] if c not in hard_counters)
        response = None
        if hard_counters:
            response = '{} very strong against {}'.format(
                cls._advantage_hero_list(hard_counters),
                enemy.name)
        if soft_counters:
            if response:
                response += '. {} also good'.format(cls._advantage_hero_list(soft_counters))
            else:
                response = '{} good against {}'.format(
                    cls._advantage_hero_list(soft_counters),
                    enemy.name)
        print(response)
        return response
