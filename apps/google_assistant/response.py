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
    _next_context = None

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
        self.useage_count += 1
        try:
            response = self._generate_direct_response(question)
        except InnapropriateContextError:
            # The current context is unable to answer the question,
            # let's get a new context from the question itself
            try:
                new_context = Context.get_context_from_question(question)
                assert type(self) != type(new_context)
                return new_context._generate_direct_response(question)
            except DoNotUnderstandQuestion:
                # The question doesn't include enough to get a new context.
                # But perhaps the response was yes or no and we can respond to that?
                if self._can_respond_to_yes_no_responses:
                    if question.yes:
                        return self._yes_response, self
                    if question.no:
                        raise Goodbye
                raise

        if not response[-1:] in ('.', '?'):
            response += '.'

        next_context = False
        if self._can_be_used_for_next_context:
            next_context = self
            if next_context.useage_count == 1:
                follow_up_question = next_context._first_follow_up_question
            else:
                follow_up_question = next_context._second_follow_up_question
            response = "{} {}".format(response, follow_up_question)

        return response, next_context

    @property
    def _can_respond_to_yes_no_responses(self):
        return False

    @property
    def _can_be_used_for_next_context(self):
        return False

    def _generate_direct_response(self, question):
        raise NotImplemented


class SingleAbilityContext(Context):
    _first_follow_up_question = "Any other ability?"
    _second_follow_up_question = "Any others?"
    _yes_response = "Which ability?"

    @property
    def _can_respond_to_yes_no_responses(self):
        return True

    @property
    def _can_be_used_for_next_context(self):
        return True


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
    _first_follow_up_question = "Any other hero?"
    _second_follow_up_question = "Any others?"
    _yes_response = "Which hero?"

    @property
    def _can_respond_to_yes_no_responses(self):
        return True

    @property
    def _can_be_used_for_next_context(self):
        return True


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
