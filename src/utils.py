from db_psql.reading import get_player_attributes, get_player_stats
from players import GamePlayers

def create_players(squad):
    player_objects = []
    for id in squad:
        res = get_player_attributes(id)
        res_stats = get_player_stats(id)
        temp = GamePlayers(res['id'],res['name'],res['team'],res['overall_rating'],res['nationality'],res['role'], res_stats['powerplay_batted'], res_stats['powerplay_bowled'], res['bowling_style'], res['batting_hand'], res['potential'], res['age'])
        player_objects.append(temp)
    return player_objects

def create_player(id):
    res = get_player_attributes(id)
    res_stats = get_player_stats(id)
    temp = GamePlayers(res['id'],res['name'],res['team'],res['overall_rating'],res['nationality'],res['role'], res_stats['powerplay_batted'], res_stats['powerplay_bowled'], res['bowling_style'], res['batting_hand'], res['potential'], res['age'])
    return temp