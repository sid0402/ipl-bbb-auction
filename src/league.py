from data_cleaner import DataCleaner
from game import MatchState
from players import CreatePlayers
import random
from auction import Auction
import pandas as pd
from user import User
import pickle
from db_psql.insertion import insert_player, insert_player_stats, insert_player_cpts, insert_schedule,update_season_stats, clear_schedule, retire_players, increment_age_for_all_players
from db_psql.reading import get_team_players, get_match_details, get_user_matches


class League():
    def __init__(self, user, year):
        self.standings = {}
        self.matches = 0
        self.results = []
        self.user = user
        self.match_number = 1
        self.completed_matches = set()
        self.teamPlayers = get_team_players()
        self.teams = list(self.teamPlayers.keys())
        self.year = year
        self.completed = False

        
    def makeTeams(self):
        temp = CreatePlayers(self.year)
        temp.build_teams()
        self.leagueTeams = temp
        self.insert_psql()

    def insert_psql(self):
        df = pd.read_csv('../data/players.csv')
        for player in self.leagueTeams.idToPlayer.values():
            player.overall_rating = df[df['player_id']==player.playerId]['Overall'].values[0]
            player.potential = df[df['player_id']==player.playerId]['Potential'].values[0]
            print(player.name, player.overall_rating, player.potential)
            insert_player(player)
            insert_player_stats(player)
            insert_player_cpts(player)

         
    def makeSchedule(self):
        schedule = []
        teams = [x for x in self.teams if x!='Out of League']
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                user_team = True if self.user.team in [teams[i], teams[j]] else False
                schedule.append([teams[i], teams[j], user_team])
                schedule.append([teams[j], teams[i], user_team])
        random.shuffle(schedule)
        for i,match in enumerate(schedule):
            match.append(i+1)
        self.matches = len(schedule)
        insert_schedule(schedule)
        
    def simulateUntil(self, match_number=-1):
        while (self.match_number < self.matches):
            if self.match_number == match_number:
                self.completed_matches.add(self.match_number)
                self.match_number+=1
                break
            res = self.simulateNextMatch()
            if not res:
                #self.match_number+=1
                #continue
                print("USER NEEDS TO SIMULATE HIS MATCH")
                return

    def simulateNextMatch(self):
        match_number, team1, team2, user_team = get_match_details(self.match_number)
        print(match_number, team1, team2)
        #if self.user.team in [team1, team2]:
        #    return False
        match = MatchState(team1, team2)
        match.playGame()
        update_season_stats(match.scorecard, self.year)
        self.updateStandings(match)
        self.updateResults(match)
        self.completed_matches.add(self.match_number)
        print(self.completed_matches)
        self.match_number+=1
        return True

    def updateResults(self, match):
        match_result = [match.team1, match.team2, match.win, match.scorecards]
        self.results.append(match_result)
    
    def updateStandings(self, match):
            if match.team1 not in self.standings:
                self.standings[match.team1] = {'games':0, 'points':0}
            if match.team2 not in self.standings:
                self.standings[match.team2] = {'games':0, 'points':0}
            self.standings[match.win]['games']+=1
            self.standings[match.win]['points']+=2
            self.standings[match.loss]['games']+=1
            sorted_standings = sorted(self.standings.items(), key=lambda item: item[1]['points'], reverse=True)
            self.standings = {team: stats for team, stats in sorted_standings}
    
    def simulatePlayoffs(self):
        playoffTeams = list(self.standings.keys())
        self.Q1 = (playoffTeams[0], playoffTeams[1])
        self.eliminator = (playoffTeams[2], playoffTeams[3])
        
        print(f"QUALIFIER 1: {self.Q1[0]} vs {self.Q1[1]}")
        Q1 = MatchState(self.Q1[0], self.Q1[1])
        Q1.playGame()

        print(f"ELIMINATOR: {self.eliminator[0]} vs {self.eliminator[1]}")
        eliminator = MatchState(self.eliminator[0], self.eliminator[1])
        eliminator.playGame()

        print(f"Q2: {Q1.loss} vs {eliminator.win}")
        Q2 = MatchState(Q1.loss, eliminator.win)
        Q2.playGame()

        print(f"FINAL: {Q1.win} vs {Q2.win}")
        final = MatchState(Q1.win, Q2.win)
        final.playGame()

        self.champions = final.win
        self.runner_up = final.loss
        
        print("WINNERS: ", self.champions)

        self.completed = True
    
    def new_season(self):
        clear_schedule()
        retire_players(self.year)
        increment_age_for_all_players()
        self.year += 1
        self.standings = {}
        self.matches = 0
        self.results = []