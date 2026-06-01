#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车牌识别系统 - 图形界面版本
支持图片和视频识别
"""

import os
import sys
import copy
import time
import yaml
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# 导入核心模块
from core.plate_detector import PlateDetector
from core.utils import check_environment


class PlateRecognitionGUI:
    """车牌识别图形界面类"""

    def __init__(self, root, config):
        self.root = root
        self.root.title("车牌识别系统 v2.0")
        self.root.geometry("900x750")
        self.config = config

        # 初始化检测器
        self.detector = None
        self.current_file = None
        self.is_video = False

        # 创建界面
        self._create_ui()

        # 加载模型
        self._load_model()

    def _create_ui(self):
        """创建用户界面"""
        # 顶部按钮区域
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_select = tk.Button(
            btn_frame, text="选择图片",
            command=self.select_image,
            font=("微软雅黑", 12),
            width=12, height=2
        )
        self.btn_select.pack(side=tk.LEFT, padx=5)

        self.btn_video = tk.Button(
            btn_frame, text="选择视频",
            command=self.select_video,
            font=("微软雅黑", 12),
            width=12, height=2
        )
        self.btn_video.pack(side=tk.LEFT, padx=5)

        self.btn_recognize = tk.Button(
            btn_frame, text="开始识别",
            command=self.recognize,
            font=("微软雅黑", 12),
            width=12, height=2,
            state=tk.DISABLED
        )
        self.btn_recognize.pack(side=tk.LEFT, padx=5)

        self.btn_batch = tk.Button(
            btn_frame, text="批量识别",
            command=self.batch_recognize,
            font=("微软雅黑", 12),
            width=12, height=2
        )
        self.btn_batch.pack(side=tk.LEFT, padx=5)

        # 图片显示区域
        self.image_label = tk.Label(self.root, text="请选择图片或视频", bg='gray90')
        self.image_label.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # 结果显示区域
        result_frame = tk.Frame(self.root, bg='white', bd=2, relief=tk.GROOVE)
        result_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(
            result_frame, text="识别结果",
            font=("微软雅黑", 14, "bold"),
            bg='white'
        ).pack(pady=5)

        self.result_text = tk.Label(
            result_frame,
            text="等待识别...",
            font=("微软雅黑", 16),
            bg='white',
            fg='blue',
            height=2
        )
        self.result_text.pack(pady=10)

        # 状态栏
        self.status_bar = tk.Label(
            self.root,
            text="就绪",
            bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _load_model(self):
        """加载模型"""
        self.status_bar.config(text="正在加载模型...")
        self.root.update()

        try:
            if not check_environment(self.config):
                messagebox.showerror("错误", "环境检查失败，请检查模型文件")
                return

            self.detector = PlateDetector(self.config)
            self.status_bar.config(text="模型加载完成，就绪")

        except Exception as e:
            messagebox.showerror("错误", f"模型加载失败: {e}")
            self.status_bar.config(text="模型加载失败")

    def select_image(self):
        """选择图片"""
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.current_file = file_path
            self.is_video = False
            self._display_image(file_path)
            self.btn_recognize.config(state=tk.NORMAL)
            self.result_text.config(text="点击'开始识别'按钮", fg='blue')
            self.status_bar.config(text=f"已选择图片: {os.path.basename(file_path)}")

    def select_video(self):
        """选择视频"""
        file_path = filedialog.askopenfilename(
            title="选择视频",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mov *.mkv"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.current_file = file_path
            self.is_video = True
            self.btn_recognize.config(state=tk.NORMAL)
            self.result_text.config(text="点击'开始识别'按钮（视频处理可能需要较长时间）", fg='blue')
            self.status_bar.config(text=f"已选择视频: {os.path.basename(file_path)}")

            # 显示视频第一帧作为预览
            import cv2
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                max_size = (800, 500)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=photo, bg='white')
                self.image_label.image = photo
            cap.release()

    def _display_image(self, image_path):
        """显示图片"""
        img = Image.open(image_path)
        max_size = (800, 500)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=photo, bg='white')
        self.image_label.image = photo

    def recognize(self):
        """执行识别"""
        if not self.current_file or not self.detector:
            return

        if self.is_video:
            self._recognize_video()
        else:
            self._recognize_image()

    def _recognize_image(self):
        """识别单张图片"""
        self.status_bar.config(text="正在识别...")
        self.result_text.config(text="识别中...")
        self.root.update()

        try:
            result = self.detector.recognize_image(self.current_file)

            if result:
                self.result_text.config(text=result, fg='green')
                self.status_bar.config(text="识别完成")

                output_path = self.config['paths']['output_path']
                result_img_path = os.path.join(
                    output_path,
                    os.path.basename(self.current_file)
                )
                if os.path.exists(result_img_path):
                    self._display_image(result_img_path)
            else:
                self.result_text.config(text="未识别到车牌", fg='red')
                self.status_bar.config(text="识别完成，未检测到车牌")

        except Exception as e:
            messagebox.showerror("错误", f"识别失败: {e}")
            self.status_bar.config(text="识别失败")

    def _recognize_video(self):
        """识别视频"""
        import cv2

        self.status_bar.config(text="正在处理视频，请耐心等待...")
        self.result_text.config(text="视频处理中...")
        self.root.update()

        start_time = time.time()

        try:
            video_path = self.current_file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                messagebox.showerror("错误", "无法打开视频文件")
                return

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 输出路径
            output_dir = self.config['paths']['output_path']
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'result_' + os.path.basename(video_path))

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            frame_count = 0
            all_plates = []

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                frame_ori = frame.copy()
                try:
                    result_list = self.detector._detect_and_recognize(frame, frame_ori)
                    result_frame, _ = self.detector._draw_result(frame, result_list)

                    for r in result_list:
                        all_plates.append(str(r['plate_no']))
                except Exception:
                    result_frame = frame

                writer.write(result_frame)
                frame_count += 1

                # 更新进度
                if frame_count % 30 == 0:
                    progress = frame_count / max(total_frames, 1) * 100
                    self.status_bar.config(
                        text=f"处理中: {frame_count}/{total_frames} 帧 ({progress:.0f}%)"
                    )
                    self.root.update()

            cap.release()
            writer.release()

            elapsed = time.time() - start_time
            unique_plates = list(set(all_plates))

            result_msg = (
                f"视频识别完成！\n\n"
                f"总帧数: {total_frames}\n"
                f"已处理: {frame_count} 帧\n"
                f"帧率: {fps} FPS\n"
                f"分辨率: {width}x{height}\n"
                f"处理耗时: {elapsed:.2f} 秒\n"
                f"检测次数: {len(all_plates)}\n"
                f"识别到的车牌: {', '.join(unique_plates) if unique_plates else '无'}\n\n"
                f"结果已保存到: {output_path}"
            )

            self.result_text.config(text=f"识别完成，发现 {len(unique_plates)} 个车牌", fg='green')
            self.status_bar.config(text="视频识别完成")
            messagebox.showinfo("视频识别完成", result_msg)

        except Exception as e:
            messagebox.showerror("错误", f"视频识别失败: {e}")
            self.status_bar.config(text="视频识别失败")

    def batch_recognize(self):
        """批量识别"""
        input_dir = filedialog.askdirectory(title="选择输入文件夹")
        if not input_dir:
            return

        output_dir = filedialog.askdirectory(title="选择输出文件夹")
        if not output_dir:
            return

        self.status_bar.config(text="批量识别中...")
        self.result_text.config(text="批量识别中，请稍候...")
        self.root.update()

        try:
            stats = self.detector.batch_recognize(input_dir, output_dir)

            result_msg = (
                f"批量识别完成！\n\n"
                f"图片文件: {stats['images']} 个\n"
                f"视频文件: {stats['videos']} 个\n"
                f"成功识别: {stats['success']} 个\n"
                f"识别失败: {stats['failed']} 个\n"
                f"总耗时: {stats['total_time']:.2f} 秒"
            )

            messagebox.showinfo("批量识别完成", result_msg)
            self.status_bar.config(text="批量识别完成")
            self.result_text.config(text="批量识别完成")

        except Exception as e:
            messagebox.showerror("错误", f"批量识别失败: {e}")
            self.status_bar.config(text="批量识别失败")


def main():
    """主函数"""
    config_path = 'config.yaml'
    if not os.path.exists(config_path):
        messagebox.showerror("错误", f"配置文件不存在: {config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    root = tk.Tk()
    app = PlateRecognitionGUI(root, config)

    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))

    root.mainloop()


if __name__ == "__main__":
    main()
