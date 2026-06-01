# 🚗 车牌识别系统 — License Plate Recognition

基于 **YOLOv8 + CNN** 的深度学习车牌检测与识别系统，支持中国大陆蓝牌、绿牌、黄牌、黑牌、白牌以及港澳/警车/军车等多种车牌类型，同时识别车牌颜色。

> 🎯 Web界面 · GUI桌面应用 · 命令行 · REST API 四种使用方式

---

## 📸 功能概览

- 🔍 **车牌检测** — YOLOv8s 精确定位车牌位置
- 🔤 **字符识别** — 轻量 CNN（~0.18M 参数）识别车牌号码
- 🎨 **颜色识别** — 同时识别车牌颜色（蓝/绿/黄/黑/白）
- 🖼️ **图片识别** — 支持 JPG / PNG / BMP 格式
- 🎬 **视频处理** — 支持 MP4 / AVI / MOV / MKV 格式
- 📂 **批量处理** — 一键识别文件夹内所有图片和视频
- 🌐 **Web 服务** — Flask 提供 Web 界面和 RESTful API
- 🖥️ **桌面 GUI** — 基于 PyQt5 / Tkinter 的图形界面
- ⌨️ **命令行** — 灵活的命令行参数，适合脚本调用

---

## 🏗️ 架构设计

```
输入图片/视频
      │
      ▼
┌─────────────┐
│  YOLOv8s    │  ← 车牌位置检测
│  (3.01M参数) │
└─────┬───────┘
      │ 车牌区域 (ROI)
      ▼
┌─────────────┐
│   CNN网络    │  ← 字符识别 + 颜色分类
│  (0.18M参数) │
└─────┬───────┘
      │
      ▼
  车牌号码 + 颜色
  (例: 京A12345 · 蓝色)
```

---

## 📁 项目结构

```
plate-recognition_YOLOv8_CNN-main/
├── core/                       # 核心检测器
│   ├── plate_detector.py       # 车牌检测器封装类
│   └── utils.py                # 环境检查工具
│
├── plate_recognition/          # CNN 识别模块
│   ├── plateNet.py             # 轻量 CNN 网络定义
│   ├── plate_rec.py            # 识别推理逻辑
│   └── double_plate_split_merge.py  # 双层车牌处理
│
├── ultralytics/                # YOLOv8 模型框架
│   ├── nn/                     # 网络层定义
│   ├── models/                 # 模型架构配置
│   ├── engine/                 # 训练 / 推理 / 导出引擎
│   └── utils/                  # 工具函数
│
├── fonts/                      # 中文字体（用于标注）
├── static/                     # Web 前端资源
│   ├── css/style.css
│   └── js/main.js
├── templates/                  # Web 页面模板
│   └── index.html
├── weights/                    # ⚠️ 预训练模型权重
│   ├── yolov8s.pt              # YOLOv8 检测模型 (~24MB)
│   └── plate_rec_color.pth     # CNN 识别模型 (~750KB)
│
├── web.py                      # Flask Web 服务入口
├── run.py                      # 命令行 / 交互模式入口
├── gui.py                      # PyQt5 图形界面入口
├── config.yaml                 # 全局配置文件
├── requirements.txt            # Python 依赖列表
└── 启动车牌识别.bat             # Windows 一键启动脚本
```

---

## 🚀 快速开始

### 环境要求

| 项目 | 版本要求 |
|------|---------|
| Python | **3.11**（推荐，3.13 不兼容） |
| PyTorch | 2.0.0 |
| CUDA | 可选（CPU 也能运行） |

### 1. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境（必须用 Python 3.11）
py -3.11 -m venv .venv

# 激活环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# ⚠️ requirements.txt 不含 flask，需手动安装（web.py 需要）
pip install flask
```

### 2. 配置模型权重

确保 `weights/` 目录下有以下两个文件：
- `yolov8s.pt` — YOLOv8 检测模型
- `plate_rec_color.pth` — CNN 识别模型

> 模型权重文件可从 Release 页面下载。

### 3. 运行

```bash
# 🌐 Web 服务（推荐）
python web.py
# 浏览器打开 http://localhost:5000

# 🖥️ 图形界面
python run.py --gui

# ⌨️ 命令行交互模式
python run.py

# 📸 识别单张图片
python run.py --image 车牌照片.jpg

# 📂 批量识别文件夹
python run.py --input ./输入文件夹 --output ./结果文件夹
```

---

## ⚙️ 配置说明 (`config.yaml`)

```yaml
models:
  detect_model: "weights/yolov8s.pt"     # YOLOv8 检测模型路径
  rec_model: "weights/plate_rec_color.pth" # CNN 识别模型路径

params:
  img_size: 640          # 输入图像尺寸
  conf_threshold: 0.3    # 检测置信度阈值
  iou_threshold: 0.5     # NMS IoU 阈值

web:
  host: "0.0.0.0"        # 监听地址
  port: 5000              # 端口号
  debug: false            # 调试模式

formats:
  images: [".jpg", ".jpeg", ".png", ".bmp"]
  videos: [".mp4", ".avi", ".mov", ".mkv"]
```

---

## 🌐 Web API 文档

启动 `python web.py` 后，访问 `http://localhost:5000` 获得 Web 界面。

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/detect` | 上传图片进行识别 |
| `POST` | `/api/detect_base64` | Base64 图片识别 |

### 请求示例

```bash
# 上传文件识别
curl -X POST http://localhost:5000/api/detect \
  -F "file=@car_plate.jpg"

# 返回示例
{
  "success": true,
  "data": {
    "plate_no": "京A12345",
    "color": "蓝色",
    "confidence": 0.96,
    "image": "base64编码的标注图片..."
  }
}
```

---

## 🖥️ 界面预览

### Web 界面

浏览器打开 `http://localhost:5000`，支持拖拽或点击上传图片，实时显示识别结果。

### GUI 桌面应用

```bash
python gui.py
```

基于 PyQt5 的桌面窗口，支持选择图片/视频文件，显示识别结果和标注图像。

### 命令行批量处理

```bash
python run.py --input T_T_imgs --output T_T_result
```

---

## 🧠 模型详情

| 模型 | 参数量 | 用途 | 文件 |
|------|--------|------|------|
| YOLOv8s | ~3.01M | 车牌位置检测 | `weights/yolov8s.pt` |
| CNN 识别网络 | ~0.18M | 字符+颜色识别 | `weights/plate_rec_color.pth` |

识别网络采用轻量 CNN 架构（Conv + BatchNorm + MaxPool），使用 CTC 思想解码车牌字符序列，同时多任务输出车牌颜色。

---

## 📦 依赖清单

| 类别 | 主要包 |
|------|--------|
| 深度学习 | `torch==2.0.0` `torchvision==0.15.1` |
| 图像处理 | `opencv-python==4.8.1.78` `Pillow==10.0.0` `matplotlib==3.8.0` |
| 数据处理 | `numpy==1.26.4` `scipy==1.11.4` `pandas==2.1.4` |
| Web 框架 | `flask` |
| GUI | `PyQt5==5.15.9` |
| 工具 | `PyYAML==6.0.1` `requests==2.31.0` `tqdm==4.66.1` |

完整清单见 [requirements.txt](requirements.txt)

---

## 🐛 常见问题

<details>
<summary><b>Q: 提示 <code>import yaml</code> 失败？</b></summary>
确认已激活正确的虚拟环境（<code>.venv\Scripts\activate</code>），并用 <code>pip list | findstr PyYAML</code> 检查。
</details>

<details>
<summary><b>Q: 运行 web.py 找不到 config.yaml？</b></summary>
需要 <b>先 cd 到项目目录</b>再运行 <code>python web.py</code>，不要在父级目录执行。
</details>

<details>
<summary><b>Q: Python 3.13 安装依赖报错？</b></summary>
项目依赖（torch 2.0.0、numpy 1.26.4 等）不支持 Python 3.13。请用 <code>py -3.11 -m venv .venv</code> 创建 Python 3.11 虚拟环境。
</details>

<details>
<summary><b>Q: 如何使用 GPU 加速？</b></summary>
安装 CUDA 版本的 PyTorch：<code>pip install torch==2.0.0+cu118 --index-url https://download.pytorch.org/whl/cu118</code>
</details>

---

## 📄 License

本项目仅供学习和研究使用。

---

## 🙏 致谢

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) — 目标检测框架
- [PyTorch](https://pytorch.org/) — 深度学习框架
