from cpts import CPT
from data_cleaner import DataCleaner
import numpy as np
from scipy import stats
import random
import pandas as pd
from db_psql.reading import get_cpt_bowl_wicket_prob, get_cpt_bat_wicket_prob, get_cpt_run,get_cpt_shot, get_cpt_ll, get_cpt_control, get_cpt_ball_outcome, get_team_players, get_player_attributes, get_player_stats, get_bowling_batting_rating

class CreatePlayers():
    def __init__(self, year):
        self.data = DataCleaner().clean_data()
        self.playerToId = {}
        self.idToPlayer = {}
        self.all_stats = [[],[]]
        self.year = year
        self.teamPlayers = {}
        self.build_players()
        self.normalize_bowling_stats()

    def build_global_cpts(self):
        self.global_cpt = CPT(data=self.data)
        self.global_cpt.set_distributions()

    def build_players(self):
        self.players = list(set(self.data['p_bat']).union(set(self.data['p_bowl'])))
        for pId in self.players:
            if len(self.data[(self.data['p_bat']==pId)]) != 0:
                name = self.data[(self.data['p_bat']==pId)]['bat'].mode()[0]
            else:
                name = self.data[(self.data['p_bowl']==pId)]['bowl'].mode()[0]
            #name = self.data[(self.data['p_bat']==pId) | (self.data['p_bowl']==pId) ]['bat'].mode()[0]
            self.playerToId[name] = pId
            temp = Player(pId, self.data, name, self.year)
            temp.cpt.set_distributions()
            self.idToPlayer[pId] = temp  
            self.all_stats[0].append(temp.economy)
            self.all_stats[1].append(temp.wicket_taking_ability)

    def normalize_bowling_stats(self):
        min_econ = min(self.all_stats[0])
        max_econ = max(self.all_stats[0])
        min_wicket_taking = min(self.all_stats[1])
        max_wicket_taking = max(self.all_stats[1])
        l = []
        for player in self.players:
            player_obj = self.idToPlayer[player]
            if player_obj.name in ["Matheesha Pathirana","Yash Thakur"]:
                print(player_obj.cpt.cpt_ball_outcome)
            player_obj.economy = ((player_obj.economy - min_econ) / (max_econ - min_econ))*100
            player_obj.wicket_taking_ability = ((player_obj.wicket_taking_ability - min_wicket_taking) / (max_wicket_taking - min_wicket_taking))*100    
            player_obj.setOveralls()
            t = {'name':player_obj.name, 'age':player_obj.age,'role':player_obj.role,'batting':player_obj.batting_rating, 'bowling':player_obj.bowling_rating, 'Overall':player_obj.overall_rating, 'Attacking ability':player_obj.attacking_ability, 'Control':player_obj.control, 'Economy':player_obj.economy, 'Wicket taking ability':player_obj.wicket_taking_ability}
            l.append(t)
            #print(f'{player_obj.name}: Batting: {player_obj.batting_rating}, Bowling: {player_obj.bowling_rating}, Overall: {player_obj.overall_rating}, Potential:{player_obj.potential}')  
        #pd.DataFrame(l).to_csv('../data/player_ratings.csv')
    
    def build_teams(self):
        for pId in self.idToPlayer:
            team = self.idToPlayer[pId].team
            if team not in self.teamPlayers:
                self.teamPlayers[team] = []
            self.teamPlayers[team].append(self.idToPlayer[pId])
        self.teams = [team for team in self.teamPlayers.keys() if team != 'Out of League']
        self.teamToId = {team:i for i, team in enumerate(self.teams)}
        self.idToTeam = {i:team for team,i in self.teamToId.items()}

    def update_player_ratings(self):
        for player in self.players:
            player_obj = self.idToPlayer[player]
            player_obj.age = self.year - player_obj.dob

            if player_obj.overall_rating < player_obj.potential:
                mean = (player_obj.potential + player_obj.overall_rating)/2
                std_dev = (player_obj.potential - player_obj.overall_rating)/4
                value = np.random.normal(mean, std_dev)
                value = np.clip(value, player_obj.overall_rating, player_obj.potential)
            
                #print(f"{player_obj.name}: {player_obj.overall_rating}, {player_obj.potential}, {value}")

                delta = (value - player_obj.overall_rating)/player_obj.overall_rating + 0.01

                if player_obj.role == 'bowler' or player_obj.role == 'all-rounder':
                    player_obj.cpt.cpt_ball_outcome[player_obj.cpt.otoi['normal']]+=delta
                    player_obj.cpt.cpt_ball_outcome /= np.sum(player_obj.cpt.cpt_ball_outcome)
                    #player_obj.cpt.cpt_ball_outcome[player_obj.cpt.otoi['out']]+=delta
                    for i,phase in enumerate(player_obj.cpt.cpt_ll):
                        if i < 2:
                            phase[player_obj.cpt.lltoi[('outside_off','good_length')]]+=delta
                            phase[player_obj.cpt.lltoi[('stumps','good_length')]]+=delta
                            player_obj.cpt.cpt_ll[i] = phase/np.sum(phase)
                        else:
                            phase[player_obj.cpt.lltoi[('outside_off','yorker')]]+=delta
                            phase[player_obj.cpt.lltoi[('stumps','yorker')]]+=delta
                            phase[player_obj.cpt.lltoi[('down_leg','yorker')]]+=delta
                            player_obj.cpt.cpt_ll[i] = phase/np.sum(phase)
                
                if player_obj.role != 'bowler':
                    for i,phase in enumerate(player_obj.cpt.cpt_control):
                        phase[1]+=2*delta
                        player_obj.cpt.cpt_control[i] = phase / np.sum(phase)

            else: #if player rating == player potential
                decay = abs((32-player_obj.age) * 0.02 + random.uniform(0,0.04))
                #print(player_obj.name, player_obj.overall_rating, player_obj.age, decay)
                if player_obj.role == 'bowler' or player_obj.role == 'all-rounder':
                    player_obj.cpt.cpt_ball_outcome[player_obj.cpt.otoi['normal']]+=delta
                    player_obj.cpt.cpt_ball_outcome /= np.sum(player_obj.cpt.cpt_ball_outcome)
                    #player_obj.cpt.cpt_ball_outcome[player_obj.cpt.otoi['out']]+=delta
                    for i,phase in enumerate(player_obj.cpt.cpt_ll):
                        phase[player_obj.cpt.lltoi[('outside_off','full')]]+=decay
                        phase[player_obj.cpt.lltoi[('stumps','full_toss')]]+=decay
                        phase[player_obj.cpt.lltoi[('down_leg','full_toss')]]+=decay
                        player_obj.cpt.cpt_ll[i] = phase/np.sum(phase)     
                if player_obj.role != 'bowler':
                    for i,phase in enumerate(player_obj.cpt.cpt_control):
                        phase[0]+=2*decay
                        player_obj.cpt.cpt_control[i] = phase / np.sum(phase)
                player_obj.overall_rating -= decay * 30
                player_obj.potential = player_obj.overall_rating
                

                
class Player():
    def __init__(self, playerId, data, name, year):
        self.playerId = playerId
        self.cpt = CPT(data, self.playerId)
        self.data = self.cpt.total_data
        self.bat_data = self.cpt.data
        self.bowl_data = self.cpt.bowl_data
        self.bowling_style = "none"
        self.batting_hand = "right"
        self.bowling_hand = "none"
        self.name = name
        self.overall_rating = 0
        if len(self.bat_data['bat_role']) != 0:
            self.role = str(self.bat_data['bat_role'].mode()[0])
            self.age = year - self.bat_data['bat_dob'].mode()[0]
            self.dob = self.bat_data['bat_dob'].mode()[0]
            self.nationality = str(self.bat_data['bat_nationality'].mode()[0])
            if len(self.bat_data[self.bat_data['year']==2024]) != 0:
                self.team = str(self.bat_data[self.bat_data['year']==2024]['team_bat'].mode()[0])
            else:
                self.team = "Out of League"
        else:
            self.role = self.bowl_data['bowl_role'].mode()[0]
            self.age = year - self.bowl_data['bowl_dob'].mode()[0]
            self.dob = self.bowl_data['bowl_dob'].mode()[0]
            self.nationality = self.bowl_data['bat_nationality'].mode()[0]
            if len(self.bowl_data[self.bowl_data['year']==2024]) != 0:
                self.team = self.bowl_data[self.bowl_data['year']==2024]['team_bowl'].mode()[0]
            else:
                self.team = "Out of League"

        self.setAttributes()
        self.setStats()
        self.setOveralls()
        #self.setPotential()
    
    def setAttributes(self):
        if len(self.data['p_bat'])>0:
            self.batting_hand = self.bat_data['bat_hand'].mode()[0]
        self.bowling_style = 'RF'
        self.bowling_hand = "right"
        if len(self.bowl_data['p_bowl'])>0:
            bowling_hand = {
                'LF':'left',
                'SLA':'left',
                'RF':'right',
                'OB':'right',
                'LB':'right'
            }
            self.bowling_style = self.bowl_data['bowl_style'].mode()[0]
            self.bowling_hand = self.bowl_data['bowl_style'].map(bowling_hand) 
    
    def setStats(self):
        #self._timing()
        self.timing = 0
        self._attacking_intent()
        self._attacking_ability()
        self._control()
        self._wicket_taking_ability()
        self._economy()
        self._phase_batted()
        self._phase_bowled()
        #self._bowling_control()
        #self._death_bowling_ability()
        #self._new_ball_ability()
    
    def setOveralls(self):
        weights = {
            'intent': 0,
            'attacking_ability': 0.22,
            'timing': 0,
            'control': 0.92
        }
        
        self.batting_rating = (weights['intent'] * self.attacking_intent +
                weights['attacking_ability'] * self.attacking_ability +
                weights['timing'] * self.timing +
                weights['control'] * self.control)
        
        self.bowling_rating = (0.65*self.economy + 0.35*self.wicket_taking_ability)

        if self.role == "batsman":
            self.overall_rating = self.batting_rating
        elif self.role == 'bowler':
            self.overall_rating = self.bowling_rating
        elif self.role == 'all-rounder':
            self.overall_rating = 0.73 * max(self.batting_rating, self.bowling_rating) + 0.34*min(self.batting_rating,self.bowling_rating)
        elif self.role == 'wicket-keeper':
            self.overall_rating = self.batting_rating

        age_gap = 32-self.age
        if age_gap<=0:
            self.potential = self.overall_rating
        else:
            self.potential = self.overall_rating + age_gap * random.uniform(0,1.5)

    # Batting statistics
    def _control(self):
        try:
            total_controls = self.bat_data['control'].count()
            if total_controls < 50:
                weight = 0.5
            elif total_controls < 100:
                weight = 0.75
            else:
                weight = 1
            one_in_control = self.bat_data[(self.bat_data['control'] == 1)].shape[0]
            self.control = (one_in_control / total_controls) * 100 * weight
        except: 
            self.control = 0

    def _attacking_ability(self):
        try:
            total_balls = len(self.bat_data[self.bat_data['shot']=='attack']['score'])
            if total_balls < 100:
                weight = 0.5
            elif total_balls < 300:
                weight = 0.75
            else:
                weight = 1
            boundaries = self.bat_data[self.bat_data['score'].isin([4, 6])].shape[0]
            self.attacking_ability = (boundaries / total_balls) * 100 * weight * self.attacking_intent
        except:
            self.attacking_ability = 0

    def _attacking_intent(self):
        '''
        """Calculate the percentage of shots that are attacking."""
        total_shots = self.data['shot'].count()
        attacking_shots = self.data[self.data['shot']=='attack'].shape[0]
        self.attacking_intent = (attacking_shots / total_shots) * 100
        '''
        try:
            attacking_df = self.bat_data[self.bat_data['cur_bat_bf']<10]
            if len(attacking_df) < 50:
                weight = 0.7
            elif len(attacking_df) < 100:
                weight = 0.85
            else:
                weight = 1
            self.attacking_intent = (attacking_df['score'].sum() / len(attacking_df)) * weight
        except:
            self.attacking_intent = 0

    def _timing(self):
        """Calculate the percentage of times runs were scored when the shot was rotating."""
        try:
            rotating_shots = self.bat_data[self.bat_data['shot']=='rotate']
            total_rotating_shots = rotating_shots['shot'].count()
            if total_rotating_shots < 50:
                weight = 0.7
            elif total_rotating_shots < 100:
                weight = 0.85
            else:
                weight = 1
            runs_scored = rotating_shots[rotating_shots['score'] > 0].shape[0]
            self.timing = (runs_scored / total_rotating_shots) * 100 * weight
        except:
            self.timing = 0
    
    def _wicket_taking_ability(self):
        try:
            if len(self.bowl_data) < 50:
                weight = 0.1
            elif len(self.bowl_data) < 200:
                weight = 0.25
            elif len(self.bowl_data) < 400:
                weight = 0.5
            elif len(self.bowl_data) < 600:
                weight = 0.8
            else:
                weight = 1
            wickets = len(self.bowl_data[self.bowl_data['outcome']=='out'])
            self.wicket_taking_ability = (wickets/len(self.bowl_data)) * weight
        except:
            self.wicket_taking_ability = 0

    def _economy(self):
        try:
            if len(self.bowl_data) < 50:
                self.economy = random.uniform(-15, -13)
                return
            elif len(self.bowl_data) < 200:
                weight = 1.6
            elif len(self.bowl_data) < 400:
                weight = 1.4
            else:
                weight = 1
            total_runs = self.bowl_data['score'].sum()
            self.economy = -6 * (total_runs/len(self.bowl_data)) * weight
        except:
            self.economy = 0

    def _phase_batted(self):
        try:
            if len(self.bat_data) < 50:
                weight = 0.7
            elif len(self.bat_data) < 200:
                weight = 0.8
            elif len(self.bat_data) < 400:
                weight = 0.9
            else:
                weight = 1
            powerplay_df = self.bat_data[self.bat_data['match_phase']=='powerplay']
            self.powerplay_batted = (len(powerplay_df)/len(self.bat_data)) * weight
            middle_df = self.bat_data[self.bat_data['match_phase']=='middle']
            self.middle_batted = (len(middle_df)/len(self.bat_data)) * weight
            death_df = self.bat_data[self.bat_data['match_phase']=='death']
            self.death_batted = (len(death_df)/len(self.bat_data)) * weight
        except:
            self.powerplay_batted = 0
            self.middle_batted = 0
            self.death_batted = 0

    def _phase_bowled(self):
        try:
            if len(self.bowl_data) < 50:
                weight = 0.7
            elif len(self.bowl_data) < 200:
                weight = 0.8
            elif len(self.bowl_data) < 400:
                weight = 0.9
            else:
                weight = 1
            powerplay_df = self.bowl_data[self.bowl_data['match_phase']=='powerplay']
            self.powerplay_bowled = (len(powerplay_df)/len(self.bowl_data)) * weight
            middle_df = self.bowl_data[self.bowl_data['match_phase']=='middle']
            self.middle_bowled = (len(middle_df)/len(self.bowl_data)) * weight
            death_df = self.bowl_data[self.bowl_data['match_phase']=='death']
            self.death_bowled = (len(death_df)/len(self.bowl_data)) * weight
        except:
            self.powerplay_bowled = 0
            self.middle_bowled = 0
            self.death_bowled = 0

    def setPotential(self):
        if self.age>32:
            self.potential = self.overall_rating
        else:
            self.potential = 33.3546 + 0.904 * self.overall_rating - 0.7822 * self.age


class GamePlayers():
    def __init__(self, id, name, team, overall_rating, nationality, role, powerplay_batted, powerplay_bowled, bowling_style, batting_hand, potential, age):
        self.playerId = id
        self.name = name
        self.team = team
        self.overall_rating = overall_rating
        self.nationality = nationality
        self.role = role
        self.powerplay_batted = powerplay_batted
        self.powerplay_bowled = powerplay_bowled
        self.bowling_style = bowling_style
        self.batting_hand = batting_hand
        self.potential = potential
        self.age = age
        self.set_ratings()
    
    def set_cpts(self, batsmen):
        if batsmen:
            self.bat_wicket_prob = get_cpt_bat_wicket_prob(self.playerId)
            self.run_dist = np.array(get_cpt_run(self.playerId)).reshape((3,2,6))
            self.shot_dist = np.array(get_cpt_shot(self.playerId)).reshape((15,5,3))
            self.control_dist = np.array(get_cpt_control(self.playerId)).reshape((3,2))
        else:
            self.bowl_wicket_prob = get_cpt_bowl_wicket_prob(self.playerId)
            self.ll_dist = np.array(get_cpt_ll(self.playerId)).reshape((3, 15))
            self.outcome_dist = get_cpt_ball_outcome(self.playerId)
    
    def set_ratings(self):
        self.bowling_rating, self.batting_rating = get_bowling_batting_rating(self.playerId)

'''
data = DataCleaner('../data/t20_bbb.csv')
data = data.clean_data()

temp = Player(961713, data, "Jasprit Bumrah", 2024)
print("INTENT: ",temp.attacking_intent)
print("ATTACKING ABILITY: ",temp.attacking_ability)
print("TIMING: ",temp.timing)
print("CONTROL: ",temp.control)
print()
print("ECONOMY: ",temp.economy)
print("WICKET TAKING ABILITY: ",temp.wicket_taking_ability)

CPTs:
bowling: outcomes | match phase
bowling: line,length | match phase
batting: shot | line and length, bowler type
batting: control | match phase
batting: run | control, shot

good things for each cpt:
outcomes: wicket and normal
line, length:
    - powerplay and middle:
        - length, outside off
        - length, stumps
        - yorker
    - death:
        - yorkers
control:
    - 1
run:
    - 4
    - 6


Batting
Timing - % of 1s in control
Attacking ability - boundary %
Attacking intent - % of shots that are attacking
Control - % of times runs were scored when shot was rotating

Bowling
Death bowling ability: % yorkers at death
New ball ability: % of wickets at powerplay 
Control: % of (off, length) and (off, full) in powerplay and middle
'''
