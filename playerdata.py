import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging

# 设置日志记录，便于调试和查看错误信息
logging.basicConfig(filename='player_scraper.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')


# 读取三个不同category的player.json
def read_player_json(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")
        return []


# 通过player handle进行搜索，获取player id
def get_player_id(handle):
    try:
        search_url = f"https://www.vlr.gg/search/auto/?term={handle}"
        response = requests.get(search_url)
        response.raise_for_status()  # 检查请求是否成功

        search_results = response.json()
        for result in search_results:
            if result.get('type') == 'player' and handle.lower() in result.get('name', '').lower():
                # 提取link，形如 '/player/14313/raina'
                return result.get('link')
    except requests.RequestException as req_err:
        logging.error(f"Network error during player ID fetch for {handle}: {str(req_err)}")
    except Exception as e:
        logging.error(f"Error fetching player ID for {handle}: {str(e)}")
    return None


# 解析player页面，获取game play stat, recent match result, latest news
def fetch_player_data(player_id):
    try:
        url = f"https://www.vlr.gg{player_id}/?timespan=all"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Get Agents Gameplay Statistics
        game_play_stat = {}
        table = soup.find('table', class_='wf-table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cells = row.find_all('td')
                if len(cells) > 0:
                    agent = cells[0].find('img')['alt'] if cells[0].find('img') else 'Unknown'
                    stats = [cell.text.strip() for cell in cells[1:]]
                    game_play_stat[agent] = stats

        # Get Recent Results (up to 5 matches)
        recent_match_results = []
        recent_results_section = soup.find('h2', string=lambda text: 'recent results' in text.lower() if text else False)
        if recent_results_section:
            recent_matches = recent_results_section.find_next('div').find_all('a', class_='wf-card fc-flex m-item')
            for match in recent_matches[:5]:
                match_date = match.find('div', class_='m-item-date').text.strip().replace('\t', '').replace('\n',
                                                                                                            '').strip()
                match_title = match.find('div', class_='m-item-event').text.strip().replace('\t', '').replace('\n',
                                                                                                              '').strip()
                match_url = 'https://www.vlr.gg' + match['href']
                recent_match_results.append({
                    'date': match_date,
                    'title': match_title,
                    'url': match_url
                })

        # Get Latest News (if available)
        latest_news = []
        news_section = soup.find('h2', string=lambda text: 'latest news' in text.lower() if text else False)
        if news_section:
            news_items = news_section.find_next('div').find_all('a', class_='wf-module-item')
            for news_item in news_items:
                news_title = news_item.find('div',
                                            style='font-weight: 500; margin-top: 4px; line-height: 1.4;').text.strip()
                news_time = news_item.find('div', class_='ge-text-light').text.strip()
                news_url = 'https://www.vlr.gg' + news_item['href']
                latest_news.append({
                    'title': news_title,
                    'time': news_time,
                    'url': news_url
                })

        # Get Nationality
        nationality = None
        nationality_section = soup.find('div', class_='ge-text-light',
                                        style='font-size: 11px; padding-bottom: 5px; margin-top: 12px;')
        if nationality_section:
            nationality = nationality_section.text.strip()

        # Get Past Teams
        past_teams = []
        past_teams_section = soup.find('h2', string=lambda text: 'past teams' in text.lower() if text else False)
        if past_teams_section:
            team_cards = past_teams_section.find_next('div', class_='wf-card').find_all('a',
                                                                                        class_='wf-module-item')
            for team_card in team_cards:
                team_name = team_card.find('div', style='font-weight: 500;').text.strip()
                team_period = team_card.find_all('div', class_='ge-text-light')[-1].text.strip()
                past_teams.append({
                    'team_name': team_name,
                    'period': team_period
                })

        return (game_play_stat if game_play_stat else None,
                recent_match_results if recent_match_results else None,
                latest_news if latest_news else None,
                nationality if nationality else None,
                past_teams if past_teams else None)
    except requests.RequestException as req_err:
        logging.error(f"Network error during player data fetch for ID {player_id}: {str(req_err)}")
    except Exception as e:
        logging.error(f"Error fetching player data for ID {player_id}: {str(e)}")
    return None, None, None


# 将数据保存为CSV文件
def save_to_csv(players_data, output_file):
    try:
        df = pd.DataFrame(players_data)
        df.to_csv(output_file, index=False)
    except Exception as e:
        logging.error(f"Error saving data to {output_file}: {str(e)}")


# 主函数：从不同category的player.json提取信息，爬取数据并保存为CSV
def main():
    json_files = ['vct-international/esports-data/players.json', 'game-changers/esports-data/players.json', 'vct-challengers/esports-data/players.json']
    players_data = []
    rate_limit = 10  # Limit to 10 requests per second
    time_between_requests = 1 / rate_limit
    total_players = sum(len(read_player_json(json_file)) for json_file in json_files)
    players_fetched = 0

    for json_file in json_files:
        league = json_file.split('/')[0]  # 从文件路径中提取league名称
        players = read_player_json(json_file)

        for player in players:
            handle = player.get('handle')  # 获取玩家的handle
            if not handle:
                logging.error(f"No handle found for player in file {json_file}. Skipping player.")
                continue

            player_id = get_player_id(handle)

            if player_id:
                game_play_stat, recent_match_results, latest_news, nationality, past_teams = fetch_player_data(
                    player_id)

                # Save the data, fill None if not available
                player_entry = {
                    'player_id': player.get('id'),
                    'handle': handle,
                    'league': league,
                    'game_play_stat': json.dumps(game_play_stat) if game_play_stat else None,
                    'recent_match_result': json.dumps(recent_match_results) if recent_match_results else None,
                    'latest_news': json.dumps(latest_news) if latest_news else None,
                    'nationality': nationality,
                    'past_teams': json.dumps(past_teams) if past_teams else None
                }
                players_data.append(player_entry)

            else:
                # If player link is not found, save basic info with other fields as None
                player_entry = {
                    'player_id': player.get('id'),
                    'handle': handle,
                    'league': league,
                    'game_play_stat': None,
                    'recent_match_result': None,
                    'latest_news': None,
                    'nationality': None,
                    'past_teams': None
                }
                players_data.append(player_entry)

            # time.sleep(time_between_requests)  # 等待以避免频繁请求
            players_fetched += 1
            print(f"Finished {players_fetched}/{total_players}")

    # 保存数据到CSV
    save_to_csv(players_data, 'players_data1019.csv')


if __name__ == '__main__':
    main()

