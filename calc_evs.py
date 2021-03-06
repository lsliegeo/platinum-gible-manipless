from math import floor
from enum import Enum, auto

table_file = 'ev_table.csv'
chimchar_route = 'chimchar_route.txt'
routes = [(17, 'lvl_17.txt'), (18, 'lvl_18.txt'), (19, 'lvl_19.txt'), (20, 'lvl_20.txt')]
output_file_name = 'route.mdr'
chimchar_stats = ':::tracker{species=Chimchar baseStats="[[44, 58, 44, 58, 44, 61], [64, 78, 52, 78, 52, 81]]"}'
gible_stats = ':::tracker{species=Gible baseStats="[[58, 70, 45, 40, 45, 42], [68, 90, 65, 50, 55, 82], [108, 130, 95, 80, 85, 102]]"}'

# {pokemon_name: (exp_yield, [ev_yields])}
data = {}
with open(table_file) as f:
    for line in f:
        line = line.replace('\n', '').split(',')
        name = line[0].lower()
        exp = int(line[1])
        evs = [int(ev) for ev in line[2:8]]
        data[name] = (exp, evs)

class LevelingRate(Enum):
    ERRATIC = auto(),
    FAST = auto(),
    MEDIUM_FAST = auto(),
    MEDIUM_SLOW = auto(),
    SLOW = auto(),
    FLUCTUATING = auto(),

# total experience needed in order to reach 'lvl'
def total_exp_needed(lvl, rate):
    if rate == LevelingRate.ERRATIC:
        if lvl <= 50:
            return floor(lvl ** 3 * (100 - lvl) / 50)
        elif lvl <= 68:
            return floor(lvl ** 3 * (150 - lvl) / 100)
        elif lvl <= 98:
            return floor(lvl ** 3 * floor((1911 - 10 * lvl) / 3) / 500)
        else:
            return floor(lvl ** 3 * (160 - lvl) / 100)

    if rate == LevelingRate.FAST:
        return floor(4 * lvl ** 3 / 5)

    if rate == LevelingRate.MEDIUM_FAST:
        return lvl ** 3

    if rate == LevelingRate.MEDIUM_SLOW:
        return floor(6 / 5 * lvl ** 3 - 15 * lvl ** 2 + 100 * lvl - 140)

    if rate == LevelingRate.SLOW:
        return floor(5 * lvl ** 3 / 4)

    if rate == LevelingRate.FLUCTUATING:
        if lvl <= 15:
            return floor(lvl ** 3 * (floor((lvl + 1) / 3) + 24) / 50)
        elif lvl <= 36:
            return floor(lvl ** 3 * (lvl + 14) / 50)
        else:
            return flor(lvl ** 3 * (floor(n / 2) + 32) / 50)

# experience needed in order to level up from 'current_lvl' to 'current_lvl + 1'
def exp_to_next_lvl(current_lvl, rate):
    return total_exp_needed(current_lvl + 1, rate) - total_exp_needed(current_lvl, rate)

# state for managing current lvl, exp and writing evs during level up
class Pokemon:

    def __init__(self, start_lvl, file, leveling_rate):
        self.lvl = start_lvl
        self.rate = leveling_rate
        self.exp_remaining = exp_to_next_lvl(self.lvl, self.rate)
        self.evs = [0, 0, 0, 0, 0, 0]
        self.file = file
        self.opponents = []
        file.write(f'\n{start_lvl}:\n')
        self.print()

    # write evs at the start of current level
    def print(self):
        self.file.write(f'   {self.lvl} -> {", ".join([str(ev) for ev in self.evs])}')
        if self.opponents:
            self.file.write(f' # {", ".join(self.opponents)}')
        self.file.write('\n')

    def check_lvl_up(self):
        if self.exp_remaining <= 0:
            self.lvl += 1
            self.exp_remaining += exp_to_next_lvl(self.lvl, self.rate)
            self.print()
            self.opponents.clear()
            self.check_lvl_up() # multiple level ups in a row

    def candy(self):
        self.exp_remaining = 0
        self.check_lvl_up()

    # force the current level and throw away any remaining exp, in order to simulate rare candies
    def force(self, target_lvl):
        while self.lvl < target_lvl:
            self.candy()

    # gain exp and evs for a defeated (trainer) pokemon
    def fight(self, other_poke_name, other_poke_lvl, shared=False):
        exp, evs = data[other_poke_name]
        self.exp_remaining -= floor(floor(exp * other_poke_lvl / 7) * 1.5 * (0.5 if shared else 1))
        self.evs = [x + y for x, y in zip(self.evs, evs)]
        self.opponents.append(other_poke_name)
        self.check_lvl_up()

def parse_route(route_file, poke):
    with open(route_file) as file:
        route = file.read()

    for line_ in route.split('\n'):
        # print(line_)
        line = line_
        
        # skip empty lines ?
        if not line:
            continue

        # trim comments
        if '#' in line:
            line = line[:line.find('#')]

        # skip empty lines ?
        if not line:
            continue

        # split line into words
        line = [part.lower() for part in line.split(' ')]

        # skip empty lines ?
        if not line:
            continue

        # workaround for space in 'mr. mime' and 'mime jr.'
        if line[0][-1] == '.' or line[1][-1] == '.':
            line[0] += ' ' + line[1]
            del line[1]

        # finally we can start parsing lines
        if line[0] == 'force':
            target_lvl = int(line[1])
            poke.force(target_lvl)

        if line[0] == 'candy':
            amount = int(line[1]) if len(line) == 2 else 1
            for _ in range(amount):
                poke.candy()

        else:
            if line[0] not in data:
                print(f'invalid line: {line_}')
                continue

            poke.fight(line[0], int(line[1]), line[-1] == 'shared')


# create output file
with open(output_file_name, 'w') as output_file:

    # CHIMCHAR
    output_file.write(chimchar_stats)
    chimchar = Pokemon(5, output_file, LevelingRate.MEDIUM_SLOW)
    parse_route(chimchar_route, chimchar)
    output_file.write(':::\n\n')

    # GIBLE
    output_file.write(gible_stats)

    # the route has different starts, we do separate calculations for different starting levels
    for start_lvl, route_file in routes:
        gible = Pokemon(start_lvl, output_file, LevelingRate.SLOW)        
        parse_route(route_file, gible)

    output_file.write(':::')

