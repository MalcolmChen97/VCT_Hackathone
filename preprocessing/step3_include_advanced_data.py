import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import json

# Setup logging for error tracking
logging.basicConfig(filename='game_advanced_stats.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')


# Read the CSV file that contains existing player data
def read_player_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        print("reading")
        print(df.iloc[1])
        return df
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")
        return pd.DataFrame()


# Fetch the advanced stats for players from the vlr.gg stats page
def fetch_game_advanced_stats():
    try:
        url = "https://www.vlr.gg/stats/?event_group_id=all&event_id=all&region=all&min_rounds=0&min_rating=1550&agent=all&map_id=all&timespan=90d"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Parse the stats table
        stats_table = soup.find('table', class_='wf-table')
        if not stats_table:
            logging.error("Could not find the stats table on the page.")
            return {}

        players_stats = {}
        rows = stats_table.find('tbody').find_all('tr')  # Get rows from tbody
        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 0:
                handle = cells[0].find('div', class_='text-of').text.strip()
                stats = {
                    'agents_played': ', '.join(
                        [img['src'].split('/')[-1].replace('.png', '') for img in cells[1].find_all('img')]),
                    'rnd': cells[2].text.strip(),
                    'rating': cells[3].find('span').text.strip() if cells[3].find('span') else cells[3].text.strip(),
                    'acs': cells[4].find('span').text.strip() if cells[4].find('span') else cells[4].text.strip(),
                    'k_d_ratio': cells[5].find('span').text.strip() if cells[5].find('span') else cells[5].text.strip(),
                    'kast': cells[6].find('span').text.strip() if cells[6].find('span') else cells[6].text.strip(),
                    'adr': cells[7].find('span').text.strip() if cells[7].find('span') else cells[7].text.strip(),
                    'kpr': cells[8].find('span').text.strip() if cells[8].find('span') else cells[8].text.strip(),
                    'apr': cells[9].find('span').text.strip() if cells[9].find('span') else cells[9].text.strip(),
                    'fkpr': cells[10].find('span').text.strip() if cells[10].find('span') else cells[10].text.strip(),
                    'fdpr': cells[11].find('span').text.strip() if cells[11].find('span') else cells[11].text.strip(),
                    'hs_percentage': cells[12].find('span').text.strip() if cells[12].find('span') else cells[
                        12].text.strip(),
                    'clutch_success': cells[13].find('span').text.strip() if cells[13].find('span') else cells[
                        13].text.strip(),
                    'clutches': cells[14].text.strip(),
                    'kmax': cells[15].text.strip(),
                    'kills': cells[16].text.strip(),
                    'deaths': cells[17].text.strip(),
                    'assists': cells[18].text.strip(),
                    'first_kills': cells[19].text.strip(),
                    'first_deaths': cells[20].text.strip()
                }
                players_stats[handle] = stats
        return players_stats
    except requests.RequestException as req_err:
        logging.error(f"Network error while fetching game advanced stats: {str(req_err)}")
    except Exception as e:
        logging.error(f"Error fetching game advanced stats: {str(e)}")
    return {}

# Update the existing player CSV file with the advanced stats
def update_player_csv(player_csv_path, players_stats):
    try:
        player_df = read_player_csv(player_csv_path)
        if player_df.empty:
            print("No player data found in CSV.")
            return

        # Add a new column for the advanced stats if not already present
        if 'game_advanced_stats' not in player_df.columns:
            player_df['game_advanced_stats'] = None

        # Update player data with advanced stats
        for index, row in player_df.iterrows():
            handle = row['handle']
            if handle in players_stats:
                player_df.at[index, 'game_advanced_stats'] = json.dumps(players_stats[handle])
            else:
                # Fill stats with None if not found in advanced stats
                if pd.isna(player_df.at[index, 'game_advanced_stats']):
                    player_df.at[index, 'game_advanced_stats'] = json.dumps(None)

        # Save the updated CSV
        player_df.to_csv("players_data1019.csv", index=False)
        print("Player data updated successfully.")
    except Exception as e:
        logging.error(f"Error updating player CSV: {str(e)}")


# Main function
def main():
    player_csv_path = 'players_data_cleaned.csv'
    players_stats = fetch_game_advanced_stats()
    if players_stats:
        update_player_csv(player_csv_path, players_stats)
    else:
        print("No advanced stats fetched.")


if __name__ == '__main__':
    main()
