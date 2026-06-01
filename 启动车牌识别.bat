@echo off
chcp 65001 >nul 2>&1
title 车牌识别服务

:: 1. 进入项目目录
cd /d F:\studySoft\ShiXunWork\plate-recognition_YOLOv8_CNN-main\plate-recognition_YOLOv8_CNN-main

:: 2. 调用虚拟环境的python运行web.py
F:\studySoft\ShiXunWork\.venv\Scripts\python.exe web.py

:: 3. 运行完不自动关窗口（方便看报错）
pause