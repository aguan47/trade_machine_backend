from flask import Flask
from flask import request

app = Flask(__name__)

import pandas as pd
import time
import csv
import numpy as np
from fuzzywuzzy import process

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


#tm_list1
#tm_list2 

from nba_api.stats.endpoints import playergamelogs

# Get active players
def act_players():
    global act_players_info
    data = playergamelogs.PlayerGameLogs(season_nullable = '2022-23')
    stats_df = data.get_data_frames()[0]
    stats_df2 = stats_df[['PLAYER_ID','PLAYER_NAME']]
    act_players_info = stats_df2.drop_duplicates(keep = 'first')
    return act_players_info

# Creates list to match and searches for closest value if there are minor name errors
def matching(lst):
    global var
    dito = []
    for x in range(0, len(lst)):
        str1 = lst[x]
        str2 = act_players_info.PLAYER_NAME

        highest = process.extractOne(str1, str2)
        a = highest[0]
        dito.append(a)
    return dito

# Get the league player stats
def leagueplayer_stats(p_id):
    global stats_df2
    data = playergamelogs.PlayerGameLogs(season_nullable = '2022-23', player_id_nullable = p_id, last_n_games_nullable = 15)
    stats_df = data.get_data_frames()[0]
    stats_df2 = stats_df[['PLAYER_ID','PLAYER_NAME','GAME_ID'
             ,'FGM','FGA','FG_PCT','FG3M','FG3A','FG3_PCT','FTM','FTA','FT_PCT',
            'REB','AST','TOV','STL','BLK','PTS']]
    return stats_df2

# Get stats of the players?
def get_player_stats(plyrs):
    plyr_det = []
    for x in plyrs:
        plyr_df = leagueplayer_stats(x)
        time.sleep(0.85)
        plyr_det.append(plyr_df)
    
    plyr_stats = pd.concat(plyr_det)
    return plyr_stats




@app.route("/")
def hello_world():
    data = request.json
    to_be_traded = data['toBeTraded']
    to_get = data['toGet']

    # Get active players
    act_players()

    # Match the names of the players if there are errors
    list1 = matching(to_be_traded)
    list2 = matching(to_get)

    # Get the information of the players
    player_id1 = act_players_info.query('PLAYER_NAME in @list1')
    player_id2 = act_players_info.query('PLAYER_NAME in @list2')


    team1_plyr = player_id1.PLAYER_ID
    team2_plyr = player_id2.PLAYER_ID

    plyr_ros1 = get_player_stats(team1_plyr)
    plyr_ros2 = get_player_stats(team2_plyr)

    frame1 = [plyr_ros1]
    frame2 = [plyr_ros2]

    player_stats1 = pd.concat(frame1)
    player_stats2 = pd.concat(frame2)

    player_stats1['NBA_FANTASY_PTS'] = (player_stats1['FGM']*1) + (player_stats1['FGA']*-0.5) + ((player_stats1['FTM'] - player_stats1['FTA'])*0.5) + (player_stats1['FG3M']*1) + \
            (player_stats1['PTS']*1) + (player_stats1['REB']*1.2) + (player_stats1['AST']*1.5) + (player_stats1['STL']*3) + (player_stats1['BLK']*3) + (player_stats1['TOV']*-1)

    player_stats2['NBA_FANTASY_PTS'] = (player_stats2['FGM']*1) + (player_stats2['FGA']*-0.5) + ((player_stats2['FTM'] - player_stats2['FTA'])*0.5) + (player_stats2['FG3M']*1) + \
            (player_stats2['PTS']*1) + (player_stats2['REB']*1.2) + (player_stats2['AST']*1.5) + (player_stats2['STL']*2) + (player_stats2['BLK']*2) + (player_stats2['TOV']*-1)


    # Statistical tests
    from scipy import stats

    trade1 = player_stats1.NBA_FANTASY_PTS
    trade2 = player_stats2.NBA_FANTASY_PTS

    t_value, p_value = stats.ttest_ind(trade1, trade2)
    alpha = 0.05

    if p_value <= alpha:
        return {
            'isBalanced': False,
            'message': 'TRADE IS NOT BALANCED with a p-value of {}, alpha of {}'.format(p_value, alpha)
        }

    return {
        'isBalanced': True,
        'message': 'TRADE IS BALANCED with a p-value of {}, alpha of {}'.format(p_value, alpha)
    }