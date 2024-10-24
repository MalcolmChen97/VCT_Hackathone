import pandas as pd
import json
import logging
from itertools import combinations

# Setting up logging
logging.basicConfig(filename='team_formation.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Load the CSV file containing player data
def load_csv(file_path):
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logging.error(f"Error reading CSV file {file_path}: {str(e)}")
        return None

# Calculate an overall score for a player
def calculate_score(row, role_weight, league_weights):
    try:
        return (
            (row['clutch_factor'] * role_weight['clutch_factor'] +
            row['acs'] * role_weight['acs'] +
            row['kd_ratio'] * role_weight['kd_ratio'] +
            row['assist_score'] * role_weight['assist_score'] +
            row['map_awareness'] * role_weight['map_awareness'] +
            row['team_survival_trade_efficiency'] * role_weight['team_survival_trade_efficiency'] +
            row['adr'] * role_weight['adr']) * league_weights.get(row['league'], 1.0)
        )
    except Exception as e:
        logging.error(f"Error calculating score for player {row['handle']}: {str(e)}")
        return 0

# Filter players based on given criteria
def filter_players(player_data, region=None, league=None):
    filtered_data = player_data.copy()
    if region:
        if 'region_list' in region:
            filtered_data = filtered_data[filtered_data['current_region'].isin(region['region_list'])]
    if league:
        for league_name, min_count in league.items():
            league_players = filtered_data[filtered_data['league'] == league_name]
            if len(league_players) < min_count:
                logging.error(f"Not enough players from league {league_name}")
                return None
            filtered_data = pd.concat([filtered_data, league_players.head(min_count)])
    return filtered_data

# Determine role based on agent specialization
def determine_role(agent):
    duelists = ['jett', 'raze', 'reyna', 'phoenix', 'yoru', 'neon']
    sentinels = ['sage', 'killjoy', 'cypher', 'chamber']
    controllers = ['viper', 'brimstone', 'omen', 'astra', 'harbor']
    initiators = ['sova', 'breach', 'skye', 'kayo', 'fade', 'gekko']

    if agent in duelists:
        return 'Duelist'
    elif agent in sentinels:
        return 'Sentinel'
    elif agent in controllers:
        return 'Controller'
    elif agent in initiators:
        return 'Initiator'
    return None

# Assign players to specific roles
def assign_players_to_roles(filtered_data, league_weights):
    role_weights = {
        'Duelist': {'clutch_factor': 0.3, 'acs': 0.2, 'kd_ratio': 0.2, 'assist_score': 0.05, 'map_awareness': 0.05, 'team_survival_trade_efficiency': 0.1, 'adr': 0.1},
        'Sentinel': {'clutch_factor': 0.2, 'acs': 0.1, 'kd_ratio': 0.15, 'assist_score': 0.2, 'map_awareness': 0.1, 'team_survival_trade_efficiency': 0.15, 'adr': 0.1},
        'Controller': {'clutch_factor': 0.2, 'acs': 0.1, 'kd_ratio': 0.15, 'assist_score': 0.25, 'map_awareness': 0.1, 'team_survival_trade_efficiency': 0.1, 'adr': 0.1},
        'Initiator': {'clutch_factor': 0.2, 'acs': 0.1, 'kd_ratio': 0.1, 'assist_score': 0.3, 'map_awareness': 0.1, 'team_survival_trade_efficiency': 0.1, 'adr': 0.1},
        'Flex': {'clutch_factor': 0.2, 'acs': 0.15, 'kd_ratio': 0.15, 'assist_score': 0.15, 'map_awareness': 0.1, 'team_survival_trade_efficiency': 0.15, 'adr': 0.1}
    }

    roles = {'Duelist': None, 'Sentinel': None, 'Controller': None, 'Initiator': None, 'Flex': None}
    assigned_handles = set()

    for role in roles.keys():
        role_candidates = []
        for _, player in filtered_data.iterrows():
            if player['handle'] in assigned_handles:
                continue
            agent_specialization = json.loads(player['agent_specialization'])
            for agent in agent_specialization.keys():
                if determine_role(agent) == role:
                    role_candidates.append(player)
                    break

        if role_candidates:
            selected_player = max(role_candidates, key=lambda x: calculate_score(x, role_weights[role], league_weights))
            roles[role] = selected_player
            assigned_handles.add(selected_player['handle'])

    # Assign Flex role if not already assigned
    if roles['Flex'] is None:
        remaining_candidates = [player for _, player in filtered_data.iterrows() if player['handle'] not in assigned_handles]
        if remaining_candidates:
            roles['Flex'] = max(remaining_candidates, key=lambda x: calculate_score(x, role_weights['Flex'], league_weights.get(x['league'], 1.0)))
            assigned_handles.add(roles['Flex']['handle'])

    return roles

# Calculate team chemistry
def calculate_team_chemistry(team, chemistry_weight=0.2):
    chemistry_score = 0
    players = list(team.values())
    players = [player for player in players if player is not None]
    for player1, player2 in combinations(players, 2):
        if player1['nationality'] == player2['nationality']:
            chemistry_score += 2 * chemistry_weight
        elif isinstance(player2['previous_regions'], str) and (player1['current_region'] == player2['current_region'] or player1['current_region'] in json.loads(player2['previous_regions'])):
            chemistry_score += 1 * chemistry_weight
    return chemistry_score

# Form a team based on the given criteria
def form_team(player_data, region=None, league=None, specific_players=[]):
    # Filter players based on region and league
    filtered_data = filter_players(player_data, region, league)
    if filtered_data is None or len(filtered_data) < 5:
        logging.error("Not enough players to form a team")
        return None

    # Add specific players to the team
    specific_team = filtered_data[filtered_data['handle'].isin(specific_players)]
    remaining_slots = 5 - len(specific_team)

    # Get potential candidates and assign roles
    candidates = filtered_data[~filtered_data['handle'].isin(specific_players)]
    league_weights = {'vct-international': 1.3, 'vct-challengers': 1.0, 'game-changer': 0.8}
    roles = assign_players_to_roles(candidates, league_weights)

    # Fill in specific players
    for role, player in roles.items():
        if player is not None and player['handle'] not in specific_players and remaining_slots > 0:
            specific_team = pd.concat([specific_team, pd.DataFrame([player])])
            remaining_slots -= 1

    # Calculate chemistry score
    chemistry_score = calculate_team_chemistry(roles)
    print(f"Team Chemistry Score: {chemistry_score}")

    # Return the player handles of the final team with their roles
    return {role: player['handle'] for role, player in roles.items() if player is not None}

# Main function to handle the API requests
def main():
    # Load player data CSV
    player_data = load_csv('enriched_player_data.csv')
    if player_data is None:
        return

    # Example API request
    request_data = {
        "region": {
            "diversity": 3,
            "region_list": ["EU", "NA", "JP"]
        },
        "league": {
            "game-changer": 2
        },
        "player": ["Nbs", "Derke"]
    }

    # Form the team based on the request
    team = form_team(player_data)
    if team:
        print("Formed Team Player Handles:", team)
    else:
        print("Failed to form a team.")

if __name__ == '__main__':
    main()
