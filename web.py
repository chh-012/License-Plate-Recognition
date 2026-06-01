#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车牌识别系统 - Flask Web 服务
提供 RESTful API 和网页界面
"""

import os
import io
import base64
import json
import time
import yaml
import torch
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory
from core.plate_detector import PlateDetector
from core.utils import check_environment

app = Flask(__name__)

# 全局检测器实例
detector = None


def load_config():
    """加载配置文件"""
    config_path = 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def init_detector():
    """初始化检测器"""
    global detector
    config = load_config()
    if not check_environment(config):
        raise RuntimeError("环境检查失败")
    detector = PlateDetector(config)
    print("检测器初始化完成")


def numpy_to_base64(img):
    """将OpenCV图像转为base64字符串"""
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer.tobytes()).decode('utf-8')


def base64_to_numpy(base64_str):
    """将base64字符串转为OpenCV图像"""
    img_data = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


# ============ 路由 ============

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/recognize', methods=['POST'])
def api_recognize():
    """
    识别接口
    接收JSON格式: {"image": "base64编码的图片"}
    返回JSON格式: {"success": true, "results": [...], "image": "base64编码的结果图片"}
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': '请提供图片数据'}), 400

        # 解码图片
        img = base64_to_numpy(data['image'])
        if img is None:
            return jsonify({'success': False, 'error': '图片格式无效'}), 400

        # 识别
        img_ori = img.copy()
        result_list = detector._detect_and_recognize(img, img_ori)
        result_img, result_str = detector._draw_result(img, result_list)

        # 构建返回数据
        results = []
        for r in result_list:
            results.append({
                'plate_no': str(r['plate_no']),
                'plate_color': str(r['plate_color']),
                'plate_type': '双层' if r['plate_type'] == 1 else '单层',
                'detect_conf': float(r['detect_conf']),
                'color_conf': float(r['color_conf']),
                'rect': [int(x) for x in r['rect']]
            })

        return jsonify({
            'success': True,
            'results': results,
            'result_text': str(result_str).strip(),
            'image': numpy_to_base64(result_img)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/recognize/file', methods=['POST'])
def api_recognize_file():
    """
    文件上传识别接口
    接收 multipart/form-data 格式: {"file": 图片文件}
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '请上传图片文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400

        # 读取图片
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'success': False, 'error': '无法解析图片'}), 400

        # 识别
        img_ori = img.copy()
        result_list = detector._detect_and_recognize(img, img_ori)
        result_img, result_str = detector._draw_result(img, result_list)

        # 构建返回数据
        results = []
        for r in result_list:
            results.append({
                'plate_no': str(r['plate_no']),
                'plate_color': str(r['plate_color']),
                'plate_type': '双层' if r['plate_type'] == 1 else '单层',
                'detect_conf': float(r['detect_conf']),
                'color_conf': float(r['color_conf']),
                'rect': [int(x) for x in r['rect']]
            })

        return jsonify({
            'success': True,
            'results': results,
            'result_text': str(result_str).strip(),
            'image': numpy_to_base64(result_img)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def api_health():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'device': str(detector.device) if detector else 'not initialized',
        'cuda_available': torch.cuda.is_available()
    })


@app.route('/api/batch_recognize', methods=['POST'])
def api_batch_recognize():
    """
    批量识别接口
    接收 multipart/form-data 格式，支持多个文件上传
    返回JSON格式: {"success": true, "results": [...]}
    """
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': '请上传文件'}), 400

        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({'success': False, 'error': '未选择文件'}), 400

        results = []
        total_files = len(files)
        processed = 0
        success_count = 0

        for file in files:
            if file.filename == '':
                continue

            file_result = {
                'filename': file.filename,
                'success': False,
                'plates': [],
                'error': None
            }

            try:
                # 读取图片
                img_bytes = file.read()
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if img is None:
                    file_result['error'] = '无法解析图片'
                    results.append(file_result)
                    continue

                # 识别
                img_ori = img.copy()
                result_list = detector._detect_and_recognize(img, img_ori)
                result_img, result_str = detector._draw_result(img, result_list)

                # 构建结果
                plates = []
                for r in result_list:
                    plates.append({
                        'plate_no': str(r['plate_no']),
                        'plate_color': str(r['plate_color']),
                        'plate_type': '双层' if r['plate_type'] == 1 else '单层',
                        'detect_conf': float(r['detect_conf']),
                        'color_conf': float(r['color_conf']),
                        'rect': [int(x) for x in r['rect']]
                    })

                file_result['success'] = True
                file_result['plates'] = plates
                file_result['result_text'] = str(result_str).strip()
                file_result['result_image'] = numpy_to_base64(result_img)
                success_count += 1

            except Exception as e:
                file_result['error'] = str(e)

            results.append(file_result)
            processed += 1

        return jsonify({
            'success': True,
            'total': total_files,
            'processed': processed,
            'success_count': success_count,
            'results': results
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/recognize_video', methods=['POST'])
def api_recognize_video():
    """
    视频识别接口
    接收 multipart/form-data 格式: {"file": 视频文件}
    返回JSON格式: {"success": true, "video": "base64编码的结果视频", "stats": {...}}
    """
    import tempfile

    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '请上传视频文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400

        # 检查视频格式
        valid_ext = ('.mp4', '.avi', '.mov', '.mkv')
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in valid_ext:
            return jsonify({'success': False, 'error': f'不支持的视频格式: {ext}，支持: {", ".join(valid_ext)}'}), 400

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            # 处理视频
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                return jsonify({'success': False, 'error': '无法打开视频文件'}), 400

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 创建输出视频（临时文件）
            out_tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            out_path = out_tmp.name
            out_tmp.close()

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

            frame_count = 0
            all_plates = []
            start_time = time.time()

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                frame_ori = frame.copy()
                try:
                    result_list = detector._detect_and_recognize(frame, frame_ori)
                    result_frame, _ = detector._draw_result(frame, result_list)

                    for r in result_list:
                        all_plates.append({
                            'frame': frame_count,
                            'plate_no': str(r['plate_no']),
                            'plate_color': str(r['plate_color']),
                        })
                except Exception:
                    result_frame = frame

                writer.write(result_frame)
                frame_count += 1

            cap.release()
            writer.release()

            elapsed = time.time() - start_time

            # 读取输出视频并转为base64
            with open(out_path, 'rb') as f:
                video_bytes = f.read()
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')

            # 统计唯一车牌号
            unique_plates = list(set(p['plate_no'] for p in all_plates))

            return jsonify({
                'success': True,
                'video': video_base64,
                'stats': {
                    'total_frames': total_frames,
                    'processed_frames': frame_count,
                    'fps': fps,
                    'resolution': f'{width}x{height}',
                    'elapsed': round(elapsed, 2),
                    'unique_plates': unique_plates,
                    'total_detections': len(all_plates)
                }
            })

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("  车牌识别系统 Web 服务")
    print("=" * 50)

    # 初始化检测器
    print("\n正在初始化模型...")
    start = time.time()
    init_detector()
    print(f"模型加载完成，耗时 {time.time() - start:.2f} 秒")

    # 启动服务
    config = load_config()
    host = config.get('web', {}).get('host', '0.0.0.0')
    port = config.get('web', {}).get('port', 5000)
    debug = config.get('web', {}).get('debug', False)

    print(f"\n服务启动成功!")
    print(f"  访问地址: http://localhost:{port}")
    print(f"  API文档: http://localhost:{port}/api/health")
    print(f"\n按 Ctrl+C 停止服务\n")

    app.run(host=host, port=port, debug=debug)
