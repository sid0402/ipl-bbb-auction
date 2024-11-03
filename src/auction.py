#from data_cleaner import DataCleaner
from collections import defaultdict
import random
from db_psql.reading import get_team_players, get_price
import utils
from db_psql.insertion import insert_auctioned_player
import math

class Auction():
    def __init__(self, user, auction_type='mini'):
        self.auction_type = auction_type
        self.players = 0
        self.categories = []
        self.allowed_nationalities = {'indian':3,'overseas':2}
        self.rtms = 0
        self.budget = 120
        self.retainedPlayers = {}
        self.squad_types = {}
        if auction_type=='mini':
            self.allowed_retention = 25
        if auction_type=='mega':
            self.allowed_retention = 6
        self.max_squad = 25
        self.min_squad = 18
        self.max_overseas = 8
        self.teamPlayers = get_team_players()
        self.player_pool = {id:utils.create_player(id) for team in self.teamPlayers.values() for id in team}
        self.budgets = {team:self.budget for team in self.teamPlayers.keys() if team != 'Out of League'}
        self.assign_base_values()
        self.user = user
        self.auction_index=-1
        self.auction_pool = []
        self.price_factor = 2.5

    def retain_players(self, retained_player_ids):
        if self.auction_type == 'mega':
            rp = {}
            price_mapping = {0:18,1:14,2:11,3:18,4:14,5:4}
            for team in self.teamPlayers.keys():
                self.retainedPlayers[team] = []
                if team in ['Out of League']:
                    continue
                self.squad_types[team] = {'nationality':{'overseas':0,'indian':0},'bowling_type':{},'batting_hand':{'right':0,'left':0},'role':{'batsman':0,'bowler':0,'wicket-keeper':0,'all-rounder':0}}
                rp[team] = []
                price_retained = 0
                if team == self.user.team:
                    retained_players = [self.player_pool[id] for id in retained_player_ids]
                    for player in retained_players:
                        if player:
                            self.retainedPlayers[self.user.team].append(player)
                            val = price_mapping[len(self.retainedPlayers[self.user.team])-1]
                            self.update_squad_type(player, self.user.team)
                            insert_auctioned_player(player.playerId, val, team)
                            price_retained+=val
                else:
                    players = {self.player_pool[id]:self.assign_value(self.player_pool[id], team) for id in self.teamPlayers[team]}
                    players = dict(sorted(players.items(), key=lambda p: p[1], reverse=True))
                    print({player.name:val for player, val in players.items()})
                    for player in players:
                        if len(self.retainedPlayers[team])==self.allowed_retention:
                            break
                        if players[player] < 8:
                            break
                        self.retainedPlayers[team].append(player)
                        rp[team].append(player.name)
                        #self.update_squad_type(player, team)
                        val = price_mapping[len(self.retainedPlayers[team])-1]
                        insert_auctioned_player(player.playerId, val, team)
                        price_retained+=val
                self.budgets[team]-=price_retained
        else:
            rp = {}
            for team in self.teamPlayers.keys():
                self.squad_types[team] = {'nationality':{'overseas':0,'indian':0},'bowling_type':{},'batting_hand':{'right':0,'left':0},'role':{'batsman':0,'bowler':0,'wicket-keeper':0,'all-rounder':0}}
                if team in ['Out of League']:
                    continue
                self.retainedPlayers[team] = []
                rp[team] = []
                price_retained = 0
                if team == self.user.team:
                    retained_players = [self.player_pool[id] for id in retained_player_ids]
                    for player in retained_players:
                        if player:
                            self.retainedPlayers[self.user.team].append(player)
                            self.update_squad_type(player, self.user.team)
                            #insert_auctioned_player(player.playerId, val, team)
                            price_retained+=get_price(player.playerId)
                else:
                    players = {self.player_pool[id]:self.assign_value(self.player_pool[id], team) for id in self.teamPlayers[team]}
                    players = dict(sorted(players.items(), key=lambda p: p[1], reverse=True))
                    #print({player.name:val for player, val in players.items()})
                    for player in players:
                        if len(self.retainedPlayers[team])==self.allowed_retention:
                            break
                        if players[player] < 7:
                            break
                        self.retainedPlayers[team].append(player)
                        rp[team].append(player.name)
                        price_retained+=get_price(player.playerId)
                    self.budgets[team]-=price_retained
        print(rp)
        retained_players = set([player for tp in list(self.retainedPlayers.values()) for player in tp])
        players = [player for player in self.player_pool.values() if player not in retained_players and player.team != 'Out of League']
        self.auction_pool = sorted(players, key=lambda p:p.overall_rating, reverse=True) 

    def update_squad_type(self, player, team):
        self.squad_types[team]['nationality'][player.nationality]+=1
        if player.bowling_style not in self.squad_types[team]['bowling_type']:
            self.squad_types[team]['bowling_type'][player.bowling_style] = 0
        if player.bowling_style == 'bowler' or player.bowling_style == 'all-rounder':
            self.squad_types[team]['bowling_type'][player.bowling_style]+=1
        if player.bowling_style != 'bowler':
            self.squad_types[team]['batting_hand'][player.batting_hand]+=1
        self.squad_types[team]['role'][player.role]+=1

    def assign_base_values(self):
        self.base_values = {
            'nationality':{'overseas':2, 'indian':3},
            'bowling_type':defaultdict(lambda: 4.0),
            'batting_hand':{'right':2, 'left':3},
            'role':{'batsman':6,'bowler':3,'all-rounder':2,'wicket-keeper':6}
        }

    def get_next_player(self):
        #self.auction_index = len(self.auction_pool)-1
        self.auction_index +=1
        if self.auction_index == len(self.auction_pool):
            return None
        return self.auction_pool[self.auction_index]

    def make_auction_sets(self, players):
        sets = []
        marquee = players[:10]
        #sets.append(marquee)
        players = players[10:]
        for role in ['bowler','batsman','wicket-keeper','all-rounder']:
            set = [player for player in players if player.role == role]
            set = [set[i:i + 10] for i in range(0, len(set), 10)]
            sets.append(set)
        def regroup_sublists(list_of_lists):
            min_length = min(len(sublist) for sublist in list_of_lists)
            regrouped = [list(group) for group in zip(*(sublist[:min_length] for sublist in list_of_lists))]
            return regrouped
        return [marquee] + regroup_sublists(sets)

    def adjust_value(self, base_value, count):
        return base_value / (1 + count)
    
    def simulate_player(self, player, user_bid):
        player_value = {}
        purchased_val, purchased_team = 0,''
        for team in self.teamPlayers.keys():
            if team == 'Out of League':
                continue
            if team == self.user.team:
                player_value[team] = user_bid/self.price_factor
            else:
                player_value[team] = self.assign_value(player, team)
        player_value = dict(sorted(player_value.items(), key=lambda p:p[1], reverse=True))
        if list(player_value.values())[0] <= 0:
            print(f"{player.name}: UNSOLD")
            print()
            self.retainedPlayers['Out of League'].append(player)
            insert_auctioned_player(player.playerId,max(player_value.values()) * self.price_factor, 'Out of League')
            return "Out of League", 0
        print(player_value)
        for team in player_value:
            if self.validate_player(player, team, player_value[team]*self.price_factor):
                purchased_team = team
                break
        if purchased_team == '':
            print(f"{player.name}: UNSOLD")
            print()
            purchased_team = 'Out of League'
            self.retainedPlayers['Out of League'].append(player)
            insert_auctioned_player(player.playerId,max(player_value.values()) * self.price_factor, 'Out of League')
            return "Out of League", 0
        self.retainedPlayers[purchased_team].append(player)
        self.budgets[purchased_team]-=player_value[purchased_team] * self.price_factor
        self.update_squad_type(player, purchased_team)
        insert_auctioned_player(player.playerId,max(player_value.values()) * self.price_factor, purchased_team)
        print(f"{player.name}: {purchased_team}, {max(player_value.values()) * self.price_factor}")
        print()
        return purchased_team, max(player_value.values()) * self.price_factor

    def get_player_by_id(self, player_id):
        return self.player_pool.get(player_id, None)

    def assign_value(self, player, team):
        #player = utils.create_player(player)
        nationality_value = self.adjust_value(self.base_values['nationality'][player.nationality], self.squad_types[team]['nationality'].get(player.nationality, 0))
        bowling_value = self.adjust_value(self.base_values['bowling_type'][player.bowling_style], self.squad_types[team]['bowling_type'].get(player.bowling_style, 0))
        batting_value = self.adjust_value(self.base_values['batting_hand'][player.batting_hand], self.squad_types[team]['batting_hand'].get(player.batting_hand, 0))
        role_value = self.adjust_value(self.base_values['role'][player.role], self.squad_types[team]['role'].get(player.role, 0))

        combined_value = nationality_value + role_value        
        if player.role == 'batsman' or player.role=='wicket-keeper':
            combined_value += batting_value
        elif player.role=='all-rounder':
            combined_value += batting_value + bowling_value
        else:
            combined_value += bowling_value

        budget_factor = self.budgets[team]/self.budget

        age_bias = -0.1 * player.age if player.age > 38 else 0

        val = float(combined_value) * float(budget_factor) * ((player.overall_rating + player.potential)/200)**2 + age_bias + random.uniform(0, 1)
        if math.isnan(val):
            return -1

        return val
    
    def validate_player(self, player, team, value):
        if self.budgets[team] < value:
            return False
        if len(self.retainedPlayers[team]) == self.max_squad:
            return False
        if self.squad_types[team]['nationality']['overseas'] == self.max_overseas and player.nationality == 'overseas':
            return False
        return True    
