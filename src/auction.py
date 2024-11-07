#from data_cleaner import DataCleaner
from collections import defaultdict
import random
from db_psql.reading import get_team_players, get_price
import utils
from db_psql.insertion import insert_auctioned_player
import math
import random

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
        self.player_pool = {id:utils.create_player(id) for team in self.teamPlayers.values() for id in set(team)}
        self.budgets = {team:self.budget for team in self.teamPlayers.keys() if team != 'Out of League'}
        self.assign_base_values()
        self.user = user
        self.auction_index=-1
        self.auction_pool = []
        self.price_factor = 1.75

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
        print(self.auction_pool)
        self.make_auction_sets()

    def manual_retain_players(self):
        # Define player IDs and their respective retention prices
        manual_retained_players = {
            1060380: 18, 234675: 18, 714451: 12, 1194795: 13, 28081: 4,       # Chennai Super Kings
            554691: 16.5, 559235: 13.25, 595978: 10, 1277545: 4,              # Delhi Capitals
            1070173: 16.5, 793463: 18, 1151288: 8.5, 423838: 4, 719719: 4,    # Gujarat Titans
            230558: 12, 723105: 13, 1312645: 4, 719719: 12, 276298: 12, 1079470: 4,  # Kolkata Knight Riders
            604302: 21, 1175441: 11, 1292563: 11, 1132005: 4, 1151270: 4,     # Lucknow Super Giants
            625371: 16.35, 446507: 16.35, 34102: 16.3, 625383: 18, 1170265: 8, # Mumbai Indians
            377534: 5.5, 1161024: 4,                                          # Punjab Kings
            425943: 18, 1151278: 18, 1079434: 14, 1175488: 14, 670025: 11,    # Rajasthan Royals
            438362: 4, 
            253802: 21, 823703: 11, 1159720: 5,                               # Royal Challengers Bengaluru
            489889: 18, 530011: 14, 436757: 23, 1175496: 6, 1070183: 14       # Sunrisers Hyderabad
        }
        
        rp = {}
        for team in self.teamPlayers.keys():
            self.retainedPlayers[team] = []
            if team in ['Out of League']:
                continue
            
            # Initializing the team structure
            self.squad_types[team] = {
                'nationality': {'overseas': 0, 'indian': 0},
                'bowling_type': {},
                'batting_hand': {'right': 0, 'left': 0},
                'role': {'batsman': 0, 'bowler': 0, 'wicket-keeper': 0, 'all-rounder': 0}
            }
            rp[team] = []
            price_retained = 0
            
            # Retain the players for this team with specified retention prices
            retained_players = [self.player_pool[id] for id in manual_retained_players.keys() if id in self.teamPlayers[team]]
            for player in retained_players:
                if len(self.retainedPlayers[team]) >= self.allowed_retention:
                    break
                self.retainedPlayers[team].append(player)
                rp[team].append(player.name)
                self.update_squad_type(player, team)
                
                # Get the retention price from the dictionary
                val = manual_retained_players[player.playerId]
                insert_auctioned_player(player.playerId, val, team)
                price_retained += val
            
            # Deduct the retained price from the team's budget
            self.budgets[team] -= price_retained
        
        print("Manual retention complete:", rp)

        # Exclude retained players from the auction pool
        retained_players_set = set(player for tp in self.retainedPlayers.values() for player in tp)
        #self.auction_pool = sorted(
        #    [player for player in self.player_pool.values() if player not in retained_players_set and player.team != 'Out of League'],
        #    key=lambda p: p.overall_rating,
        #    reverse=True
        #)
        retained_players = set([player for tp in list(self.retainedPlayers.values()) for player in tp])
        players = [player for player in self.player_pool.values() if player not in retained_players and player.team != 'Out of League']
        self.auction_pool = sorted(players, key=lambda p:p.overall_rating, reverse=True) 
        print(self.auction_pool)
        self.make_auction_sets()

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
            'nationality':{'overseas':2, 'indian':4},
            'bowling_type':defaultdict(lambda: 4.0),
            'batting_hand':{'right':2, 'left':3},
            'role':{'batsman':6,'bowler':2,'all-rounder':2,'wicket-keeper':5}
        }

    def get_next_player(self):
        if not hasattr(self, 'set_index'):
            self.set_index = 0
        if not hasattr(self, 'auction_index'):
            self.auction_index = 0

        if self.set_index >= len(self.auction_sets):
            return None

        current_set = list(self.auction_sets[self.set_index].items())

        if self.auction_index < len(current_set):
            player_id, player_obj = current_set[self.auction_index]
            self.auction_index += 1  # Move to the next player in the current set
            return player_obj

        self.set_index += 1
        self.auction_index = 0  # Reset auction index for the new set

        return self.get_next_player()

    def make_auction_sets(self):
        # Convert the player pool dictionary to a sorted list of (id, player) tuples
        #sorted_players = sorted(self.auction_pool.items(), key=lambda item: item[1].overall_rating, reverse=True)
        sorted_players = self.auction_pool

        print(sorted_players)

        # Create the marquee set of the 10 best players with id: player format
        marquee_set = sorted_players[:10]
        remaining_players = sorted_players[10:]
        remaining_players = list({p.playerId:p for p in remaining_players}.items())
        
        # Group remaining players by role
        roles = ['batsman', 'bowler', 'wicket-keeper', 'all-rounder']
        role_groups = {role: [] for role in roles}
        for player_id, player in remaining_players:
            if player.role in role_groups:
                role_groups[player.role].append((player.playerId, player))
        
        # Divide each role group into chunks of 10 with id: player format
        for role in role_groups:
            # Shuffle each role group to introduce randomness before chunking
            random.shuffle(role_groups[role])
            role_groups[role] = [
                dict(role_groups[role][i:i + 10]) for i in range(0, len(role_groups[role]), 10)
            ]
        
        # Shuffle the marquee set to add randomness
        marquee_list = list({p.playerId:p for p in marquee_set}.items())
        random.shuffle(marquee_list)
        marquee_set = dict(marquee_list)
        
        # Arrange players in the desired alternating pattern
        auction_sets = [marquee_set]
        while any(role_groups[role] for role in roles):  # Continue until all role groups are empty
            for role in roles:
                if role_groups[role]:  # Check if there are remaining sets in this role
                    auction_sets.append(role_groups[role].pop(0))
        
        self.auction_sets = auction_sets


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

        team_budget = self.budgets[team]
        if team_budget > 80:
            budget_factor = 1.5
        elif team_budget > 40:
            budget_factor = 1.25
        elif team_budget > 20:
            budget_factor = 1.15
        else:
            budget_factor = 1.05

        age_bias = -0.1 * player.age if player.age > 38 else 0

        val = float(combined_value) * float(budget_factor) * ((player.overall_rating + player.potential)/200)**3 + age_bias + random.uniform(0, 1)
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
