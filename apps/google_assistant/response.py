import logging

from django.utils.functional import cached_property

from apps.hero_advantages.roles import HeroRole
from apps.hero_advantages.models import Hero
from apps.hero_abilities.models import Ability

from .exceptions import DoNotUnderstandQuestion, Goodbye
from .response_text import (
    AbilityDescriptionResponse, AbilityListResponse, AbilityUltimateResponse,
    AbilityHotkeyResponse, AbilityCooldownResponse, AbilitySpellImmunityResponse,
    SingleEnemyAdvantageResponse, TwoHeroAdvantageResponse,
)


logger = logging.getLogger(__name__)
failed_response_logger = logging.getLogger('failed_response')


class ResponseGenerator(object):
    @classmethod
    def respond(cls, question_text, conversation_token=None):
        question = QuestionParser(question_text)

        context = Context.deserialise(conversation_token)
        response, follow_up_context = context.generate_response(question)
        new_converstaion_token = None
        if follow_up_context:
            new_converstaion_token = follow_up_context.serialise()

        return response, new_converstaion_token


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
            if self.contains_any_string(h.aliases)
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
            if self.contains_any_string(words):
                if matching_role:
                    return None
                matching_role = role
        return matching_role

    @cached_property
    def words(self):
        return self.text.strip('?').strip('.').strip(',').split(' ')

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

    def contains_any_string(self, strings_to_look_for):
        """Whether any of strings in strings_to_look_for feature in the question text"""
        return any((s.lower() in self.text) for s in strings_to_look_for)

    def contains_any_word(self, words_to_look_for):
        """Whether any of the words in words_to_look_for feature in the question as a whole word"""
        print(self.words)
        return any((w in self.words) for w in words_to_look_for)

    @cached_property
    def yes(self):
        return self.contains_any_word(('yes', 'yep', 'yeah'))

    @cached_property
    def no(self):
        return self.contains_any_word(('no', 'nope'))


class Context(object):
    def __init__(self, useage_count=0):
        self.useage_count = useage_count

    disable_follow_up_question = False

    def serialise(self):
        result = self._serialise()
        result['context-class'] = type(self).__name__
        result['useage_count'] = self.useage_count
        return result

    def _serialise(self):
        return {}

    @staticmethod
    def deserialise(data):
        if not data:
            klass = CleanContext
        else:
            try:
                klass = next(
                    k for k in (AbilityCooldownContext, )
                    if data['context-class'] == k.__name__)
            except StopIteration:
                klass = CleanContext
        return klass._deserialise(data)

    @classmethod
    def _deserialise(cls, data):
        return cls()

    def generate_response(self, question):
        response, follow_up_context = self._generate_direct_response(question)
        if not response[-1:] in ('.', '?'):
            response += '.'
        if follow_up_context and not follow_up_context.disable_follow_up_question:
            follow_up_question = follow_up_context._follow_up_question()
            if follow_up_question:
                response += " {}".format(follow_up_question)
        return response, follow_up_context

    def _generate_direct_response(self, question):
        raise NotImplemented

    def _follow_up_question(self):
        return None


class CleanContext(Context):
    def _generate_direct_response(self, question):
        if len(question.abilities) == 1:
            ability = question.abilities[0]
            if question.contains_any_string(('cool down', 'cooldown')):
                return AbilityCooldownResponse.respond(ability), AbilityCooldownContext()
            if question.contains_any_string(('spell immunity', 'black king', 'king bar', 'bkb')):
                return AbilitySpellImmunityResponse.respond(ability), None

        if len(question.heroes) == 1:
            hero = question.heroes[0]
            if question.contains_any_string(('strong', 'against', 'counter', 'counters')):
                return SingleEnemyAdvantageResponse.respond(hero, question.role), None
            if question.contains_any_string(('ultimate', )):
                return AbilityUltimateResponse.respond(hero), None
            if question.contains_any_string(('abilities', )):
                return AbilityListResponse.respond(hero), None
            if question.ability_hotkey:
                return AbilityHotkeyResponse.respond(hero, question.ability_hotkey), None

        if len(question.heroes) == 2:
            return TwoHeroAdvantageResponse.respond(question.heroes[0], question.heroes[1]), None

        if len(question.abilities) == 1:
            return AbilityDescriptionResponse.respond(question.abilities[0]), None

        if len(question.heroes) == 1:
            return SingleEnemyAdvantageResponse.respond(question.heroes[0]. question.role), None

        failed_response_logger.warning("Unable to respond to question. %s", question)
        raise DoNotUnderstandQuestion


class AbilityCooldownContext(Context):
    def _generate_direct_response(self, question):
        print(question)
        if len(question.abilities) == 1:
            return (
                AbilityCooldownResponse.respond(question.abilities[0]),
                AbilityCooldownContext(self.useage_count + 1))

        try:
            return CleanContext()._generate_direct_response(question)
        except DoNotUnderstandQuestion:
            if question.yes:
                self.disable_follow_up_question = True
                return "Which ability?", self
            if question.no:
                raise Goodbye
            raise

    def _follow_up_question(self):
        if self.useage_count == 0:
            return "Would you like to know the cooldown of another ability?"
        return "Any other abilities?"
