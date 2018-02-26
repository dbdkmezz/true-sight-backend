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


class InnapropriateContextError(BaseException):
    pass


class ResponseGenerator(object):
    @classmethod
    def respond(cls, question_text, conversation_token=None):
        question = QuestionParser(question_text)

        context = Context.deserialise(conversation_token)
        if not context:
            context = Context.get_context_from_question(question)

        response, follow_up_context = context.generate_response(question)
        new_converstaion_token = None
        if follow_up_context:
            new_converstaion_token = follow_up_context.serialise()

        return response, new_converstaion_token


class Context(object):
    _can_be_used_for_next_context = False
    _can_respond_to_yes_response = False

    def __init__(self):
        self.useage_count = 0

    def serialise(self):
        result = self._serialise()
        result['context-class'] = type(self).__name__
        result['useage-count'] = self.useage_count
        return result

    def _serialise(self):
        return {}

    @staticmethod
    def deserialise(data):
        if not data:
            return None
        try:
            context_classes = (
                AbilityCooldownContext, AbilityDescriptionContext, AbilitySpellImmunityContext,
                AbilityUltimateContext, AbilityListContext,
            )
            klass = next(
                k for k in context_classes
                if data['context-class'] == k.__name__)
        except StopIteration:
            return None
        return klass._deserialise(data)

    @classmethod
    def _deserialise(cls, data):
        result = cls()
        result.useage_count = data.get('useage-count', 0)
        return result

    @staticmethod
    def get_context_from_question(question):
        """Returns the context to be used answering the question"""
        if len(question.abilities) == 1:
            if question.contains_any_string(('cool down', 'cooldown')):
                return AbilityCooldownContext()
            if question.contains_any_string(('spell immunity', 'black king', 'king bar', 'bkb')):
                return AbilitySpellImmunityContext()

        if len(question.heroes) == 1:
            if question.contains_any_string(('strong', 'against', 'counter', 'counters')):
                return SingleEnemyAdvantageContext()
            if question.contains_any_string(('ultimate', )):
                return AbilityUltimateContext()
            if question.contains_any_string(('abilities', )):
                return AbilityListContext()
            if question.ability_hotkey:
                return AbilityHotkeyContext()

        if len(question.heroes) == 2:
            return TwoHeroAdvantageContext()

        if len(question.abilities) == 1:
            return AbilityDescriptionContext()

        if len(question.heroes) == 1:
            return SingleEnemyAdvantageContext()

        failed_response_logger.warning("Unable to respond to question. %s", question)
        raise DoNotUnderstandQuestion

    def generate_response(self, question):
        try:
            response = self._generate_direct_response(question)
        except InnapropriateContextError:
            if self.useage_count == 0:
                # The current context is brand knew, and has just come from
                # get_context_from_question. This should never happen.
                raise

            # The current context is unable to answer the question,
            # let's get a new context from the question itself
            try:
                new_context = Context.get_context_from_question(question)
            except DoNotUnderstandQuestion:
                # The question doesn't include enough to get a new context,
                # But perhaps the response was yes or no and we can respond to that...
                if question.no:
                    raise Goodbye
                if question.yes and self._can_respond_to_yes_response:
                    return self._yes_response, self
                raise
            else:
                return new_context.generate_response(question)

        self.useage_count += 1
        if not response[-1:] in ('.', '?'):
            response += '.'

        if self._can_be_used_for_next_context:
            response = self._add_follow_up_question_to_response(response)
            return response, self
        else:
            return response, None

    def _add_follow_up_question_to_response(self, response):
        if self.useage_count == 1:
            follow_up_question = self._first_follow_up_question
        else:
            follow_up_question = self._second_follow_up_question
        return "{} {}".format(response, follow_up_question)

    def _generate_direct_response(self, question):
        raise NotImplemented


class SingleAbilityContext(Context):
    _can_be_used_for_next_context = True
    _first_follow_up_question = "Any other ability?"
    _second_follow_up_question = "Any others?"
    _can_respond_to_yes_response = True
    _yes_response = "Which ability?"


class AbilityCooldownContext(SingleAbilityContext):
    def _generate_direct_response(self, question):
        if len(question.abilities) == 1:
            return AbilityCooldownResponse.respond(question.abilities[0])
        raise InnapropriateContextError


class AbilityDescriptionContext(SingleAbilityContext):
    def _generate_direct_response(self, question):
        return AbilityDescriptionResponse.respond(question.abilities[0])


class AbilitySpellImmunityContext(SingleAbilityContext):
    def _generate_direct_response(self, question):
        return AbilitySpellImmunityResponse.respond(question.abilities[0])


class SingleHeroContext(Context):
    _can_be_used_for_next_context = True
    _first_follow_up_question = "Any other hero?"
    _second_follow_up_question = "Any others?"
    _can_respond_to_yes_response = True
    _yes_response = "Which hero?"


class AbilityUltimateContext(SingleHeroContext):
    def _generate_direct_response(self, question):
        return AbilityUltimateResponse.respond(question.heroes[0])


class AbilityListContext(SingleHeroContext):
    def _generate_direct_response(self, question):
        return AbilityListResponse.respond(question.heroes[0])


class AbilityHotkeyContext(Context):
    def _generate_direct_response(self, question):
        return AbilityHotkeyResponse.respond(question.heroes[0], question.ability_hotkey)


class SingleEnemyAdvantageContext(Context):
    def _generate_direct_response(self, question):
        return SingleEnemyAdvantageResponse.respond(question.heroes[0], question.role)


class TwoHeroAdvantageContext(Context):
    def _generate_direct_response(self, question):
        return TwoHeroAdvantageResponse.respond(question.heroes[0], question.heroes[1])
