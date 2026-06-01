"""
车牌检测器核心类
封装了YOLOv8检测和CNN识别的完整流程
"""

import os
import cv2
import copy
import time
import torch
import numpy as np
from pathlib import Path

# 导入原有的识别模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultralytics.nn.tasks import attempt_load_weights
from plate_recognition.plate_rec import get_plate_result, init_model, cv_imread
from plate_recognition.double_plate_split_merge import get_split_merge
from fonts.cv_puttext import cv2ImgAddText


class PlateDetector:
    """
    车牌检测器类
    
    功能：
    1. 使用YOLOv8检测车牌位置
    2. 使用CNN识别车牌号码和颜色
    3. 支持单张图片和批量处理
    4. 支持视频文件处理
    """
    
    def __init__(self, config):
        """
        初始化检测器
        
        参数:
            config: 配置字典，包含模型路径和参数设置
        """
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载模型
        self._load_models()
        
    def _load_models(self):
        """加载检测模型和识别模型"""
        # 加载YOLOv8检测模型
        detect_model_path = self.config['models']['detect_model']
        self.detect_model = attempt_load_weights(detect_model_path, device=self.device)
        self.detect_model.eval()
        
        # 加载车牌识别模型
        rec_model_path = self.config['models']['rec_model']
        self.plate_rec_model = init_model(self.device, rec_model_path, is_color=True)
        
        # 打印模型参数量
        total_detect = sum(p.numel() for p in self.detect_model.parameters())
        total_rec = sum(p.numel() for p in self.plate_rec_model.parameters())
        print(f"  检测模型参数量: {total_detect/1e6:.2f}M")
        print(f"  识别模型参数量: {total_rec/1e6:.2f}M")
        
    def recognize_image(self, image_path):
        """
        识别单张图片
        
        参数:
            image_path: 图片文件路径
            
        返回:
            result_str: 识别结果字符串
        """
        # 读取图片（支持中文路径）
        img = cv_imread(image_path)
        if img is None:
            print(f"无法读取图片: {image_path}")
            return None
        
        # 转换4通道RGBA为3通道BGR（如果有透明通道）
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
        img_ori = copy.deepcopy(img)
        
        # 执行检测和识别
        result_list = self._detect_and_recognize(img, img_ori)
        
        # 绘制结果
        result_img, result_str = self._draw_result(img, result_list)
        
        # 保存结果
        output_path = self.config['paths']['output_path']
        os.makedirs(output_path, exist_ok=True)
        save_path = os.path.join(output_path, os.path.basename(image_path))
        cv2.imwrite(save_path, result_img)
        
        return result_str
        
    def batch_recognize(self, input_dir, output_dir):
        """
        批量识别文件夹中的图片和视频
        
        参数:
            input_dir: 输入文件夹路径
            output_dir: 输出文件夹路径
            
        返回:
            stats: 统计信息字典
        """
        stats = {
            'images': 0,
            'videos': 0,
            'success': 0,
            'failed': 0,
            'total_time': 0
        }
        
        start_time = time.time()
        
        # 获取所有文件
        file_list = []
        self._get_all_files(input_dir, file_list)
        
        # 支持的格式
        image_formats = tuple(self.config['formats']['images'])
        video_formats = tuple(self.config['formats']['videos'])
        
        for file_path in file_list:
            ext = os.path.splitext(file_path)[1].lower()
            
            try:
                if ext in image_formats:
                    stats['images'] += 1
                    print(f"处理图片 [{stats['images']}]: {os.path.basename(file_path)}")
                    result = self.recognize_image(file_path)
                    if result:
                        stats['success'] += 1
                        print(f"  结果: {result}")
                    else:
                        stats['failed'] += 1
                        
                elif ext in video_formats:
                    stats['videos'] += 1
                    print(f"处理视频 [{stats['videos']}]: {os.path.basename(file_path)}")
                    self._process_video(file_path, output_dir)
                    stats['success'] += 1
                    
            except Exception as e:
                print(f"  错误: {e}")
                stats['failed'] += 1
                
        stats['total_time'] = time.time() - start_time
        return stats
        
    def _detect_and_recognize(self, img, img_ori):
        """
        执行检测和识别核心流程
        
        参数:
            img: 预处理后的图像
            img_ori: 原始图像
            
        返回:
            result_list: 识别结果列表
        """
        result_list = []
        
        # 前处理
        img_input, r, left, top = self._preprocess(img)
        
        # 检测（使用no_grad减少内存占用）
        with torch.no_grad():
            prediction = self.detect_model(img_input)[0]
            
        # 后处理
        outputs = self._postprocess(prediction, r, left, top)
        
        # 识别每个检测到的车牌
        for output in outputs:
            result_dict = self._recognize_plate(output, img_ori)
            if result_dict:
                result_list.append(result_dict)
                
        return result_list
        
    def _preprocess(self, img):
        """图像预处理"""
        # Letter box resize
        h, w = img.shape[:2]
        size = self.config['params']['img_size']
        r = min(size / h, size / w)
        new_h, new_w = int(h * r), int(w * r)
        
        resized = cv2.resize(img, (new_w, new_h))
        left = (size - new_w) // 2
        top = (size - new_h) // 2
        right = size - new_w - left
        bottom = size - new_h - top
        
        padded = cv2.copyMakeBorder(
            resized, top, bottom, left, right,
            cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )
        
        # BGR to RGB, HWC to CHW
        padded = padded[:, :, ::-1].transpose(2, 0, 1).copy()
        
        # To tensor
        tensor = torch.from_numpy(padded).to(self.device).float() / 255.0
        tensor = tensor.unsqueeze(0)
        
        return tensor, r, left, top
        
    def _postprocess(self, prediction, r, left, top):
        """检测后处理"""
        conf_thresh = self.config['params']['conf_threshold']
        iou_thresh = self.config['params']['iou_threshold']
        
        prediction = prediction.permute(0, 2, 1).squeeze(0)
        
        # 过滤低置信度
        scores = prediction[:, 4:6].amax(1)
        mask = scores > conf_thresh
        candidates = prediction[mask]
        
        if len(candidates) == 0:
            return []
            
        # 转换坐标格式
        boxes = candidates[:, :4]
        boxes = self._xywh2xyxy(boxes)
        
        # 获取类别和分数
        scores, classes = torch.max(candidates[:, 4:6], dim=1)
        
        # 组合结果
        detections = torch.cat([
            boxes, scores.unsqueeze(1),
            candidates[:, 6:14], classes.unsqueeze(1)
        ], dim=1)
        
        # NMS
        keep = self._nms(detections, iou_thresh)
        detections = detections[keep]
        
        # 还原坐标到原图
        detections[:, [0, 2]] -= left
        detections[:, [1, 3]] -= top
        detections[:, :4] /= r
        
        return detections
        
    def _recognize_plate(self, output, img_ori):
        """识别单个车牌"""
        output = output.squeeze().cpu().numpy()
        
        # 获取检测框
        x1, y1, x2, y2 = map(int, output[:4])
        label = int(output[-1])
        
        # 裁剪车牌区域
        roi = img_ori[y1:y2, x1:x2]
        if roi.size == 0:
            return None
            
        # 双层车牌处理
        if label == 1:
            roi = get_split_merge(roi)
            
        # 识别车牌号码和颜色
        plate_num, conf, color, color_conf = get_plate_result(
            roi, self.device, self.plate_rec_model, is_color=True
        )
        
        return {
            'plate_no': plate_num,
            'plate_color': color,
            'rect': [x1, y1, x2, y2],
            'detect_conf': output[4],
            'color_conf': color_conf,
            'plate_type': label,
            'roi_height': roi.shape[0]
        }
        
    def _draw_result(self, img, result_list):
        """在图像上绘制识别结果"""
        result_str = ""
        
        for result in result_list:
            x1, y1, x2, y2 = result['rect']
            
            # 添加padding
            w, h = x2 - x1, y2 - y1
            padding_w = int(0.05 * w)
            padding_h = int(0.11 * h)
            
            x1 = max(0, x1 - padding_w)
            y1 = max(0, y1 - padding_h)
            x2 = min(img.shape[1], x2 + padding_w)
            y2 = min(img.shape[0], y2 + padding_h)
            
            # 构建结果文本
            text = result['plate_no'] + " " + result['plate_color']
            if result['plate_type'] == 1:
                text += "双层"
            result_str += text + " "
            
            # 画框
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # 画文字背景
            font_size = self.config['display']['font_size']
            label_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            text_w = label_size[0][0]
            text_h = label_size[0][1]
            
            # 防止文字越界
            if x1 + text_w > img.shape[1]:
                x1 = img.shape[1] - text_w
                
            # 白色背景
            cv2.rectangle(img, (x1, y1 - int(1.6 * text_h)),
                         (x1 + int(1.2 * text_w), y1 + text_h),
                         (255, 255, 255), cv2.FILLED)
            
            # 写文字（中文）
            img = cv2ImgAddText(img, text, x1, y1 - int(1.6 * text_h), (0, 0, 0), font_size)
            
        print(f"识别结果: {result_str}")
        return img, result_str
        
    def _process_video(self, video_path, output_dir):
        """处理视频文件"""
        cap = cv2.VideoCapture(video_path)
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # 创建输出视频
        output_path = os.path.join(output_dir, os.path.basename(video_path))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        show_video = self.config['display']['show_video']
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                break
                
            frame_ori = copy.deepcopy(frame)
            
            try:
                # 检测和识别
                result_list = self._detect_and_recognize(frame, frame_ori)
                result_frame, _ = self._draw_result(frame, result_list)
                
                # 显示（可选）
                if show_video:
                    try:
                        cv2.imshow('Plate Recognition', result_frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    except cv2.error:
                        show_video = False
                        
                writer.write(result_frame)
                frame_count += 1
                
                if frame_count % 30 == 0:
                    print(f"  已处理 {frame_count} 帧")
                    
            except Exception as e:
                print(f"  处理帧错误: {e}")
                writer.write(frame)
                
        cap.release()
        writer.release()
        cv2.destroyAllWindows()
        
        print(f"  视频处理完成，共 {frame_count} 帧")
        print(f"  输出文件: {output_path}")
        
    def _get_all_files(self, root_path, file_list):
        """递归获取所有文件"""
        for item in os.listdir(root_path):
            full_path = os.path.join(root_path, item)
            if os.path.isfile(full_path):
                file_list.append(full_path)
            else:
                self._get_all_files(full_path, file_list)
                
    def _xywh2xyxy(self, boxes):
        """坐标格式转换"""
        y = boxes.clone()
        y[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
        y[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
        y[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
        y[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
        return y
        
    def _nms(self, detections, iou_thresh):
        """非极大值抑制"""
        if len(detections) == 0:
            return []
            
        # 按分数排序
        scores = detections[:, 4]
        indices = torch.argsort(scores, descending=True)
        
        keep = []
        while len(indices) > 0:
            current = indices[0]
            keep.append(current.item())
            
            if len(indices) == 1:
                break
                
            # 计算IOU
            current_box = detections[current, :4]
            other_boxes = detections[indices[1:], :4]
            
            ious = self._compute_iou(current_box, other_boxes)
            
            # 保留IOU小于阈值的
            mask = ious <= iou_thresh
            indices = indices[1:][mask]
            
        return keep
        
    def _compute_iou(self, box, boxes):
        """计算IOU"""
        # box: (4,)
        # boxes: (N, 4)
        
        x1 = torch.maximum(box[0], boxes[:, 0])
        y1 = torch.maximum(box[1], boxes[:, 1])
        x2 = torch.minimum(box[2], boxes[:, 2])
        y2 = torch.minimum(box[3], boxes[:, 3])
        
        inter_w = torch.clamp(x2 - x1, min=0)
        inter_h = torch.clamp(y2 - y1, min=0)
        inter_area = inter_w * inter_h
        
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        
        union_area = box_area + boxes_area - inter_area
        iou = inter_area / (union_area + 1e-6)
        
        return iou
