import string

from django.utils.functional import cached_property

from apps.hero_advantages.roles import HeroRole
from apps.hero_advantages.models import Hero
from apps.hero_abilities.models import Ability


class QuestionParser(object):
    def __init__(self, question_text, user_id):
        try:
            self.text = question_text.lower()
        except AttributeError:
            #  question_text is None
            self.text = ""
        self.user_id = user_id

    def __str__(self):
        return "User: {}. Question: '{}'. Abilities: {}, heroes: {}, role: {}.".format(
            self.user_id, self.text, self.abilities, self.heroes, self.role)

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
        # Find all the heroes referred to in the text, if we are using a two letter abbreviation
        # of a heroes name then it must be a whole word
        result = {}
        for hero in Hero.objects.all():
            for alias in (a.lower() for a in hero.aliases):
                if (
                        (len(alias) > 2 and alias in self.text)
                        or (len(alias) == 2 and alias in self.words)
                ):
                    result[alias] = hero

        if len(result) <= 1:
            return list(result.values())

        # Remove heroes which share common substrings by removing the those that we have already
        # found, starting with the longer aliases.
        no_overlaps_text = self.text
        for alias in sorted(result, key=len, reverse=True):
            if alias in no_overlaps_text:
                no_overlaps_text = no_overlaps_text.replace(alias, '')
            else:
                del result[alias]

        if len(result) <= 1:
            return list(result.values())

        # Order the heroes in the order they are in the text
        positions = {}
        for alias, hero in result.items():
            if len(alias) > 2:
                position = self.text.find(alias)
            else:
                # this excludes punctution, but it's close enough
                word_number = self.words.index(alias)
                position = sum((1 + len(word)) for word in self.words[:word_number])
            if position != -1:
                if not positions.get(hero) or position < positions[hero]:
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

    _punctuation_remover = str.maketrans('', '', string.punctuation)

    @cached_property
    def words(self):
        return self.text.translate(self._punctuation_remover).split(' ')

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
        return any((w in self.words) for w in words_to_look_for)

    @cached_property
    def yes(self):
        return self.contains_any_word(('yes', 'yep', 'yeah'))

    @cached_property
    def no(self):
        return self.contains_any_word(('no', 'nope'))
