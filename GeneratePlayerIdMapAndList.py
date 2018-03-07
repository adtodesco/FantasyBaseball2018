import csv
import json
import glob

if __name__ == '__main__':
    player_id_map = {}
    player_id_list = []
    for projection in glob.iglob("./FangraphProjections/*.csv"):
        with open(projection) as p:
            reader = csv.DictReader(p)
            for line in reader:
                player_id_map[line['Name']] = line['playerid']
                player_id_list.append(line['playerid'])
    with open('./PlayerId/PlayerIdMap.json', 'w') as m:
        m.write(json.dumps(player_id_map))
    with open('./PlayerId/PlayerIdList.json', 'w') as l:
        l.write(json.dumps(player_id_list))
