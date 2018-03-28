import logging

from apps.hero_advantages.models import Hero

from .exceptions import DoNotUnderstandQuestion, Goodbye
from .question_parser import QuestionParser
from .response_text import (
    AbilityDescriptionResponse, AbilityListResponse, AbilityUltimateResponse,
    AbilityHotkeyResponse, AbilityCooldownResponse, AbilitySpellImmunityResponse,
    SingleEnemyAdvantageResponse, TwoHeroAdvantageResponse, IntroductionResponse,
    DescriptionResponse, SampleQuestionResponse
)


logger = logging.getLogger(__name__)
failed_response_logger = logging.getLogger('failed_response')


class InnapropriateContextError(BaseException):
    pass


class ResponseGenerator(object):
    @classmethod
    def respond(cls, question_text, conversation_token=None, user_id=None):
        question = QuestionParser(question_text, user_id)

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
        return {
            'context-class': type(self).__name__,
            'useage-count': self.useage_count,
        }

    @staticmethod
    def deserialise(data):
        if not data:
            return None
        try:
            context_classes = (
                AbilityCooldownContext, AbilityDescriptionContext, AbilitySpellImmunityContext,
                AbilityUltimateContext, AbilityListContext, EnemyAdvantageContext, FreshContext,
                IntroductionContext, DescriptionContext,
            )
            klass = next(
                k for k in context_classes
                if data['context-class'] == k.__name__)
        except StopIteration:
            return None

        result = klass()
        result._deserialise(data)
        return result

    def _deserialise(self, data):
        self.useage_count = data.get('useage-count', 0)  # no get?

    SPELL_IMMUNITY_WORDS = ('spell immunity', 'spell amenity', 'black king', 'king bar', 'bkb')
    COUNTER_WORDS = ('strong', 'against', 'counter', 'counters')
    ABILITY_WORDS = ('abilities', 'spells')
    ULTIMATE_WORDS = ('ultimate', )

    @classmethod
    def get_context_from_question(cls, question):
        """Returns the context to be used answering the question"""
        if not question.text:
            return IntroductionContext()

        if len(question.abilities) == 1:
            if question.contains_any_string(('cool down', 'cooldown')):
                return AbilityCooldownContext()
            if question.contains_any_string(cls.SPELL_IMMUNITY_WORDS):
                return AbilitySpellImmunityContext()

        if len(question.heroes) == 1:
            if question.contains_any_string(cls.COUNTER_WORDS):
                return EnemyAdvantageContext(question.heroes[0])
            if question.contains_any_string(cls.ULTIMATE_WORDS):
                return AbilityUltimateContext()
            if question.contains_any_string(cls.ABILITY_WORDS):
                return AbilityListContext()
            if question.ability_hotkey:
                return AbilityHotkeyContext()

        if len(question.heroes) == 2:
            return EnemyAdvantageContext(question.heroes[1])

        if len(question.abilities) == 1:
            return AbilityDescriptionContext()

        if len(question.heroes) == 1:
            return EnemyAdvantageContext(question.heroes[0])

        if question.contains_any_string((
                'what can you do', 'what do you do', 'how does this work')):
            return DescriptionContext()

        failed_response_logger.warning("%s", question)
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
                    return FreshContext().generate_response(question)
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


class ContextWithBlankFollowUpQuestions(Context):
    """Context which doesn't append a follow up question.

    This may be used when the response itself includes a follow up question.
    """
    _can_be_used_for_next_context = True

    def _add_follow_up_question_to_response(self, response):
        return response


class IntroductionContext(ContextWithBlankFollowUpQuestions):
    def _generate_direct_response(self, question):
        if self.useage_count > 0:
            raise InnapropriateContextError
        return IntroductionResponse.respond(user_id=question.user_id)


class DescriptionContext(ContextWithBlankFollowUpQuestions):
    def _generate_direct_response(self, question):
        if self.useage_count > 0:
            raise InnapropriateContextError
        return DescriptionResponse.respond(user_id=question.user_id)


class FreshContext(ContextWithBlankFollowUpQuestions):
    """A clean context, which asks the user what they'd like to know, giving sample questions"""
    def _generate_direct_response(self, question):
        if self.useage_count > 0:
            if question.no:
                raise Goodbye
            raise InnapropriateContextError
        return SampleQuestionResponse.respond(user_id=question.user_id)


class SingleAbilityContext(Context):
    _can_be_used_for_next_context = True
    _first_follow_up_question = "Any other ability?"
    _second_follow_up_question = "Any others?"
    _can_respond_to_yes_response = True
    _yes_response = "Which ability?"


class AbilityCooldownContext(SingleAbilityContext):
    def _generate_direct_response(self, question):
        if len(question.abilities) == 1:
            return AbilityCooldownResponse.respond(question.abilities[0], user_id=question.user_id)
        raise InnapropriateContextError


class AbilityDescriptionContext(SingleAbilityContext):
    def _generate_direct_response(self, question):
        if len(question.abilities) < 1:  # or == 1?
            raise InnapropriateContextError
        return AbilityDescriptionResponse.respond(question.abilities[0], user_id=question.user_id)


class AbilitySpellImmunityContext(SingleAbilityContext):
    def _generate_direct_response(self, question):
        if len(question.abilities) < 1:  # or == 1?
            raise InnapropriateContextError
        return AbilitySpellImmunityResponse.respond(question.abilities[0], user_id=question.user_id)


class SingleHeroContext(Context):
    _can_be_used_for_next_context = True
    _first_follow_up_question = "Any other hero?"
    _second_follow_up_question = "Any others?"
    _can_respond_to_yes_response = True
    _yes_response = "Which hero?"

    @classmethod
    def _check_context_is_appropriate(cls, question):
        if len(question.heroes) < 1:
            raise InnapropriateContextError
        if question.contains_any_string(cls.COUNTER_WORDS):
            raise InnapropriateContextError


class AbilityUltimateContext(SingleHeroContext):
    def _generate_direct_response(self, question):
        self._check_context_is_appropriate(question)
        return AbilityUltimateResponse.respond(question.heroes[0], user_id=question.user_id)


class AbilityListContext(SingleHeroContext):
    def _generate_direct_response(self, question):
        self._check_context_is_appropriate(question)
        return AbilityListResponse.respond(question.heroes[0], user_id=question.user_id)


class AbilityHotkeyContext(Context):
    def _generate_direct_response(self, question):
        if len(question.heroes) < 1:
            raise InnapropriateContextError
        return AbilityHotkeyResponse.respond(
            question.heroes[0], question.ability_hotkey, user_id=question.user_id)


class EnemyAdvantageContext(Context):
    _can_be_used_for_next_context = True
    _first_follow_up_question = "Any specific hero you'd like to know about?"
    _second_follow_up_question = "Any others?"

    def __init__(self, enemy=None):
        super().__init__()
        self.enemy = enemy

    def serialise(self):
        result = super().serialise()
        result['enemy'] = self.enemy.name
        return result

    def _deserialise(self, data):
        super()._deserialise(data)
        self.enemy = Hero.objects.get(name=data['enemy'])

    def _generate_direct_response(self, question):
        if len(question.heroes) < 1:
            raise InnapropriateContextError
        if (
                len(question.heroes) == 1
                and question.contains_any_string(self.ABILITY_WORDS + self.ULTIMATE_WORDS)):
            raise InnapropriateContextError
        all_heroes = set(question.heroes + [self.enemy])
        if len(all_heroes) == 2:
            other_hero = all_heroes.difference(set([self.enemy])).pop()
            return TwoHeroAdvantageResponse.respond(
                hero=other_hero, enemy=self.enemy, user_id=question.user_id)
        if len(all_heroes) == 1:
            return SingleEnemyAdvantageResponse.respond(
                all_heroes.pop(), question.role, user_id=question.user_id)
        raise InnapropriateContextError
