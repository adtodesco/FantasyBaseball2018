import csv
import glob
import os
import operator


class DraftSheetGenerator:
    BATTER_MULTIPLIER = 1.02
    STARTER_MULTIPLIER = 1.46
    RELIEF_MULTIPLIER = 1.10

    def __init__(self, pids, stat_map, league_size=12, team_size=23):
        self.stat_map = stat_map
        self.league_size = league_size
        self.team_size = team_size
        self.projections = {}
        self.stats = {}
        self.rankings = {}
        self.players = {}
        for pid in pids:
            self.players[pid] = {}

    def read_projection(self, projection_file):
        projection, player_type = os.path.splitext(os.path.basename(projection_file))[0].split('-')
        if projection not in self.projections:
            self.projections[projection] = {}
        with open(projection_file) as f:
            reader = csv.DictReader(f)
            for line in reader:
                player = line['playerid']
                self.projections[projection][player] = {}
                self.projections[projection][player]['type'] = player_type
                for stat in self.stat_map:
                    if stat in line:
                        if self.stat_map[stat] == "int":
                            self.projections[projection][player][stat] = int(line[stat])
                        elif self.stat_map[stat] == "float":
                            self.projections[projection][player][stat] = float(line[stat])
                        else:
                            self.projections[projection][player][stat] = line[stat]

    def read_stat(self, stat_file):
        season, player_type = os.path.splitext(os.path.basename(stat_file))[0].split('-')
        if season not in self.stats:
            self.stats[season] = {}
        with open(stat_file) as f:
            reader = csv.DictReader(f)
            for line in reader:
                player = line['playerid']
                # Skipping over pitchers in the Batter stats
                if player_type == 'Batter' and player in self.stats[season]:
                    continue
                self.stats[season][player] = {}
                self.stats[season][player]['type'] = player_type
                self.stats[season][player]['Age'] = int(line['Age'])
                for stat in self.stat_map:
                    if stat in line:
                        if self.stat_map[stat] == "int":
                            self.stats[season][player][stat] = int(line[stat])
                        elif self.stat_map[stat] == "float":
                            self.stats[season][player][stat] = float(line[stat])
                        else:
                            self.stats[season][player][stat] = line[stat]

    def read_ranking(self, ranking_file, pid_map):
        ranking = os.path.splitext(os.path.basename(ranking_file))[0]
        self.rankings[ranking] = {}
        with open(ranking_file) as f:
            reader = csv.DictReader(f)
            for line in reader:
                if line['Player'] + ':' + line['Team'] in pid_map:
                    self.rankings[pid_map[line['Player'] + ':' + line['Team']]] = line
                else:
                    print("Cannot find %s:%s in player id map." % (line['Player'], line['Team']))

    def __create_average_projection(self):
        average_projection = {}
        for player in self.players:
            average_projection[player] = {}
            for stat in self.stat_map:
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
                    if self.stat_map[stat] == 'int':
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
                    if 'HBP' in self.projections[projection][player]:
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
        for season in self.stats:
            for player in self.stats[season]:
                if self.stats[season][player]['type'] == 'Batter':
                    points = self.stats[season][player]['H'] * 2
                    points += self.stats[season][player]['2B'] * 2
                    points += self.stats[season][player]['3B'] * 4
                    points += self.stats[season][player]['HR'] * 6
                    points += self.stats[season][player]['R']
                    points += self.stats[season][player]['RBI']
                    points += self.stats[season][player]['BB']
                    if 'HBP' in self.stats[season][player]:
                        points += self.stats[season][player]['HBP']
                    points += self.stats[season][player]['SO'] * -1
                    points += self.stats[season][player]['SB'] * 2
                    points += self.stats[season][player]['CS'] * -1
                    self.stats[season][player]['points'] = points
                else:
                    points = self.stats[season][player]['IP'] * 3
                    points += self.stats[season][player]['ER'] * -2
                    points += self.stats[season][player]['W'] * 5
                    points += self.stats[season][player]['L'] * -5
                    if 'SV' in self.stats[season][player]:
                        points += self.stats[season][player]['SV'] * 7
                    points += self.stats[season][player]['SO']
                    points += self.stats[season][player]['H'] * -1
                    points += self.stats[season][player]['BB'] * -1
                    self.stats[season][player]['points'] = points

    def __create_players(self):
        for player in self.players:
            player_map = self.players[player]
            if player in self.rankings:
                player_map['FantasyPros Ranking'] = self.rankings[player]['Rank']
                player_map['Team'] = self.rankings[player]['Team']
                player_map['Positions'] = list(set(self.rankings[player]['Positions'].replace(" ", "")
                                                   .replace('LF', 'OF').replace('CF', 'OF').replace('RF', 'OF')
                                                   .split(',')))

            for projection in self.projections:
                projection_map = self.projections[projection]
                if player in projection_map:
                    player_map['Player'] = projection_map[player]['Name']
                    player_map['ADP'] = projection_map[player]['ADP']
                    if projection_map[player]['type'] == 'Batter':
                        player_map[projection] = int(round(projection_map[player]['points']
                                                           * self.BATTER_MULTIPLIER))
                    elif 'Positions' in player_map and 'SP' in player_map['Positions']:
                        player_map[projection] = int(round(projection_map[player]['points']
                                                           * self.STARTER_MULTIPLIER))
                    else:
                        player_map[projection] = int(round(projection_map[player]['points']
                                                           * self.RELIEF_MULTIPLIER))

            for season in self.stats:
                if player in self.stats[season]:
                    player_map['Age'] = self.stats[season][player]['Age'] + 1
                    if self.stats[season][player]['type'] == 'Batter':
                        player_map[season] = int(round(self.stats[season][player]['points']
                                                       * self.BATTER_MULTIPLIER))
                    elif 'Positions' in player_map and 'SP' in player_map['Positions']:
                        player_map[season] = int(round(self.stats[season][player]['points']
                                                       * self.STARTER_MULTIPLIER))
                    else:
                        player_map[season] = int(round(self.stats[season][player]['points']
                                                       * self.RELIEF_MULTIPLIER))

    def __calculate_position_ranks(self):
        position_ranks = {}
        for player in self.players:
            if 'Positions' not in self.players[player]:
                continue
            position = self.players[player]['Positions'][0]
            if position in ['LF', 'CF', 'RF']:
                position = 'OF'
            if position == 'P':
                position = 'SP'
            if position not in position_ranks:
                position_ranks[position] = {}
            for projection in self.projections:
                if projection not in self.players[player]:
                    continue
                if projection not in position_ranks[position]:
                    position_ranks[position][projection] = {}
                position_ranks[position][projection][player] = self.players[player][projection]
            for season in self.stats:
                if season not in self.players[player]:
                    continue
                if season not in position_ranks[position]:
                    position_ranks[position][season] = {}
                position_ranks[position][season][player] = self.players[player][season]

        for position in position_ranks:
            for item in position_ranks[position]:
                ranked_order = sorted(position_ranks[position][item].items(), reverse=True,
                                      key=operator.itemgetter(1))
                for index in range(len(ranked_order)):
                    self.players[ranked_order[index][0]][item + " Position Rank"] = position + str(index + 1)

    def __write_draft_sheet(self, ds_file):
        with open(ds_file, 'w') as d:
            writer = csv.writer(d)
            columns = ['Player', 'Team', 'Positions', 'Age', 'ZiPS', 'ZiPS Position Rank', 'Fans', 'Fans Position Rank',
                       'Streamer', 'Streamer Position Rank', 'DepthCharts', 'DepthCharts Position Rank', 'Average',
                       'Average Position Rank', '2017', '2017 Position Rank', 'FantasyPros Ranking', 'ADP']
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
        self.__calculate_position_ranks()
        self.__write_draft_sheet(draft_sheet_file)


def generate_metadata(p_files):
    team_name_map = {
        'Angels': 'LAA',
        'Astros': 'HOU',
        'Athletics': 'OAK',
        'Blue Jays': 'TOR',
        'Braves': 'ATL',
        'Brewers': 'MIL',
        'Cardinals': 'STL',
        'Cubs': 'CHC',
        'Diamondbacks': 'ARI',
        'Dodgers': 'LAD',
        'Giants': 'SF',
        'Indians': 'CLE',
        'Mariners': 'SEA',
        'Marlins': 'MIA',
        'Mets': 'NYM',
        'Nationals': 'WSH',
        'Orioles': 'BAL',
        'Padres': 'SD',
        'Phillies': 'PHI',
        'Pirates': 'PIT',
        'Rangers': 'TEX',
        'Rays': 'TB',
        'Red Sox': 'BOS',
        'Reds': 'CIN',
        'Rockies': 'COL',
        'Royals': 'KC',
        'Tigers': 'DET',
        'Twins': 'MIN',
        'White Sox': 'CWS',
        'Yankees': 'NYY',
        '': ''
    }
    pid_map = {}
    pid_set = set([])
    st_map = {}
    for p_file in p_files:
        with open(p_file) as p:
            reader = csv.DictReader(p)
            for line in reader:
                pid_map[line['Name'] + ":" + team_name_map[line['Team']]] = line['playerid']
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
    projection_files = "./Projections/*.csv"
    stat_files = "./Stats/*.csv"
    ranking_file = "./Rankings/FantasyPros.csv"

    player_id_map, player_id_set, st_map = generate_metadata(glob.iglob(projection_files))
    draft_sheet_generator = DraftSheetGenerator(player_id_set, st_map)
    for proj_file in glob.iglob(projection_files):
        draft_sheet_generator.read_projection(proj_file)
    for st_file in glob.iglob(stat_files):
        draft_sheet_generator.read_stat(st_file)
    draft_sheet_generator.read_ranking(ranking_file, player_id_map)
    draft_sheet_generator.generate_draft_sheet("./DraftSheet.csv")
