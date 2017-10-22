#!/usr/bin/python

import sys
import json
import random

if (sys.version_info > (3, 0)):
    print("Python 3.X detected")
    import socketserver as ss
else:
    print("Python 2.X detected")
    import SocketServer as ss


class NetworkHandler(ss.StreamRequestHandler):
    def handle(self):
        game = Game()

        # somehow adjust - keep adding moves for duration of turn, one response
        while True:
            data = self.rfile.readline().decode() # reads until '\n' encountered
            json_data = json.loads(str(data))
            # uncomment the following line to see pretty-printed data
            print(json.dumps(json_data, indent=4, sort_keys=True))
            # response = game.get_random_move(json_data).encode()
            response = game.get_move(json_data).encode()
            self.wfile.write(response)



class Game:
    def __init__(self):
        # self.units = set() # set of unique unit ids
        self.units = []
        self.tiles = []
        self.directions = ['N', 'S', 'E', 'W']
        # self.numWorkers = 0
        # self.numScouts = 0
        # self.numTanks = 0

    def get_random_move(self, json_data):
        units = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])
        self.units |= units # add any additional ids we encounter
        unit = random.choice(tuple(self.units))
        direction = random.choice(self.directions)
        move = 'MOVE'
        command = {"commands": [{"command": move, "unit": unit, "dir": direction}]}
        response = json.dumps(command, separators=(',',':')) + '\n'
        return response

    def get_move(self, json_data):
        move = 'MOVE'
        gather = 'GATHER'
        create = 'CREATE'
        shoot = 'SHOOT'
        commands = {"commands": []}
        # add new units
        units = []
        for unit in json_data['unit_updates']:
            add = True
            if unit['type'] != 'base':
                for u in self.units:
                    if unit['id'] == u['id']:
                        add = False
                if add:
                    units.append(unit)
        self.units.extend(units)
        # add new tiles
        tiles = []
        for tile in json_data['tile_updates']:
            add = True
            if tile['visible']:
                for t in self.tiles:
                    if t['x'] == tile['x'] and t['y'] == tile['y']:
                        add = False
                if add:
                    tiles.append(tile)
        self.tiles.extend(tiles)
        # count units alive (for create)
        workersAlive = 0
        scoutsAlive = 0
        tanksAlive = 0
        for unit in self.units:
            if unit['type'] == 'worker' and unit['status'] != 'dead':
                workersAlive += 1
            if unit['type'] == 'scout' and unit['status'] != 'dead':
                scoutsAlive += 1
            if unit['type'] == 'tank' and unit['status'] != 'dead':
                tanksAlive += 1
        # add needed units
        if workersAlive < 2:
            command = {"command": create, "type": 'worker'}
            commands['commands'].append(command)
        if scoutsAlive < 1:
            command = {"command": create, "type": 'scout'}
            commands['commands'].append(command)
        if tanksAlive < 1:
            command = {"command": create, "type": 'tank'}
            commands['commands'].append(command)
        # make moves for each unit in self.units
        for moveUnit in self.units:
            # only make a move if idle (can't move otherwise)
            if moveUnit['status'] == 'idle':
                # worker moves
                if moveUnit['type'] == 'worker':
                    moved = False
                    if moveUnit['resource'] == 0: # get more resources
                        # if tile to N/S/E/W has resources, gather
                        for tile in self.tiles:
                            # north
                            if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                if type(tile['resources']) == 'int':
                                    if tile['resources'] > 0:
                                        direction = 'N'
                                        command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                        moved = True
                                        break;
                            # south
                            elif tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                if type(tile['resources']) == 'int':
                                    if tile['resources'] > 0:
                                        direction = 'S'
                                        command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                        moved = True
                                        break;
                            # east
                            elif tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                if type(tile['resources']) == 'int':
                                    if tile['resources'] > 0:
                                        direction = 'E'
                                        command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                        moved = True
                                        break;
                            # west
                            elif tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                if type(tile['resources']) == 'int':
                                    if tile['resources'] > 0:
                                        direction = 'W'
                                        command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                        moved = True
                                        break;
                        # use A* to find nearby tile with resource and go to
                        # if didn't gather or move to gather, just move where not blocked
                        if moved == False:
                            for tile in self.tiles:
                                # north
                                if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                    if tile['blocked']:
                                        moveN = False
                                    else:
                                        moveN = True
                                # south
                                elif tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                    if tile['blocked']:
                                        moveS = False
                                    else:
                                        moveS = True
                                # east
                                elif tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked']:
                                        moveE = False
                                    else:
                                        moveE = True
                                # west
                                elif tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked']:
                                        moveW = False
                                    else:
                                        moveW = True
                    # take resources home
                    else :
                        # if x > 1, move W (unless blocked), pos. would be (0+x-1, y)
                        if moveUnit['x'] > 1:
                            moveW = True
                        # if x < 1, move E (unless blocked), pos. would be (0+x+1, y)
                        if moveUnit['x'] < 1:
                            moveE = True
                        # if y > 1, move S (unless blocked), pos. would be (x, 0+x-1)
                        if moveUnit['y'] > 1:
                            moveS = True
                        # if y < 1, move N (unless blocked), pos. would be (x, 0+x+1)
                        if moveUnit['y'] < 1:
                            moveN = True
                        # for visible tiles
                        # if moveD && pos clear = move
                    # actually make the move (unless gathered)
                    if moved == False:
                        for tile in self.tiles:
                            if moveN:
                                if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                    if tile['blocked'] == False:
                                        direction = 'N'
                                        command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                        break;
                            elif moveS:
                                if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                    if tile['blocked'] == False:
                                        direction = 'S'
                                        command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                        break;
                            elif moveE:
                                if tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked'] == False:
                                        direction = 'E'
                                        command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                        break;
                            elif moveW:
                                if tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked'] == False:
                                        direction = 'W'
                                        command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                        break;
                # scout moves
                elif moveUnit['type'] == 'scout':
                    if moveUnit['status'] == 'idle':
                        if moveUnit['can_attack']:
                            for tile in self.tiles:
                                # TODO if <= 1, melee
                                # attack if at base / opposing team nearby
                                if (abs(moveUnit['x'] - tile['x'])) <= 5 and (abs(moveUnit['y'] - tile['y'])) <= 5:
                                    if len(tile['units']) > 0:
                                        for enemy in tile['units']:
                                            command = {"command": shoot, "unit": enemy['id'], "dx": tile['x'], "dy": tile['y']}
                        # use A* to expand map TODO - random rn
                        else:
                            direction = random.choice(self.directions)
                            command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                # tank moves (only unit left)
                else :
                    if moveUnit['status'] == 'idle':
                        if moveUnit['can_attack']:
                            for tile in self.tiles:
                                # TODO if <= 1, melee
                                # attack if at base / opposing team nearby
                                if (abs(moveUnit['x'] - tile['x'])) <= 2 and (abs(moveUnit['y'] - tile['y'])) <= 2:
                                    if len(tile['units']) > 0:
                                        for enemy in tile['units']:
                                            command = {"command": shoot, "unit": enemy['id'], "dx": tile['x'], "dy": tile['y']}
                        # use A* to search for opposing base TODO - random rn
                        else:
                            direction = random.choice(self.directions)
                            command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                commands['commands'].append(command)
        response = json.dumps(commands, separators=(',',':')) + '\n'
        print(response)
        return response


if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '127.0.0.1'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
