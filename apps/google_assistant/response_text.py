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
        '<emphasis level="reduced">'
        'Dota 2 is a registered trademark of Valve Corporation, all Dota 2 content is '
        'property of Valve Corporation, this Application is not affiliated with Valve '
        'Corporation.'
        '</emphasis>'
    )

    @classmethod
    def _respond(cls):
        return "Hi, {} {} {} {}".format(
            DescriptionResponse.DESCRIPTION,
            cls.TRADEMARKS,
            "What would you like to know?",
            SampleQuestionResponse.sample_question(),
        )


class DescriptionResponse(Response):
    DESCRIPTION = (
        "I'm the Gem of True Sight. "
        "You can ask me about Dota hero counters, and abilities "
        "(such as their cooldown, damage type, or whether they are blocked by BKB)."
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
        return "For example, you could ask me '{}'".format(random.choice((
            "Which mid heroes are good against Invoker?",
            "Which supports counter Disruptor?",
            "Which roaming heroes counter Sniper?",
            "Who does Alchemist counter?",
            "What is the cooldown of Monkey King's ultimate?",
            "Does Assassinate go through BKB?",
            "What are Dark Willow's abilities?",
        )))

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
    def parse_damage_type(damage_type):
        damage_type_map = {
            DamageType.MAGICAL: 'magical',
            DamageType.PHYSICAL: 'physical',
            DamageType.PURE: 'pure',
        }
        return damage_type_map[damage_type]

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
        response = "{} its cooldown is {} seconds".format(
            response,
            cls.parse_cooldown(ability),
        )
        return response.replace(". its", ". Its")


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
    def _respond(cls, ability):
        response = "{}'s ultimate is {}".format(
                ability.hero.name,
                ability.name,
            )
        response = cls.append_cooldown_to_response(response, ability)
        return cls.append_description_to_response(response, ability, True)


class MultipleUltimateResponse(AbilityResponse):
    @classmethod
    def _respond(cls, hero):
        abilities = Ability.objects.filter(hero=hero, is_ultimate=True)
        return "{} has multiple ultimates: {}".format(
            hero.name,
            cls.comma_separate_with_final_and([a.name for a in abilities]),
        )


class AbilityHotkeyResponse(AbilityResponse):
    @classmethod
    def _respond(cls, ability):
        response = "{}'s {} is {}".format(
            ability.hero.name,
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


class AbilityDamageTypeResponse(AbilityResponse):
    @classmethod
    def _respond(cls, ability):
        if not ability.damage_type:
            return "{} is a passive ability, with no cooldown".format(
                ability.name,
            )
        response = "{} does {} damage".format(
            ability.name,
            cls.parse_damage_type(ability.damage_type),
        )
        if ability.aghanims_damage_type and ability.aghanims_damage_type != ability.damage_type:
            response += ", and with Aghanim's Scepter it does {} damage".format(
                cls.parse_damage_type(ability.aghanims_damage_type))
        return response


class AbilitySpellImmunityResponse(AbilityResponse):
    @classmethod
    def _respond(cls, ability):
        spell_immunity_map = {
            SpellImmunity.PIERCES: 'fully pierces spell immunity',
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

    @staticmethod
    def _role_to_string(role):
        role_map = {
            HeroRole.CARRY: 'carry',
            HeroRole.MIDDLE: 'mid',
            HeroRole.SUPPORT: 'support',
            HeroRole.OFF_LANE: 'off-lane',
            HeroRole.JUNGLER: 'jungle',
            HeroRole.ROAMING: 'roaming',
        }
        return role_map[role]

    @staticmethod
    def _heroes_with_role(role):
        role_map = {
            HeroRole.CARRY: Hero.objects.filter(is_carry=True),
            HeroRole.MIDDLE: Hero.objects.filter(is_mid=True),
            HeroRole.SUPPORT: Hero.objects.filter(is_support=True),
            HeroRole.OFF_LANE: Hero.objects.filter(is_off_lane=True),
            HeroRole.JUNGLER: Hero.objects.filter(is_jungler=True),
            HeroRole.ROAMING: Hero.objects.filter(is_roaming=True),
        }
        return role_map[role]


class SingleHeroCountersResponse(AdvantageResponse):
    """Gives the list of heroes a hero is weak against"""

    @classmethod
    def _counters_hero_list(cls, heroes):
        names = [h.hero.name for h in heroes]
        result = cls.comma_separate_with_final_and(names)
        if len(names) == 1:
            result += ' is'
        else:
            result += ' are'
        return result

    @classmethod
    def _respond(cls, enemy, role):
        counters = Advantage.objects.filter(
            enemy=enemy, advantage__gte=0).order_by('-advantage')
        if role:
            counters = counters.filter(hero__in=cls._heroes_with_role(role))

        hard_counters = counters.filter(advantage__gte=cls.STRONG_ADVANTAGE)
        soft_counters = [c for c in counters[:8] if c not in hard_counters]
        response = None
        if hard_counters:
            response = '{} very strong against {}'.format(
                cls._counters_hero_list(hard_counters),
                enemy.name)
        if soft_counters:
            if response:
                response += '. {} also good'.format(cls._counters_hero_list(soft_counters))
            else:
                response = '{} good against {}'.format(
                    cls._counters_hero_list(soft_counters),
                    enemy.name)
        if response:
            return response
        return cls._no_match_response(enemy, role)

    @classmethod
    def _no_match_response(cls, enemy, role):
        if not role:
            raise Exception("Apparently no one counters %s, presumably that's a bug", enemy)
        return "Sorry, I don't know of any {} heroes which counter {}".format(
            cls._role_to_string(role),
            enemy.name,
        )


class SingleHeroAdvantagesResponse(AdvantageResponse):
    """Gives the list of heroes a hero is strong against"""

    @classmethod
    def _advantage_hero_list(cls, heroes):
        names = [h.enemy.name for h in heroes]
        return cls.comma_separate_with_final_and(names)

    @classmethod
    def _respond(cls, hero, role):
        counters = Advantage.objects.filter(
            hero=hero, advantage__gte=0).order_by('-advantage')
        if role:
            counters = counters.filter(enemy__in=cls._heroes_with_role(role))

        hard_counters = counters.filter(advantage__gte=cls.STRONG_ADVANTAGE)
        soft_counters = [c for c in counters[:8] if c not in hard_counters]
        response = None
        if hard_counters:
            response = '{} is very strong against {}'.format(
                hero.name,
                cls._advantage_hero_list(hard_counters))
        if soft_counters:
            if response:
                response += ', and also counters {}'.format(
                    cls._advantage_hero_list(soft_counters))
            else:
                response = '{} is good against {}'.format(
                    hero.name,
                    cls._advantage_hero_list(soft_counters))
        if response:
            return response
        return cls._no_match_response(hero, role)

    @classmethod
    def _no_match_response(cls, hero, role):
        if not role:
            raise Exception("Apparently %s doesn't counter anyone, presumably that's a bug", hero)
        return "Sorry, I don't know of any {} heroes which {} counters".format(
            cls._role_to_string(role),
            hero.name,
        )


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
