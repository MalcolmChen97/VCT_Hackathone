import pandas as pd
import logging
import json
import os

# Setup logging for error tracking
logging.basicConfig(filename='update_player_regions.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')


# Read the CSV file that contains existing player data
def read_player_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")
        return pd.DataFrame()


def read_league_player_tournament_data(folders):
    players_region_data = {}
    try:
        for folder in folders:
            league_path = os.path.join(folder, 'leagues.json')
            players_path = os.path.join(folder, 'players.json')
            tournaments_path = os.path.join(folder, 'tournaments.json')
            mapping_data_path = os.path.join(folder, 'mapping_data.json')

            with open(league_path, 'r') as f:
                league_data = json.load(f)
            with open(players_path, 'r') as f:
                players_data = json.load(f)
            with open(tournaments_path, 'r') as f:
                tournaments_data = json.load(f)
            with open(mapping_data_path, 'r') as f:
                mapping_data_list = json.load(f)

            league_regions = {league['league_id']: league['region'] for league in league_data}

            for mapping_data in mapping_data_list:
                participant_mapping = mapping_data['participantMapping']
                tournament_id = mapping_data['tournamentId']

                for tournament in tournaments_data:
                    if tournament['id'] == tournament_id:
                        league_id = tournament['league_id']
                        if league_id in league_regions:
                            region = league_regions[league_id]
                            for participant_id, player_id in participant_mapping.items():
                                if player_id not in players_region_data:
                                    players_region_data[player_id] = {'current_region': None, 'previous_regions': set()}

                                # Track player's participation in tournaments and regions
                                players_region_data[player_id]['previous_regions'].add(region)
                                players_region_data[player_id]['current_region'] = region

        # Convert sets to lists for JSON serialization
        for player_id, region_data in players_region_data.items():
            region_data['previous_regions'] = list(region_data['previous_regions'])

    except Exception as e:
        logging.error(f"Error reading league, player, tournament, and mapping data: {str(e)}")

    return players_region_data

# Update the player CSV with current and previous regions
def update_player_regions(player_csv_path, folders):
    try:
        player_df = read_player_csv(player_csv_path)
        if player_df.empty:
            print("No player data found in CSV.")
            return

        # Add new columns for regions if not already present
        if 'current_region' not in player_df.columns:
            player_df['current_region'] = None
        if 'previous_regions' not in player_df.columns:
            player_df['previous_regions'] = None

        # Get region data from league, player, tournament, and mapping data
        players_region_data = read_league_player_tournament_data(folders)
        print(players_region_data)
        # Update player data with region info
        for index, row in player_df.iterrows():
            player_id = str(row['player_id'])
            if player_id in players_region_data:
                print(player_id)

                player_df.at[index, 'current_region'] = players_region_data[player_id]['current_region']
                player_df.at[index, 'previous_regions'] = json.dumps(players_region_data[player_id]['previous_regions'])

        # Save the updated CSV
        player_df.to_csv('player_new_data.csv', index=False)
        print("Player regions updated successfully.")
    except Exception as e:
        logging.error(f"Error updating player regions in CSV: {str(e)}")


# Main function
def main():
    player_csv_path = 'players_data1019.csv'
    folders = ['vct-international/esports-data/', 'game-changers/esports-data/', 'vct-challengers/esports-data/']

    # Update player regions
    update_player_regions(player_csv_path, folders)


if __name__ == '__main__':
    main()
