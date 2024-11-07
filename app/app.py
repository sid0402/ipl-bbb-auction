import sys
import os
from threading import Thread

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

app = Flask(__name__)
app.secret_key = 'your_secret_key'  


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
    matches = get_all_matches()
    
    day_mapping = {
        0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday",
        5: "Saturday (Match 1)", 6: "Saturday (Match 2)",
        7: "Sunday (Match 1)", 8: "Sunday (Match 2)"
    }
    
    weeks = {}
    for match in matches:
        week = match[4]  # Assuming week is stored at index 4
        day_index = match[5]  # Assuming day_index is stored at index 5
        day = day_mapping[day_index]
        
        if week not in weeks:
            weeks[week] = []
        weeks[week].append((day, match[1], match[2], match[0]))  # (day, team1, team2)
        weeks = dict(sorted(weeks.items()))
    
    return render_template('matches.html', weeks=weeks, standings=league.standings)

@app.route('/api/current_status')
def current_status():
    response = {
        "matches": [],
        "standings": {}
    }

    if league.results:
        response['matches'] = [
            {
                "match_number": i + 1,
                "team1": result[0],
                "team2": result[1],
                "winner": result[2],
                "scorecard": result[3]
            }
            for i, result in enumerate(league.results)
        ]

    sorted_standings = sorted(league.standings.items(), key=lambda item: item[1]['points'], reverse=True)
    response['standings'] = [
        {
            "team": team,
            "games": stats['games'],
            "points": stats['points']
        }
        for team, stats in sorted_standings
    ]

    return jsonify(response)


@app.route('/match_center/<int:match_number>')
def match_center(match_number):
    # Adjust for zero-based indexing in Python lists
    if match_number - 1 >= len(league.results) or match_number - 1 < 0:
        return "Match not found", 404

    # Retrieve match data based on the match number
    match_data = league.results[match_number - 1]
    match_details = {
        "match_number": match_number,
        "team1": match_data[0],
        "team2": match_data[1],
        "winner": match_data[2],
        "scorecard": match_data[3]
    }
    
    return render_template('match_centre.html', match_data=match_details)

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
            #auction.retain_players(retained_player_ids)
            auction.manual_retain_players()
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