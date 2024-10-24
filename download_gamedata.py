import requests
import json
import gzip
import shutil
import time
import os
from io import BytesIO
import re

S3_BUCKET_URL = "https://vcthackathon-data.s3.us-west-2.amazonaws.com"

LEAGUES = ["game-changers", "vct-international", "vct-challengers"]
YEARS = [2022, 2023, 2024]

def sanitize_filename(filename):
    return re.sub(r'[<>:]', '_', filename)

def download_gzip_and_write_to_json(file_name):
    sanitized_file_name = sanitize_filename(file_name)
    if os.path.isfile(f"{sanitized_file_name}.json"):
        return False

    remote_file = f"{S3_BUCKET_URL}/{file_name}.json.gz"
    response = requests.get(remote_file, stream=True)

    if response.status_code == 200:
        with gzip.open(BytesIO(response.content), 'rb') as gzipped_file:
            with open(f"{sanitized_file_name}.json", 'wb') as output_file:
                shutil.copyfileobj(gzipped_file, output_file)
            print(f"{sanitized_file_name}.json written")
        return True
    elif response.status_code == 404:
        # Ignore
        return False
    else:
        print(response)
        print(f"Failed to download {file_name}")
        return False

def download_esports_files(league):
    directory = f"{league}/esports-data"

    if not os.path.exists(directory):
        os.makedirs(directory)

    esports_data_files = ["leagues", "tournaments", "players", "teams", "mapping_data"]
    for file_name in esports_data_files:
        download_gzip_and_write_to_json(f"{directory}/{file_name}")

def download_games(league, year):
    start_time = time.time()

    local_mapping_file = f"{league}/esports-data/mapping_data.json"
    if not os.path.isfile(local_mapping_file):
        print(f"Mapping data file not found for {league}, skipping year {year}")
        return

    with open(local_mapping_file, "r") as json_file:
        mappings_data = json.load(json_file)

    local_directory = f"{league}/games/{year}"
    if not os.path.exists(local_directory):
        os.makedirs(local_directory)

    game_counter = 0

    for esports_game in mappings_data:
        s3_game_file = f"{league}/games/{year}/{esports_game['platformGameId']}"

        response = download_gzip_and_write_to_json(s3_game_file)

        if response == True:
            game_counter += 1
            if game_counter % 10 == 0:
                print(f"----- Processed {game_counter} games for {league} {year}, current run time: {round((time.time() - start_time) / 60, 2)} minutes")

def download_all_data():
    for league in LEAGUES:
        download_esports_files(league)
        for year in YEARS:
            download_games(league, year)

if __name__ == "__main__":
    download_all_data()