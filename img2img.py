import base64
import os
import csv
from http import HTTPStatus
from dashscope import ImageSynthesis
import mimetypes
import requests
import uuid
from datetime import datetime
import time
from PIL import Image  # 用于图像处理

# --- 准备工作：确保 API Key 已设置 ---
api_key = os.getenv('DASHSCOPE_API_KEY', 'sk-90893d33219e4b4b83cb80e96ab744f5')

# --- 下载并保存图片 ---
def save_image_from_url(url, save_dir="./output", filename=None):
    """从URL下载图片并保存到本地"""
    os.makedirs(save_dir, exist_ok=True)
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        filename = f"generated_image_{timestamp}_{unique_id}.png"
    
    save_path = os.path.join(save_dir, filename)
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ 图片已保存至: {save_path}")
        return save_path
    else:
        print(f"❌ 下载失败，状态码: {response.status_code}")
        return None

# --- 新增函数：调整图片尺寸 ---
def resize_image_to_valid_dimensions(image_path, min_size=512, max_size=4096):
    """
    调整图片尺寸使其在指定范围内（512-4096像素）
    返回调整后的图片路径
    """
    try:
        # 打开原始图片
        img = Image.open(image_path)
        width, height = img.size
        
        print(f"原始图片尺寸: {width}x{height}")
        
        # 检查尺寸是否在有效范围内
        if min(width, height) >= min_size and max(width, height) <= max_size:
            print("图片尺寸在有效范围内 (512-4096像素)，无需调整")
            return image_path
        
        # 计算调整比例
        ratio = 1.0
        
        # 如果图片太小，放大到最小尺寸
        if min(width, height) < min_size:
            ratio = max(min_size / min(width, height), min_size / max(width, height))
            print(f"图片太小，需要放大 {ratio:.2f} 倍")
        
        # 如果图片太大，缩小到最大尺寸
        if max(width, height) > max_size:
            ratio = min(ratio, max_size / max(width, height)) if ratio > 1 else max_size / max(width, height)
            print(f"图片太大，需要缩小 {ratio:.2f} 倍")
        
        # 计算新尺寸
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # 确保新尺寸在有效范围内
        new_width = max(min(new_width, max_size), min_size)
        new_height = max(min(new_height, max_size), min_size)
        
        print(f"调整后尺寸: {new_width}x{new_height}")
        
        # 调整图片尺寸
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 创建临时目录保存调整后的图片
        temp_dir = "./temp_imgs"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 生成唯一文件名
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        temp_path = os.path.join(temp_dir, f"{name}_resized{ext}")
        
        # 保存调整后的图片
        resized_img.save(temp_path)
        print(f"调整后的图片已保存至: {temp_path}")
        
        return temp_path
    
    except Exception as e:
        print(f"调整图片尺寸时出错: {str(e)}")
        return None

def process_task(row):
    """处理单个任务"""
    # 修复：正确处理可能的BOM字段名
    task_id = row.get('index') or row.get('\ufeffindex') or 'unknown'
    
    print(f"\n正在处理任务 {task_id}: {row['prompt']}")
    
    try:
        # 获取原始图片路径
        img_path = os.path.abspath(f'./data/imgs/{row["ori_image"]}')
        
        # 调整图片尺寸并获取调整后的图片路径
        resized_img_path = resize_image_to_valid_dimensions(img_path)
        if resized_img_path is None:
            print("❌ 无法调整图片尺寸，跳过此任务")
            return None
        
        # 使用调整后的图片路径构建URL
        base_image_url = "file://" + resized_img_path
        print(f'使用图片: {base_image_url}')
        
        # 调用API - 使用base_image_url参数传递文件路径
        rsp = ImageSynthesis.call(
            api_key=api_key,
            model="wanx2.1-imageedit",
            function="description_edit",
            prompt=row['prompt'],
            base_image_url=base_image_url,  # 使用文件路径
            n=1
        )
        
        # 检查API响应状态
        if rsp.status_code != HTTPStatus.OK:
            print(f'❌ API调用失败，状态码: {rsp.status_code}, 错误信息: {rsp.message}')
            return None
        
        # 处理生成结果
        results = rsp.output.results
        if not results:
            print("⚠️ 未生成任何图片")
            return None
        
        print(f"🎉 成功生成 {len(results)} 张图片")
        
        # 保存图片
        saved_files = []
        for i, result in enumerate(results, 1):
            print(f"图片 {i} URL: {result.url}")
            saved_path = save_image_from_url(
                result.url,
                save_dir="./imgs",
                filename=f"{task_id}.jpg"  # 使用任务ID作为文件名
            )
            if saved_path:
                saved_files.append(saved_path)
        
        return saved_files
        
    except Exception as e:
        print(f"处理任务 {task_id} 时出错: {str(e)}")
        return None

def main():
    # 修复：使用utf-8-sig编码读取CSV文件，处理BOM问题
    tasks = []
    with open('./data/task.csv', 'r', encoding='utf-8-sig') as f:  # 使用utf-8-sig处理BOM
        reader = csv.DictReader(f)
        # 打印字段名用于调试
        print(f"CSV字段: {reader.fieldnames}")
        
        for row in reader:
            if row.get('task_type') in ('tie', 'vttie') and row.get('ori_image'):
                tasks.append(row)

    print(f"找到 {len(tasks)} 个有效任务")
    
    # 处理每个任务
    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*50}")
        print(f"处理任务 {i}/{len(tasks)}")
        result = process_task(task)
        
        # 添加延迟以避免API速率限制
        if i < len(tasks):
            print("等待3秒后继续下一个任务...")
            time.sleep(3)

if __name__ == '__main__':
    # 确保安装Pillow库：pip install Pillow
    main()