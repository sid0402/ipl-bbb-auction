from db_psql.connection import get_db_connection, close_db_connection

def get_cpt_bowl_wicket_prob(player_id):
    conn, cursor = get_db_connection()
    if not conn:
        return None
    
    try:
        query = "SELECT cpt_bowl_wicket_prob FROM player_cpts WHERE player_id = %s;"
        cursor.execute(query, (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    except Exception as e:
        print(f"Error fetching cpt_bowl_wicket_prob for player ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_cpt_bat_wicket_prob(player_id):
    conn, cursor = get_db_connection()
    if not conn:
        return None
    
    try:
        query = "SELECT cpt_bat_wicket_prob FROM player_cpts WHERE player_id = %s;"
        cursor.execute(query, (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    except Exception as e:
        print(f"Error fetching cpt_bat_wicket_prob for player ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_cpt_run(player_id):
    conn, cursor = get_db_connection()
    if not conn:
        return None
    
    try:
        query = "SELECT cpt_run FROM player_cpts WHERE player_id = %s;"
        cursor.execute(query, (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    except Exception as e:
        print(f"Error fetching cpt_run for player ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_cpt_shot(player_id):
    conn, cursor = get_db_connection()
    if not conn:
        return None
    
    try:
        query = "SELECT cpt_shot FROM player_cpts WHERE player_id = %s;"
        cursor.execute(query, (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    except Exception as e:
        print(f"Error fetching cpt_shot for player ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_cpt_ll(player_id):
    conn, cursor = get_db_connection()
    if not conn:
        return None
    
    try:
        query = "SELECT cpt_ll FROM player_cpts WHERE player_id = %s;"
        cursor.execute(query, (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    except Exception as e:
        print(f"Error fetching cpt_ll for player ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_cpt_control(player_id):
    conn, cursor = get_db_connection()
    if not conn:
        return None
    
    try:
        query = "SELECT cpt_control FROM player_cpts WHERE player_id = %s;"
        cursor.execute(query, (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    except Exception as e:
        print(f"Error fetching cpt_control for player ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_cpt_ball_outcome(player_id):
    conn, cursor = get_db_connection()
    if not conn:
        return None
    
    try:
        query = "SELECT cpt_ball_outcome FROM player_cpts WHERE player_id = %s;"
        cursor.execute(query, (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    except Exception as e:
        print(f"Error fetching cpt_ball_outcome for player ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_team_players():
    # Establish a connection to the database
    conn, cursor = get_db_connection()
    if not conn:
        return {}
    
    # Initialize an empty dictionary to store the team-player mappings
    team_players = {}
    
    try:
        # Query to select player_id and team from the players table
        cursor.execute("""
            SELECT player_id, team 
            FROM players;
        """)
        
        # Fetch all the results
        results = cursor.fetchall()
        
        # Iterate through each row in the results
        for player_id, team in results:
            # If the team is not in the dictionary, add it with an empty list
            if team not in team_players:
                team_players[team] = []
            
            # Append the player ID to the list of players for the team
            team_players[team].append(player_id)
    
    except Exception as e:
        print(f"Error fetching team-player mappings: {e}")
        return {}
    
    finally:
        # Close the database connection
        close_db_connection(conn, cursor)
    
    # Return the team-player dictionary
    return team_players

def get_match_details(match_number):
    """
    Retrieves match details from the PostgreSQL schedule table based on the match number.
    
    :param match_number: The match number to query.
    :return: A tuple containing (match_number, team1, team2, user_team) or None if not found.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return None
    
    try:
        query = """
            SELECT match_number, team1, team2, user_team
            FROM schedule
            WHERE match_number = %s;
        """
        
        cursor.execute(query, (match_number,))
        
        result = cursor.fetchone()
        
        if result is None:
            print(f"No match found with match number {match_number}.")
            return None
        
        match_number, team1, team2, user_team = result
        
        return match_number, team1, team2, user_team
    
    except Exception as e:
        print(f"Error fetching match details for match number {match_number}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_all_matches():
    """
    Retrieves match details from the PostgreSQL schedule table based on the match number.
    
    :param match_number: The match number to query.
    :return: A tuple containing (match_number, team1, team2, user_team) or None if not found.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return None
    
    try:
        query = """
            SELECT match_number, team1, team2, user_team, week, day
            FROM schedule;
        """
        
        cursor.execute(query,)
        
        result = cursor.fetchall()
        
        if result is None:
            #print(f"No match found with match number {match_number}.")
            return None
        
        print(result)
        
        return result

    except Exception as e:
        print(f"Error fetching match details for match number {match_number}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_player_attributes(player_id):
    """
    Fetches the specified attributes of a player from the database given their ID.

    :param player_id: The ID of the player to fetch.
    :return: A dictionary containing the player's id, name, team, overall_rating, nationality, and role.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return None
    
    try:
        query = """
            SELECT player_id, name, team, overall_rating, nationality, role, bowling_style, batting_hand, potential, age
            FROM players
            WHERE player_id = %s;
        """
        cursor.execute(query, (player_id,))
        
        result = cursor.fetchone()
        
        if result is None:
            print(f"No player found with ID {player_id}")
            return None
        
        # Unpack the result tuple into separate variables
        id, name, team, overall_rating, nationality, role, bowling_style, batting_hand, potential, age = result

        # Return the attributes as a dictionary
        return {
            'id': id,
            'name': name,
            'team': team,
            'overall_rating': overall_rating,
            'nationality': nationality,
            'role': role,
            'bowling_style':bowling_style,
            'batting_hand':batting_hand,
            'potential':potential,
            'age':age,
        }
    
    except Exception as e:
        print(f"Error fetching player attributes for ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_player_stats(player_id):
    """
    Fetches the specified attributes of a player from the database given their ID.

    :param player_id: The ID of the player to fetch.
    :return: A dictionary containing the player's id, name, team, overall_rating, nationality, and role.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return None
    
    try:
        query = """
            SELECT player_id, powerplay_batted, powerplay_bowled
            FROM player_stats
            WHERE player_id = %s;
        """
        cursor.execute(query, (player_id,))
        
        result = cursor.fetchone()
        
        if result is None:
            print(f"No player found with ID {player_id}")
            return None
        
        # Unpack the result tuple into separate variables
        player_id, powerplay_batted, powerplay_bowled = result

        # Return the attributes as a dictionary
        return {
            'id': id,
            'powerplay_batted': powerplay_batted,
            'powerplay_bowled': powerplay_bowled,
        }
    
    except Exception as e:
        print(f"Error fetching player attributes for ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)


def get_user_matches():
    """
    Fetches the specified attributes of a player from the database given their ID.

    :param player_id: The ID of the player to fetch.
    :return: A dictionary containing the player's id, name, team, overall_rating, nationality, and role.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return None
    
    try:
        query = """
            SELECT match_number, team1, team2
            FROM schedule
            WHERE user_team = TRUE;
        """
        cursor.execute(query,)
        
        result = cursor.fetchall()
        
        if result is None:
            print(f"No user matches found")
            return None
        
        return result
    
    except Exception as e:
        print(f"Error fetching user matches: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_match(match_number):
    """
    Fetches the specified attributes of a player from the database given their ID.

    :param player_id: The ID of the player to fetch.
    :return: A dictionary containing the player's id, name, team, overall_rating, nationality, and role.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return None
    
    try:
        query = """
            SELECT match_number, team1, team2
            FROM schedule
            WHERE match_number = %s;
        """
        cursor.execute(query,(match_number,))
        
        result = cursor.fetchone()
        
        if result is None:
            print(f"No matches found")
            return None
        
        return result
    
    except Exception as e:
        print(f"Error fetching match with number {match_number}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)


def get_bowling_batting_rating(id):
    """
    Fetches the specified attributes of a player from the database given their ID.

    :param player_id: The ID of the player to fetch.
    :return: A dictionary containing the player's id, name, team, overall_rating, nationality, and role.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return None
    
    try:
        query = """
            SELECT bowling_rating, batting_rating
            FROM player_stats
            WHERE player_id = %s;
        """
        cursor.execute(query,(id,))
        
        result = cursor.fetchone()
        
        if result is None:
            print(f"No player found")
            return None
        
        return result
    
    except Exception as e:
        print(f"Error fetching player with id {id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)

def get_price(player_id):
    conn, cursor = get_db_connection()
    if not conn:
        return None
    
    try:
        query = "SELECT price FROM players WHERE player_id = %s;"
        cursor.execute(query, (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    except Exception as e:
        print(f"Error fetching price for player ID {player_id}: {e}")
        return None
    
    finally:
        close_db_connection(conn, cursor)