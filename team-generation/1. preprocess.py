import csv
import json

# Agent to Role Mapping
agent_role_mapping = {
    'jett': 'Duelist', 'raze': 'Duelist', 'reyna': 'Duelist', 'phoenix': 'Duelist',
    'yoru': 'Duelist', 'neon': 'Duelist', 'iso': 'Duelist', 'clove': 'Duelist',
    'sage': 'Sentinel', 'killjoy': 'Sentinel', 'cypher': 'Sentinel', 'chamber': 'Sentinel',
    'deadlock': 'Sentinel', 'vyse': 'Sentinel',
    'viper': 'Controller', 'brimstone': 'Controller', 'omen': 'Controller',
    'astra': 'Controller', 'harbor': 'Controller',
    'sova': 'Initiator', 'breach': 'Initiator', 'skye': 'Initiator',
    'kayo': 'Initiator', 'fade': 'Initiator', 'gekko': 'Initiator'
}

def load_and_preprocess_players(file_path):
    players = []
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Handle null fields
            for key, value in row.items():
                if value == '':
                    row[key] = None
            # Parse JSON fields
            if row['roles']:
                row['roles'] = json.loads(row['roles'])
            else:
                row['roles'] = []
            if row['agent_specialization']:
                row['agent_specialization'] = json.loads(row['agent_specialization'])
            else:
                row['agent_specialization'] = {}
            if row['past_teams']:
                row['past_teams'] = json.loads(row['past_teams'])
            else:
                row['past_teams'] = []
            if row['previous_regions']:
                row['previous_regions'] = json.loads(row['previous_regions'])
            else:
                row['previous_regions'] = []
            # Convert numerical fields to floats
            numerical_fields = ['acs', 'kd_ratio', 'assist_score', 'map_awareness',
                                'team_survival_trade_efficiency', 'adr', 'clutch_factor']
            for field in numerical_fields:
                if row[field]:
                    row[field] = float(row[field])
                else:
                    row[field] = 0.0
            players.append(row)
    return players

def determine_player_roles(players):
    for player in players:
        agent_usage = player['agent_specialization']
        role_counts = {'Duelist': 0, 'Initiator': 0, 'Controller': 0, 'Sentinel': 0}
        for agent, usage in agent_usage.items():
            role = agent_role_mapping.get(agent.lower())
            if role:
                role_counts[role] += int(usage)
        # Sort roles by usage
        sorted_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
        player['roles'] = [role for role, count in sorted_roles if count > 0]
    return players

def save_preprocessed_data(players, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(players, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    input_csv = '../preprocessing/enriched_player_data.csv'  # Replace with your actual CSV file path
    output_json = 'preprocessed_players(before determine league).json'
    players = load_and_preprocess_players(input_csv)
    players = determine_player_roles(players)
    save_preprocessed_data(players, output_json)
    print(f"Preprocessed data saved to {output_json}")
