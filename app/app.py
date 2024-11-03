import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from league import League
from user import User
import pickle
from auction import Auction
from db_psql.reading import get_all_matches, get_user_matches, get_match
import db_psql.insertion as insertion
import utils
from game import MatchState

user = User()
league = League(user, 2024)
insertion.copy_original_players()

#league.makeTeams()

#with open('players.pkl', 'wb') as f:
#    pickle.dump(league.leagueTeams, f)

#with open('players.pkl', 'rb') as f:
#    league.leagueTeams = pickle.load(f)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

# Initialize league and user objects
#data = DataCleaner('../data/t20_bbb.csv', 'IPL')
#data = data.clean_data()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/select_team', methods=['POST'])
def select_team():
    selected_team = request.form['team']
    user.select_team(selected_team)
    return redirect(url_for('start_league'))

@app.route('/start_league')
def start_league():
    league.makeSchedule()
    return render_template('dashboard.html', team=league.user.team, year=league.year)

@app.route('/matches')
def all_matches():
    all_matches = [(match[1], match[2]) for match in get_all_matches()]
    return render_template('matches.html', matches=all_matches)

@app.route('/user_matches')
def user_matches():
    user_matches = [[match[0], match[1], match[2]] for match in get_user_matches()]
    next_available_match = None
    completed_matches = list(league.completed_matches)
    for match in user_matches:
        if match[0] not in completed_matches:
            next_available_match = match[0]
            break
    return jsonify({
        'matches': user_matches,
        'user_team': user.team,
        'completed_matches': completed_matches,
        'next_available_match': next_available_match
    })

@app.route('/user_matches_page')
def user_matches_page():
    return render_template('user_matches.html')

@app.route('/match_centre/<int:match_number>', methods=['GET', 'POST'])
def match_centre(match_number):
    league.simulateUntil(match_number)
    match_number, team1, team2 = get_match(match_number)
    global match
    match = MatchState(team1, team2)
    if not match.innings_completed:
        match.playGame()  # Continue or resume the game
    return render_template('match_centre.html', 
                           match=match, 
                           match_number=match_number,
                           batting_team=match.playersTeam1,
                           bowling_team=match.playersTeam2)

@app.route('/check_match_state/<int:match_number>')
def check_match_state(match_number):    
    if match.waiting_for_openers:
        return jsonify({'needsInput': True, 'inputType': 'openers'})
    elif match.waiting_for_opening_bowler:
        return jsonify({'needsInput': True, 'inputType': 'opening_bowler'})
    elif match.waiting_for_batsman and match.is_user_batting():
        return jsonify({'needsInput': True, 'inputType': 'batsman'})
    elif match.waiting_for_bowler and match.is_user_bowling():
        return jsonify({'needsInput': True, 'inputType': 'bowler'})
    else:
        return jsonify({'needsInput': False})

@app.route('/get_match_state/<int:match_number>')
def get_match_state(match_number):
    #match = league.matches[match_number-1]
    if hasattr(match,'win'):
        league.completed_matches.add(match_number)
        league.updateResults(match)
        #print(league.results)
    return jsonify({
        'runs': match.runs,
        'wickets': match.wickets,
        'current_over': match.current_over,
        'current_ball': match.current_ball,
        'match_phase': match.match_phase,
        'scorecard': match.scorecard,
        'innings_completed': match.innings_completed,
        'win': match.win if hasattr(match, 'win') else None,
        'loss': match.loss if hasattr(match, 'loss') else None
    })

@app.route('/select_player/<int:match_number>', methods=['POST'])
def select_player(match_number):
    #match = league.matches[match_number-1]
    data = request.json
    #print(f"Selecting player: {data}")  # Log the incoming data
    #print(f"Current match state: {match.__dict__}")  # Log the current match state
    if data['type'] == 'openers':
        match.user_select_openers(data['striker'], data['non_striker'])
    elif data['type'] == 'opening_bowler':
        match.user_select_opening_bowler(data['bowler'])
    elif data['type'] == 'batsman':
        match.user_select_batsman(data['player'])
    elif data['type'] == 'bowler':
        match.user_select_bowler(data['player'])
    match.simulateInning()  # Continue the game after selection
    return jsonify({'success': True})

@app.route('/start_next_innings/<int:match_number>', methods=['POST'])
def start_next_innings(match_number):
    #match = league.matches[match_number-1]
    match.switch_innings()
    match.initializeInning()
    print(match.innings)
    return jsonify({
        'success': True,
        'userBatting': match.is_user_batting(),
        'userBowling': match.is_user_bowling()
    })
    '''
    if match.innings == 1:
        pass
    else:
        return jsonify({'success': False, 'message': 'Match is already completed'})
    '''

@app.route('/get_player_lists/<int:match_number>')
def get_player_lists(match_number):
    #match = league.matches[match_number-1]
    return jsonify({
        'battingTeam': [{'name': player.name} for player in match.playersTeam1],
        'bowlingTeam': [{'name': player.name} for player in match.playersTeam2]
    })

@app.route('/retain_players', methods=['GET', 'POST'])
def retain_players():
    global auction
    auction_type = "mega" if league.year in [2024+3*i for i in range(10)] else "mini"
    auction = Auction(user, auction_type)
    user_team = user.team
    max_retentions = auction.allowed_retention
    
    if request.method == 'POST':
        retained_player_ids = [int(id) for id in request.form.getlist('retained_players')]
        if len(retained_player_ids) <= max_retentions:
            auction.retain_players(retained_player_ids)
            flash("Players retained successfully!")
            return redirect(url_for('auction_page'))
        else:
            flash(f"You can only retain up to {max_retentions} players.")
    available_players = utils.create_players(auction.teamPlayers[user_team])
    return render_template('retain_players.html', players=available_players, 
                           max_retentions=max_retentions)

@app.route('/choose_playing_eleven/<int:match_number>', methods=['GET', 'POST'])
def choose_playing_eleven(match_number):
    current_match = league.matches[match_number]
    user_team = user.team
    
    if user_team not in [current_match.team1, current_match.team2]:
        return "You are not part of this match", 403

    if request.method == 'POST':
        selected_players = request.form.getlist('players')
        if len(selected_players) != 11:
            return "You must select exactly 11 players", 400
        
        if user_team == current_match.team1:
            current_match.team1_playing_eleven = selected_players
        else:
            current_match.team2_playing_eleven = selected_players
        
        return redirect(url_for('match_centre', match_number=match_number))
    
    player_squad = current_match.team1_squad if user_team == current_match.team1 else current_match.team2_squad
    return render_template('choose_playing_eleven.html', match_number=match_number, player_squad=player_squad)

@app.route('/auction', methods=['GET', 'POST'])
def auction_page():
    if 'current_player_id' not in session:
        player = auction.get_next_player()
        if player is None:
            flash("Auction has ended!")
            return redirect(url_for('all_matches'))
        session['current_player_id'] = player.playerId

    player = auction.get_player_by_id(session['current_player_id'])

    # Simulate other teams' bids
    player_values = {}
    for team in auction.teamPlayers.keys():
        if team == 'Out of League':
            continue
        player_value = auction.assign_value(player, team)
        player_values[team] = player_value
    
    # Get the highest bid from other teams
    other_bids = {team: bid for team, bid in player_values.items() if team != auction.user.team}
    highest_other_bid_team = max(other_bids, key=other_bids.get, default=None)
    highest_other_bid = other_bids[highest_other_bid_team] * auction.price_factor if highest_other_bid_team else 0

    if request.method == 'POST':
        if 'simulate_rest' in request.form:  # Simulate the rest of the auction
            while player:
                team_value = auction.assign_value(player, auction.user.team)
                purchased_team, final_price = auction.simulate_player(player, team_value)
                #flash(f"{player.name}: {'UNSOLD' if purchased_team == 'Out of League' else f'{purchased_team}, {final_price}'}")
                session.pop('current_player_id', None)
                player = auction.get_next_player()
                if not player:
                    break
            flash("Auction has ended!")
            return redirect(url_for('all_matches'))

        user_choice = request.form.get('choice')
        if user_choice == 'buy':
            purchased_team, final_price = auction.simulate_player(player, highest_other_bid + 1)  # User matches and slightly exceeds the highest bid
        else:
            purchased_team, final_price = auction.simulate_player(player, -100)
        flash(f"{player.name} sold to {purchased_team} for {final_price}")
        session.pop('current_player_id', None)
        return redirect(url_for('auction_page'))

    # Get the remaining budgets and bought players
    budgets = auction.budgets
    bought_players = {team: auction.retainedPlayers[team] for team in auction.retainedPlayers if team != 'Out of League'}

    return render_template('auction.html', 
                           player=player, 
                           budgets=budgets, 
                           bought_players=bought_players, 
                           highest_other_bid=highest_other_bid, 
                           highest_other_bid_team=highest_other_bid_team)

@app.route('/simulate_league')
def simulate_league():
    league.simulateUntil()
    formatted_results = [f"{i+1}: {result[0]} vs {result[1]} --> {result[2]}" 
                         for i, result in enumerate(league.results)]
    print(league.results[0][3])
    return render_template('results.html', results=formatted_results)

@app.route('/view_standings')
def view_standings():
    return render_template('standings.html', standings=league.standings)

@app.route('/simulate_playoffs')
def simulate_playoffs():
    league.simulatePlayoffs()
    return render_template('playoffs.html', champions=league.champions, runner_up=league.runner_up)

@app.route('/start-new-year')
def start_new_year():
    league.new_season()
    return render_template('start_new_year.html', year=league.year)

if __name__ == '__main__':
    app.run(debug=True)