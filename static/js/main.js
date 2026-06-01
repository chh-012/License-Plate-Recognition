/**
 * 车牌识别系统 - 前端交互逻辑
 */

document.addEventListener('DOMContentLoaded', () => {
    // ===== DOM 元素 - 单张识别 =====
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const selectBtn = document.getElementById('selectBtn');
    const clearBtn = document.getElementById('clearBtn');
    const recognizeBtn = document.getElementById('recognizeBtn');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');

    // ===== DOM 元素 - 批量识别 =====
    const batchDropZone = document.getElementById('batchDropZone');
    const batchFileInput = document.getElementById('batchFileInput');
    const batchSelectBtn = document.getElementById('batchSelectBtn');
    const batchClearBtn = document.getElementById('batchClearBtn');
    const batchRecognizeBtn = document.getElementById('batchRecognizeBtn');
    const fileListContainer = document.getElementById('fileListContainer');
    const fileList = document.getElementById('fileList');
    const fileCount = document.getElementById('fileCount');

    // ===== DOM 元素 - 模式切换 =====
    const modeTabs = document.querySelectorAll('.mode-tab');
    const singleMode = document.getElementById('singleMode');
    const batchMode = document.getElementById('batchMode');

    // ===== DOM 元素 - 结果区域 =====
    const resultImage = document.getElementById('resultImage');
    const resultPlaceholder = document.getElementById('resultPlaceholder');
    const resultCards = document.getElementById('resultCards');
    const batchResults = document.getElementById('batchResults');
    const batchSummary = document.getElementById('batchSummary');
    const batchList = document.getElementById('batchList');
    const timeInfo = document.getElementById('timeInfo');
    const timeValue = document.getElementById('timeValue');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const loadingProgress = document.getElementById('loadingProgress');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    // ===== DOM 元素 - 视频识别 =====
    const videoDropZone = document.getElementById('videoDropZone');
    const videoFileInput = document.getElementById('videoFileInput');
    const videoSelectBtn = document.getElementById('videoSelectBtn');
    const videoClearBtn = document.getElementById('videoClearBtn');
    const videoRecognizeBtn = document.getElementById('videoRecognizeBtn');
    const videoInfoContainer = document.getElementById('videoInfoContainer');
    const videoFileName = document.getElementById('videoFileName');
    const videoFileSize = document.getElementById('videoFileSize');
    const videoResultContainer = document.getElementById('videoResultContainer');
    const resultVideo = document.getElementById('resultVideo');
    const downloadVideoBtn = document.getElementById('downloadVideoBtn');
    const videoStats = document.getElementById('videoStats');
    const videoMode = document.getElementById('videoMode');

    // ===== 状态变量 =====
    let currentFile = null;
    let batchFiles = [];
    let currentVideoFile = null;
    let currentMode = 'single';

    // 检查服务状态
    checkHealth();

    // ===== 模式切换 =====
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            if (mode === currentMode) return;

            // 更新标签状态
            modeTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // 切换模式显示
            if (mode === 'single') {
                singleMode.style.display = 'block';
                batchMode.style.display = 'none';
                videoMode.style.display = 'none';
                batchResults.style.display = 'none';
            } else if (mode === 'batch') {
                singleMode.style.display = 'none';
                batchMode.style.display = 'block';
                videoMode.style.display = 'none';
                resultImage.style.display = 'none';
                resultCards.style.display = 'none';
            } else if (mode === 'video') {
                singleMode.style.display = 'none';
                batchMode.style.display = 'none';
                videoMode.style.display = 'block';
                resultImage.style.display = 'none';
                resultCards.style.display = 'none';
                batchResults.style.display = 'none';
            }

            currentMode = mode;
            clearResults();
        });
    });

    // ===== 单张识别事件绑定 =====
    selectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    clearBtn.addEventListener('click', clearSingle);
    recognizeBtn.addEventListener('click', recognize);

    // ===== 批量识别事件绑定 =====
    batchSelectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        batchFileInput.click();
    });

    batchDropZone.addEventListener('click', () => batchFileInput.click());

    batchFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            addBatchFiles(Array.from(e.target.files));
        }
    });

    batchDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        batchDropZone.classList.add('dragover');
    });

    batchDropZone.addEventListener('dragleave', () => {
        batchDropZone.classList.remove('dragover');
    });

    batchDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        batchDropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            addBatchFiles(Array.from(e.dataTransfer.files));
        }
    });

    batchClearBtn.addEventListener('click', clearBatch);
    batchRecognizeBtn.addEventListener('click', batchRecognize);

    // ===== 视频识别事件绑定 =====
    videoSelectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        videoFileInput.click();
    });

    videoDropZone.addEventListener('click', () => videoFileInput.click());

    videoFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleVideoFile(e.target.files[0]);
        }
    });

    videoDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        videoDropZone.classList.add('dragover');
    });

    videoDropZone.addEventListener('dragleave', () => {
        videoDropZone.classList.remove('dragover');
    });

    videoDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        videoDropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleVideoFile(e.dataTransfer.files[0]);
        }
    });

    videoClearBtn.addEventListener('click', clearVideo);
    videoRecognizeBtn.addEventListener('click', recognizeVideo);

    // ===== 单张识别函数 =====
    function handleFile(file) {
        const validTypes = ['image/jpeg', 'image/png', 'image/bmp'];
        if (!validTypes.includes(file.type)) {
            alert('请上传 JPG、PNG 或 BMP 格式的图片');
            return;
        }

        currentFile = file;

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewContainer.style.display = 'block';
            dropZone.style.display = 'none';
            recognizeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function clearSingle() {
        currentFile = null;
        fileInput.value = '';
        previewImage.src = '';
        previewContainer.style.display = 'none';
        dropZone.style.display = 'block';
        recognizeBtn.disabled = true;
        clearResults();
    }

    async function recognize() {
        if (!currentFile) return;

        showLoading('正在识别中...');
        const startTime = performance.now();

        try {
            const formData = new FormData();
            formData.append('file', currentFile);

            const response = await fetch('/api/recognize/file', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);

            if (data.success) {
                showSingleResults(data, elapsed);
            } else {
                alert('识别失败: ' + data.error);
            }
        } catch (error) {
            alert('请求失败，请检查服务是否启动: ' + error.message);
        } finally {
            hideLoading();
        }
    }

    // ===== 批量识别函数 =====
    function addBatchFiles(files) {
        const validTypes = ['image/jpeg', 'image/png', 'image/bmp'];
        const validFiles = files.filter(f => validTypes.includes(f.type));

        if (validFiles.length === 0) {
            alert('请上传 JPG、PNG 或 BMP 格式的图片');
            return;
        }

        batchFiles = [...batchFiles, ...validFiles];
        updateFileList();
    }

    function updateFileList() {
        fileCount.textContent = `(${batchFiles.length})`;

        if (batchFiles.length === 0) {
            fileListContainer.style.display = 'none';
            batchRecognizeBtn.disabled = true;
            return;
        }

        fileListContainer.style.display = 'block';
        batchRecognizeBtn.disabled = false;

        fileList.innerHTML = '';
        batchFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-item-info">
                    <div class="file-item-icon">
                        <i class="fas fa-image"></i>
                    </div>
                    <span class="file-item-name">${file.name}</span>
                    <span class="file-item-size">${formatFileSize(file.size)}</span>
                </div>
                <button class="file-item-remove" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            fileList.appendChild(fileItem);
        });

        // 绑定删除按钮
        document.querySelectorAll('.file-item-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                batchFiles.splice(index, 1);
                updateFileList();
            });
        });
    }

    function clearBatch() {
        batchFiles = [];
        batchFileInput.value = '';
        updateFileList();
        clearResults();
    }

    async function batchRecognize() {
        if (batchFiles.length === 0) return;

        showLoading('正在批量识别...', `0 / ${batchFiles.length}`);
        const startTime = performance.now();

        try {
            const formData = new FormData();
            batchFiles.forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('/api/batch_recognize', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);

            if (data.success) {
                showBatchResults(data, elapsed);
            } else {
                alert('批量识别失败: ' + data.error);
            }
        } catch (error) {
            alert('请求失败，请检查服务是否启动: ' + error.message);
        } finally {
            hideLoading();
        }
    }

    // ===== 结果显示函数 =====
    function showSingleResults(data, elapsed) {
        clearResults();

        // 显示结果图片
        resultImage.src = 'data:image/jpeg;base64,' + data.image;
        resultImage.style.display = 'block';
        resultPlaceholder.style.display = 'none';

        // 显示车牌卡片
        if (data.results && data.results.length > 0) {
            resultCards.innerHTML = '';
            resultCards.style.display = 'flex';

            data.results.forEach((result, index) => {
                const card = createPlateCard(result, index);
                resultCards.appendChild(card);
            });
        } else {
            showNoResult();
        }

        // 显示耗时
        timeValue.textContent = elapsed;
        timeInfo.style.display = 'flex';
    }

    function showBatchResults(data, elapsed) {
        clearResults();

        // 显示统计摘要
        batchSummary.innerHTML = `
            <div class="batch-summary-item">
                <div class="batch-summary-value">${data.total}</div>
                <div class="batch-summary-label">总文件</div>
            </div>
            <div class="batch-summary-item">
                <div class="batch-summary-value" style="color: var(--success);">${data.success_count}</div>
                <div class="batch-summary-label">识别成功</div>
            </div>
            <div class="batch-summary-item">
                <div class="batch-summary-value" style="color: var(--danger);">${data.total - data.success_count}</div>
                <div class="batch-summary-label">识别失败</div>
            </div>
        `;

        // 显示结果列表
        batchList.innerHTML = '';
        data.results.forEach((result, index) => {
            const item = document.createElement('div');
            item.className = 'batch-result-item';

            if (result.success && result.plates.length > 0) {
                const platesHtml = result.plates.map(p => 
                    `<span class="batch-result-plate">${p.plate_no}</span>`
                ).join('');

                item.innerHTML = `
                    <div class="batch-result-header">
                        <span class="batch-result-filename">${result.filename}</span>
                        <span class="batch-result-status success">
                            <i class="fas fa-check"></i> 识别成功
                        </span>
                    </div>
                    <div class="batch-result-plates">${platesHtml}</div>
                `;
            } else if (result.success) {
                item.innerHTML = `
                    <div class="batch-result-header">
                        <span class="batch-result-filename">${result.filename}</span>
                        <span class="batch-result-status success">
                            <i class="fas fa-check"></i> 识别成功
                        </span>
                    </div>
                    <div class="batch-result-error">未检测到车牌</div>
                `;
            } else {
                item.innerHTML = `
                    <div class="batch-result-header">
                        <span class="batch-result-filename">${result.filename}</span>
                        <span class="batch-result-status error">
                            <i class="fas fa-times"></i> 识别失败
                        </span>
                    </div>
                    <div class="batch-result-error">${result.error || '未知错误'}</div>
                `;
            }

            batchList.appendChild(item);
        });

        batchResults.style.display = 'block';

        // 显示耗时
        timeValue.textContent = elapsed;
        timeInfo.style.display = 'flex';
    }

    // ===== 视频识别函数 =====
    function handleVideoFile(file) {
        const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/x-msvideo'];
        const validExt = ['.mp4', '.avi', '.mov', '.mkv'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();

        if (!validExt.includes(ext)) {
            alert('请上传 MP4、AVI、MOV 或 MKV 格式的视频');
            return;
        }

        currentVideoFile = file;
        videoFileName.innerHTML = `<i class="fas fa-file-video"></i> ${file.name}`;
        videoFileSize.innerHTML = `<i class="fas fa-hdd"></i> ${formatFileSize(file.size)}`;
        videoInfoContainer.style.display = 'block';
        videoDropZone.style.display = 'none';
        videoRecognizeBtn.disabled = false;
    }

    function clearVideo() {
        currentVideoFile = null;
        videoFileInput.value = '';
        videoInfoContainer.style.display = 'none';
        videoDropZone.style.display = 'block';
        videoRecognizeBtn.disabled = true;
        videoResultContainer.style.display = 'none';
        videoStats.style.display = 'none';
        resultVideo.src = '';
        clearResults();
    }

    async function recognizeVideo() {
        if (!currentVideoFile) return;

        showLoading('正在处理视频，请耐心等待...', '视频处理可能需要较长时间');
        const startTime = performance.now();

        try {
            const formData = new FormData();
            formData.append('file', currentVideoFile);

            const response = await fetch('/api/recognize_video', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);

            if (data.success) {
                showVideoResults(data, elapsed);
            } else {
                alert('视频识别失败: ' + data.error);
            }
        } catch (error) {
            alert('请求失败: ' + error.message);
        } finally {
            hideLoading();
        }
    }

    function showVideoResults(data, elapsed) {
        clearResults();

        // 显示结果视频
        const videoBlob = base64ToBlob(data.video, 'video/mp4');
        const videoUrl = URL.createObjectURL(videoBlob);
        resultVideo.src = videoUrl;
        videoResultContainer.style.display = 'block';

        // 下载按钮
        downloadVideoBtn.href = videoUrl;

        // 显示统计信息
        const stats = data.stats;
        videoStats.innerHTML = `
            <div class="video-stat-item">
                <div class="video-stat-value">${stats.total_frames}</div>
                <div class="video-stat-label">总帧数</div>
            </div>
            <div class="video-stat-item">
                <div class="video-stat-value">${stats.processed_frames}</div>
                <div class="video-stat-label">已处理帧</div>
            </div>
            <div class="video-stat-item">
                <div class="video-stat-value">${stats.fps}</div>
                <div class="video-stat-label">帧率(FPS)</div>
            </div>
            <div class="video-stat-item">
                <div class="video-stat-value">${stats.resolution}</div>
                <div class="video-stat-label">分辨率</div>
            </div>
            <div class="video-stat-item">
                <div class="video-stat-value">${stats.elapsed}s</div>
                <div class="video-stat-label">处理耗时</div>
            </div>
            <div class="video-stat-item">
                <div class="video-stat-value">${stats.total_detections}</div>
                <div class="video-stat-label">检测次数</div>
            </div>
        `;

        // 显示识别到的车牌
        if (stats.unique_plates && stats.unique_plates.length > 0) {
            const platesHtml = stats.unique_plates.map(p =>
                `<span class="video-plate-tag">${p}</span>`
            ).join('');
            videoStats.innerHTML += `
                <div style="width:100%;">
                    <div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">识别到的车牌号</div>
                    <div class="video-plates-list">${platesHtml}</div>
                </div>
            `;
        }

        videoStats.style.display = 'flex';

        // 显示耗时
        timeValue.textContent = elapsed;
        timeInfo.style.display = 'flex';
    }

    function base64ToBlob(base64, mimeType) {
        const bytes = atob(base64);
        const buffer = new ArrayBuffer(bytes.length);
        const array = new Uint8Array(buffer);
        for (let i = 0; i < bytes.length; i++) {
            array[i] = bytes.charCodeAt(i);
        }
        return new Blob([buffer], { type: mimeType });
    }

    // ===== 辅助函数 =====
    function createPlateCard(result, index) {
        const card = document.createElement('div');
        card.className = 'plate-card';
        card.style.animationDelay = (index * 0.1) + 's';
        card.innerHTML = `
            <div class="plate-card-left">
                <div class="plate-icon">
                    <i class="fas fa-car"></i>
                </div>
                <div class="plate-info">
                    <h3>${result.plate_no}</h3>
                    <div class="plate-meta">
                        <span><i class="fas fa-palette"></i> ${result.plate_color}</span>
                        <span><i class="fas fa-layer-group"></i> ${result.plate_type}</span>
                    </div>
                </div>
            </div>
            <div class="plate-card-right">
                <div class="confidence">置信度</div>
                <div class="confidence-value">${(result.detect_conf * 100).toFixed(1)}%</div>
            </div>
        `;
        return card;
    }

    function showNoResult() {
        resultCards.innerHTML = `
            <div class="plate-card" style="justify-content: center; text-align: center;">
                <div class="plate-info">
                    <h3 style="color: var(--warning);">未检测到车牌</h3>
                    <div class="plate-meta">
                        <span>请尝试更清晰的图片</span>
                    </div>
                </div>
            </div>
        `;
        resultCards.style.display = 'flex';
    }

    function clearResults() {
        resultImage.style.display = 'none';
        resultImage.src = '';
        resultPlaceholder.style.display = 'flex';
        resultCards.style.display = 'none';
        resultCards.innerHTML = '';
        batchResults.style.display = 'none';
        batchSummary.innerHTML = '';
        batchList.innerHTML = '';
        timeInfo.style.display = 'none';
    }

    function showLoading(text, progress = '') {
        loadingText.textContent = text;
        loadingProgress.textContent = progress;
        loadingOverlay.classList.add('active');
    }

    function hideLoading() {
        loadingOverlay.classList.remove('active');
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    async function checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            if (data.status === 'ok') {
                statusDot.classList.add('online');
                statusText.textContent = '服务就绪 (' + data.device + ')';
            }
        } catch (error) {
            statusText.textContent = '服务未连接';
        }
    }
});
