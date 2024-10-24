import json
import requests
from bs4 import BeautifulSoup

# 加载现有的JSON文件
with open('preprocessed_players(before determine league).json', 'r') as file:
    data = json.load(file)


# 定义函数从页面提取比赛数据
def extract_match_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:

        # 提取赛事名称
        event_name = soup.find('a', class_='match-header-event').findNext('div', style='font-weight: 700;').get_text(strip=True)
        event_series = soup.find('div', class_='match-header-event-series').get_text(strip=True)

        # 提取队伍名
        team_a = soup.find('a', class_='match-header-link wf-link-hover mod-1').findNext('div', class_='wf-title-med').get_text(strip=True)
        team_b = soup.find('a', class_='match-header-link wf-link-hover mod-2').findNext('div', class_='wf-title-med').get_text(strip=True)

        # 提取比分
        score_winner = soup.find('span', class_='match-header-vs-score-winner').get_text(strip=True)
        score_loser = soup.find('span', class_='match-header-vs-score-loser').get_text(strip=True)

        # 提取比赛结果和类型
        match_note = soup.find_all('div', class_='match-header-vs-note')[0].get_text(strip=True)
        match_type = soup.find_all('div', class_='match-header-vs-note')[1].get_text(strip=True)

        # 提取比赛日期和时间
        match_date = soup.find('div', {'data-moment-format': 'dddd, MMMM Do'}).get_text(strip=True)
        match_time = soup.find('div', {'data-moment-format': 'h:mm A z'}).get_text(strip=True)

        # 构建结果对象
        match_data = {
            "title": f"{team_a} vs {team_b} ({match_note}, {match_type})",
            "result": {team_a: int(score_loser), team_b: int(score_winner)},
            "date": match_date,
            "time": match_time,
            "event": f"{event_name} - {event_series}"
        }
        print(match_data)

        return match_data
    except Exception as e:
        print(f"Error processing URL {url}: {e}")
        match_data = {
            "title": None,
            "result": {"team_a": None, "team_b": None},
            "date": None,
            "time": None,
            "event": None
        }

    return match_data

# 遍历JSON文件中的数据
for player in data:
    if 'recent_match_result' in player and player['recent_match_result']:
        try:
            # 将 JSON 字符串解析为对象
            recent_matches = json.loads(player['recent_match_result'])
            # 遍历所有recent_match_result中的比赛链接
            for match in recent_matches:
                if 'url' in match:
                    match_info = extract_match_data(match['url'])
                    # 更新当前比赛的结果
                    match.update(match_info)
            # 将更新后的对象重新转换为字符串存储回去
            player['recent_match_result'] = json.dumps(recent_matches)
        except json.JSONDecodeError:
            continue


# 保存更新后的JSON数据
with open('preprocessed_players(before determine league).json', 'w') as file:
    json.dump(data, file, indent=4)

