from enum import Enum, unique


@unique
class HeroRole(Enum):
    CARRY = 1
    SUPPORT = 2
    OFF_LANE = 3
    JUNGLER = 4
    MIDDLE = 5
    ROAMING = 6
