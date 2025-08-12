import os
import base64
import requests
import csv
from volcenginesdkarkruntime import Ark

def image_to_base64(image_path):
    """将本地图片转换为API要求的Base64格式字符串"""
    # 获取图片格式（小写）
    ext = os.path.splitext(image_path)[1].lower().lstrip('.')
    if ext not in ['jpeg', 'png']:
        raise ValueError("图片格式必须是jpeg或png")
    
    # 读取图片并转换为Base64
    with open(image_path, 'rb') as f:
        image_data = f.read()
        base64_str = base64.b64encode(image_data).decode('utf-8')
    
    # 按照API要求的格式返回
    return f"data:image/{ext};base64,{base64_str}"

def save_image_from_url(image_url, save_path):
    """从图片URL下载并保存到本地"""
    try:
        # 发送请求获取图片数据
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()  # 检查请求是否成功
        
        # 确保保存目录存在
        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 写入文件
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"图片已保存至：{save_path}")
    except Exception as e:
        print(f"保存图片失败：{e}")

def process_tasks_from_csv(csv_path):
    """从CSV文件读取任务并处理符合条件的任务"""
    # 初始化Ark客户端
    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=os.environ.get("ARK_API_KEY"),
    )
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_path):
        print(f"错误：CSV文件 '{csv_path}' 不存在")
        return
    
    # 读取CSV并处理任务
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)  # 使用字典读取，便于获取列值
        for row in reader:
            try:
                # 提取任务信息（处理可能的空值）
                task_index = row.get('index', '未知索引')
                task_type = row.get('task_type', '').strip().lower()  # 统一转为小写处理
                prompt = row.get('prompt', '').strip()
                ori_image = row.get('ori_image', '').strip()
                
                # 输出当前任务信息
                print(f"\n===== 开始处理任务 {task_index} =====")
                print(f"任务索引：{task_index}")
                print(f"任务类型：{task_type}")
                print(f"提示词：{prompt}")
                
                # 根据任务类型处理
                if task_type in ['tie', 'vttie']:
                    # 处理图像编辑任务
                    
                    # 检查ori_image是否存在
                    if not ori_image:
                        print(f"跳过任务 {task_index}（ori_image为空，无原始图片）")
                        continue
                    
                    # 构建原始图片路径：data\imgs\{ori_image}
                    local_image_path = os.path.join("data", "imgs", ori_image)
                    if not os.path.exists(local_image_path):
                        print(f"跳过任务 {task_index}（原始图片不存在：{local_image_path}）")
                        continue
                    
                    # 转换本地图片为Base64
                    image_base64 = image_to_base64(local_image_path)
                    
                    # 构建保存路径：imgs\{任务索引}（保留原图片扩展名）
                    ext = os.path.splitext(ori_image)[1]  # 获取原始图片扩展名
                    save_image_path = os.path.join("imgs", f"{task_index}{ext}")
                    
                    # 调用图像编辑模型
                    imagesResponse = client.images.generate(
                        model="ep-20250810215112-2r7w4",
                        prompt=prompt,  # 使用当前任务的prompt
                        image=image_base64,
                        seed=123,
                        guidance_scale=5.5,
                        size="adaptive",
                        watermark=True 
                    )

                elif task_type == 't2i':
                    # 处理文本生成图像任务
                    
                    # 构建保存路径：imgs\{任务索引}.png（t2i默认使用png格式）
                    save_image_path = os.path.join("imgs", f"{task_index}.png")
                    
                    # 调用文本生成图像模型
                    imagesResponse = client.images.generate(
                        model="ep-20250811010554-qn4cd",
                        prompt=prompt,
                        size="512x512",
                        guidance_scale=2.5,
                        seed=12345,
                        watermark=True
                    )
                
                else:
                    # 不处理其他类型任务
                    print(f"跳过任务 {task_index}（不支持的任务类型）")
                    continue
                
                # 获取生成图片的URL并保存
                generated_image_url = imagesResponse.data[0].url
                print(f"生成图片URL：{generated_image_url}")
                save_image_from_url(generated_image_url, save_image_path)
                
                print(f"任务 {task_index} 处理完成")
                
            except Exception as e:
                print(f"任务 {task_index} 处理失败：{str(e)}")
    
    print("\n所有任务处理完毕")

if __name__ == "__main__":
    # 处理task.csv中的任务（假设csv文件与程序同目录）
    process_tasks_from_csv(r"data\task.csv")
