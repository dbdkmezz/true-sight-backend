import re
import random
import logging

from apps.hero_advantages.roles import HeroRole
from apps.metadata.models import ResponderUse
from apps.hero_advantages.models import Hero, Advantage
from apps.hero_abilities.models import Ability, SpellImmunity, DamageType


logger = logging.getLogger(__name__)


class PassiveAbilityError(BaseException):
    pass


class Response(object):
    def __init__(self):
        raise NotImplemented

    @classmethod
    def respond(cls, *args, **kwargs):
        ResponderUse.log_use(cls.__name__, kwargs['user_id'])
        del kwargs['user_id']
        return cls._respond(*args, **kwargs)

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


class IntroductionResponse(Response):
    TRADEMARKS = (
        "Dota 2 is a registered trademark of Valve Corporation, all Dota 2 content is "
        "property of Valve Corporation, this Application is not affiliated with Valve "
        "Corporation."
    )

    @classmethod
    def _respond(cls):
        return "{} {} {} {} ".format(
            DescriptionResponse.DESCRIPTION,
            cls.TRADEMARKS,
            "What would you like to know?",
            SampleQuestionResponse.sample_question(),
        )


class DescriptionResponse(Response):
    DESCRIPTION = (
        "Hi, I'm the Gem of True Sight. "
        "You can ask me about Dota hero counters, and abilities, such as their cooldown or "
        "whether they are blocked by BKB."
    )

    @classmethod
    def _respond(cls):
        return "{} {}".format(
            cls.DESCRIPTION,
            SampleQuestionResponse.sample_question(),
        )


class SampleQuestionResponse(Response):
    @staticmethod
    def sample_question():
        return "For example, you could ask me '" + random.choice((
            "Which mid heroes are good against Invoker?",
            "What is the cooldown of Monkey King's ultimate?",
            "Does Assassinate go through BKB?",
            "What are Dark Willow's abilities?",
        ))

    @classmethod
    def _respond(cls):
        return "Is there anything else you'd like to know? {}".format(cls.sample_question())


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
    def parse_damange_type(damage_type):
        damange_type_map = {
            DamageType.MAGICAL: 'magical',
            DamageType.PHYSICAL: 'physical',
            DamageType.PURE: 'pure',
        }
        return damange_type_map[damage_type]

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
    @classmethod
    def _respond(cls, ability):
        response = "{}'s ability {}".format(ability.hero, ability.name)
        response = cls.append_description_to_response(response, ability, False)
        return cls.append_cooldown_to_response(response, ability)


class AbilityListResponse(AbilityResponse):
    @classmethod
    def _respond(cls, hero):
        abilities = Ability.standard_objects.filter(hero=hero)
        names = [a.name for a in cls.order_abilities(abilities)]
        return "{}'s abilities are {}".format(
            hero.name,
            cls.comma_separate_with_final_and(names)
        )


class AbilityUltimateResponse(AbilityResponse):
    @classmethod
    def _respond(cls, hero):
        try:
            ability = Ability.objects.get(hero=hero, is_ultimate=True)
        except Ability.MultipleObjectsReturned:
            logger.warn("Multiple ultimate response.")
            abilities = Ability.objects.filter(hero=hero, is_ultimate=True)
            return "{} has multiple ultimates: {}".format(
                hero.name,
                cls.comma_separate_with_final_and([a.name for a in abilities]),
            )

        response = "{}'s ultimate is {}".format(
                hero.name,
                ability.name,
            )
        response = cls.append_cooldown_to_response(response, ability)
        return cls.append_description_to_response(response, ability, True)


class AbilityHotkeyResponse(AbilityResponse):
    @classmethod
    def _respond(cls, hero, ability_hotkey):
        ability = Ability.objects.get(hero=hero, hotkey=ability_hotkey)
        response = "{}'s {} is {}".format(
            hero.name,
            ability.hotkey,
            ability.name,
        )
        return cls.append_description_to_response(response, ability, True)


class AbilityCooldownResponse(AbilityResponse):
    @classmethod
    def _respond(cls, ability):
        try:
            return "The cooldown of {} is {} seconds".format(
                ability.name,
                cls.parse_cooldown(ability),
            )
        except PassiveAbilityError:
            return "{} is a passive ability, with no cooldown".format(
                ability.name,
            )


class AbilityDamangeTypeResponse(AbilityResponse):
    @classmethod
    def _respond(cls, ability):
        if not ability.damage_type:
            return "{} is a passive ability, with no cooldown".format(
                ability.name,
            )
        response = "{} does {} damange".format(
            ability.name,
            cls.parse_damange_type(ability.damage_type),
        )
        if ability.aghanims_damage_type and ability.aghanims_damage_type != ability.damage_type:
            response += ", and with Aghanim's Scepter it does {} damage".format(
                cls.parse_damange_type(ability.aghanims_damage_type))
        return response


class AbilitySpellImmunityResponse(AbilityResponse):
    @classmethod
    def _respond(cls, ability):
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


class AdvantageResponse(Response):
    STRONG_ADVANTAGE = 2


class SingleEnemyAdvantageResponse(AdvantageResponse):
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
    def _respond(cls, enemy, role):
        counters = Advantage.objects.filter(
            enemy=enemy, advantage__gte=0).order_by('-advantage')
        counters = cls._filter_by_role(counters, role)
        hard_counters = counters.filter(advantage__gte=cls.STRONG_ADVANTAGE)
        soft_counters = [c for c in counters[:8] if c not in hard_counters]
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
        return response


class TwoHeroAdvantageResponse(AdvantageResponse):
    @classmethod
    def _respond(cls, hero, enemy):
        advantage = Advantage.objects.get(hero=hero, enemy=enemy).advantage
        return "{hero} is {description} against {enemy}. {hero}'s advantage is {advantage}".format(
            hero=hero,
            description=cls.get_advantage_description_text(advantage),
            enemy=enemy,
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
