import sqlite3
import random
import time
import sys
import os
import importlib as imp

def make_testing():
    folder = './bots'
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)

        try:
            if os.path.isfile(file_path) and file_path.find(".m")!=-1:
                print(the_file)
                os.unlink(file_path)
        except Exception as e:
            print(e)
    conn = sqlite3.connect('tanks.sqlite')
    c = conn.cursor()

    #get settings
    c.execute("SELECT * FROM settings")
    result = c.fetchall()
    settings = dict()
    for string in result:
        settings[string[1]] = string[2]
    print(settings)
    #get bots
    #change to in game
    names = dict()
    c.execute("SELECT key, name FROM players WHERE state = 'ready'")
    result = c.fetchall()
    players = list()
    print("CURRENT PLAYERS:")
    for string in result:
        print(string[0]+" - "+string[1])
        players.append(string[0])
        names[string[0]]=string[1]
    print("")
    print("")

    #clear current state
    c.execute("DELETE FROM statistics")
    c.execute("DELETE FROM actions")
    c.execute("DELETE FROM game")

    #make map
    mainMap = [['.' for i in range(int(settings["height"]))] for j in range(int(settings["width"]))]
    healthMap = [[0 for i in range(int(settings["height"]))] for j in range(int(settings["width"]))]

    coords = dict()
    health = dict()
    errors = dict()
    crashes = dict()
    lifeplayers = len(players)
    kills = dict()
    ticks = 0;
    steps = dict()
    shots = dict()
    banlist = list()



    for player in players:
        coords[player] = dict()
        steps[player] = 0
        errors[player] = 0
        crashes[player] = 0
        shots[player] = 0
        health[player] = int(settings["max_health"])
        kills[player] = 0
        x = random.randint(0, int(settings["width"])-1)
        y = random.randint(0, int(settings["height"])-1)
        while mainMap[x][y]!='.':
            x = random.randint(0, int(settings["width"])-1)
            y = random.randint(0, int(settings["height"])-1)
        mainMap[x][y] = player
        healthMap[x][y] = int(settings["max_health"])
        coords[player]["x"]=x
        coords[player]["y"] =y
        c.execute("INSERT INTO statistics (key) VALUES (?)", [player])
        c.execute("INSERT INTO game (key,x,y,life) VALUES (?,?,?,?)", [player,x,y, str(health[player])])
    c.execute("UPDATE settings SET value = ? WHERE param = ?", ["running", "game_state"])

    conn.commit()

    sys.path.append(os.path.dirname(__file__) + "/bots")
    while lifeplayers>int(settings['game_stop']):
        if int(settings['stop_ticks'])!=0 and ticks>int(settings['stop_ticks']):
            break
        print("current tick:"+str(ticks))
        choices = dict()
        ticks += 1
        for player in players:
            choices[player] = ""
            if player in banlist:
                continue
            try:
                c.execute("SELECT code FROM players WHERE key = ?", [player])
                code = c.fetchone()
                output_file = open("./bots/" + player + ".py", 'wb')
                output_file.write(code[0])
                output_file.close()
                module = __import__(player, fromlist=["make_choice"])
                module = imp.reload(module)
                makeChoice = getattr(module, "make_choice")
                #print("Now running:" +player+" ("+names[player]+")")
                choices[player] = makeChoice(int(coords[player]["x"]), int(coords[player]["y"]), healthMap); #тут выбор
            except Exception as e:
                print(player+" ("+names[player]+") has crashed :( :"+str(e))
                choices[player] = "crash"
                crashes[player]+=1
                c.execute("INSERT INTO actions (key, value) VALUES (?, ?)", [player, choices[player]])
                c.execute(
                    "UPDATE statistics SET crashes = " + str(crashes[player]) + " WHERE key = ?",
                    [player])
        conn.commit()
        #print(healthMap)
        for player in players:
            if player in banlist:
                continue
            if choices[player]=="go_up":
                steps[player]+=1
                if int(coords[player]["y"]) > 0 and mainMap[coords[player]["x"]][coords[player]["y"] - 1] == '.':
                    mainMap[coords[player]["x"]][coords[player]["y"]] = '.'
                    healthMap[coords[player]["x"]][coords[player]["y"]] = 0
                    coords[player]["y"] -= 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = player
                    healthMap[coords[player]["x"]][coords[player]["y"]] = health[player]
                    c.execute("UPDATE game SET y = " + str(coords[player]["y"]) + " WHERE key = ?", [player])
            if choices[player] == "go_down":
                steps[player] += 1
                if int(coords[player]["y"]) < int(settings["height"]) - 1 and mainMap[coords[player]["x"]][coords[player]["y"]+1] == '.':
                    mainMap[coords[player]["x"]][coords[player]["y"]] = '.'
                    healthMap[coords[player]["x"]][coords[player]["y"]] = 0
                    coords[player]["y"] += 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = player
                    healthMap[coords[player]["x"]][coords[player]["y"]] = health[player]
                    c.execute("UPDATE game SET y = " + str(coords[player]["y"]) + " WHERE key = ?", [player])
            if choices[player] == "go_left":
                steps[player] += 1
                if int(coords[player]["x"]) > 0 and mainMap[int(coords[player]["x"]) -1][coords[player]["y"]] == '.':
                    mainMap[coords[player]["x"]][coords[player]["y"]] = '.'
                    healthMap[coords[player]["x"]][coords[player]["y"]] = 0
                    coords[player]["x"] -= 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = player
                    healthMap[coords[player]["x"]][coords[player]["y"]] = health[player]
                    c.execute("UPDATE game SET x = " + str(coords[player]["x"]) + " WHERE key = ?", [player])
            if choices[player] == "go_right":
                steps[player] += 1
                if int(coords[player]["x"]) < int(settings["width"]) - 1 and mainMap[int(coords[player]["x"])+1][coords[player]["y"]] == '.':
                    mainMap[coords[player]["x"]][coords[player]["y"]] = '.'
                    healthMap[coords[player]["x"]][coords[player]["y"]] = 0
                    coords[player]["x"]+=1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = player
                    healthMap[coords[player]["x"]][coords[player]["y"]] = health[player]
                    c.execute("UPDATE game SET x = " + str(coords[player]["x"]) + " WHERE key = ?", [player])
            if choices[player]=="go_up" or choices[player] == "go_down" or choices[player] == "go_left" or choices[player] == "go_right" or  choices[player] == "fire_up" or choices[player] == "fire_down" or choices[player] == "fire_left" or choices[player] == "fire_right" or choices[player] == "crash":
                c.execute("INSERT INTO actions (key, value) VALUES (?, ?)", [player, choices[player]])

            else:
                print(player+" ("+names[player]+") sent incorrect command: "+str(choices[player]))
                errors[player] += 1
            #db record
        for player in players:
            if player in banlist:
                continue
            px = coords[player]["x"]
            py = coords[player]["y"]
            if choices[player] == "fire_up":
                shots[player] += 1
                for y in range(py-1, -1, -1):
                    if mainMap[px][y] != '.':
                        hit_player = mainMap[px][y]

                        health[hit_player]-=1
                        healthMap[px][y] -= 1

                        kills[player]+=1

                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(px) + ", " + str(
                            y) + "] " + choices[player])

                        if health[hit_player]<=0:
                            mainMap[px][y] = '.'
                            healthMap[px][y] = 0
                            health[hit_player] = 0
                            lifeplayers-=1
                            players.remove(hit_player)
                            print(hit_player+" is dead!")

                        c.execute("UPDATE game SET life = " + str(health[hit_player]) + " WHERE key = ?", [hit_player])
                        break
            if choices[player] == "fire_down":
                shots[player] += 1
                for y in range(py+1, int(settings["height"])):
                    if mainMap[px][y] != '.':
                        hit_player = mainMap[px][y]

                        health[hit_player] -= 1
                        healthMap[px][y] -= 1

                        kills[player] += 1

                        print(player + " ("+str(health[player])+") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> ["+str(px)+", "+str(y)+"] " + choices[player])

                        if health[hit_player] <= 0:
                            mainMap[px][y] = '.'
                            healthMap[px][y] = 0
                            health[hit_player] = 0
                            lifeplayers -= 1
                            print(hit_player + " is dead!")
                            players.remove(hit_player)

                        c.execute("UPDATE game SET life = " + str(health[hit_player]) + " WHERE key = ?", [hit_player])
                        break
            if choices[player] == "fire_left":
                shots[player] += 1
                for x in range(px-1, -1, -1):
                    if mainMap[x][py] != '.':
                        hit_player = mainMap[x][py]

                        health[hit_player] -= 1
                        healthMap[x][py] -= 1

                        kills[player] += 1

                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(x) + ", " + str(
                            py) + "] " + choices[player])

                        if health[hit_player] <= 0:
                            mainMap[x][py] = '.'
                            healthMap[x][py] = 0
                            health[hit_player] = 0
                            lifeplayers -= 1
                            print(hit_player + " is dead!")
                            players.remove(hit_player)

                        c.execute("UPDATE game SET life = " + str(health[hit_player]) + " WHERE key = ?", [hit_player])
                        break
            if choices[player] == "fire_right":
                shots[player] += 1
                for x in range(px+1, int(settings["width"])):
                    if mainMap[x][py] != '.':
                        hit_player = mainMap[x][py]

                        health[hit_player] -= 1
                        healthMap[x][py] -= 1

                        kills[player] += 1

                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(x) + ", " + str(
                            py) + "] " + choices[player])

                        if health[hit_player] <= 0:
                            mainMap[x][py] = '.'
                            healthMap[x][py] = 0
                            health[hit_player] = 0
                            lifeplayers -= 1
                            print(hit_player + " is dead!")
                            players.remove(hit_player)


                        c.execute("UPDATE game SET life = " + str(health[hit_player]) + " WHERE key = ?", [hit_player])
                        break
            if choices[player] == "fire_up" or choices[player] == "fire_down" or choices[player] == "fire_left" or choices[player] == "fire_right":
                c.execute(
                    "UPDATE statistics SET kills = " + str(kills[player]) + " WHERE key = ?",
                    [player])
                #print(player + " sent "+choices[player])

                # db record

            if int(health[player])>0:
                c.execute(
                    "UPDATE statistics SET lifetime = " + str(ticks) + " WHERE key = ?",
                    [player])
                c.execute(
                    "UPDATE statistics SET shots = " + str(shots[player]) + " WHERE key = ?",
                    [player])
                c.execute(
                    "UPDATE statistics SET steps = " + str(steps[player]) + " WHERE key = ?",
                    [player])
                c.execute(
                    "UPDATE statistics SET errors = " + str(errors[player]) + " WHERE key = ?",
                    [player])


            conn.commit()
        conn.commit()
        time.sleep(0.7)

    c.execute("UPDATE settings SET value = ? WHERE param = ?", ["stop", "game_state"])

    conn.commit()
    return settings

while 1:
    s = make_testing()
    if s['mode']!='sandbox':
        break
    time.sleep(5)









