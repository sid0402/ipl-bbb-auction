import pandas as pd
from player_mapping import player_roles, nationality, birth_years

class DataCleaner:
    def __init__(self, data_path='/Users/siddhantagarwal/Desktop/Programming/match_simulator/data/t20_bbb.csv', competition='IPL'):
        self.data_path = data_path
        self.df = pd.read_csv(data_path)
        self.df = self.df[self.df['competition']==competition].dropna(subset=['length','line','shot','control','score'])
        self.df = self.df[self.df['year']>=2023]

        self.left_off = {'year':set(),'nationality':set(),'role':set()}
        #self.df['bat'] = self.df['bat'].str.replace(r'[^\w\s]', ' ', regex=True)
        #self.df['bat'] = self.df['bat'].str.replace(r'\s+', ' ', regex=True).str.strip()
        #self.df['bowl'] = self.df['bowl'].str.replace(r'[^\w\s]', ' ', regex=True)
        #self.df['bowl'] = self.df['bowl'].str.replace(r'\s+', ' ', regex=True).str.strip()


    def clean_data(self):
        self._clean_line()
        self._clean_length()
        self._create_match_phase()
        self._clean_bowl_style()
        self._map_shot()
        self._clean_runs()
        self._clean_outcome()
        self._make_roles()
        self._make_nationality()
        self._make_birth_years()
        return self.df

    def _clean_line(self):
        line_mapping = {
            'WIDE_DOWN_LEG': 'down_leg',
            'DOWN_LEG': 'down_leg',
            'ON_THE_STUMPS': 'stumps',
            'OUTSIDE_OFFSTUMP': 'outside_off',
            'WIDE_OUTSIDE_OFFSTUMP': 'outside_off'
        }
        self.df['line'] = self.df['line'].map(line_mapping)

    def _clean_length(self):
        self.df['length'] = self.df['length'].str.lower().str.strip()
        self.df['length'] = self.df['length'].replace('short_of_a_good_length', 'good_length')

    def _create_match_phase(self):
        self.df['match_phase'] = self.df['over'].apply(self._match_phase)

    @staticmethod
    def _match_phase(over):
        if 1 <= over <= 6:
            return 'powerplay'
        elif 7 <= over <= 16:
            return 'middle'
        elif 17 <= over <= 20:
            return 'death'
        else:
            return 'unknown'

    def _clean_bowl_style(self):
        bowl_mapping = {
            'OB/LB':'OB',
            'RM/OB/LB': 'OB',
            'SLA/LWS': 'LB',
            'RM/OB':'OB',
            'RF':'RF',
            'LF':'LF',
            'LMF':'LF',
            'RMF':'RF',
            'LB':'LB',
            'OB':'OB',
            'LM':'LF',
            'LFM':'LF',
            'RM':'RF',
            'LWS':'LB',
            'OB/LBG':'OB',
            'LBG':'LB',
            'RFM':'RF',
            'SLA':'SLA'
        }
        self.df['bowl_style'] = self.df['bowl_style'].map(bowl_mapping)

    def _map_shot(self):
        shot_mapping = {
            'paddle_sweep':'attack',
            'reverse_pull':'attack',
            'late_cut':'attack',
            'flick':'attack',
            'reverse_sweep':'attack',
            'hook':'attack',
            'straight_drive':'rotate',
            'paddle_away':'attack',
            'reverse_scoop':'attack',
            'leg_glance':'rotate',
            'defended':'defend',
            'slog_sweep':'attack',
            'push':'rotate',
            'ramp':'attack',
            'on_drive':'rotate',
            'dab':'rotate',
            'slog_shot':'attack',
            'steered':'rotate',
            'square_drive':'rotate',
            'cut_shot':'rotate',
            'upper_cut':'attack',
            'pull':'attack',
            'sweep_shot':'attack',
            'cover_drive':'rotate',
            'left_alone':'defend'
        }
        self.df['shot'] = self.df['shot'].apply(lambda x: shot_mapping.get(x.lower(), x))

    def _clean_runs(self):
        def clean_runs_helper(number):
            if number == 7:
                return 6
            elif number == 5:
                return 4
            return number
        self.df['score'] = self.df['score'].apply(clean_runs_helper)

    def _clean_outcome(self):
        outcome_mapping = {
            'wide': 'wide',
            'no ball': 'nb',
            'out': 'out'
        }
        self.df['outcome'] = self.df['outcome'].apply(lambda x: outcome_mapping.get(x, 'normal'))
        outcome_mapping = {
            'wide':'wide',
            'nb':'nb'
        }
        self.df['outcome2'] = self.df['outcome'].apply(lambda x: outcome_mapping.get(x, 'normal'))

    def _make_roles(self):
        roles = player_roles()
        def apply_roles(name):
            if name not in roles:
                self.left_off['role'].add(name)
            return roles.get(name,'all-rounder').lower()
        self.df['bat_role'] = self.df['bat'].apply(apply_roles)
        self.df['bowl_role'] = self.df['bowl'].apply(apply_roles)
    
    def _make_nationality(self):
        nationalities = nationality()
        def apply_roles(name):
            if name not in nationalities:
                self.left_off['nationality'].add(name)
            return nationalities.get(name,'indian').lower()
        self.df['bat_nationality'] = self.df['bat'].apply(apply_roles)
        self.df['bowl_nationality'] = self.df['bowl'].apply(apply_roles)
    
    def _make_birth_years(self):
        dob = birth_years()
        def apply_roles(name):
            if name not in dob:
                self.left_off['year'].add(name)
            return dob.get(name,0)
        self.df['bat_dob'] = self.df['bat'].apply(apply_roles)
        self.df['bowl_dob'] = self.df['bowl'].apply(apply_roles)

'''
column1 = 'p_bowl'
column2 = 'p_bat'

count1 = data[column1].value_counts()
count2 = data[column2].value_counts()

# Combine the counts
combined_counts = pd.DataFrame({column1: count1, column2: count2}).fillna(0)

# Find rows where count in column1 is at least 5 times more than in column2
result = combined_counts[combined_counts[column1] >= 3 * combined_counts[column2]]
values_to_filter = result.index.tolist()
filtered_df = data[data['p_bat'].isin(values_to_filter)]
filtered_df['p_bat']=-1
data = data.append(filtered_df,ignore_index=True)
'''