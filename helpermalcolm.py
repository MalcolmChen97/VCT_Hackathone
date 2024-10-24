import json

# 文件列表
json_files = [
    'vct-international/esports-data/players.json',
    'game-changers/esports-data/players.json',
    'vct-challengers/esports-data/players.json'
]

total_objects = 0

for file_path in json_files:
    with open(file_path, 'r') as file:
        data = json.load(file)  # 假设文件中的数据是一个对象列表
        total_objects += len(data)

print(f"总共有 {total_objects} 个对象。")
