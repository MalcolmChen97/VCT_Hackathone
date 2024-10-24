import pandas as pd
import json
import logging

logging.basicConfig(filename='json_fix.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def clean_json_string(json_string):
    try:
        # 尝试加载JSON字符串，转换空字符串为 None
        json_data = json.loads(json_string)

        # 如果是字典，遍历每个键值对处理
        if isinstance(json_data, dict):
            cleaned_json_data = {}
            for key, value in json_data.items():
                if isinstance(value, list):
                    # 如果值是列表，替换其中的空字符串为 None
                    cleaned_value = [v if v != "" else None for v in value]
                    cleaned_json_data[key] = cleaned_value
                else:
                    cleaned_json_data[key] = value if value != "" else None
        # 如果是列表，直接处理列表中的空字符串
        elif isinstance(json_data, list):
            cleaned_json_data = [v if v != "" else None for v in json_data]
        else:
            return json_string  # 如果既不是字典也不是列表，直接返回原字符串

        return json.dumps(cleaned_json_data)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {str(e)}. String: {json_string}")
        return None

def clean_csv(input_csv_path, output_csv_path):
    try:
        df = pd.read_csv(input_csv_path)

        # 列出包含JSON字符串的列
        json_columns = ['game_play_stat', 'recent_match_result', 'latest_news', 'past_teams']

        for col in json_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: clean_json_string(x) if pd.notna(x) else None)

        # 保存为新的CSV文件
        df.to_csv(output_csv_path, index=False)
        print("CSV cleaned and saved successfully.")
    except Exception as e:
        logging.error(f"Error processing CSV: {str(e)}")

if __name__ == "__main__":
    input_csv_path = './players_data.csv'
    output_csv_path = './players_data_cleaned.csv'
    clean_csv(input_csv_path, output_csv_path)
    import pandas as pd
    import json

    # 读取清理后的CSV文件
    df = pd.read_csv('./players_data_cleaned.csv')

    # 解析JSON字段
    df['game_play_stat'] = df['game_play_stat'].apply(lambda x: json.loads(x) if pd.notna(x) else None)

    # 打印数据查看
    print(df.head())

