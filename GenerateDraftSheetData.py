import csv
import json

class GenerateDraftSheetData:
    def __init__(self, player_ids, stat_list, league_size=12, team_size=23):
        self.stat_list = stat_list
        self.league_size = league_size
        self.team_size = team_size
        self.projections = {}
        self.rankings = {}
        self.players = {}
        for player_id in player_ids:
            self.players[player_id] = {}

    def read_projection(self, projection_source, projection_file):
        self.projections[projection_source] = {}
        with open(projection_file) as f:
            reader = csv.DictReader(f)
            for line in reader:
                self.projections[projection_source][line['playerid']] = line

    def read_ranking(self, ranking_source, ranking_file):
        self.rankings[ranking_source] = {}
        with open(ranking_file) as f:
            reader = csv.DictReader(f)
            for line in reader:
                self.rankings[ranking_source][line['playerid']] = line

    def __create_average_projection(self):
        self.projections['average'] = {}
        for player in self.players:
            projection_count = 0
            for projection in self.projections:
                if player in self.projections[projection]:
                    if player in self.projections['average']:
                        for stat in self.projections[projection][player]:
                            if stat not in ['playerid', 'Name', 'Team', 'ADP']:
                                self.projections['average'][player][stat] = \
                                    (float(self.projections['average'][player][stat]) * projection_count
                                     + float(self.projections[projection][player][stat])) / (projection_count + 1)
                    else:
                        self.projections['average'][player] = self.projections[projection][player]
                    projection_count += 1
                    print(self.projections['average'][player])

    def __calculate_points(self):
        print('Calculate points')
        # Calculate points

    def create_players(self):
        self.__create_average_projection()
        self.__calculate_points()
        for player in self.players:
            # Add Age (API?)
            if player in self.rankings:
                print('Add ranking')
                # Add Team (from FantasyPros)
                # Add Position (from FantasyPros)
            for projection in self.projections:
                if player in self.projections[projection]:
                    print('Add projection')
                    # Add ADP (from projections)
                    # Add points

if __name__ == '__main__':
    with open("./PlayerId/PlayerIdList.json", "r") as p:
        player_id_list = p.read()
    with open("./StatList/StatList.json", "r") as s:
        stat_list = s.read()
    data_generator = GenerateDraftSheetData(json.loads(player_id_list), json.loads(stat_list))
    data_generator.read_projection("ZiPS", "./FangraphProjections/ZiPS.csv")
    data_generator.create_players()

