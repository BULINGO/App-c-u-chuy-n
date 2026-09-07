// --- BIẾN TOÀN CỤC PHÁT ÂM THANH ---
let currentAudioObject = null;
let currentPlayingSceneIndex = -1;
let isPlayingFullStory = false;
let speechRate = 1.0;
let currentStoryData = null;

function showCreateSection() {
    document.getElementById("createSection").style.display = "block";
    document.getElementById("librarySection").style.display = "none";
    
    document.getElementById("navHome").classList.add("active");
    document.getElementById("navLibrary").classList.remove("active");
    document.getElementById("navMyStories").classList.remove("active");
    
    scrollToCreate();
}

function showLibrarySection() {
    document.getElementById("createSection").style.display = "none";
    document.getElementById("librarySection").style.display = "block";
    
    document.getElementById("navHome").classList.remove("active");
    document.getElementById("navLibrary").classList.add("active");
    document.getElementById("navMyStories").classList.add("active");
    
    loadStoryHistory();
}

function scrollToCreate() {
    document.getElementById("createSection").scrollIntoView({
        behavior: "smooth"
    });
}

async function createStory() {
    let storyInput = document.getElementById("storyInput").value.trim();
    let age = document.getElementById("age").value;
    let style = document.getElementById("style").value;
    let voiceSelect = document.getElementById("voice");
    let voice = voiceSelect ? voiceSelect.value : "female";

    if (storyInput === "") {
        alert("Bạn hãy nhập ý tưởng câu chuyện trước nhé!");
        return;
    }

    // Hiển thị phần kết quả & loading
    let resultBox = document.getElementById("result");
    let loadingBox = document.getElementById("loadingBox");
    let storyOutput = document.getElementById("storyOutput");
    let btnSubmit = document.querySelector(".btn-submit");

    resultBox.style.display = "block";
    loadingBox.style.display = "block";
    storyOutput.style.display = "none";
    btnSubmit.disabled = true;

    // Dừng âm thanh cũ nếu có
    stopAudio();

    // Cuộn xuống khu vực kết quả
    resultBox.scrollIntoView({ behavior: "smooth" });

    try {
        const response = await fetch("/api/story/create", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                prompt: storyInput,
                age: age,
                style: style,
                voice: voice
            })
        });

        const resData = await response.json();

        loadingBox.style.display = "none";
        btnSubmit.disabled = false;

        if (!resData.success) {
            storyOutput.style.display = "block";
            storyOutput.innerHTML = `
                <div style="background: #fef2f2; border: 1px solid #fca5a5; padding: 20px; border-radius: 12px; color: #991b1b;">
                    <h3>⚠️ Đã xảy ra lỗi</h3>
                    <p>${resData.error || "Không thể khởi tạo câu chuyện với AI."}</p>
                </div>
            `;
            return;
        }

        const data = resData.data;
        renderStoryData(data, style, age);

    } catch (err) {
        loadingBox.style.display = "none";
        btnSubmit.disabled = false;
        storyOutput.style.display = "block";
        storyOutput.innerHTML = `
            <div style="background: #fef2f2; border: 1px solid #fca5a5; padding: 20px; border-radius: 12px; color: #991b1b;">
                <h3>⚠️ Không thể kết nối Máy chủ Backend</h3>
                <p>Vui lòng đảm bảo máy chủ Backend FastAPI đang chạy tại port 8000.</p>
                <p><small>Chi tiết lỗi: ${err.message}</small></p>
            </div>
        `;
    }
}

async function loadStoryHistory() {
    let grid = document.getElementById("libraryGrid");
    grid.innerHTML = `<p style="color: #64748b; padding: 20px; text-align: center;">Đang tải danh sách câu chuyện...</p>`;

    try {
        const response = await fetch("/api/story/history");
        const resData = await response.json();

        if (!resData.success || !resData.data || resData.data.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px 20px; background: #f8fafc; border-radius: 12px; color: #64748b;">
                    <div style="font-size: 40px; margin-bottom: 10px;">📖</div>
                    <h3>Chưa có câu chuyện nào trong Thư viện</h3>
                    <p style="font-size: 14px; margin-top: 5px;">Hãy nhập ý tưởng và tạo câu chuyện đầu tiên bằng AI!</p>
                    <button onclick="showCreateSection()" style="margin-top: 15px; background: #2878d4; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">
                        ✨ Tạo câu chuyện mới
                    </button>
                </div>
            `;
            return;
        }

        grid.innerHTML = resData.data.map(story => {
            let thumbUrl = "https://placehold.co/600x400/2878d4/ffffff?text=AI+Story";
            if (story.scenes && story.scenes.length > 0 && story.scenes[0].image_url) {
                thumbUrl = story.scenes[0].image_url;
            }

            return `
                <div class="library-card">
                    <div class="library-thumb">
                        <img src="${thumbUrl}" alt="${story.title}" loading="lazy" onerror="this.src='https://placehold.co/600x400/2878d4/ffffff?text=Truyen+AI'">
                    </div>
                    <div class="library-body">
                        <div class="library-title">${story.title}</div>
                        <div class="library-summary">${story.story_summary || story.user_input}</div>
                        <div class="library-date">🕒 ${story.created_at || 'Mới đây'} | 🎓 ${story.age || 'Tiểu học'}</div>
                    </div>
                    <div class="library-actions">
                        <button class="btn-view-story" onclick="viewStoryDetail('${story.id}')">📖 Xem lại</button>
                        <button class="btn-delete-story" onclick="deleteStory('${story.id}')">🗑️ Xóa</button>
                    </div>
                </div>
            `;
        }).join("");

    } catch (err) {
        grid.innerHTML = `<p style="color: #dc2626; text-align: center; padding: 20px;">Lỗi tải thư viện: ${err.message}</p>`;
    }
}

async function viewStoryDetail(storyId) {
    try {
        const response = await fetch(`/api/story/detail/${storyId}`);
        const resData = await response.json();

        if (resData.success && resData.data) {
            showCreateSection();
            document.getElementById("result").style.display = "block";
            document.getElementById("loadingBox").style.display = "none";
            renderStoryData(resData.data, resData.data.style || "Hoạt hình", resData.data.age || "Tiểu học");
            document.getElementById("result").scrollIntoView({ behavior: "smooth" });
        }
    } catch (err) {
        alert("Không thể tải chi tiết câu chuyện: " + err.message);
    }
}

async function deleteStory(storyId) {
    if (!confirm("Bạn có chắc chắn muốn xóa câu chuyện này khỏi Thư viện?")) return;

    try {
        const response = await fetch(`/api/story/delete/${storyId}`, { method: "DELETE" });
        const resData = await response.json();

        if (resData.success) {
            loadStoryHistory();
        } else {
            alert(resData.detail || "Không thể xóa câu chuyện!");
        }
    } catch (err) {
        alert("Lỗi khi xóa câu chuyện: " + err.message);
    }
}

function renderStoryData(data, style, age) {
    currentStoryData = data;
    let storyOutput = document.getElementById("storyOutput");
    storyOutput.style.display = "block";

    let charHtml = "";
    if (data.characters && data.characters.length > 0) {
        charHtml = data.characters.map(c => 
            typeof c === 'object' ? `<b>${c.name}</b> (${c.appearance || ''})` : `<b>${c}</b>`
        ).join(", ");
    } else {
        charHtml = "Mèo Bông, Thỏ Ngọc";
    }

    let scenesHtml = "";
    if (data.scenes && data.scenes.length > 0) {
        scenesHtml = data.scenes.map((scene, idx) => `
            <div class="scene-card" id="sceneCard_${idx}">
                <div class="scene-image-wrap">
                    <img src="${scene.image_url}" alt="Cảnh ${scene.scene_id || idx + 1}" loading="lazy" onerror="this.src='https://placehold.co/600x400/2878d4/ffffff?text=Anh+Hoat+Hinh'">
                </div>
                <div class="scene-content">
                    <div class="scene-number">🎬 CẢNH ${scene.scene_id || idx + 1}</div>
                    <div class="scene-narration">"${scene.narration || scene.description || ''}"</div>
                    <div class="scene-details">
                        📍 <b>Bối cảnh:</b> ${scene.background || 'Tự nhiên'}<br>
                        🎭 <b>Hành động:</b> ${scene.action || 'Diễn biến câu chuyện'}
                    </div>
                    <button class="btn-scene-audio" id="btnSceneAudio_${idx}" onclick="playSceneAudio(${idx})">
                        ▶️ Nghe giọng đọc Cảnh ${scene.scene_id || idx + 1}
                    </button>
                </div>
            </div>
        `).join("");
    }

    let evalBadge = "";
    if (data.evaluation) {
        evalBadge = `
            <div style="margin-top: 20px; text-align: center; background: #e0f2fe; padding: 12px; border-radius: 10px; color: #0369a1; font-weight: 600; font-size: 14px;">
                🛡️ AI Evaluator: ${data.evaluation.feedback || 'Nội dung đạt chuẩn an toàn & nhân văn cho học sinh tiểu học'} (Score: ${data.evaluation.score || 9}/10)
            </div>
        `;
    }

    storyOutput.innerHTML = `
        <div class="story-header-card">
            <h3>📚 ${data.title || 'Câu chuyện AI'}</h3>
            <div class="story-meta">
                <span class="meta-item">🎨 Phong cách: <b>${style}</b></span>
                <span class="meta-item">🎓 Lứa tuổi: <b>${age}</b></span>
                <span class="meta-item">✨ Chủ đề: <b>${data.theme || 'Tình bạn'}</b></span>
            </div>
            <p style="color: #475569; margin-bottom: 12px;"><b>Dàn nhân vật:</b> ${charHtml}</p>
            <p style="color: #475569; margin-bottom: 15px;"><b>Tóm tắt:</b> ${data.story_summary || ''}</p>
            ${data.moral ? `<div class="moral-box">💡 <b>Bài học giáo dục:</b> ${data.moral}</div>` : ''}
        </div>

        <!-- BẢNG ĐIỀU KHIỂN GIỌNG ĐỌC AI -->
        <div class="audio-player-bar">
            <div class="audio-player-title">
                <span>🗣️ Giọng đọc AI:</span>
                <div id="soundWaveIcon" class="sound-wave" style="display: none;">
                    <span></span><span></span><span></span><span></span>
                </div>
                <span id="audioStatusText" style="font-weight: 500; font-size: 13px; color: #475569;">Sẵn sàng phát</span>
            </div>
            <div class="audio-controls">
                <button class="btn-audio" id="btnPlayAll" onclick="playFullStoryAudio()">🔊 Đọc toàn bộ câu chuyện</button>
                <button class="btn-audio secondary" id="btnPauseAudio" onclick="pauseAudio()" style="display: none;">⏸️ Tạm dừng</button>
                <button class="btn-audio secondary" id="btnStopAudio" onclick="stopAudio()" style="display: none;">⏹️ Dừng</button>
                <select class="audio-speed-select" id="speedSelect" onchange="changeAudioSpeed(this.value)">
                    <option value="0.8">⚡ 0.8x (Chậm)</option>
                    <option value="1.0" selected>⚡ 1.0x (Chuẩn)</option>
                    <option value="1.2">⚡ 1.2x (Nhanh)</option>
                </select>
            </div>
        </div>

        <h3 style="color: #2878d4; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
            🖼️ Các phân cảnh trực quan (Qwen Image 3 Pro Agent)
        </h3>

        <div class="scenes-container">
            ${scenesHtml}
        </div>

        ${evalBadge}
    `;
}

// --- LOGIC PHÁT ÂM THANH GIỌNG ĐỌC ---

function changeAudioSpeed(val) {
    speechRate = parseFloat(val);
    if (currentAudioObject) {
        currentAudioObject.playbackRate = speechRate;
    }
}

function playFullStoryAudio() {
    if (!currentStoryData || !currentStoryData.scenes || currentStoryData.scenes.length === 0) {
        alert("Không tìm thấy dữ liệu phân cảnh để đọc!");
        return;
    }
    
    stopAudio();
    isPlayingFullStory = true;
    playSceneAudio(0);
}

function playSceneAudio(sceneIdx) {
    if (!currentStoryData || !currentStoryData.scenes || !currentStoryData.scenes[sceneIdx]) {
        return;
    }

    // Nếu đang phát chính cảnh này -> Tạm dừng/Phát tiếp
    if (currentPlayingSceneIndex === sceneIdx && currentAudioObject) {
        if (currentAudioObject.paused) {
            currentAudioObject.play();
            updateAudioUI(true, `Đang đọc Cảnh ${sceneIdx + 1}...`);
        } else {
            currentAudioObject.pause();
            updateAudioUI(false, `Tạm dừng Cảnh ${sceneIdx + 1}`);
        }
        return;
    }

    // Dừng âm thanh trước đó
    stopAudioStateOnly();

    currentPlayingSceneIndex = sceneIdx;
    let scene = currentStoryData.scenes[sceneIdx];
    let narrationText = scene.narration || scene.description || "";

    // Scroll cảnh đang đọc vào màn hình
    let cardEl = document.getElementById(`sceneCard_${sceneIdx}`);
    if (cardEl) {
        cardEl.scrollIntoView({ behavior: "smooth", block: "center" });
        cardEl.classList.add("active-narration");
    }

    // Nếu có audio_url từ server (Edge-TTS / gTTS)
    if (scene.audio_url) {
        currentAudioObject = new Audio(scene.audio_url);
        currentAudioObject.playbackRate = speechRate;

        currentAudioObject.play().then(() => {
            updateAudioUI(true, `Đang đọc Cảnh ${sceneIdx + 1}...`);
        }).catch(err => {
            console.warn("Lỗi phát audio MP3, chuyển sang Web Speech API:", err);
            speakTextBrowser(narrationText, sceneIdx);
        });

        currentAudioObject.onended = () => {
            onSceneAudioEnded(sceneIdx);
        };
    } else {
        // Fallback: Web Speech API của trình duyệt
        speakTextBrowser(narrationText, sceneIdx);
    }
}

function speakTextBrowser(text, sceneIdx) {
    if (!('speechSynthesis' in window)) {
        alert("Trình duyệt của bạn không hỗ trợ tính năng Đọc Văn Bản (Text-to-Speech).");
        return;
    }

    window.speechSynthesis.cancel();

    let utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'vi-VN';
    utterance.rate = speechRate;

    utterance.onstart = () => {
        updateAudioUI(true, `Đang đọc Cảnh ${sceneIdx + 1} (Browser Voice)...`);
    };

    utterance.onend = () => {
        onSceneAudioEnded(sceneIdx);
    };

    utterance.onerror = (e) => {
        console.error("SpeechSynthesis error:", e);
        onSceneAudioEnded(sceneIdx);
    };

    window.speechSynthesis.speak(utterance);
}

function onSceneAudioEnded(sceneIdx) {
    let cardEl = document.getElementById(`sceneCard_${sceneIdx}`);
    if (cardEl) {
        cardEl.classList.remove("active-narration");
    }

    if (isPlayingFullStory && currentStoryData && sceneIdx + 1 < currentStoryData.scenes.length) {
        // Tự động phát cảnh tiếp theo
        setTimeout(() => {
            playSceneAudio(sceneIdx + 1);
        }, 500);
    } else {
        // Hoàn thành đọc toàn bộ
        stopAudio();
        let statusText = document.getElementById("audioStatusText");
        if (statusText) statusText.innerText = "Đã hoàn thành đọc câu chuyện 🎉";
    }
}

function pauseAudio() {
    if (currentAudioObject && !currentAudioObject.paused) {
        currentAudioObject.pause();
        updateAudioUI(false, "Tạm dừng phát giọng đọc");
    } else if (window.speechSynthesis && window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
        updateAudioUI(false, "Tạm dừng phát giọng đọc");
    }
}

function stopAudioStateOnly() {
    if (currentAudioObject) {
        currentAudioObject.pause();
        currentAudioObject.currentTime = 0;
        currentAudioObject = null;
    }
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }

    // Gỡ highlight tất cả cảnh
    document.querySelectorAll(".scene-card").forEach(card => {
        card.classList.remove("active-narration");
    });
}

function stopAudio() {
    stopAudioStateOnly();
    isPlayingFullStory = false;
    currentPlayingSceneIndex = -1;
    updateAudioUI(false, "Sẵn sàng phát");
}

function updateAudioUI(isPlaying, statusMsg) {
    let soundWave = document.getElementById("soundWaveIcon");
    let statusText = document.getElementById("audioStatusText");
    let btnPause = document.getElementById("btnPauseAudio");
    let btnStop = document.getElementById("btnStopAudio");

    if (soundWave) soundWave.style.display = isPlaying ? "inline-flex" : "none";
    if (statusText) statusText.innerText = statusMsg || (isPlaying ? "Đang đọc..." : "Tạm dừng");

    if (btnPause) btnPause.style.display = isPlaying ? "inline-block" : "none";
    if (btnStop) btnStop.style.display = (isPlaying || currentPlayingSceneIndex >= 0) ? "inline-block" : "none";
}
