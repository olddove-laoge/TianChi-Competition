from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath, Path
import requests
from dashscope import ImageSynthesis
import os
import csv

API_KEY = os.getenv('DASHSCOPE_API_KEY', 'sk-90893d33219e4b4b83cb80e96ab744f5')

# 确保imgs目录存在
os.makedirs('data/imgs', exist_ok=True)

try:
    with open('data/task.csv', 'r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        
        for row in reader:
            if len(row) >= 3 and row[1] == "t2i" and row[0] == '83':
                task_index = row[0]  # 补零到3位，如001
                prompt = row[2]
                
                if not prompt:
                    continue
                
                
                print(f'----处理第{task_index}条记录----')
                print(f'当前任务: {prompt}')
                try:
                    rsp = ImageSynthesis.call(
                        api_key=API_KEY,
                        model="wan2.2-t2i-flash",
                        prompt=prompt,
                        n=1,
                        size='1024*1024'
                    )
                    
                    if rsp.status_code == HTTPStatus.OK:
                        for i, result in enumerate(rsp.output.results):
                            # 构建保存路径：data/imgs/001_0.jpg
                            save_path = Path(f'imgs/{task_index}.jpg')
                            
                            # 下载并保存图片
                            with open(save_path, 'wb+') as img_file:
                                img_file.write(requests.get(result.url).content)
                            print(f'图片已保存至: {save_path}')
                    else:
                        print(f'生成失败: 状态码{rsp.status_code}, 错误: {rsp.message}')
                
                except Exception as api_error:
                    print(f'API调用出错: {str(api_error)}')

except FileNotFoundError:
    print("错误：CSV文件未找到")
except Exception as e:
    print(f"处理CSV文件时出错: {str(e)}")