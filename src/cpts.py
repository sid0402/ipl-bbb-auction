import pandas as pd
import numpy as np
from data_cleaner import DataCleaner

#data = DataCleaner('../data/t20_bbb.csv','IPL')
#data = data.clean_data()

class CPTParent():
    '''
    shot_types = list(set(data['shot']))
    lengths = list(set(data['length']))
    lines = list(set(data['line']))
    match_phases = list(set(data['match_phase']))
    bowler_types = list(set(data['bowl_style']))
    run_types = list(set(data['score']))
    outcomes = list(set(data['outcome2']))
    #outcomes = list(set(data['outcome']))
    controls = [0,1]

    line_lengths = []
    for line in lines:
        for length in lengths:
            line_lengths.append((line, length))

    lltoi = {k:i for i,k in enumerate(line_lengths)}
    itoll = {i:k for k,i in lltoi.items()}

    sttoi = {k:i for i,k in enumerate(shot_types)}
    itost = {i:k for k,i in sttoi.items()}

    mptoi = {k:i for i,k in enumerate(match_phases)}
    itomp = {i:k for k,i in sttoi.items()}

    bttoi = {k:i for i,k in enumerate(bowler_types)}
    itobt = {i:k for k,i in bttoi.items()}

    rtoi = {k:i for i,k in enumerate(run_types)}
    itor = {i:k for k,i in rtoi.items()}

    otoi = {k:i for i,k in enumerate(outcomes)}
    itoo = {i:k for k,i in otoi.items()}
    '''
    
class CPT(CPTParent):
    def __init__(self, data, playerId=None):
        if playerId != None:
            self.playerId = playerId
            self.data = data[data['p_bat']==playerId]
            self.bowl_data = data[data['p_bowl']==playerId]
            self.total_data = data[(data['p_bat']==playerId) | data['p_bowl']==playerId]
        else:
            self.playerId = 0
            self.data = data
            self.bowl_data = data
        self.bowling_style = None
        self.batting_hand = None
        self.bowling_hand = None

        self.setAttributes()
    
    def setAttributes(self):
        if len(self.data['p_bat'])>0:
            self.batting_hand = self.data['bat_hand'].mode()[0]
        if len(self.data['p_bowl'])>0:
            bowling_hand = {
                'LF':'left',
                'SLA':'left',
                'RF':'right',
                'OB':'right',
                'LB':'right'
            }
            self.bowling_style = self.data['bowl_style'].mode()[0]
            self.bowling_hand = self.data['bowl_style'].map(bowling_hand)
        if len(self.data[self.data['year']==2022]) != 0:
            self.team = self.data[self.data['year']==2022]['team_bat'].mode()[0]
        else:
            self.team = "Out of League"

    def set_distributions(self):
        self.__cpt_ball_outcome()
        self.__cpt_ll()
        self.__cpt_shot()
        self.__cpt_control()
        self.__cpt_run()
        self.__wicket_prob()

    def __wicket_prob(self):
        try:
            self.bat_wicket_prob = len(self.data[self.data['outcome']=='out'])/len(self.data)
        except:
            self.bat_wicket_prob = 0.01
        try:
            self.bowl_wicket_prob = len(self.bowl_data[self.bowl_data['outcome']=='out'])/len(self.bowl_data)
        except:
            self.bowl_wicket_prob = 0.01

    def __cpt_ball_outcome(self):
        outcomes = []
        for outcome in self.outcomes:
            df = self.data[self.data['outcome2']==outcome]
            outcomes.append(len(df))
        if sum(outcomes)==0:
            #cpts = np.array([1, 1, 1, 1])
            cpts = np.array([0.05, 0.95, 0.05])
        else:
            cpts = np.array(outcomes)
        distributions = cpts / np.sum(cpts, axis=-1, keepdims=True)
        self.cpt_ball_outcome = distributions
        return distributions
    
    def __cpt_ll(self):
        cpts = []
        for match_phase in self.match_phases:
            phases = []
            match_phase_df = self.bowl_data[self.bowl_data['match_phase']==match_phase]
            for line, length in self.line_lengths:
                df = match_phase_df[(match_phase_df['line'] == line) & (match_phase_df['length'] == length)]
                phases.append(len(df))
            if sum(phases)==0:
                phases = np.ones(len(self.line_lengths))
            cpts.append(phases)
        cpts = np.array(cpts)
        distributions = cpts / np.sum(cpts, axis=-1, keepdims=True)
        self.cpt_ll = distributions
        return distributions
    
    def __cpt_shot(self):
        cpts = []
        for line, length in self.line_lengths:
            ll = []
            for bowler_type in self.bowler_types:
                bt = []
                for shot_type in self.shot_types:
                    df = self.data[(self.data['shot']==shot_type) & (self.data['bowl_style']==bowler_type) & (self.data['line']==line) & (self.data['length']==length)]
                    bt.append(len(df))
                if sum(bt)==0:
                    bt = np.ones(len(self.shot_types))
                ll.append(bt)
            cpts.append(ll)
        cpts = np.array(cpts)
        distributions = cpts / np.sum(cpts, axis=-1, keepdims=True)
        self.cpt_shot = distributions
        return distributions
    
    def __cpt_control(self):
        cpts = []
        for match_phase in self.match_phases:
            phase = []
            for control_val in self.controls:
                df = self.data[(self.data['control']==control_val) & (self.data['match_phase']==match_phase)]
                phase.append(len(df))
            if sum(phase)==0:
                phase = np.array([0.7,0.3])
            cpts.append(phase)
        cpts = np.array(cpts)
        distributions = cpts / np.sum(cpts, axis=-1, keepdims=True)
        self.cpt_control = distributions
        return distributions
    
    def __cpt_run(self):
        cpts = []
        for shot_played in self.shot_types:
            sp = []
            for control in [0,1]:
                c = []
                for run in self.run_types:
                    df = self.data[(self.data['control']==control) & (self.data['shot']==shot_played) & (self.data['score']==run)]
                    temp = len(df)
                    #if run == 0:
                    #    temp *= 0.75
                    c.append(temp)
                if sum(c)==0:
                    c = np.array([0.4, 0.3, 0.2, 0.05, 0.03, 0.02])
                sp.append(c)
            cpts.append(sp)
        cpts = np.array(cpts)
        distributions = cpts / np.sum(cpts, axis=-1, keepdims=True)
        self.cpt_run = distributions
        return distributions


'''

{0: ('stumps', 'short'), 1: ('stumps', 'yorker'), 2: ('stumps', 'full_toss'), 3: ('stumps', 'full'), 4: ('stumps', 'good_length'), 5: ('outside_off', 'short'), 6: ('outside_off', 'yorker'), 7: ('outside_off', 'full_toss'), 8: ('outside_off', 'full'), 9: ('outside_off', 'good_length'), 10: ('down_leg', 'short'), 11: ('down_leg', 'yorker'), 12: ('down_leg', 'full_toss'), 13: ('down_leg', 'full'), 14: ('down_leg', 'good_length')}
{0: 'defend', 1: 'attack', 2: 'rotate'}
{0: 'defend', 1: 'attack', 2: 'rotate'}
{0: 'LB', 1: 'OB', 2: 'LF', 3: 'SLA', 4: 'RF'}
{0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 6}
{0: 'wide', 1: 'normal', 2: 'nb', 3: 'out'}

'''