import pandas as pd
import json
import logging

# Setting up logging
logging.basicConfig(filename='feature_extraction.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Load the CSV file containing player data
def load_csv(file_path):
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logging.error(f"Error reading CSV file {file_path}: {str(e)}")
        return None

# Extract features from game_play_stat and game_advanced_stats
def extract_features(row):
    try:
        # Load game_play_stat and game_advanced_stats if they are valid JSON
        game_play_stat = json.loads(row['game_play_stat']) if pd.notna(row['game_play_stat']) else {}
        advanced_stats = json.loads(row['game_advanced_stats']) if pd.notna(row['game_advanced_stats']) else {}

        # Feature 1: Performance Under Pressure (Clutch Factor)
        clutch_success = float(advanced_stats.get('clutch_success', "0").strip('%')) / 100 if 'clutch_success' in advanced_stats else 0
        clutches_won_played = advanced_stats.get('clutches', "0/0").split('/')
        clutch_factor = float(clutches_won_played[0]) / max(1, float(clutches_won_played[1])) if len(clutches_won_played) == 2 else 0

        # Feature 2: Role Versatility
        duelists = ['jett', 'raze', 'reyna', 'phoenix', 'yoru', 'neon', 'iso', 'clove']
        sentinels = ['sage', 'killjoy', 'cypher', 'chamber', 'deadlock', 'vyse']
        controllers = ['viper', 'brimstone', 'omen', 'astra', 'harbor']
        initiators = ['sova', 'breach', 'skye', 'kayo', 'fade', 'gekko']

        agent_roles = {agent: 'Duelist' for agent in duelists}
        agent_roles.update({agent: 'Sentinel' for agent in sentinels})
        agent_roles.update({agent: 'Controller' for agent in controllers})
        agent_roles.update({agent: 'Initiator' for agent in initiators})

        role_set = list(set(agent_roles.get(agent, 'Unknown') for agent in game_play_stat.keys()))
        unknown_roles = [agent for agent in game_play_stat.keys() if agent_roles.get(agent) is None]
        if unknown_roles:
            print(f"Unknown roles found: {unknown_roles}")
        role_versatility = min(len(role_set), 4)

        # Feature 3: Average Combat Score (ACS)
        acs = float(advanced_stats.get('acs', max([float(stats[3]) for stats in game_play_stat.values() if len(stats) > 3], default=0)))

        # Feature 4: Kill/Death Ratio (K/D Ratio)
        kd_ratio = float(advanced_stats.get('k_d_ratio', max([float(stats[4]) for stats in game_play_stat.values() if len(stats) > 4], default=0)))

        # Feature 5: Assist Potential (Assist Score)
        assist_potential = float(advanced_stats.get('apr', max([float(stats[8]) for stats in game_play_stat.values() if len(stats) > 8], default=0)))
        kast = float(advanced_stats.get('kast', max([float(stats[6].strip('%')) / 100 for stats in game_play_stat.values() if len(stats) > 6], default=0)))
        assist_score = (assist_potential + kast) / 2

        # Feature 6: Map Awareness (First Kill/First Death Ratio)
        fkpr = float(advanced_stats.get('fkpr', max([float(stats[9]) for stats in game_play_stat.values() if len(stats) > 9], default=0)))
        fdpr = float(advanced_stats.get('fdpr', max([float(stats[10]) for stats in game_play_stat.values() if len(stats) > 10], default=0)))
        map_awareness = fkpr / max(1, fdpr)

        # Feature 7: Team Survival and Trade Efficiency (KAST%)
        team_survival_trade_efficiency = kast

        # Feature 8: Damage Output (Average Damage per Round - ADR)
        adr = float(advanced_stats.get('adr', max([float(stats[5]) for stats in game_play_stat.values() if len(stats) > 5], default=0)))

        # Feature 9: Agent Specialization Level
        agent_specialization = {agent: int(stats[1]) for agent, stats in game_play_stat.items() if len(stats) > 1}

        return {
            'clutch_factor': clutch_factor,
            'role_versatility': role_versatility,
            'roles': json.dumps(role_set),
            'acs': acs,
            'kd_ratio': kd_ratio,
            'assist_score': assist_score,
            'map_awareness': map_awareness,
            'team_survival_trade_efficiency': team_survival_trade_efficiency,
            'adr': adr,
            'agent_specialization': json.dumps(agent_specialization)
        }
    except Exception as e:
        logging.error(f"Error extracting features for row {row['player_id']}: {str(e)}")
        return None

# Main function to create a new CSV with extracted features
def main():
    # Load player data CSV
    player_data = load_csv('player_new_data_deduplicated.csv')
    if player_data is None:
        return

    # Extract features for each player
    feature_rows = []
    for _, row in player_data.iterrows():
        features = extract_features(row)
        if features:
            feature_row = row.to_dict()
            feature_row.update(features)
            feature_rows.append(feature_row)

    # Create a new DataFrame with the extracted features
    enriched_data = pd.DataFrame(feature_rows)

    # Drop old game_play_stat and game_advanced_stats columns
    enriched_data = enriched_data.drop(columns=['game_play_stat', 'game_advanced_stats'])

    # Save the new enriched CSV
    try:
        enriched_data.to_csv('enriched_player_data.csv', index=False)
    except Exception as e:
        logging.error(f"Error saving enriched CSV file: {str(e)}")

if __name__ == '__main__':
    main()
