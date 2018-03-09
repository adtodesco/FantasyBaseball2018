import csv
import glob
import os


class DraftSheetGenerator:
    BATTER_MULTIPLIER = 1.03
    STARTER_MULTIPLIER = 1.46
    RELIEF_MULTIPLIER = 1.10

    def __init__(self, pids, stats, league_size=12, team_size=23):
        self.stats = stats
        self.league_size = league_size
        self.team_size = team_size
        self.projections = {}
        self.rank = {}
        self.players = {}
        for pid in pids:
            self.players[pid] = {}

    def read_projection(self, projection_file):
        projection, player_type = os.path.splitext(os.path.basename(projection_file))[0].split('-')
        if projection not in self.projections:
            self.projections[projection] = {}
        with open(projection_file) as f:
            reader = csv.DictReader(f)
            count = 0
            for line in reader:
                count += 1
                player = line['playerid']
                self.projections[projection][player] = {}
                self.projections[projection][player]['type'] = player_type
                for stat in self.stats:
                    if stat in line:
                        if self.stats[stat] == "int":
                            self.projections[projection][player][stat] = int(line[stat])
                        elif self.stats[stat] == "float":
                            self.projections[projection][player][stat] = float(line[stat])
                        else:
                            self.projections[projection][player][stat] = line[stat]

    def read_ranking(self, ranking_file, pid_map):
        ranking = os.path.splitext(os.path.basename(ranking_file))[0]
        self.rank[ranking] = {}
        with open(ranking_file) as f:
            reader = csv.DictReader(f)
            for line in reader:
                if line['Player'] in pid_map:
                    self.rank[pid_map[line['Player']]] = line

    def __create_average_projection(self):
        average_projection = {}
        for player in self.players:
            average_projection[player] = {}
            for stat in self.stats:
                total = count = 0
                for projection in self.projections:
                    if player in self.projections[projection]:
                        average_projection[player]['type'] = self.projections[projection][player]['type']
                        if stat in ['playerid', 'Name', 'Team', 'ADP']:
                            average_projection[player][stat] = self.projections[projection][player][stat]
                        elif stat in self.projections[projection][player]:
                            total += self.projections[projection][player][stat]
                            count += 1
                # Ensure player is in projections that have been read; skip string stats; skip non applicable stats
                if count > 0:
                    if self.stats[stat] == 'int':
                        average_projection[player][stat] = int(total / count)
                    else:
                        average_projection[player][stat] = total / count
        self.projections['Average'] = average_projection

    def __calculate_points(self):
        for projection in self.projections:
            for player in self.projections[projection]:
                if self.projections[projection][player]['type'] == 'Batter':
                    points = self.projections[projection][player]['H'] * 2
                    points += self.projections[projection][player]['2B'] * 2
                    points += self.projections[projection][player]['3B'] * 4
                    points += self.projections[projection][player]['HR'] * 6
                    points += self.projections[projection][player]['R']
                    points += self.projections[projection][player]['RBI']
                    points += self.projections[projection][player]['BB']
                    points += self.projections[projection][player]['HBP']
                    points += self.projections[projection][player]['SO'] * -1
                    points += self.projections[projection][player]['SB'] * 2
                    points += self.projections[projection][player]['CS'] * -1
                    self.projections[projection][player]['points'] = points
                else:
                    points = self.projections[projection][player]['IP'] * 3
                    points += self.projections[projection][player]['ER'] * -2
                    points += self.projections[projection][player]['W'] * 5
                    points += self.projections[projection][player]['L'] * -5
                    if 'SV' in self.projections[projection][player]:
                        points += self.projections[projection][player]['SV'] * 7
                    points += self.projections[projection][player]['SO']
                    points += self.projections[projection][player]['H'] * -1
                    points += self.projections[projection][player]['BB'] * -1
                    self.projections[projection][player]['points'] = points

    def __create_players(self):
        for player in self.players:
            # TODO: Add Age (API?)
            if player in self.rank:
                self.players[player]['Rank'] = self.rank[player]['Rank']
                self.players[player]['Team'] = self.rank[player]['Team']
                self.players[player]['Positions'] = self.rank[player]['Positions'].split(',')
            for projection in self.projections:
                if player in self.projections[projection]:
                    self.players[player][projection] = {}
                    self.players[player]['Player'] = self.projections[projection][player]['Name']
                    self.players[player]['ADP'] = self.projections[projection][player]['ADP']
                    if self.projections[projection][player]['type'] == 'Batter':
                        self.players[player][projection] = int(round(self.projections[projection][player]['points']
                                                                     * self.BATTER_MULTIPLIER))
                    elif 'Positions' in self.players[player] and 'SP' in self.players[player]['Positions']:
                        self.players[player][projection] = int(round(self.projections[projection][player]['points']
                                                                     * self.STARTER_MULTIPLIER))
                    else:
                        self.players[player][projection] = int(round(self.projections[projection][player]['points']
                                                                     * self.RELIEF_MULTIPLIER))
                    # TODO: Add 2017 Points
                    # TODO: Add player rank
                    # TODO: Add position rank

    def __write_draft_sheet(self, ds_file):
        with open(ds_file, 'w') as d:
            writer = csv.writer(d)
            columns = ['Player', 'Team', 'Positions', 'ZiPS', 'Fans', 'Streamer', 'DepthCharts', 'Average', 'Rank',
                       'ADP']
            writer.writerow(columns)
            for player in self.players:
                row = []
                for column in columns:
                    if column in self.players[player]:
                        row.append(self.players[player][column])
                    else:
                        row.append('')
                writer.writerow(row)

    def generate_draft_sheet(self, draft_sheet_file):
        self.__create_average_projection()
        self.__calculate_points()
        self.__create_players()
        self.__write_draft_sheet(draft_sheet_file)


def generate_metadata(p_files):
    pid_map = {}
    pid_set = set([])
    st_map = {}
    for p_file in p_files:
        with open(p_file) as p:
            reader = csv.DictReader(p)
            for line in reader:
                pid_map[line['Name']] = line['playerid']
                pid_set.add(line['playerid'])
                for stat in line:
                    if stat in ['-1']:
                        break
                    elif stat in ['playerid', 'Team', 'Name']:
                        st_map[stat] = 'str'
                    elif stat not in st_map:
                        st_map[stat] = 'int'
                    if "." in line[stat]:
                        st_map[stat] = 'float'
    return pid_map, pid_set, st_map


if __name__ == '__main__':
    projection_files = "./FangraphProjections/*.csv"
    player_id_map, player_id_set, stat_map = generate_metadata(glob.iglob(projection_files))
    draft_sheet_generator = DraftSheetGenerator(player_id_set, stat_map)
    for csv_file in glob.iglob(projection_files):
        draft_sheet_generator.read_projection(csv_file)
    draft_sheet_generator.read_ranking("./Rankings/FantasyPros_Fantasy_Baseball_Rankings_ALL.csv", player_id_map)
    draft_sheet_generator.generate_draft_sheet("./DraftSheet.csv")
