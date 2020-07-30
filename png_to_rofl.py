import cv2
import os 
import numpy as np
import pytesseract
import json
weekdays = ["Th","F","S","M","Tu","W"]
directory = "Scrim_files"
stat_types_page1 = ["kda","TOTAL_DAMAGE_DEALT_TO_CHAMPIONS","TOTAL_DAMAGE_DEALT_TO_TURRETS"]
stat_types_page2 = ["GOLD_SPENT","VISION_SCORE","CONTROL_WARDS_PURCHASED"]
players_order = ["GW Enjavwe","GW Seelame","GW KarimKt","GW Salut a tous","GW Von"]
stats_to_compare = ["TOTAL_DAMAGE_DEALT_TO_CHAMPIONS"]
comparisons_field_names = {"TOTAL_DAMAGE_DEALT_TO_CHAMPIONS" : "DAMAGE_DIFFERENCE"}
decalage_pix_entre_le_type_de_stat_et_la_stat = 222
arrangment = [0,1,3,4,2]

largeur_stat = 75
used_fields = ["NAME","SKIN","GOLD_SPENT","CHAMPIONS_KILLED","NUM_DEATHS","ASSISTS","VISION_SCORE","TOTAL_DAMAGE_DEALT_TO_CHAMPIONS","TOTAL_DAMAGE_DEALT_TO_TURRETS","CONTROL_WARDS_PURCHASED","DAMAGE_DIFFERENCE"]
records = json.loads(open("manual_record.json").read())

champion_template = cv2.imread("Resources/champion_template.png")
champion_describer = json.loads(open("Resources/describer.json").read())
dirs_to_ignore = ["09-07-2020","10-07-2020"]

def get_week_scrims_to_rofl():
    game_rofls_dict = {}
    dirs = [x for x in os.listdir(directory) if x not in dirs_to_ignore]
    for date_dir in dirs:
        print("Scrims of",date_dir)
        for filename in os.listdir(directory + "/" + date_dir):
            if (filename.endswith(".PNG") or filename.endswith(".png")) and "BW" not in filename:
                game_identifier = date_dir + filename[:2]
                stats_computed_already = False
                print(filename)
                if game_identifier not in game_rofls_dict.keys():
                    try:
                        game_rofl = json.loads(open("Scrim_files/"+game_identifier[:10]+"/"+game_identifier[10:]+".json").read())
                        print("Game found, reusing already found stats")
                        stats_computed_already = True
                    except FileNotFoundError:
                        game_rofl = get_empty_game_dict()
                    
                else:
                    game_rofl = game_rofls_dict[game_identifier]
                print(stats_computed_already)
                if not stats_computed_already:
                    img = cv2.imread("Scrim_files/"+date_dir+"/"+filename,cv2.IMREAD_UNCHANGED)
                    if len(img.shape) > 2 and img.shape[2] == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    name = directory + "/"+date_dir + "/" + filename.replace(".PNG","")
                    color_img = np.copy(img)
                    
                    convert_to_bw(img,name)
                    
                    game_in_scrim = filename[2]
                    
                    if filename.count(game_in_scrim) == 2:
                        print("Analyzing :"+game_identifier,filename)
                        win, MPx, MPy = did_we_win(img)
                        game_rofl["MatchMetadata"]["Win"] = win
                        if game_rofl["MatchMetadata"]["GameDuration"] is 0:
                            game_rofl["MatchMetadata"]["GameDuration"] = read_game_duration(img,MPx,MPy)
                        if win:
                            print("WIN")
                        else:
                            print("DEFEAT")
                        #game_rofl["MatchMetadata"]["GameDuration"] = read_game_duration(img)
                        index = 0
                        #for champion in read_champions(color_img,MPx,MPy):
                        #    game_rofl["MatchMetadata"]["AllPlayers"][index]["SKIN"] = champion
                        #    index +=1
                        #cv2.imwrite("CONNARDEDEMERDE.PNG",champion_template)
                        
                        for stat_type in stat_types_page1:
                            MPx,MPy,trows,tcols  = find_line(stat_type,img,name)
                            result = read_stat(MPx,MPy,trows,img,name,stat_type)
                            if stat_type == "kda":
                                index = 0
                                for stat in result:
                                    k,d,a = stat.rsplit("/")
                                    game_rofl["MatchMetadata"]["AllPlayers"][index]["CHAMPIONS_KILLED"] = k
                                    game_rofl["MatchMetadata"]["AllPlayers"][index]["NUM_DEATHS"] = d
                                    game_rofl["MatchMetadata"]["AllPlayers"][index]["ASSISTS"] = a
                                    index +=1
                            elif stat_type in stats_to_compare:
                                stat_name = comparisons_field_names[stat_type]
                                for stat in result[:5]:
                                    index = result.index(stat)
                                    game_rofl["MatchMetadata"]["AllPlayers"][index][stat_type] = stat
                                for stat in result[5:]:
                                    print("Rewrite ok")
                                    index = result[5:].index(stat)
                                    game_rofl["MatchMetadata"]["AllPlayers"][index][stat_name] = str(int(result[arrangment[index%5]]) - int(stat))
                            else:
                                index = 0
                                for stat in result:
                                    if stat_type=="CONTROL_WARDS_PURCHASED":
                                        print(game_rofl["MatchMetadata"]["AllPlayers"][index]["SKIN"] + " WAS CORRECTLY WRITTEN FU NOW")
                                    game_rofl["MatchMetadata"]["AllPlayers"][index][stat_type] = stat
                                    index +=1

                    if filename.count(game_in_scrim) == 4:
                        for stat_type in stat_types_page2:
                            MPx,MPy,trows,tcols  = find_line(stat_type,img,name)
                            result = read_stat(MPx,MPy,trows,img,name,stat_type)
                            index = 0
                            for stat in result:
                                game_rofl["MatchMetadata"]["AllPlayers"][index][stat_type] = stat
                                index +=1
                    game_rofls_dict[game_identifier] = game_rofl
                
                else:
                    still_empty_stats = check_dict_status(game_rofl)
                    img = cv2.imread("Scrim_files/"+date_dir+"/"+filename,cv2.IMREAD_UNCHANGED)
                    if len(img.shape) > 2 and img.shape[2] == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    name = directory + "/"+date_dir + "/" + filename.replace(".PNG","")
                    color_img = np.copy(img)
                    convert_to_bw(img,name)
                    game_in_scrim = filename[2]
                    if filename.count(game_in_scrim) == 2:
                        print("Analyzing :"+game_identifier,filename)
                        win, MPx, MPy = did_we_win(img)
                        game_rofl["MatchMetadata"]["Win"] = win
                        game_rofl["MatchMetadata"]["GameDuration"] = read_game_duration(img,MPx,MPy)
                        if win:
                            print("WIN")
                        else:
                            print("DEFEAT")
                        #game_rofl["MatchMetadata"]["GameDuration"] = read_game_duration(img)
                        index = 0
                        #for champion in read_champions(color_img,MPx,MPy):
                        #    game_rofl["MatchMetadata"]["AllPlayers"][index]["SKIN"] = champion
                        #    index +=1
                        #cv2.imwrite("CONNARDEDEMERDE.PNG",champion_template)
                        
                        for stat_type in stat_types_page1:
                            if stat_type in still_empty_stats:
                                MPx,MPy,trows,tcols  = find_line(stat_type,img,name)
                                result = read_stat(MPx,MPy,trows,img,name,stat_type)
                                if stat_type == "kda":
                                    index = 0
                                    for stat in result:
                                        
                                        k,d,a = stat.rsplit("/")
                                        game_rofl["MatchMetadata"]["AllPlayers"][index]["CHAMPIONS_KILLED"] = k
                                        game_rofl["MatchMetadata"]["AllPlayers"][index]["NUM_DEATHS"] = d
                                        game_rofl["MatchMetadata"]["AllPlayers"][index]["ASSISTS"] = a
                                        index +=1
                                elif stat_type in stats_to_compare:
                                    stat_name = comparisons_field_names[stat_type]
                                    for stat in result[:5]:
                                        
                                        index = result.index(stat)
                                        game_rofl["MatchMetadata"]["AllPlayers"][index][stat_type] = stat
                                    for stat in result[5:]:
                                        index = result[5:].index(stat)
                                        game_rofl["MatchMetadata"]["AllPlayers"][index][stat_name] = str(int(result[arrangment[index%5]]) - int(stat))
                                else:
                                    index = 0
                                    for stat in result:
                                        game_rofl["MatchMetadata"]["AllPlayers"][index][stat_type] = stat
                                        index +=1
                    if filename.count(game_in_scrim) == 4:
                        for stat_type in stat_types_page2:
                            if stat_type in still_empty_stats:
                                MPx,MPy,trows,tcols  = find_line(stat_type,img,name)
                                result = read_stat(MPx,MPy,trows,img,name,stat_type)
                                index =0
                                for stat in result:
                                    index = result.index(stat)
                                    game_rofl["MatchMetadata"]["AllPlayers"][index][stat_type] = stat
                                    index +=1
                    game_rofls_dict[game_identifier] = game_rofl
    for scrim in game_rofls_dict.keys():
        try:
            kills = 0
            scr = game_rofls_dict[scrim]
            for player in scr["MatchMetadata"]["AllPlayers"]:
                kills += int(player["CHAMPIONS_KILLED"])
            for player in scr["MatchMetadata"]["AllPlayers"]:
                player["Kill participation"] = str((int(player["CHAMPIONS_KILLED"]) + int(player["ASSISTS"]))/kills)

            file = open("Scrim_files/"+scrim[:10]+"/"+scrim[10:]+".json","w+")
            file.write(json.dumps(game_rofls_dict[scrim]))
            print(scrim+".json written")
        except:
            pass
    
    file = open("manual_record.json","w+")
    file.write(json.dumps(records))
    return game_rofls_dict

def convert_to_bw(image,name):
    for i in range(len(image)):
        for j in range(len(image[i])):
            pixel = image[i][j]
            if pixel[2] > 50:
                pixel[0] = 0
                pixel[1] = 0
                pixel[2] = 0
            else:             
                pixel[0] = 255
                pixel[1] = 255
                pixel[2] = 255
    cv2.imwrite(name+"BW.PNG",image)

def find_line(stat_type,large_image,name):
    print("Reading:",stat_type)
    small_image = cv2.imread("Resources/"+stat_type+".png")
    method = cv2.TM_CCOEFF_NORMED
    

    result = cv2.matchTemplate(small_image, large_image, method)

    mn, value, mnLoc, mxLoc = cv2.minMaxLoc(result)

    MPx, MPy = mxLoc
    trows, tcols = small_image.shape[:2]
    cv2.rectangle(large_image, (MPx, MPy), (MPx + tcols, MPy + trows), (0, 0, 255), 2)
    return MPx,MPy,trows,tcols

def read_stat(MPx,MPy,trows,image,name,type):
    print("Analyzing stat:",type)
    toRet = []

    nb_to_read = (int(type in stats_to_compare)+1)*5
    print(nb_to_read)
    for stat_index in range(nb_to_read):
        stat_id = name + type + str(stat_index)

        left_border = MPx+decalage_pix_entre_le_type_de_stat_et_la_stat + largeur_stat * stat_index
        right_border = MPx+decalage_pix_entre_le_type_de_stat_et_la_stat + largeur_stat * (stat_index+1)

        stat_number = image[MPy:MPy+trows,  left_border:right_border]
        
        
        number = pytesseract.image_to_string(stat_number)
        number = number.replace(",","").replace("(","")

        while (number == "" or conditions_respected(type,number) == False):
            try:
                if conditions_respected(type,records[stat_id]) == False:
                    cv2.imshow("Number",stat_number)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                    number = input("Please type the number who appears on screen, computer detected "+number+"but it seems false:")
                    records[stat_id] = number
                else:
                    number = records[stat_id]
            except:
                cv2.imshow("Number",stat_number)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                number = input("Please type the number who appears on screen, computer detected "+number+"but it seems false:")
                records[stat_id] = number
            

        cv2.imwrite("Training_sets/"+number+".PNG",stat_number)
        toRet.append(number)
    print(toRet)
    return toRet

def read_game_duration(large_image,MPx,MPy):
    space_between_vic_and_duration = ( 226-90 , 49-21)
    left_border = MPx+space_between_vic_and_duration[0] 
    right_border = MPx+space_between_vic_and_duration[0] + 42
    MPy = MPy + space_between_vic_and_duration[1]
    stat_number = large_image[MPy:MPy+12,  left_border:right_border]
     
    
    
    number = pytesseract.image_to_string(stat_number)
    if conditions_respected("duration",number):
        number = number.rsplit(":")
        minutes = int(number[0])
        seconds = int(number[1])
        return minutes*60 + seconds
    else:
        cv2.imshow("Number",stat_number)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        number = input("Please type the number who appears on screen, computer detected "+number+"but it seems false:")
        number = number.rsplit(":")
        minutes = int(number[0])
        seconds = int(number[1])
        return minutes*60 + seconds

def did_we_win(large_image):
    win_img = cv2.imread("Resources/victory.png")
    loose_img = cv2.imread("Resources/defeat.png")
    
    method = cv2.TM_CCOEFF_NORMED
    

    result_win = cv2.matchTemplate(win_img, large_image, method)
    result_loose = cv2.matchTemplate(loose_img, large_image, method)
    __, value_win, __, mxLocWin = cv2.minMaxLoc(result_win)
    __, value_loose, __, mxLocLoose = cv2.minMaxLoc(result_loose)
    
    
    if value_win>value_loose:
        MPx, MPy = mxLocWin
        trows, tcols = win_img.shape[:2]
        cv2.rectangle(large_image, (MPx, MPy), (MPx + tcols, MPy + trows), (0, 0, 255), 2)
        return True,MPx,MPy
    else:
        MPx, MPy = mxLocLoose
        trows, tcols = loose_img.shape[:2]
        cv2.rectangle(large_image, (MPx, MPy), (MPx + tcols, MPy + trows), (0, 0, 255), 2)
        return False,MPx,MPy

def read_champions(img,Mpx,MPy):
    #Bard : 293,130
    #Vic : 83,17
    ecart = 75
    size = (10,10)

    space_between_vic_and_champion = ( 293-83 , 149-17)

    Mpx = Mpx + space_between_vic_and_champion[0]
    MPy = space_between_vic_and_champion[1]
    toRet = []
    fname = ""
    for index in range(5):
        
        posx = Mpx + (index*ecart)
        left_border = posx
        right_border = posx + size[0]
        champion_image = img[MPy:MPy+size[1],  left_border:right_border]
        cv2.imshow("bite",champion_image)
        cv2.waitKey(0)
        
        method = cv2.TM_CCOEFF_NORMED
        result = cv2.matchTemplate(champion_image, champion_template, method)
        __, value , __, mxLocWin = cv2.minMaxLoc(result)
        resX,resY = mxLocWin
        toRet.append(champion_describer[resX])
        cv2.rectangle(img, (posx, MPy), (posx + 15, MPy + 15), (0, 0, 255), 2)
        cv2.rectangle(champion_template,(resX,resY),(resX+15,resY + 15), (0, 0, 255), 2)
        print(resX)
        print(champion_describer[resX])
        
        cv2.imshow("connard",champion_template)
        cv2.waitKey(0)
        fname+=champion_describer[resX]
        
    
    cv2.imwrite(fname+".PNG",img)
    return toRet 

def conditions_respected(type, number_string):
    if type == "kda":
        if number_string.count('/') !=2:
            return False
        return number_string.replace("/","").isdigit()
    if type == "duration":
        if number_string.count(':') !=1:
            return False
        test = number_string.rsplit(":")
        if len(test[0]) != 2 or len(test[1])!=2:
            return False
        if test[0].isdigit() and test[1].isdigit():
            return True
    return number_string.isdigit() and number_string!=""


def get_empty_game_dict():
    toRet = {}
    toRet["MatchMetadata"] = {}
    toRet["MatchMetadata"]["GameDuration"] = 0
    toRet["MatchMetadata"]["AllPlayers"] = [get_player_stat_dict() for x in range(5)]
    for player in players_order:
        index = players_order.index(player)
        toRet["MatchMetadata"]["AllPlayers"][index]["NAME"] = player
    return toRet

def get_player_stat_dict():
    player_stat_dict = {}
    for field in used_fields:
        player_stat_dict[field] = ""
    return player_stat_dict
    
def check_dict_status(game_rofl):
    empty_stats = []
    for participant in game_rofl["MatchMetadata"]["AllPlayers"]:
        for stat in used_fields:
            if (stat not in participant.keys() or participant[stat] == "") and stat not in empty_stats:
                empty_stats.append(stat)
    if ("CHAMPIONS_KILLED" in empty_stats or "NUM_DEATHS" in empty_stats or "ASSISTS" in empty_stats):
        empty_stats.append("kda")
    empty_stats.append("CONTROL_WARDS_PURCHASED")
    print(empty_stats)
    return empty_stats

get_week_scrims_to_rofl()