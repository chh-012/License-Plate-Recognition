#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车牌识别系统 - 简化版主程序
功能：自动识别图片/视频中的车牌号码和颜色
作者：AI Assistant
版本：2.2
"""

import os
import sys
import yaml
import argparse
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.plate_detector import PlateDetector
from core.utils import print_banner, check_environment


def load_config(config_path='config.yaml'):
    """加载配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def select_folder(title="选择文件夹"):
    """弹出文件夹选择对话框"""
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    folder_path = filedialog.askdirectory(title=title)
    root.destroy()
    
    return folder_path


def select_file(title="选择文件", filetypes=None):
    """弹出文件选择对话框"""
    import tkinter as tk
    from tkinter import filedialog
    
    if filetypes is None:
        filetypes = [
            ("图片文件", "*.jpg *.jpeg *.png *.bmp"),
            ("视频文件", "*.mp4 *.avi *.mov *.mkv"),
            ("所有文件", "*.*")
        ]
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    
    return file_path


def recognize_single_file(detector, file_path, output_dir):
    """识别单张图片或视频"""
    ext = os.path.splitext(file_path)[1].lower()
    image_exts = ['.jpg', '.jpeg', '.png', '.bmp']
    video_exts = ['.mp4', '.avi', '.mov', '.mkv']
    
    if ext in image_exts:
        print("正在识别图片...")
        result = detector.recognize_image(file_path)
        if result:
            print(f"\n识别结果: {result}")
            print(f"结果已保存到: {output_dir}")
        else:
            print("未识别到车牌")
            
    elif ext in video_exts:
        print("正在处理视频，请耐心等待...")
        import cv2
        import copy
        
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            print("✗ 无法打开视频文件")
            return
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        output_path = os.path.join(output_dir, 'result_' + os.path.basename(file_path))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        all_plates = []
        start = time.time()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            
            frame_ori = frame.copy()
            try:
                result_list = detector._detect_and_recognize(frame, frame_ori)
                result_frame, _ = detector._draw_result(frame, result_list)
                for r in result_list:
                    all_plates.append(str(r['plate_no']))
            except Exception:
                result_frame = frame
            
            writer.write(result_frame)
            frame_count += 1
            
            if frame_count % 30 == 0:
                print(f"  处理进度: {frame_count}/{total_frames} 帧")
        
        cap.release()
        writer.release()
        
        elapsed = time.time() - start
        unique_plates = list(set(all_plates))
        
        print(f"\n视频处理完成!")
        print(f"  总帧数: {total_frames}")
        print(f"  处理耗时: {elapsed:.2f} 秒")
        print(f"  识别到的车牌: {', '.join(unique_plates) if unique_plates else '无'}")
        print(f"  结果保存到: {output_path}")
    else:
        print(f"✗ 不支持的文件格式: {ext}")


def batch_recognize_folder(detector, input_dir, output_dir):
    """批量识别文件夹"""
    print(f"\n开始批量识别...")
    print(f"输入路径: {input_dir}")
    print(f"输出路径: {output_dir}\n")
    
    stats = detector.batch_recognize(input_dir, output_dir)
    print_stats(stats)


def print_stats(stats):
    """打印统计结果"""
    print("\n" + "="*50)
    print("识别完成!")
    print("="*50)
    print(f"图片文件: {stats['images']} 个")
    print(f"视频文件: {stats['videos']} 个")
    print(f"成功识别: {stats['success']} 个")
    print(f"识别失败: {stats['failed']} 个")
    print(f"总耗时: {stats['total_time']:.2f} 秒")
    if stats['success'] > 0:
        print(f"平均耗时: {stats['total_time']/stats['success']:.2f} 秒/个")
    print("="*50)


def interactive_mode(detector, output_dir):
    """交互模式：循环选择，直到用户退出"""
    while True:
        print("\n" + "-"*50)
        print("请选择要识别的文件或文件夹...")
        print("\n选择模式:")
        print("  1 - 选择单张图片/视频")
        print("  2 - 选择文件夹（批量识别）")
        print("  0 - 退出")
        
        try:
            choice = input("\n请输入选项 (0/1/2): ").strip()
        except KeyboardInterrupt:
            print("\n已取消")
            break
        
        if choice == '0':
            print("已退出")
            break
            
        elif choice == '1':
            # 选择单张文件
            file_path = select_file("选择要识别的图片或视频")
            if not file_path:
                print("未选择文件，返回主菜单")
                continue
            
            print(f"\n已选择: {file_path}")
            recognize_single_file(detector, file_path, output_dir)
                
        elif choice == '2':
            # 选择文件夹
            input_dir = select_folder("选择包含图片/视频的文件夹")
            if not input_dir:
                print("未选择文件夹，返回主菜单")
                continue
            
            batch_recognize_folder(detector, input_dir, output_dir)
            
        else:
            print("无效选项，请重新输入")


def main():
    # 打印程序标题
    print_banner()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='车牌识别系统 - 自动识别车牌号码和颜色',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互模式（弹出选择对话框）
  python run.py
  
  # 识别单张图片
  python run.py --image 车牌照片.jpg
  
  # 识别整个文件夹
  python run.py --input 我的图片文件夹/ --output 结果/
  
  # 服务器环境（不显示视频窗口）
  python run.py --no-display
  
  # 启动图形界面
  python run.py --gui
        """
    )
    
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='配置文件路径 (默认: config.yaml)')
    parser.add_argument('--image', type=str, default=None,
                        help='识别单张图片')
    parser.add_argument('--input', type=str, default=None,
                        help='输入文件夹路径')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件夹路径')
    parser.add_argument('--no-display', action='store_true',
                        help='不显示视频窗口（服务器环境使用）')
    parser.add_argument('--gui', action='store_true',
                        help='启动图形界面版本')
    
    args = parser.parse_args()
    
    # 如果请求GUI版本
    if args.gui:
        print("启动图形界面版本...")
        os.system(f'python gui.py')
        return
    
    # 加载配置
    try:
        config = load_config(args.config)
        print(f"✓ 配置文件加载成功: {args.config}")
    except Exception as e:
        print(f"✗ 配置文件错误: {e}")
        return
    
    # 命令行参数覆盖配置文件
    if args.output:
        config['paths']['output_path'] = args.output
    if args.no_display:
        config['display']['show_video'] = False
    
    # 检查运行环境
    if not check_environment(config):
        return
    
    # 创建输出目录
    output_dir = config['paths']['output_path']
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化检测器
    print("\n正在初始化模型...")
    start_time = time.time()
    
    try:
        detector = PlateDetector(config)
        init_time = time.time() - start_time
        print(f"✓ 模型初始化完成 (耗时: {init_time:.2f}秒)\n")
    except Exception as e:
        print(f"✗ 模型初始化失败: {e}")
        return
    
    # 执行识别
    if args.image:
        # 单张图片识别（命令行指定）
        print(f"识别图片: {args.image}")
        recognize_single_file(detector, args.image, output_dir)
            
    elif args.input:
        # 批量识别（命令行指定文件夹）
        input_dir = args.input
        if not os.path.exists(input_dir):
            print(f"✗ 输入路径不存在: {input_dir}")
            return
        
        batch_recognize_folder(detector, input_dir, output_dir)
        
    else:
        # 交互模式
        interactive_mode(detector, output_dir)


if __name__ == "__main__":
    main()
