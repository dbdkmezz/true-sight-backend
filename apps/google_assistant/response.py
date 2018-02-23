import logging

from .exceptions import DoNotUnderstandQuestion, Goodbye
from .question_parser import QuestionParser
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


class Context(object):
    def __init__(self, useage_count=0):
        self.useage_count = useage_count

    _follow_up_question = None

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
        response, next_context = self._generate_direct_response(question)
        if not response[-1:] in ('.', '?'):
            response += '.'
        if next_context and next_context._follow_up_question:
            response += " {}".format(next_context._follow_up_question)
        return response, next_context

    def _generate_direct_response(self, question):
        raise NotImplemented


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
    _follow_up_question = "Any other ability?"

    def _generate_direct_response(self, question):
        self.useage_count += 1
        if len(question.abilities) == 1:
            if False and self.useage_count == 0:
                self._follow_up_question = "Any other ability?"
            else:
                self._follow_up_question = "Any others?"
            return AbilityCooldownResponse.respond(question.abilities[0]), self

        try:
            return CleanContext()._generate_direct_response(question)
        except DoNotUnderstandQuestion:
            if question.yes:
                self._follow_up_question = None
                return "Which ability?", self
            if question.no:
                raise Goodbye
            raise
