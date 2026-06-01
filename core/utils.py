"""
工具函数模块
"""

import os
import sys
import torch


def print_banner():
    """打印程序标题"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           🚗 车牌识别系统 v2.0 🚗                        ║
    ║                                                          ║
    ║     基于 YOLOv8 + CNN 深度学习模型                       ║
    ║     支持：图片识别 | 视频识别 | 批量处理                 ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_environment(config):
    """检查运行环境"""
    print("检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("✗ Python版本过低，需要3.8或更高版本")
        return False
    print(f"✓ Python版本: {sys.version.split()[0]}")
    
    # 检查CUDA可用性
    if torch.cuda.is_available():
        print(f"✓ CUDA可用: {torch.cuda.get_device_name(0)}")
    else:
        print("! 使用CPU运行（建议安装CUDA以获得更快速度）")
    
    # 检查模型文件
    detect_model = config['models']['detect_model']
    rec_model = config['models']['rec_model']
    
    if not os.path.exists(detect_model):
        print(f"✗ 检测模型不存在: {detect_model}")
        return False
    print(f"✓ 检测模型: {detect_model}")
    
    if not os.path.exists(rec_model):
        print(f"✗ 识别模型不存在: {rec_model}")
        return False
    print(f"✓ 识别模型: {rec_model}")
    
    return True


def cv_imread(file_path):
    """
    读取图片（支持中文路径）
    
    参数:
        file_path: 图片文件路径
    
    返回:
        img: OpenCV图像对象，失败返回None
    """
    import cv2
    import numpy as np
    
    try:
        img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
        return img
    except Exception as e:
        print(f"读取图片失败: {file_path}, 错误: {e}")
        return None
