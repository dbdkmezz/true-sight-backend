import re

from django.utils.functional import cached_property

from apps.hero_advantages.models import Hero
from apps.hero_abilities.models import Ability

from .exceptions import DoNotUnderstandQuestion


class QuestionParser(object):
    def __init__(self, question_text):
        self.text = question_text.lower()

    @cached_property
    def abilities(self):
        return [
            a for a in Ability.objects.all()
            if a.name.lower() in self.text
        ]

    @cached_property
    def heroes(self):
        return [
            h for h in Hero.objects.all()
            if h.name.lower() in self.text
        ]

    def get_responder(self):
        if AbilityCooldownResponse.matches_question(self):
            return AbilityCooldownResponse(self)
        if AbilityListResponse.matches_question(self):
            return AbilityListResponse(self)
        raise DoNotUnderstandQuestion


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
        return re.sub(
            r'^(.*), (.*?)$',
            r'\1, and \2',
            ', '.join(words))


class AbilityListResponse(Response):
    def __init__(self, question):
        self.hero = question.heroes[0]

    @staticmethod
    def matches_question(question):
        return 'abilities' in question.text and len(question.heroes) == 1

    def generate_response(self):
        abilities = [a.name for a in Ability.objects.filter(hero=self.hero)]
        return "{}'s abilities are {}".format(
            self.hero.name,
            self.comma_separate_with_final_and(abilities)
        )


class AbilityCooldownResponse(Response):
    def __init__(self, question):
        self.ability = question.abilities[0]

    @staticmethod
    def matches_question(question):
        return 'cooldown' in question.text and len(question.abilities) == 1

    def generate_response(self):
        return "The cooldown of {} is {} seconds".format(
            self.ability.name,
            self.ability.cooldown,
        )
