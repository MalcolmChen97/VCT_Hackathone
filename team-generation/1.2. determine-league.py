import json
from datetime import datetime

# Load players data from different league files
def load_players_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

game_changers_data = load_players_data("../game-changers/esports-data/players.json")
vct_challengers_data = load_players_data("../vct-challengers/esports-data/players.json")
vct_international_data = load_players_data("../vct-international/esports-data/players.json")

# Combine players data from all league files
league_files = [
    ("game-changers", game_changers_data),
    ("vct-challengers", vct_challengers_data),
    ("vct-international", vct_international_data),
]

# Create a dictionary to store the latest league information for each player
latest_player_leagues = {}

for league_name, league_data in league_files:
    for player in league_data:
        player_id = player["id"]
        updated_at = datetime.strptime(player["updated_at"], "%Y-%m-%dT%H:%M:%SZ")

        if player_id not in latest_player_leagues or updated_at > latest_player_leagues[player_id]["updated_at"]:
            latest_player_leagues[player_id] = {
                "league": league_name,
                "updated_at": updated_at,
            }

# Load the current player_enriched JSON data
with open("preprocessed_players(before determine league).json", "r") as file:
    player_enriched_data = json.load(file)

# Update the league information for each player
for player in player_enriched_data:
    player_id = player["player_id"]
    if player_id in latest_player_leagues:
        player["league"] = latest_player_leagues[player_id]["league"]

# Save the updated player_enriched JSON data
with open("preprocessed_players.json", "w") as file:
    json.dump(player_enriched_data, file, indent=4)

print("Player league information updated successfully.")