
'''
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
    if match.innings == 1:
        pass
    else:
        return jsonify({'success': False, 'message': 'Match is already completed'})

@app.route('/get_player_lists/<int:match_number>')
def get_player_lists(match_number):
    #match = league.matches[match_number-1]
    return jsonify({
        'battingTeam': [{'name': player.name} for player in match.playersTeam1],
        'bowlingTeam': [{'name': player.name} for player in match.playersTeam2]
    })

'''

'''
@app.route('/matches')
def all_matches():
    all_matches = [(match[1], match[2]) for match in get_all_matches()]
    return render_template('matches.html', matches=all_matches)
'''

#league.makeTeams()

#with open('players.pkl', 'wb') as f:
#    pickle.dump(league.leagueTeams, f)

#with open('players.pkl', 'rb') as f:
#    league.leagueTeams = pickle.load(f)

# Initialize league and user objects
#data = DataCleaner('../data/t20_bbb.csv', 'IPL')
#data = data.clean_data()