import cv2
import os 
import numpy as np
import pytesseract
import json
weekdays = ["Th","F","S","M","Tu","W"]
directory = "Scrim_files"
stat_types_page1 = ["kda","TOTAL_DAMAGE_DEALT_TO_CHAMPIONS"]
stat_types_page2 = ["GOLD_SPENT","VISION_SCORE"]
players_order = ["GW Enjavwe","GW Seelame","GW KarimKt","GW Salut a tous","GW Von"]

decalage_pix_entre_le_type_de_stat_et_la_stat = 222

largeur_stat = 75
used_fields = ["NAME","SKIN","GOLD_SPENT","CHAMPIONS_KILLED","NUM_DEATHS","ASSISTS","VISION_SCORE","TOTAL_DAMAGE_DEALT_TO_CHAMPIONS"]
records = json.loads(open("Scrim_files/manual_record.json").read())


def get_week_scrims_to_rofl():
    game_rofls_dict = {}
    for filename in os.listdir(directory):
        if filename.endswith(".PNG") and "BW" not in filename:
            if filename[:3] not in game_rofls_dict.keys():
                game_rofl = get_empty_game_dict()
            else:
                game_rofl = game_rofls_dict[filename[:3]]
            img = cv2.imread("Scrim_files/"+filename,cv2.IMREAD_UNCHANGED)
            if len(img.shape) > 2 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            name = "Scrim_files/"+filename.replace(".PNG","")
            convert_to_bw(img,name)
            if "STATS1" in filename:
                for stat_type in stat_types_page1:
                    MPx,MPy,trows,tcols  = find_line(stat_type,img,name)
                    result = read_stat(MPx,MPy,trows,img,name,stat_type)
                    if stat_type == "kda":
                        for stat in result:
                            index = result.index(stat)
                            k,d,a = stat.rsplit("/")
                            game_rofl["MatchMetadata"]["AllPlayers"][index]["CHAMPIONS_KILLED"] = k
                            game_rofl["MatchMetadata"]["AllPlayers"][index]["NUM_DEATHS"] = d
                            game_rofl["MatchMetadata"]["AllPlayers"][index]["ASSISTS"] = a
                    else:
                        for stat in result:
                            index = result.index(stat)
                            game_rofl["MatchMetadata"]["AllPlayers"][index][stat_type] = stat
            else:
                for stat_type in stat_types_page2:
                    MPx,MPy,trows,tcols  = find_line(stat_type,img,name)
                    result = read_stat(MPx,MPy,trows,img,name,stat_type)
                    for stat in result:
                        index = result.index(stat)
                        game_rofl["MatchMetadata"]["AllPlayers"][index][stat_type] = stat
            game_rofls_dict[filename[:3]] = game_rofl
    
    for scrim in game_rofls_dict.keys():
        file = open("Scrim_files/"+scrim+".json","w+")
        file.write(json.dumps(game_rofls_dict[scrim]))
        print(scrim+".json written")
    
    file = open("Scrim_files/manual_record.json","w+")
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
    small_image = cv2.imread("Resources/"+stat_type+".png")
    method = cv2.TM_CCOEFF_NORMED
    

    result = cv2.matchTemplate(small_image, large_image, method)

    mn, value, mnLoc, mxLoc = cv2.minMaxLoc(result)

    MPx, MPy = mxLoc
    trows, tcols = small_image.shape[:2]
    cv2.rectangle(large_image, (MPx, MPy), (MPx + tcols, MPy + trows), (0, 0, 255), 2)
    return MPx,MPy,trows,tcols

def read_stat(MPx,MPy,trows,image,name,type):
    toRet = []
    for stat_index in range(5):
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

def conditions_respected(type, number_string):
    if type == "kda":
        if number_string.count('/') !=2:
            return False
        return number_string.replace("/","").isdigit()
    return number_string.isdigit()


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
    


get_week_scrims_to_rofl()