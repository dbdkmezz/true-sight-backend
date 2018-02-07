import re
import logging

from django.utils.functional import cached_property

from apps.metadata.models import ResponderUse
from apps.hero_advantages.roles import HeroRole
from apps.hero_advantages.models import Hero, Advantage
from apps.hero_abilities.models import Ability, SpellImmunity

from .exceptions import DoNotUnderstandQuestion


logger = logging.getLogger(__name__)
failed_response_logger = logging.getLogger('failed_response')


class ResponseGenerator(object):
    @classmethod
    def respond(cls, question_text, context=None):
        question = QuestionParser(question_text)

        responder, context = cls._get_responder(question, context)
        if not responder:
            failed_response_logger.warning("Unable to respond to question. %s", question)
            raise DoNotUnderstandQuestion

        ResponderUse.log_use(type(responder).__name__)
        return responder.respond(), context.serialise()

    @staticmethod
    def _get_responder(question, context):
        if len(question.abilities) == 1:
            if (
                    question.contains_any_word(('cool down', 'cooldown'))
                    or context == AbilityCooldownContext()
            ):
                return AbilityCooldownResponse(question), AbilityCooldownContext(question)
            if question.contains_any_word(('spell immunity', 'black king', 'king bar', 'bkb')):
                return AbilitySpellImmunityResponse(question)

        if len(question.heroes) == 1:
            if question.contains_any_word(('strong', 'against', 'counter', 'counters')):
                return SingleEnemyAdvantageResponse(question)
            if question.contains_any_word(('ultimate', )):
                return AbilityUltimateResponse(question)
            if question.contains_any_word(('abilities', )):
                return AbilityListResponse(question)
            if question.ability_hotkey:
                return AbilityHotkeyResponse(question)

        if len(question.heroes) == 2:
            return TwoHeroAdvantageResponse(question)

        if len(question.abilities) == 1:
            return AbilityDescriptionResponse(question)

        if len(question.heroes) == 1:
            return SingleEnemyAdvantageResponse(question)


class QuestionParser(object):
    def __init__(self, question_text):
        self.text = question_text.lower()

    def __str__(self):
        return "Question: '{}'. Abilities: {}, heroes: {}, role: {}.".format(
            self.text, self.abilities, self.heroes, self.role)

    @cached_property
    def abilities(self):
        """Returns a list of all abilities found in the question.

        Does not include the names of abilities found whose name is a substring of another ability
        whose name is in the question.
        E.g. if 'Chemical Rage' is in the question then this will not return the ability 'Rage'.
        """
        abilities_found = [
            a for a in Ability.objects.all()
            if a.name and a.name.lower() in self.text
        ]
        result = []
        for ability in abilities_found:
            other_ability_names = [a.name for a in abilities_found if a != ability]
            if not any((ability.name in n) for n in other_ability_names):
                result.append(ability)
        return result

    @cached_property
    def heroes(self):
        result = [
            h for h in Hero.objects.all()
            if self.contains_any_word(h.aliases)
        ]
        if len(result) < 1:
            return result

        # We need to order them in the order they are in the text
        positions = {}
        for hero in result:
            for alias in hero.aliases:
                position = self.text.find(alias.lower())
                if position != -1:
                    if not positions.get(hero) or position < positions['hero']:
                        positions[hero] = position
        return [k for k in sorted(positions, key=positions.get)]

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


class Response(object):
    def respond(self):
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


class PassiveAbilityError(BaseException):
    pass


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
        if not ability.cooldown:
            return response

        if not response[-1:] in ('.', ','):
            response += ','
        return "{} its cooldown is {} seconds".format(
            response,
            cls.parse_cooldown(ability),
        )


class AbilityDescriptionResponse(AbilityResponse):
    def __init__(self, question):
        self.ability = question.abilities[0]

    def respond(self):
        response = "{}'s ability {}".format(self.ability.hero, self.ability.name)
        response = self.append_description_to_response(response, self.ability, False)
        return self.append_cooldown_to_response(response, self.ability)


class AbilityListResponse(AbilityResponse):
    def __init__(self, question):
        self.hero = question.heroes[0]

    def respond(self):
        abilities = Ability.standard_objects.filter(hero=self.hero)
        names = [a.name for a in self.order_abilities(abilities)]
        return "{}'s abilities are {}".format(
            self.hero.name,
            self.comma_separate_with_final_and(names)
        )


class AbilityUltimateResponse(AbilityResponse):
    def __init__(self, question):
        self.hero = question.heroes[0]

    def respond(self):
        try:
            self.ability = Ability.objects.get(hero=self.hero, is_ultimate=True)
        except Ability.MultipleObjectsReturned:
            abilities = Ability.objects.filter(hero=self.hero, is_ultimate=True)
            return "{} has multiple ultimates: {}".format(
                self.hero.name,
                self.comma_separate_with_final_and([a.name for a in abilities]),
            )

        response = "{}'s ultimate is {}".format(
                self.hero.name,
                self.ability.name,
            )
        response = self.append_cooldown_to_response(response, self.ability)
        return self.append_description_to_response(response, self.ability, True)


class AbilityHotkeyResponse(AbilityResponse):
    def __init__(self, question):
        self.hero = question.heroes[0]
        self.ability = Ability.objects.get(hero=self.hero, hotkey=question.ability_hotkey)

    def respond(self):
        response = "{}'s {} is {}".format(
            self.hero.name,
            self.ability.hotkey,
            self.ability.name,
        )
        return self.append_description_to_response(response, self.ability, True)


class AbilityCooldownResponse(AbilityResponse):
    def __init__(self, question):
        self.ability = question.abilities[0]

    def respond(self):
        try:
            return "The cooldown of {} is {} seconds".format(
                self.ability.name,
                self.parse_cooldown(self.ability),
            )
        except PassiveAbilityError:
            return "{} is a passive ability, with no cooldown".format(
                self.ability.name,
            )


class AbilitySpellImmunityResponse(AbilityResponse):
    def __init__(self, question):
        self.ability = question.abilities[0]

    def respond(self):
        spell_immunity_map = {
            SpellImmunity.PIERCES: 'does pierce spell immunity',
            SpellImmunity.PARTIALLY_PIERCES: 'partially pierces spell immunity',
            SpellImmunity.DOES_NOT_PIERCE: 'does not pierce spell immunity',
        }
        response = "{} {}".format(
            self.ability.name,
            spell_immunity_map[self.ability.spell_immunity],
        )
        return self.append_spell_immunity_detail_to_response(response, self.ability)

    @staticmethod
    def append_spell_immunity_detail_to_response(response, ability):
        if not ability.spell_immunity_detail:
            return response
        return "{}. {}".format(response, ability.spell_immunity_detail)


class AdvantageResponse(Response):
    STRONG_ADVANTAGE = 2


class SingleEnemyAdvantageResponse(AdvantageResponse):
    def __init__(self, question):
        self.enemy = question.heroes[0]
        self.role = question.role

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

    def respond(self):
        counters = Advantage.objects.filter(
            enemy=self.enemy, advantage__gte=0).order_by('-advantage')
        counters = self._filter_by_role(counters, self.role)
        hard_counters = counters.filter(advantage__gte=self.STRONG_ADVANTAGE)
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
        return response


class TwoHeroAdvantageResponse(AdvantageResponse):
    def __init__(self, question):
        self.hero = question.heroes[0]
        self.enemy = question.heroes[1]

    def respond(self):
        advantage = Advantage.objects.get(hero=self.hero, enemy=self.enemy).advantage
        return "{hero} is {description} against {enemy}. {hero}'s advantage is {advantage}".format(
            hero=self.hero,
            description=self.get_advantage_description_text(advantage),
            enemy=self.enemy,
            advantage=advantage,
        )

    @classmethod
    def get_advantage_description_text(cls, advantage):
        if advantage > cls.STRONG_ADVANTAGE:
            return 'very strong'
        elif advantage > 0:
            return 'not bad'
        elif advantage > (-1 * cls.STRONG_ADVANTAGE):
            return 'not great'
        else:
            return 'terrible'


class Context(object):
    def __init__(self, question):
        raise NotImplemented

    def __eq__(self, serialised_other):
        return serialised_other['context-class'] == type(self).__name__

    def serialise(self):
        result = self._serialise
        result['context-class'] = type(self).__name__
        return result

    # this or eq override
    def deserialise(self): 


class AbilityCooldownContext(Context):
    def __init__(self, question):
        pass

    def _serialise(self):
        return {}
