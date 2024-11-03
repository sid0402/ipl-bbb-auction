from db_psql.connection import get_db_connection, close_db_connection

def insert_player(player):
    conn, cursor = get_db_connection()

    '''print([type(x) for x in [int(player.playerId),
            player.name,
            player.role,
            player.nationality,
            int(player.dob),
            player.batting_hand,
            str(player.bowling_hand),
            player.bowling_style,
            player.team,
            float(player.overall_rating),
            float(player.potential),
            int(player.age)]])'''
    if not conn or not cursor:
        return
    
    try:
        cursor.execute("""
            INSERT INTO players (player_id, name, role, nationality, dob, batting_hand, bowling_hand, 
                                bowling_style, team, overall_rating, potential, age)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                role = EXCLUDED.role,
                nationality = EXCLUDED.nationality,
                dob = EXCLUDED.dob,
                batting_hand = EXCLUDED.batting_hand,
                bowling_hand = EXCLUDED.bowling_hand,
                bowling_style = EXCLUDED.bowling_style,
                team = EXCLUDED.team,
                overall_rating = EXCLUDED.overall_rating,
                potential = EXCLUDED.potential,
                age = EXCLUDED.age;
        """, (
            int(player.playerId),
            str(player.name),
            str(player.role),
            str(player.nationality),
            int(player.dob),
            str(player.batting_hand)[:50],
            str(player.bowling_hand)[:50],
            str(player.bowling_style)[:50],
            str(player.team),
            float(player.overall_rating),
            float(player.potential),
            int(player.age)
        ))
        conn.commit()
        print(f"Inserted player {player.name}")
    except Exception as e:
        print(f"Error inserting player {player.name}: {e}")
    finally:
        close_db_connection(conn, cursor)

def insert_player_stats(player):
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return

    try:
        cursor.execute("""
            INSERT INTO player_stats (player_id, batting_rating, bowling_rating, attacking_intent, 
                                      attacking_ability, control, economy, wicket_taking_ability, 
                                      powerplay_batted, middle_batted, death_batted, 
                                      powerplay_bowled, middle_bowled, death_bowled)
            VALUES ((SELECT player_id FROM players WHERE player_id = %s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            player.playerId,
            float(player.batting_rating),
            float(player.bowling_rating),
            float(player.attacking_intent),
            float(player.attacking_ability),
            float(player.control),
            float(player.economy),
            float(player.wicket_taking_ability),
            float(player.powerplay_batted),
            float(player.middle_batted),
            float(player.death_batted),
            float(player.powerplay_bowled),
            float(player.middle_bowled),
            float(player.death_bowled)
        ))
        conn.commit()
        print(f"Inserted stats for player {player.name}")
    except Exception as e:
        print(f"Error inserting stats for player {player.name}: {e}")
    finally:
        close_db_connection(conn, cursor)

# insertion.py
from db_psql.connection import get_db_connection, close_db_connection

def insert_player_cpts(player):
    # Establish database connection and cursor
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return
    
    try:
        # Execute the INSERT statement
        cursor.execute("""
            INSERT INTO player_cpts (
                player_id, 
                cpt_bowl_wicket_prob, 
                cpt_bat_wicket_prob, 
                cpt_run, 
                cpt_shot, 
                cpt_ll, 
                cpt_control, 
                cpt_ball_outcome
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id) DO NOTHING;
        """, (
            int(player.playerId),  # Use the player ID directly
            float(player.cpt.bowl_wicket_prob),
            float(player.cpt.bat_wicket_prob),
            player.cpt.cpt_run.flatten().tolist(),      # Convert to list for PostgreSQL array
            player.cpt.cpt_shot.flatten().tolist(),     # Convert to list for PostgreSQL array
            player.cpt.cpt_ll.flatten().tolist(),       # Convert to list for PostgreSQL array
            player.cpt.cpt_control.flatten().tolist(),  # Convert to list for PostgreSQL array
            player.cpt.cpt_ball_outcome.flatten().tolist()  # Convert to list for PostgreSQL array
        ))
        
        # Commit the transaction
        conn.commit()
        print(f"Inserted CPT data for player {player.name}")
    
    except Exception as e:
        # Print error message for debugging
        print(f"Error inserting CPT data for player {player.name}: {e}")

    finally:
        close_db_connection(conn, cursor)

def insert_schedule(schedule):
    """
    Inserts the schedule into the PostgreSQL schedule table.
    
    :param schedule: A list of MatchState objects containing the schedule.
    :param season_year: The year or season of the league.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return
    
    try:
        insert_query = """
            INSERT INTO schedule (match_number, team1, team2, user_team)
            VALUES (%s, %s, %s, %s);
        """
        
        for match in schedule:
            print(match)         
            cursor.execute(insert_query, (match[3], match[0], match[1], match[2]))
        
        conn.commit()
        print(f"Inserted {len(schedule)} matches into the schedule table.")
    
    except Exception as e:
        print(f"Error inserting schedule: {e}")
    
    finally:
        close_db_connection(conn, cursor)

def update_season_stats(scorecard, season_year):
    """
    Updates the season stats table in the database with the match stats from the scorecard.
    
    :param scorecard: A dictionary containing the match scorecard with batsmen and bowlers' statistics.
    :param season_year: The year of the current season.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return

    try:
        # SQL query to update or insert season stats for batsmen
        batsman_query = """
            INSERT INTO season_stats (player_id, name, season_year, runs_scored, balls_faced, outs)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id, season_year)
            DO UPDATE SET 
                runs_scored = season_stats.runs_scored + EXCLUDED.runs_scored,
                balls_faced = season_stats.balls_faced + EXCLUDED.balls_faced,
                outs = season_stats.outs + EXCLUDED.outs,
                name = EXCLUDED.name;  -- Update name if it changes
        """

        # SQL query to update or insert season stats for bowlers
        bowler_query = """
            INSERT INTO season_stats (player_id, name, season_year, wickets_taken, balls_bowled, runs_given)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id, season_year)
            DO UPDATE SET 
                wickets_taken = season_stats.wickets_taken + EXCLUDED.wickets_taken,
                balls_bowled = season_stats.balls_bowled + EXCLUDED.balls_bowled,
                runs_given = season_stats.runs_given + EXCLUDED.runs_given,
                name = EXCLUDED.name;  -- Update name if it changes
        """

        # Update stats for all batsmen in the scorecard
        for batsman in scorecard['batsmen'].values():
            cursor.execute(batsman_query, (
                batsman['_id'], 
                batsman['name'],
                season_year, 
                batsman['runs'], 
                batsman['balls'], 
                batsman['out']
            ))

        # Update stats for all bowlers in the scorecard
        for bowler in scorecard['bowlers'].values():
            cursor.execute(bowler_query, (
                bowler['_id'], 
                bowler['name'],
                season_year, 
                bowler['out'], 
                bowler['balls'], 
                bowler['runs']
            ))

        # Commit the transaction to save the changes
        conn.commit()
        print("Season stats updated successfully for all players in the match.")

    except Exception as e:
        print(f"Error updating season stats: {e}")
        conn.rollback()
    
    finally:
        close_db_connection(conn, cursor)


def insert_auctioned_player(id, val, team):
    """
    Inserts the schedule into the PostgreSQL schedule table.
    
    :param schedule: A list of MatchState objects containing the schedule.
    :param season_year: The year or season of the league.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return
    
    try:
        insert_query = """
            INSERT INTO players (player_id, team, price)
            VALUES (%s, %s, %s)
            ON CONFLICT (player_id) 
            DO UPDATE SET 
                team = EXCLUDED.team,
                price = EXCLUDED.price;
        """
               
        cursor.execute(insert_query, (id, team, val))
        
        conn.commit()
        print(f"Inserted {id} with team {team} and price {val}.")
    
    except Exception as e:
        print(f"Error inserting player: {e}")
    
    finally:
        close_db_connection(conn, cursor)

def copy_original_players():
    """
    Copies all data from source_table to target_table.
    
    :param source_table: Name of the source table.
    :param target_table: Name of the target table.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return
    
    try:
        # SQL query to copy data from source_table to target_table
        copy_query = f"""
            INSERT INTO players (player_id, name, team, price,age)
            SELECT player_id, name, team, price,age
            FROM original_players
            ON CONFLICT (player_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                team = EXCLUDED.team,
                price = EXCLUDED.price,
                age = EXCLUDED.age;

        """
        
        cursor.execute(copy_query)
        
        conn.commit()
        print(f"Copied data from original_players to players.")
    
    except Exception as e:
        print(f"Error copying data: {e}")
    
    finally:
        close_db_connection(conn, cursor)


def clear_schedule():
    """
    Copies all data from source_table to target_table.
    
    :param source_table: Name of the source table.
    :param target_table: Name of the target table.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return
    
    try:
        # SQL query to copy data from source_table to target_table
        clear_query = f"""
            DELETE FROM schedule
        """
        
        cursor.execute(clear_query)
        
        conn.commit()
        print(f"Cleared Schedule")
    
    except Exception as e:
        print(f"Couldn't clear schedule: {e}")
    
    finally:
        close_db_connection(conn, cursor)

def retire_players(year):
    """
    Marks players as retired based on the specified criteria:
    - Age above 35.
    - Bottom 25% in performance (runs or wickets) based on their role.
    - Updates the 'retired' field to True in the players table.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return
    
    try:
        # Step 1: Identify players above the age of 35 who are not already retired
        cursor.execute("""
            SELECT player_id, role 
            FROM players 
            WHERE age > 35 AND retired = FALSE;
        """,(year,))
        eligible_players = cursor.fetchall()
        
        if not eligible_players:
            print("No eligible players to retire.")
            return

        # Step 2: Calculate thresholds for bottom 25% based on role
        # Batsmen and Wicketkeepers - Runs
        cursor.execute("""
            SELECT percentile_cont(0.25) WITHIN GROUP (ORDER BY runs_scored) AS run_threshold 
            FROM season_stats 
            WHERE player_id IN (SELECT player_id FROM players WHERE role IN ('batsman', 'wicketkeeper') AND retired = FALSE) AND season_year = %s;
        """,(year,))
        run_threshold = cursor.fetchone()[0]
        
        # Bowlers - Wickets
        cursor.execute("""
            SELECT percentile_cont(0.25) WITHIN GROUP (ORDER BY wickets_taken) AS wicket_threshold 
            FROM season_stats 
            WHERE player_id IN (SELECT player_id FROM players WHERE role = 'bowler' AND retired = FALSE) AND season_year = %s;
        """,(year,))
        wicket_threshold = cursor.fetchone()[0]

        # All-rounders - Both Runs and Wickets
        cursor.execute("""
            SELECT percentile_cont(0.25) WITHIN GROUP (ORDER BY runs_scored) AS run_threshold,
                   percentile_cont(0.25) WITHIN GROUP (ORDER BY wickets_taken) AS wicket_threshold
            FROM season_stats 
            WHERE player_id IN (SELECT player_id FROM players WHERE role = 'all-rounder' AND retired = FALSE) AND season_year = %s;
        """,(year,))
        allrounder_thresholds = cursor.fetchone()
        
        players_to_retire = []
        
        # Step 3: Identify players to retire based on their stats and role
        for player_id, role in eligible_players:
            cursor.execute("""
                SELECT runs_scored, wickets_taken 
                FROM season_stats 
                WHERE player_id = %s;
            """, (player_id,))
            stats = cursor.fetchone()

            if not stats:
                players_to_retire.append(player_id)
                continue
            
            if role in ['batsman', 'wicketkeeper'] and stats[0] <= run_threshold:
                players_to_retire.append(player_id)
            elif role == 'bowler' and stats[1] <= wicket_threshold:
                players_to_retire.append(player_id)
            elif role == 'all-rounder' and stats[0] <= allrounder_thresholds[0] and stats[1] <= allrounder_thresholds[1]:
                players_to_retire.append(player_id)
        
        # Step 4: Update 'retired' status for players in the players table
        for player_id in players_to_retire:
            try:
                # Updating 'retired' status to True in the players table
                cursor.execute("UPDATE players SET retired = TRUE WHERE player_id = %s;", (player_id,))
                conn.commit()
                print(f"Player {player_id} has been marked as retired successfully.")
            except Exception as e:
                print(f"Error retiring player {player_id}: {e}")
                conn.rollback()
    
    except Exception as e:
        print(f"Error identifying players to retire: {e}")
    finally:
        close_db_connection(conn, cursor)

def increment_age_for_all_players():
    """
    Increments the 'age' column for every player in the 'players' table by 1.
    """
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return
    
    try:
        update_query = """
            UPDATE players
            SET age = age + 1;
        """
        
        cursor.execute(update_query)
        conn.commit()
        print("Successfully incremented age for all players.")
    
    except Exception as e:
        print(f"Error incrementing age: {e}")
        conn.rollback()
    
    finally:
        close_db_connection(conn, cursor)