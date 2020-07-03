import json
import xlsxwriter
from datetime import date

gameward = ["GW Salut a tous","GW KarimKt","GW Von","GW Seelame","GW Enjavwe"]


raw_stats = ["NUM_DEATHS","CHAMPIONS_KILLED","NUM_ASSISTS"]
per_minute_stats = ["GOLD_SPENT","TOTAL_DAMAGE_DEALT_TO_CHAMPIONS","VISION_SCORE"]
per_minutes_stats_proper_names = ["Golds/min","Dmg/min","Vision/min"]

directory = "Scrim_files"


def get_week_statistics(week):
    overall = get_all_players_dict()
    per_champion = get_player_dict_per_champion()
    number_of_games = 0

    if week == "This week":
        directory = "Scrim_files"
    else:
        directory =  "Last_week_scrim_files"

    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            number_of_games+=1
            json_match = json.loads(open(filename).read())

            for player in json_match["MatchMetadata"]["AllPlayers"]:
                if player["NAME"] in gameward:
                    for stat in per_minute_stats:
                        overall[player["NAME"]][stat] += player[stat]/((json_match["MatchMetadata"]["GameDuration"]/1000)/60)
                    for stat in raw_stats:
                        overall[player["NAME"]][stat] += player[stat]/json_match["MatchMetadata"]["GameDuration"]

                if player["SKIN"] in per_champion[player["NAME"]].keys():
                    for stat in per_minute_stats:
                        per_champion[player["NAME"]][  player["SKIN"]] += player[stat]/((json_match["MatchMetadata"]["GameDuration"]/1000)/60)
                    for stat in raw_stats:
                        per_champion[player["NAME"]][  player["SKIN"]] += player[stat]/json_match["MatchMetadata"]["GameDuration"]
    
    for player in overall.keys():
        pl = overall[player]
        for stat in pl.keys():
            pl[stat] /= number_of_games
    
    for player in per_champion.keys():
        pl = overall[player]
        for champion in pl.keys():
            pla = pl[champion]
            for stat in pla.keys():
                pla[stat] /= number_of_games

    return overall, per_champion
        
                 
def get_empty_stats_dict():
    toRet = {}
    for stat in stats:
        toRet[stat] = 0
    return toRet

def kda_str(kills,death,assists):
    return str(round(kills,1)) + "/" + str(round(death,1)) + str(round(assists,1))

def stats_variation(this_week_stat, previous_week_stat):
    value = round(1 - this_week_stat/previous_week_stat,1)
    if value>1:
        return "+" + str(value) + "%"
    else:
        return str(value) + "%"
    

def get_all_players_dict():
    toRet = {}
    for player in gameward:
        toRet[player] = get_empty_stats_dict()
    return toRet

def get_player_dict_per_champion():
    toRet = {}
    for player in gameward:
        toRet[player] = {}
    return toRet

class WeekReport(xlsxwriter.Workbook):
    def init_formats(self):
        self.fmt_header = self.add_format()
        self.fmt_header.set_bg_color("orange")
        self.fmt_header.set_font_name("Fredoka One")
        self.fmt_header.set_font_color("white")
        self.fmt_header.set_align('center')
        self.fmt_header.set_align('vcenter')
        self.fmt_gray = self.add_format()
        self.fmt_gray.set_bg_color("gray")
        self.fmt_gray.set_font_name("Fredoka One")
        self.fmt_gray.set_font_color("white")
        self.fmt_gray.set_align('center')
        self.fmt_gray.set_align('vcenter')
        self.fmt_black = self.add_format()
        self.fmt_black.set_bg_color("black")
        self.fmt_black.set_font_name("Fredoka One")
        self.fmt_black.set_font_color("white")
        self.fmt_black.set_align('center')
        self.fmt_black.set_align('vcenter')
        self.fmt_blue = self.add_format()
        self.fmt_blue.set_bg_color("#0e0e7d")
        self.fmt_blue.set_font_name("Fredoka One")
        self.fmt_blue.set_font_color("white")
        self.fmt_blue.set_align('center')
        self.fmt_blue.set_align('vcenter')
        self.fmt_red = self.add_format()
        self.fmt_red.set_bg_color("#7d0e0e")
        self.fmt_red.set_font_name("Fredoka One")
        self.fmt_red.set_font_color("white")
        self.fmt_red.set_align('center')
        self.fmt_red.set_align('vcenter')
        
    def __init__(self):
        super().__init__("Week_report_"+date.today()+".xlsx")
        self.overall_stats_this_week, self.stats_per_champion_this_week = get_week_statistics("This week")
        self.overall_stats_last_week, self.stats_per_champion_last_week = get_week_statistics("Last week")
        self.init_formats()
        self.week_report = self.add_worksheet(date.today())
    
    def write_player_stats(self, starting_row,playername,player_overall_stats,player_per_champion_stats,last_week_overall,last_week_per_champion):
        self.week_report.write(starting_row, 0, playername, self.fmt_header)
        self.week_report.write(starting_row+1,0,"Overall",self.fmt_header)

        self.week_report.write(starting_row+2,0,"KDA",self.fmt_gray)
        self.week_report.write(starting_row+2,1,kda_str(player_overall_stats["CHAMPIONS_KILLED"],player_overall_stats["NUM_DEATHS"],player_overall_stats["NUM_ASSISTS"]),self.fmt_gray)

        for stat_index in range(len(per_minute_stats)):
            stat_type = per_minute_stats[stat_index]
            self.week_report.write(starting_row+3 + stat_index ,0, per_minutes_stats_proper_names[stat_index], self.fmt_gray)
            self.week_report.write(starting_row+3 + stat_index ,1, player_overall_stats[stat_type], self.fmt_gray)
            self.week_report.write(starting_row+3 + stat_index ,2, stats_variation(player_overall_stats[stat_type],last_week_overall[stat_type]), self.fmt_gray)
        