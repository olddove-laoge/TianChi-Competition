import os
from PIL import Image

def convert_jpg_to_png(folder_path):
    """
    将指定文件夹中的所有JPG/JPEG文件转换为PNG格式
    
    参数:
        folder_path: 包含JPG文件的文件夹路径
    """
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 文件夹 '{folder_path}' 不存在")
        return
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 检查文件是否为JPG/JPEG格式
        if filename.lower().endswith(('.jpg', '.jpeg')):
            # 构建完整的文件路径
            jpg_path = os.path.join(folder_path, filename)
            
            # 检查是否为文件（不是文件夹）
            if not os.path.isfile(jpg_path):
                continue
            
            # 创建新的文件名（替换扩展名）
            base_name = os.path.splitext(filename)[0]
            png_filename = f"{base_name}.png"
            png_path = os.path.join(folder_path, png_filename)
            
            # 检查PNG文件是否已存在
            if os.path.exists(png_path):
                print(f"已跳过: {png_filename} 已存在")
                continue
            
            try:
                # 打开JPG文件并转换为PNG
                with Image.open(jpg_path) as img:
                    # 如果图片有Alpha通道，转换为RGBA模式
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                        background.paste(img, img.split()[-1])
                        img = background
                    
                    # 保存为PNG格式
                    img.save(png_path, 'PNG')
                    print(f"已转换: {filename} -> {png_filename}")
            except Exception as e:
                print(f"转换失败 {filename}: {str(e)}")

if __name__ == "__main__":
    # 在这里指定要处理的文件夹路径
    target_folder = r"data\imgs"  # 可以替换为你的文件夹路径，例如 "C:/photos"
    
    # 调用转换函数
    convert_jpg_to_png(target_folder)
    print("转换完成!")
    