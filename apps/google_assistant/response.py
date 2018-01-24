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

    def get_responder(self):
        if AbilityCooldownResponse.matches_question(self):
            return AbilityCooldownResponse(self)
        if AbilityUltimateResponse.matches_question(self):
            return AbilityUltimateResponse(self)
        if AbilityListResponse.matches_question(self):
            return AbilityListResponse(self)
        if AbilityHotkeyResponse.matches_question(self):
            return AbilityHotkeyResponse(self)
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
        abilities = [a for a in Ability.objects.filter(hero=self.hero)]
        names = (a.name for a in self.order_abilities(abilities))
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
        return "{}'s ultimate is {}, it's cooldown is {} seconds".format(
            self.ability.hero.name,
            self.ability.name,
            self.ability.cooldown,
        )


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
        return 'cooldown' in question.text and len(question.abilities) == 1

    def generate_response(self):
        return "The cooldown of {} is {} seconds".format(
            self.ability.name,
            self.ability.cooldown,
        )
