import scraper

TOTAL_HEROES = 113
MAX_ADVANTAGE = 20
MIN_HEROES_IN_EACH_ROLE = 5

def run_tests(results):
    all_ok = True

    if(ensure_all_heroes_loaded(results) == False):
        all_ok = False
    if(ensure_advantages_within_expected_boundaries(results) == False):
        all_ok = False
    if(ensure_minimum_heroes_each_role(results) == False):
        all_ok = False
    if(ensure_correct_number_roaming_heroes(results) == False):
        all_ok = False

    return all_ok

def ensure_all_heroes_loaded(all_data):
    all_ok = True

    if(len(all_data) != TOTAL_HEROES):
        print("ERROR: Only loaded data for {} heroes.".format(len(all_data)))
        all_ok = False

    for data_for_one_hero in all_data:
        if(len(data_for_one_hero.advantages_data) != TOTAL_HEROES - 1):
            print("ERROR: " + data_for_one_hero.name + " has advantage data for {} heroes!".format(len(data_for_one_hero.advantages_data)))
            all_ok = False

    if(all_ok == True):
        print("PASS: All heroes have advantage data for {} heroes.".format(TOTAL_HEROES))
    return all_ok

def ensure_advantages_within_expected_boundaries(all_data):
    all_ok = True
    for data_for_one_hero in all_data:
        for line in data_for_one_hero.advantages_data:
            if(line.advantage > MAX_ADVANTAGE or line.advantage < -1 * MAX_ADVANTAGE):
                print("ERROR: {} has {} advantage over {}, which seems excessive".format(data_for_one_hero.name, line.advantage, line.name))
                all_ok = False

    if(all_ok == True):
        print("PASS: All heroes have advantage no more or less than {}.".format(MAX_ADVANTAGE))
    return all_ok

def ensure_minimum_heroes_each_role(all_data):
    carry_count = 0
    support_count = 0
    mid_count = 0
    off_lane_count = 0
    jungler_count = 0
    roaming_count = 0

    for data_for_one_hero in all_data:
        if data_for_one_hero.is_carry == 1:
            carry_count += 1
        if data_for_one_hero.is_support == 1:
            support_count += 1
        if data_for_one_hero.is_mid == 1:
            mid_count += 1
        if data_for_one_hero.is_off_lane == 1:
            off_lane_count += 1
        if data_for_one_hero.is_jungler == 1:
            jungler_count += 1
        if data_for_one_hero.is_roaming == 1:
            roaming_count += 1

    all_ok = True

    if(carry_count < MIN_HEROES_IN_EACH_ROLE):
        print("ERROR: Only {} carry heroes, need {} to pass".format(carry_count, MIN_HEROES_IN_EACH_ROLE))
        all_ok = False
    if(support_count < MIN_HEROES_IN_EACH_ROLE):
        print("ERROR: Only {} support heroes, need {} to pass".format(support_count, MIN_HEROES_IN_EACH_ROLE))
        all_ok = False
    if(mid_count < MIN_HEROES_IN_EACH_ROLE):
        print("ERROR: Only {} mid heroes, need {} to pass".format(mid_count, MIN_HEROES_IN_EACH_ROLE))
        all_ok = False
    if(off_lane_count < MIN_HEROES_IN_EACH_ROLE):
        print("ERROR: Only {} off lane heroes, need {} to pass".format(off_lane_count, MIN_HEROES_IN_EACH_ROLE))
        all_ok = False
    if(jungler_count < MIN_HEROES_IN_EACH_ROLE):
        print("ERROR: Only {} jungler heroes, need {} to pass".format(jungler_count, MIN_HEROES_IN_EACH_ROLE))
        all_ok = False
    if(roaming_count < MIN_HEROES_IN_EACH_ROLE):
        print("ERROR: Only {} roaming heroes, need {} to pass".format(roaming_count, MIN_HEROES_IN_EACH_ROLE))
        all_ok = False

    if(all_ok == True):
        print("PASS: Identified {} carry, {} support, {} mid, {} off lane, {} jungler, {} roaming heroes.".format(carry_count, support_count, mid_count, off_lane_count, jungler_count, roaming_count))

    return all_ok

def ensure_correct_number_roaming_heroes(all_data):
    roaming_count = 0
    for data_for_one_hero in all_data:
        if data_for_one_hero.is_roaming == 1:
            roaming_count += 1

    all_ok = (len(scraper.AdvantageDataForAHero.ROAMING_HEROES) == roaming_count)

    if(all_ok == True):
        print("PASS: Identified {} roaming heroes.".format(len(scraper.AdvantageDataForAHero.ROAMING_HEROES)))
    else:
        print("ERROR: Expected {} roaming heroes, but found{}.".format(len(scraper.AdvantageDataForAHero.ROAMING_HEROES), roaming_count))
        
    return all_ok
                
