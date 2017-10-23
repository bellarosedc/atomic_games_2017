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
            if unit['type'] != 'base':
                units.append(unit)
                for u in self.units:
                    if unit['id'] == u['id']:
                        self.units.remove(u)
        self.units.extend(units)
        # add new tiles
        tiles = []
        for tile in json_data['tile_updates']:
            if tile['visible']:
                tiles.append(tile)
                for t in self.tiles:
                    if t['x'] == tile['x'] and t['y'] == tile['y']:
                        self.tiles.remove(t)
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
        if workersAlive < 4:
            command = {"command": create, "type": 'worker'}
            commands['commands'].append(command)
        if scoutsAlive < 2:
            command = {"command": create, "type": 'scout'}
            commands['commands'].append(command)
        if tanksAlive < 1:
            command = {"command": create, "type": 'tank'}
            commands['commands'].append(command)
        command = ''
        # make moves for each unit in self.units
        for moveUnit in self.units:
            # only make a move if idle (can't move otherwise)
            if moveUnit['status'] == 'idle':
                # worker moves
                if moveUnit['type'] == 'worker':
                    moved = False
                    moveN = False
                    moveS = False
                    moveE = False
                    moveW = False
                    if moveUnit['resource'] == 0: # get more resources
                        # if tile to N/S/E/W has resources, gather
                        for tile in self.tiles:
                            # north
                            if not moved and tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                if tile['resources'] != None:
                                    direction = 'N'
                                    command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                    commands['commands'].append(command)
                                    moved = True
                                    break;
                            # east
                            elif not moved and tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                if tile['resources'] != None:
                                    direction = 'E'
                                    command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                    commands['commands'].append(command)
                                    moved = True
                                    break;
                            # south
                            elif not moved and tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                if tile['resources'] != None:
                                    direction = 'S'
                                    command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                    commands['commands'].append(command)
                                    moved = True
                                    break;
                            # west
                            elif not moved and tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                if tile['resources'] != None:
                                    direction = 'W'
                                    command = {"command": gather, "unit": moveUnit['id'], "dir": direction}
                                    commands['commands'].append(command)
                                    moved = True
                                    break;
                        # find nearby tile with resources
                        nextTile = self.tiles[0]
                        nextDist = 1000
                        for possNext in self.tiles:
                            if possNext['resources'] != None:
                                dist = abs(moveUnit['x'] - possNext['x']) + abs(moveUnit['y'] - possNext['y'])
                                if dist < nextDist:
                                    nextTile = possNext
                        # found a tile, find possible options
                        if nextDist != 1000:
                            # north
                            if nextTile['y'] < moveUnit['y']:
                                moveN = True
                            # south
                            elif nextTile['y'] > moveUnit['y']:
                                moveS = True
                            # east
                            elif nextTile['x'] > moveUnit['x']:
                                moveE = True
                            # west
                            elif tile['x'] < moveUnit['x']:
                                moveW = True
                            for tile in self.tiles:
                                # north
                                if moveN and tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                    if tile['blocked']:
                                        moveN = False
                                    else:
                                        moveN = True
                                # east
                                elif moveE and tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked']:
                                        moveE = False
                                    else:
                                        moveE = True
                                # south
                                elif moveS and tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                    if tile['blocked']:
                                        moveS = False
                                    else:
                                        moveS = True
                                # west
                                elif moveW and tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked']:
                                        moveW = False
                                    else:
                                        moveW = True
                        # if didn't gather or find a move or move doesn't work, just move where not blocked
                        if not moved and not moveN and not moveS and not moveE and not moveW:
                            for tile in self.tiles:
                                # north
                                if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                    if tile['blocked']:
                                        moveN = False
                                    else:
                                        moveN = True
                                # east
                                elif tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked']:
                                        moveE = False
                                    else:
                                        moveE = True
                                # south
                                elif tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                    if tile['blocked']:
                                        moveS = False
                                    else:
                                        moveS = True
                                # west
                                elif tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked']:
                                        moveW = False
                                    else:
                                        moveW = True
                    # take resources back
                    else :
                        # if x > 1, move W (unless blocked), pos. would be (0+x-1, y)
                        if moveUnit['x'] > 0:
                            moveW = True
                            moveE = False
                        # if x < 1, move E (unless blocked), pos. would be (0+x+1, y)
                        if moveUnit['x'] < 0:
                            moveE = True
                            MoveW = False
                        # if y > 1, move S (unless blocked), pos. would be (x, 0+x-1)
                        if moveUnit['y'] < 0:
                            moveS = True
                            moveN = False
                        # if y < 1, move N (unless blocked), pos. would be (x, 0+x+1)
                        if moveUnit['y'] > 0:
                            moveN = True
                            moveS = False
                    # actually make the move (unless gathered)
                    for tile in self.tiles:
                        if moveN and not moved:
                            if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                if tile['blocked'] == False:
                                    direction = 'N'
                                    command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                    commands['commands'].append(command)
                                    moved = True
                                    break;
                        elif moveE and not moved:
                            if tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                if tile['blocked'] == False:
                                    direction = 'E'
                                    command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                    commands['commands'].append(command)
                                    moved = True
                                    break;
                        elif moveS and not moved:
                            if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                if tile['blocked'] == False:
                                    direction = 'S'
                                    command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                    commands['commands'].append(command)
                                    moved = True
                                    break;
                        elif moveW and not moved:
                            if tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                if tile['blocked'] == False:
                                    direction = 'W'
                                    command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                    commands['commands'].append(command)
                                    moved = True
                                    break;
                # scout moves
                elif moveUnit['type'] == 'scout':
                    if moveUnit['status'] == 'idle':
                        moved = False
                        if moveUnit['can_attack']:
                            for tile in self.tiles:
                                # TODO if <= 1, melee
                                # attack if at base / opposing team nearby
                                if (abs(moveUnit['x'] - tile['x'])) <= 5 and (abs(moveUnit['y'] - tile['y'])) <= 5:
                                    if len(tile['units']) > 0:
                                        for enemy in tile['units']:
                                            command = {"command": shoot, "unit": enemy['id'], "dx": tile['x'], "dy": tile['y']}
                                            commands['commands'].append(command)
                                            moved = True
                        # expand map TODO fixme
                        if moved == False:
                            moveN = False
                            moveS = False
                            moveE = False
                            moveW = False
                            nextDir = 'N'
                            distN = 0
                            distS = 0
                            distE = 0
                            distW = 0
                            for possNext in self.tiles:
                                if possNext['x'] < distN:
                                    distN = possNext['x']
                                if possNext['x'] > distS:
                                    distS = possNext['x']
                                if possNext['y'] < distW:
                                    distW = possNext['y']
                                if possNext['y'] > distE:
                                    distE = possNext['y']
                            if distN < distS and distN < distW and distN < distE:
                                nextDir = 'N'
                                moveN = True
                            elif distW < distN and distW < distS and distW < distE:
                                nextDir = 'W'
                                moveE = True
                            elif distS < distN and distS < distW and distS < distE:
                                nextDir = 'S'
                                moveS = True
                            else:
                                nextDir = 'E'
                                moveW = True
                            # found a direction, check options
                            for tile in self.tiles:
                                # north
                                if nextDir == 'N' and tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                    if tile['blocked']:
                                        moveN = False
                                    else:
                                        moveN = True
                                # south
                                elif nextDir == 'S' and tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                    if tile['blocked']:
                                        moveS = False
                                    else:
                                        moveS = True
                                # east
                                elif nextDir == 'E' and tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked']:
                                        moveE = False
                                    else:
                                        moveE = True
                                # west
                                elif nextDir == 'W' and tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                    if tile['blocked']:
                                        moveW = False
                                    else:
                                        moveW = True
                            # if didn't find a move
                            if not moveN and not moveS and not moveE and not moveW:
                                for tile in self.tiles:
                                    # north
                                    if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                        if tile['blocked']:
                                            moveN = False
                                        else:
                                            moveN = True
                                    # east
                                    elif tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                        if tile['blocked']:
                                            moveE = False
                                        else:
                                            moveE = True
                                    # south
                                    elif tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                        if tile['blocked']:
                                            moveS = False
                                        else:
                                            moveS = True
                                    # west
                                    elif tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                        if tile['blocked']:
                                            moveW = False
                                        else:
                                            moveW = True
                            # actually make move
                            for tile in self.tiles:
                                if moveN and not moved:
                                    if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                        if tile['blocked'] == False:
                                            direction = 'N'
                                            command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                            commands['commands'].append(command)
                                            moved = True
                                            break;
                                elif moveE and not moved:
                                    if tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                        if tile['blocked'] == False:
                                            direction = 'E'
                                            command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                            commands['commands'].append(command)
                                            moved = True
                                            break;
                                elif moveS and not moved:
                                    if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                        if tile['blocked'] == False:
                                            direction = 'S'
                                            command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                            commands['commands'].append(command)
                                            moved = True
                                            break;
                                elif moveW and not moved:
                                    if tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                        if tile['blocked'] == False:
                                            direction = 'W'
                                            command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                            commands['commands'].append(command)
                                            moved = True
                                            break;
                # tank moves (only unit left)
                else :
                    if moveUnit['status'] == 'idle':
                        moved = False
                        if moveUnit['can_attack']:
                            for tile in self.tiles:
                                # TODO if <= 1, melee
                                # attack if at base / opposing team nearby
                                if (abs(moveUnit['x'] - tile['x'])) <= 2 and (abs(moveUnit['y'] - tile['y'])) <= 2:
                                    if len(tile['units']) > 0:
                                        for enemy in tile['units']:
                                            command = {"command": shoot, "unit": enemy['id'], "dx": tile['x'], "dy": tile['y']}
                                            commands['commands'].append(command)
                                            moved = True
                        # search for nearby enemies / where to move
                        if moved == False:
                            moveN = False
                            moveS = False
                            moveE = False
                            moveW = False
                            nextTile = self.tiles[0]
                            nextDist = 1000
                            # find a tile with enemy
                            for possNext in self.tiles:
                                if len(possNext['units']) > 0:
                                    dist = abs(moveUnit['x'] - possNext['x']) + abs(moveUnit['y'] - possNext['y'])
                                    if dist < nextDist:
                                        nextTile = possNext
                            # found a tile, find possible options
                            if nextTile != self.tiles[0]:
                                # north
                                if nextTile['y'] < moveUnit['y']:
                                    moveN = True
                                # south
                                elif nextTile['y'] > moveUnit['y']:
                                    moveS = True
                                # east
                                if nextTile['x'] > moveUnit['x']:
                                    moveE = True
                                # west
                                elif tile['x'] < moveUnit['x']:
                                    moveW = True
                                for tile in self.tiles:
                                    # north
                                    if moveN and tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                        if tile['blocked']:
                                            moveN = False
                                        else:
                                            moveN = True
                                    # south
                                    elif moveS and tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                        if tile['blocked']:
                                            moveS = False
                                        else:
                                            moveS = True
                                    # east
                                    elif moveE and tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                        if tile['blocked']:
                                            moveE = False
                                        else:
                                            moveE = True
                                    # west
                                    elif moveW and tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                        if tile['blocked']:
                                            moveW = False
                                        else:
                                            moveW = True
                            # if didn't find a move
                            if not moveN and not moveS and not moveE and not moveW:
                                for tile in self.tiles:
                                    # north
                                    if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                        if tile['blocked']:
                                            moveN = False
                                        else:
                                            moveN = True
                                    # south
                                    elif tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
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
                            # actually make move
                            for tile in self.tiles:
                                if (moveUnit['id'] % 2) == 0:
                                    if moveN and not moved:
                                        if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                            if tile['blocked'] == False:
                                                direction = 'N'
                                                command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                                commands['commands'].append(command)
                                                moved = True
                                                break;
                                    elif moveE and not moved:
                                        if tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                            if tile['blocked'] == False:
                                                direction = 'E'
                                                command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                                commands['commands'].append(command)
                                                moved = True
                                                break;
                                    elif moveS and not moved:
                                        if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                            if tile['blocked'] == False:
                                                direction = 'S'
                                                command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                                commands['commands'].append(command)
                                                moved = True
                                                break;
                                    elif moveW and not moved:
                                        if tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                            if tile['blocked'] == False:
                                                direction = 'W'
                                                command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                                commands['commands'].append(command)
                                                moved = True
                                                break;
                                else:
                                    if moveW and not moved:
                                        if tile['x'] == (moveUnit['x'] - 1) and tile['y'] == moveUnit['y']:
                                            if tile['blocked'] == False:
                                                direction = 'W'
                                                command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                                commands['commands'].append(command)
                                                moved = True
                                                break;
                                    elif moveS and not moved:
                                        if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] + 1):
                                            if tile['blocked'] == False:
                                                direction = 'S'
                                                command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                                commands['commands'].append(command)
                                                moved = True
                                                break;
                                    elif moveE and not moved:
                                        if tile['x'] == (moveUnit['x'] + 1) and tile['y'] == moveUnit['y']:
                                            if tile['blocked'] == False:
                                                direction = 'E'
                                                command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                                commands['commands'].append(command)
                                                moved = True
                                                break;
                                    elif moveN and not moved:
                                        if tile['x'] == moveUnit['x'] and tile['y'] == (moveUnit['y'] - 1):
                                            if tile['blocked'] == False:
                                                direction = 'N'
                                                command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                                                commands['commands'].append(command)
                                                moved = True
                                                break;
                            # direction = random.choice(self.directions)
                            # command = {"command": move, "unit": moveUnit['id'], "dir": direction}
                            # commands['commands'].append(command)
        response = json.dumps(commands, separators=(',',':')) + '\n'
        print(response)
        return response


if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '127.0.0.1'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
