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
        self.units = [] # set of unique unit ids
        self.tiles = []
        self.directions = ['N', 'S', 'E', 'W']

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
        commands = {"commands": []}
        # unitIDs = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])
        units = []
        for unit in json_data['unit_updates']:
            if unit['type'] != 'base':
                units.append(unit)
        # tiles = set(str([tile['x']) + ',' + str(tile['y'])] for tile in json_data['tile_updates'])
        #tiles = set(for tile in json_data['tile_updates'])
        tiles = []
        for tile in json_data['tile_updates']:
            tiles.append(tile)
        self.units.extend(units) # add any additional ids we encounter
        self.tiles.extend(tiles)
        # find out if need to create any units
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
        #print("workers:" + str(workersAlive) + '\n' + "scouts:" + str(scoutsAlive)
        #      + '\n' + "tanks:" + str(tanksAlive))
        if workersAlive < 2:
            command = {"command": create, "type": 'worker'}
            commands['commands'].append(command)
        if scoutsAlive < 1:
            command = {"command": create, "type": 'scout'}
            commands['commands'].append(command)
        if tanksAlive < 1:
            command = {"command": create, "type": 'tank'}
            commands['commands'].append(command)
        for moveUnit in self.units:
            # only make a move if idle (can't move otherwise)
            # print(moveUnit)
            if moveUnit['status'] == 'idle':
                if moveUnit['type'] == 'worker':
                    moved = False
                    # print(moveUnit)
                    if moveUnit['resource'] == 0: # get more resources
                        # if N/S/E/W has resources, gather
                        for tile in self.tiles:
                            # print(tile)
                            # north
                            if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                if tile['resources'] != None:
                                    direction = 'N'
                                    command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                    moved = True
                                    break;
                            # south
                            elif tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                if tile['resources'] != None:
                                    direction = 'S'
                                    command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                    moved = True
                                    break;
                            # east
                            elif tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                if tile['resources'] != None:
                                    direction = 'E'
                                    command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                    moved = True
                                    break;
                            # west
                            elif tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                if tile['resources'] != None:
                                    direction = 'W'
                                    command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                    moved = True
                                    break;
                        # if N+1/S+1/E+1/W+1 has resources, moveD = True TODO
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
                    if moved == False:
                        for tile in self.tiles:
                            if moveN:
                                if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                    if tile['blocked'] == False:
                                        direction = 'N'
                                        command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                        break;
                            if moveS:
                                if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                    if tile['blocked'] == False:
                                        direction = 'S'
                                        command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                        break;
                            if moveE:
                                if tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked'] == False:
                                        direction = 'E'
                                        command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                        break;
                            if moveW:
                                if tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked'] == False:
                                        direction = 'W'
                                        command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                        break;
                else :
                    # random
                    direction = random.choice(self.directions)
                    move = 'MOVE'
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
