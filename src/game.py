import numpy as np
from cpts import CPT
#from data_cleaner import DataCleaner
import random
import time
from db_psql.reading import get_cpt_bowl_wicket_prob, get_cpt_bat_wicket_prob, get_cpt_run,get_cpt_shot, get_cpt_ll, get_cpt_control, get_cpt_ball_outcome, get_team_players, get_player_attributes, get_player_stats
from cpt_mappings import lltoi, itoll, sttoi, itost, mptoi, itomp, bttoi, itobt, rtoi, itor, otoi, itoo
from players import GamePlayers
import utils

class MatchState():
    def __init__(self, team1, team2, user_team = None):
        self.team1 = team1
        self.team2 = team2
        teamPlayers = get_team_players()
        self.squad1 = utils.create_players(teamPlayers[team1])
        self.squad2 = utils.create_players(teamPlayers[team2])
        self.waiting_for_batsman = False
        self.waiting_for_bowler = False
        self.current_over = 0
        self.current_ball = 0
        self.innings_completed = False
        self.user_team = user_team
        self.waiting_for_openers = False
        self.waiting_for_opening_bowler = False
        self.innings = 1
    
    def __str__(self):
        return f"Match Number {self.match_number}: {self.team1} vs {self.team2}"

    def playingEleven(self, players):
        playing_eleven = []
        players = sorted(players, key = lambda p:p.overall_rating, reverse = True)
        playing_eleven_counts = {'overseas':0,'roles':{}}
        for player in players:
            if len(playing_eleven)==11:
                break
            if player.role == 'overseas' and playing_eleven_counts['overseas'] == 4:
                continue
            if player.role not in playing_eleven_counts['roles']:
                playing_eleven_counts['roles'][player.role] = 0
            if playing_eleven_counts['roles'][player.role] == 4:
                continue
            playing_eleven_counts['roles'][player.role]+=1
            playing_eleven.append(player)
        return playing_eleven

    def initializeInning(self):
        self.runs = 0
        self.wickets = 0
        self.playersTeam1 = sorted(self.playersTeam1, key=lambda p:p.powerplay_batted, reverse=True)
        print([player.name for player in self.playersTeam1])
        self.playersTeam2 = sorted(self.playersTeam2, key=lambda p:p.powerplay_bowled, reverse=True)
        self.match_phase = 'powerplay'

        if self.is_user_batting():
            self.waiting_for_openers = True
        else:
            self.onstrike = self.playersTeam1[0]
            self.nonstrike = self.playersTeam1[1]
            self.onstrike.set_cpts(True)
            self.nonstrike.set_cpts(True)

        if self.is_user_bowling():
            self.waiting_for_opening_bowler = True
        else:
            self.bowler = self.playersTeam2[0]
            self.bowler.set_cpts(False)

        self.scorecard = {'batsmen':{}, 'bowlers':{}}

        ## NEED TO IMPLEMENT COIN TOSS

    def playGame(self):
        self.scorecards = []
        self.playersTeam1 = self.playingEleven(self.squad1)
        self.playersTeam2 = self.playingEleven(self.squad2)

        # First innings
        self.initializeInning()
        self.simulateInning()
        if ((self.is_user_batting() or self.is_user_bowling()) and not self.innings_completed):
            return  # Pause for user input if needed

        self.displayScorecard()
        self.firstInningRuns = self.runs

        # Switch teams for second innings
        self.switch_innings()

        # Second innings
        self.initializeInning()
        self.simulateInning()
        if ((self.is_user_batting() or self.is_user_bowling()) and not self.innings_completed):
            return  # Pause for user input if needed

        self.displayScorecard()
        self.find_winner()

    def find_winner(self):
        if self.runs > self.firstInningRuns:
            self.win = self.team1
            self.loss = self.team2
        else:
            self.win = self.team2
            self.loss = self.team1

    '''
    def playGame(self):
        self.scorecards = []

        self.playersTeam1 = self.playingEleven(self.squad1)
        self.playersTeam2 = self.playingEleven(self.squad2)

        #play the first innings
        self.initializeInning()
        self.simulateInning()
        self.displayScorecard()
        self.scorecards.append(self.scorecard)
        print()
        posts = []
        for type_bb in self.scorecard:
            posts+=list(self.scorecard[type_bb].values())
        firstInningRuns = self.runs
        
        self.team1, self.team2 = self.team2, self.team1
        self.playersTeam1, self.playersTeam2 = self.playersTeam2, self.playersTeam1

        self.initializeInning()

        #play the second innings
        self.simulateInning()
        posts = []
        for type_bb in self.scorecard:
            posts+=list(self.scorecard[type_bb].values())
        self.displayScorecard()
        self.scorecards.append(self.scorecard)
        print()

        if self.runs > firstInningRuns:
            self.win = self.team1
            self.loss = self.team2
        else:
            self.win = self.team2
            self.loss = self.team1
    '''
    '''
    def simulateInning(self, overs=20):
        self.match_phase = 'powerplay'
        for over in range(overs):
            for ball_number in range(6):
                ball = self.simulateBall(self.onstrike, self.bowler)
                if ball['run'][0] % 2 == 1:
                    self.rotate()
                self.runs+=ball['run'][0]
                if ball['out']:
                    self.wickets+=1
                    self.updateScorecard(ball['run'][0], ball['out'])
                    if self.wickets==len(self.playersTeam1)-1:
                        break
                    if self.is_user_match:
                        self.wait_for_user_batsman_selection()
                    else:
                        self.send_next_batsmen()
                #    print()
                    continue
                if ball['wide'] or ball['nb']:
                    ball_number-=1
                    continue
                self.updateScorecard(ball['run'][0], ball['out'])
            if self.wickets==len(self.playersTeam1)-1:
                break
            self.rotate()
            self.change_bowler(over)
            if over>5:
                self.match_phase = "middle"
            if over>15:
                self.match_phase = "death"

    ''' 
    
    def switch_innings(self):
        self.innings += 1
        self.team1, self.team2 = self.team2, self.team1
        self.playersTeam1, self.playersTeam2 = self.playersTeam2, self.playersTeam1
        self.firstInningRuns = self.runs
        self.runs = 0
        self.wickets = 0
        self.current_over = 0
        self.current_ball = 0
        self.innings_completed = False

    def simulateInning(self, overs=20):
        if self.innings_completed:
            return

        if self.waiting_for_openers or self.waiting_for_opening_bowler:
            return

        while self.current_over < overs:
            while self.current_ball < 6:
                if (self.waiting_for_batsman and self.is_user_batting()) or (self.waiting_for_bowler and self.is_user_bowling()):
                    return

                ball = self.simulateBall(self.onstrike, self.bowler)
                self.updateScorecard(ball['run'][0], ball['out'], ball['wide'])
                if ball['run'][0] % 2 == 1:
                    self.rotate()
                self.runs+=ball['run'][0]
                
                if ball['out']:
                    self.wickets+=1
                    self.current_ball+=1
                    if self.wickets==len(self.playersTeam1)-1:
                        self.innings_completed = True
                        self.scorecards.append(self.scorecard)
                        return
                    if self.is_user_batting():
                        self.waiting_for_batsman = True
                        return
                    else:
                        self.send_next_batsmen()
                    continue

                if ball['wide'] or ball['nb']:
                    #self.current_ball-=1
                    #continue
                    pass

                self.current_ball += 1

                if self.innings == 2:
                    if self.runs > self.firstInningRuns:
                        break

            if self.wickets==len(self.playersTeam1)-1:
                self.scorecards.append(self.scorecard)
                self.innings_completed = True
                return

            if self.innings == 2:
                if self.runs > self.firstInningRuns:
                    break

            self.rotate()
            self.current_over += 1
            self.current_ball = 0
            #self.displayScorecard()

            if self.current_over>5:
                self.match_phase = "middle"
            if self.current_over>15:
                self.match_phase = "death"

            if self.is_user_bowling():
                self.waiting_for_bowler = True
                return
            else:
                self.change_bowler(self.current_over)

        self.innings_completed = True
        self.scorecards.append(self.scorecard)
        if self.innings==2:
            self.find_winner()
    
    def is_user_batting(self):
        #return self.user_team == self.team1
        return False

    def is_user_bowling(self):
        #return self.user_team == self.team2
        return False
        
    def rotate(self):
        self.onstrike, self.nonstrike = self.nonstrike, self.onstrike
    
    def send_next_batsmen(self):
        if self.match_phase == 'powerplay':
            self.onstrike = self.playersTeam1[self.wickets+1]
            self.onstrike.set_cpts(True)

        else:
            self.playersTeam1 = sorted(self.playersTeam1, key=lambda p:p.batting_rating, reverse=True)
            for player in self.playersTeam1:
                if player.name not in self.scorecard['batsmen']:
                    break
            self.onstrike = player
            self.onstrike.set_cpts(True)
            
    def change_bowler(self, over):
        prev = self.bowler
        if self.match_phase == 'powerplay':
            for bowler in self.playersTeam2:
                if bowler != prev:
                    if (bowler.name not in self.scorecard['bowlers'] )or (bowler.name in self.scorecard['bowlers'] and self.scorecard['bowlers'][bowler.name]['balls'] <= 18):
                        break
        else:
            self.playersTeam2 = sorted(self.playersTeam2, key=lambda p:p.bowling_rating, reverse=True)
            for bowler in self.playersTeam2:
                if bowler != prev:
                    if (bowler.name not in self.scorecard['bowlers'] ) or (bowler.name in self.scorecard['bowlers'] and self.scorecard['bowlers'][bowler.name]['balls'] <= 18):
                        break
        self.bowler = bowler
        self.bowler.set_cpts(False)
            
    def updateScorecard(self, run, wicket, wide):
        if self.onstrike.name not in self.scorecard['batsmen']:
            self.scorecard['batsmen'][self.onstrike.name] = {'_id':self.onstrike.playerId,'name':self.onstrike.name,'type':'batsmen','runs':0, 'balls':0,'out':0}
        self.scorecard['batsmen'][self.onstrike.name]['runs']+=run
        self.scorecard['batsmen'][self.onstrike.name]['balls']+=1
        if wicket:
            self.scorecard['batsmen'][self.onstrike.name]['out']=1

        if self.bowler.name not in self.scorecard['bowlers']:
            self.scorecard['bowlers'][self.bowler.name] = {'_id':self.bowler.playerId,'name':self.bowler.name,'type':'bowler','runs':0, 'balls':0, 'out':0}
        self.scorecard['bowlers'][self.bowler.name]['runs']+=run
        self.scorecard['bowlers'][self.bowler.name]['balls']+=1
        self.scorecard['bowlers'][self.bowler.name]['out']+=wicket
    
    def displayScorecard(self):
        print(f"BATTING TEAM: {self.runs}/{self.wickets}")
        for bat in self.scorecard['batsmen']:
            print(f"{bat}: {self.scorecard['batsmen'][bat]['runs']} ({self.scorecard['batsmen'][bat]['balls']})")
        print()
        print("BOWLING TEAM")
        for bowl in self.scorecard['bowlers']:
            print(f"{bowl}: {self.scorecard['bowlers'][bowl]['out']}/{self.scorecard['bowlers'][bowl]['runs']} ({self.scorecard['bowlers'][bowl]['balls']})")
    
    def simulateBall(self, batsmen, bowler):
        ball = {
            'run':[0,0],
            'wicket':False,
            'wide':False,
            'nb':False,
            'line_length':None,
            'shot_played':None,
            'control':None,
            'out':False
        }

        #outcome_dist = bowler.cpt.cpt_ball_outcome
        outcome_pred = np.random.multinomial(1,bowler.outcome_dist)
        outcome_pred_i = [i for i,p in enumerate(outcome_pred) if outcome_pred[i]][0]
        if itoo[outcome_pred_i] == 'wide':
            #ball['run'][0]=1
            ball['wide']=True
            #return ball
        if itoo[outcome_pred_i] == 'nb':
            ball['nb']=True
            ball['run'][0]+=1
            
        wicket_prob = (bowler.bowl_wicket_prob * batsmen.bat_wicket_prob) ** 0.5
        cpt_wicket = [wicket_prob, 1-wicket_prob]
        wicket_pred = np.random.multinomial(1,cpt_wicket)
        wicket_i = [i for i,p in enumerate(wicket_pred) if wicket_pred[i]][0]
        if wicket_i == 0:
            ball['out'] = True
            return ball
        
        ll_dist = bowler.ll_dist[mptoi[self.match_phase]]        
        ll = np.random.multinomial(1,ll_dist)
        ll_i = [i for i,p in enumerate(ll) if ll[i]][0]
        ball['line_length']=(itoll[ll_i], ll_dist[ll_i])

        shot_dist = batsmen.shot_dist[ll_i][bttoi[bowler.bowling_style]]
        shot_pred = np.random.multinomial(1,shot_dist)
        shot_i = [i for i,p in enumerate(shot_pred) if shot_pred[i]][0]
        ball['shot_played'] = (itost[shot_i], shot_dist[shot_i])

        control_dist = batsmen.control_dist[mptoi[self.match_phase]]
        control_pred = np.random.multinomial(1,control_dist)
        control_pred_i = [i for i,p in enumerate(control_pred) if control_pred[i]][0]
        ball['control'] = (control_pred_i, control_dist[control_pred_i])

        run_dist = batsmen.run_dist[shot_i][control_pred_i]
        run_pred = np.random.multinomial(1,run_dist)
        run_pred_i = [i for i,p in enumerate(run_pred) if run_pred[i]][0]
        
        ball['run'][0]+=itor[run_pred_i]
        ball['run'][1]=run_dist[run_pred_i] 

        #print(f"{self.current_over}.{self.current_ball}: {bowler.name} to {batsmen.name} - {ball['run'][0]} ({run_dist[run_pred_i]})")

        return ball

    def get_available_batsmen(self):
        return [player for player in self.playersTeam1 if player.name not in self.scorecard['batsmen']]

    def get_available_bowlers(self):
        return [player for player in self.playersTeam2 if player.name not in self.scorecard['bowlers'] or self.scorecard['bowlers'][player.name]['balls'] < 24]

    def user_select_batsman(self, batsman_name):
        selected_batsman = next(player for player in self.playersTeam1 if player.name == batsman_name)
        self.onstrike = selected_batsman
        self.waiting_for_batsman = False

    def user_select_bowler(self, bowler_name):
        selected_bowler = next(player for player in self.playersTeam2 if player.name == bowler_name)
        self.bowler = selected_bowler
        self.waiting_for_bowler = False

    def user_select_openers(self, striker, non_striker):
        self.onstrike = next(player for player in self.playersTeam1 if player.name == striker)
        self.nonstrike = next(player for player in self.playersTeam1 if player.name == non_striker)
        self.waiting_for_openers = False

    def user_select_opening_bowler(self, bowler):
        self.bowler = next(player for player in self.playersTeam2 if player.name == bowler)
        self.waiting_for_opening_bowler = False


'''
data = DataCleaner('../data/t20_bbb.csv')
data = data.clean_data()

team1_ids = [219889, 253802, 931581, 446507, 230559, 276298, 234675, 662973, 49758, 31107, 30732, 550215]
team1 = []
for player in team1_ids:
    temp = CPT(data, player)
    temp.set_distributions()
    team1.append(temp)

team2_ids = [51880, 326637, 290630, 44936, 28081, 270484, 550215, 1125976, 1064812, 489889, 277912]
team2 = []
for player in team2_ids:
    temp = CPT(data, player)
    temp.set_distributions()
    team2.append(temp)

game = MatchState(team1, team2)
game.initializeInning()
game.playGame()
'''

#temp = CPT(-1)
#temp.set_distributions()
#print(temp.cpt_shot)