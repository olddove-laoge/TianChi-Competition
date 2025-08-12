import os
from PIL import Image
import shutil

def convert_png_to_jpg(input_dir, output_dir):
    """
    将输入文件夹中的所有PNG图片转换为JPG格式并保存到输出文件夹
    
    参数:
        input_dir: 包含PNG图片的输入文件夹路径
        output_dir: 保存转换后JPG图片的输出文件夹路径
    """
    # 检查输入文件夹是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入文件夹 '{input_dir}' 不存在")
        return
    
    # 创建输出文件夹（如果不存在）
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_dir):
        # 检查文件是否为PNG格式
        if filename.lower().endswith('.png'):
            # 构建完整的文件路径
            input_path = os.path.join(input_dir, filename)
            
            # 检查是否为文件（不是文件夹）
            if not os.path.isfile(input_path):
                continue
            
            try:
                # 打开PNG图片
                with Image.open(input_path) as img:
                    # 如果图片有alpha通道（透明层），需要处理
                    if img.mode in ('RGBA', 'LA'):
                        # 创建一个白色背景
                        background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                        background.paste(img, img.split()[-1])
                        img = background
                    elif img.mode == 'P':
                        # 处理调色板模式的图片
                        img = img.convert('RGB')
                    
                    # 构建输出文件名和路径（替换扩展名）
                    base_name = os.path.splitext(filename)[0]
                    output_filename = f"{base_name}.jpg"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # 保存为JPG格式，质量设为95
                    img.save(output_path, 'JPEG', quality=95)
                    print(f"已转换: {filename} -> {output_filename}")
            
            except Exception as e:
                print(f"转换文件 '{filename}' 时出错: {str(e)}")
    
    print("转换完成！")

if __name__ == "__main__":
    # 输入文件夹路径（请根据实际情况修改）
    input_folder = "imgs"
    # 输出文件夹路径（请根据实际情况修改）
    output_folder = "./jpg_images"
    
    # 调用转换函数
    convert_png_to_jpg(input_folder, output_folder)
