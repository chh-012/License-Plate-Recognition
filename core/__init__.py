"""
车牌识别系统核心模块
"""

from .plate_detector import PlateDetector
from .utils import print_banner, check_environment

__all__ = ['PlateDetector', 'print_banner', 'check_environment']
