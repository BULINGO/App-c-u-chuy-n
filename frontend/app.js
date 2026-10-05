// --- BIẾN TOÀN CỤC PHÁT ÂM THANH & BẢO MẬT ---
let currentAudioObject = null;
let currentPlayingSceneIndex = -1;
let isPlayingFullStory = false;
let speechRate = 1.0;
let currentStoryData = null;

// Trạng thái mở khóa Truyện của tôi (Mật khẩu: 123456)
let isMyStoriesUnlocked = false;

// Khởi tạo trước danh sách giọng đọc của trình duyệt
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
}

// Điền mẫu gợi ý nhanh vào ô nhập truyện
function fillTemplate(type) {
    const input = document.getElementById("storyInput");
    const styleSelect = document.getElementById("style");
    if (!input) return;
    
    if (type === 'scenes') {
        input.value = "Cảnh 1: Bé Na tìm thấy chú mèo con lông vàng bị ướt sũng dưới gốc cây bàng trong cơn mưa rào.\nCảnh 2: Bé Na ân cần mang mèo về nhà sưởi ấm, lau khô lông và cho uống một bát sữa ấm thơm lừng.\nCảnh 3: Sáng hôm sau mèo con khỏe mạnh, vui vẻ vờn cuộn len cùng Bé Na và trở thành người bạn thân thiết.";
        if (styleSelect) styleSelect.value = "Hoạt hình";
    } else if (type === 'fantasy') {
        input.value = "Cảnh 1: Bé Bo nhặt được một viên ngọc phát sáng lung linh rơi từ bầu trời đêm xuống khu vườn kỳ diệu.\nCảnh 2: Viên ngọc biến thành một chú kỳ lân nhỏ có cánh lấp lánh, cùng Bo bay qua đám mây ngũ sắc để tìm đường về vương quốc ánh sao.\nCảnh 3: Chú kỳ lân tặng Bo chiếc lông vũ ước nguyện rồi bay về bầu trời diệu kỳ, Bo mỉm cười hạnh phúc bên người bạn kỳ ảo.";
        if (styleSelect) styleSelect.value = "Kỳ ảo";
    } else if (type === 'friendship') {
        input.value = "Kể về bạn Rùa và Thỏ cùng nhau đoàn kết giúp đỡ các bạn thú nhỏ vượt qua dòng suối sau cơn mưa lớn trong khu rừng xanh.";
        if (styleSelect) styleSelect.value = "Dễ thương";
    } else if (type === 'adventure') {
        input.value = "Cảnh 1: Chú cún Bông tìm thấy một chiếc chìa khóa lấp lánh trong khu vườn hoa rực rỡ.\nCảnh 2: Bông cùng bạn Mèo Miu tìm kiếm và mở được chiếc rương kho báu chứa đầy hạt giống hoa diệu kỳ.\nCảnh 3: Cả hai cùng gieo hạt, khu vườn nở rộ muôn sắc màu đem lại niềm vui cho cả xóm nhỏ.";
        if (styleSelect) styleSelect.value = "Cổ tích";
    }
    input.focus();
}

// ================= ĐIỀU HƯỚNG CÁC TRANG =================

function showCreateSection() {
    document.getElementById("createSection").style.display = "block";
    document.getElementById("librarySection").style.display = "none";
    document.getElementById("myStoriesSection").style.display = "none";
    
    document.getElementById("navHome").classList.add("active");
    document.getElementById("navLibrary").classList.remove("active");
    document.getElementById("navMyStories").classList.remove("active");
    
    scrollToCreate();
}

function showLibrarySection() {
    document.getElementById("createSection").style.display = "none";
    document.getElementById("librarySection").style.display = "block";
    document.getElementById("myStoriesSection").style.display = "none";
    
    document.getElementById("navHome").classList.remove("active");
    document.getElementById("navLibrary").classList.add("active");
    document.getElementById("navMyStories").classList.remove("active");
    
    loadStoryHistory();
}

function showMyStoriesSection() {
    if (!isMyStoriesUnlocked) {
        openSecurityModal();
        return;
    }

    document.getElementById("createSection").style.display = "none";
    document.getElementById("librarySection").style.display = "none";
    document.getElementById("myStoriesSection").style.display = "block";
    
    document.getElementById("navHome").classList.remove("active");
    document.getElementById("navLibrary").classList.remove("active");
    document.getElementById("navMyStories").classList.add("active");
    
    loadMyStories();
}

function scrollToCreate() {
    document.getElementById("createSection").scrollIntoView({
        behavior: "smooth"
    });
}

// ================= MODAL MẬT KHẨU (123456) =================

function openSecurityModal() {
    const modal = document.getElementById("securityModal");
    const errorBox = document.getElementById("securityModalError");
    const pwdInput = document.getElementById("securityPasswordInput");

    errorBox.style.display = "none";
    errorBox.innerText = "";
    pwdInput.value = "";

    modal.style.display = "flex";
    setTimeout(() => {
        pwdInput.focus();
    }, 100);
}

function closeSecurityModal() {
    document.getElementById("securityModal").style.display = "none";
}

async function submitSecurityModal() {
    const pwdInput = document.getElementById("securityPasswordInput").value.trim();
    const errorBox = document.getElementById("securityModalError");
    errorBox.style.display = "none";

    if (!pwdInput) {
        errorBox.innerText = "Vui lòng nhập mật khẩu!";
        errorBox.style.display = "block";
        return;
    }

    // Kiểm tra nhanh trực tiếp 123456 hoặc qua API backend
    if (pwdInput === "123456") {
        isMyStoriesUnlocked = true;
        closeSecurityModal();
        showMyStoriesSection();
        return;
    }

    try {
        const res = await fetch("/api/story/auth/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: pwdInput })
        });
        const data = await res.json();

        if (data.success) {
            isMyStoriesUnlocked = true;
            closeSecurityModal();
            showMyStoriesSection();
        } else {
            errorBox.innerText = "Mật khẩu không đúng. Vui lòng nhập lại!";
            errorBox.style.display = "block";
        }
    } catch (err) {
        // Fallback kiểm tra client nếu mất mạng
        if (pwdInput === "123456") {
            isMyStoriesUnlocked = true;
            closeSecurityModal();
            showMyStoriesSection();
        } else {
            errorBox.innerText = "Mật khẩu không chính xác!";
            errorBox.style.display = "block";
        }
    }
}

// Nhấn Enter để gửi mật khẩu
document.getElementById("securityPasswordInput")?.addEventListener("keyup", function (e) {
    if (e.key === "Enter") {
        submitSecurityModal();
    }
});

function lockMyStories() {
    isMyStoriesUnlocked = false;
    showLibrarySection();
}

// ================= TẠO CÂU CHUYỆN AI =================

async function createStory() {
    let storyInput = document.getElementById("storyInput").value.trim();
    let age = document.getElementById("age").value;
    let style = document.getElementById("style").value;
    let voiceSelect = document.getElementById("voice");
    let voice = voiceSelect ? voiceSelect.value : "female";
    let isPrivate = document.getElementById("storyIsPrivate").checked;

    if (storyInput === "") {
        alert("Bạn hãy nhập ý tưởng câu chuyện trước nhé!");
        return;
    }

    let resultBox = document.getElementById("result");
    let loadingBox = document.getElementById("loadingBox");
    let storyOutput = document.getElementById("storyOutput");
    let btnSubmit = document.querySelector(".btn-submit");

    resultBox.style.display = "block";
    loadingBox.style.display = "block";
    storyOutput.style.display = "none";
    btnSubmit.disabled = true;

    stopAudio();
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
                voice: voice,
                is_private: isPrivate
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

// ================= TẢI THƯ VIỆN CÔNG KHAI =================

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
                    <p style="font-size: 14px; margin-top: 5px;">Hãy tạo câu chuyện mới bằng AI!</p>
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
                        <button class="btn-delete-story" onclick="deleteStory('${story.id}', 'public')">🗑️ Xóa</button>
                    </div>
                </div>
            `;
        }).join("");

    } catch (err) {
        grid.innerHTML = `<p style="color: #dc2626; text-align: center; padding: 20px;">Lỗi tải thư viện: ${err.message}</p>`;
    }
}

// ================= TẢI TRUYỆN CỦA TÔI =================

async function loadMyStories() {
    let grid = document.getElementById("myStoriesGrid");
    grid.innerHTML = `<p style="color: #64748b; padding: 20px; text-align: center;">Đang tải danh sách Truyện của tôi...</p>`;

    try {
        const response = await fetch("/api/story/my-stories");
        const resData = await response.json();

        if (!resData.success || !resData.data || resData.data.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px 20px; background: #f8fafc; border-radius: 12px; color: #64748b;">
                    <div style="font-size: 40px; margin-bottom: 10px;">📖</div>
                    <h3>Chưa có câu chuyện nào trong Truyện của tôi</h3>
                    <p style="font-size: 14px; margin-top: 5px;">Khi tạo câu chuyện, hãy tích chọn <b>Lưu vào Truyện của tôi</b> để lưu vào đây.</p>
                    <button onclick="showCreateSection()" style="margin-top: 15px; background: #2878d4; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">
                        ✨ Tạo câu chuyện mới
                    </button>
                </div>
            `;
            return;
        }

        grid.innerHTML = resData.data.map(story => {
            let thumbUrl = "https://placehold.co/600x400/2878d4/ffffff?text=Truyen+Cua+Toi";
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
                        <button class="btn-delete-story" onclick="deleteStory('${story.id}', 'private')">🗑️ Xóa</button>
                    </div>
                </div>
            `;
        }).join("");

    } catch (err) {
        grid.innerHTML = `<p style="color: #dc2626; text-align: center; padding: 20px;">Lỗi tải truyện: ${err.message}</p>`;
    }
}

// ================= THAO TÁC XEM & XÓA TRUYỆN =================

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

async function deleteStory(storyId, fromSection) {
    if (!confirm("Bạn có chắc chắn muốn xóa câu chuyện này?")) return;

    try {
        const response = await fetch(`/api/story/delete/${storyId}`, { method: "DELETE" });
        const resData = await response.json();

        if (resData.success) {
            if (fromSection === 'private') {
                loadMyStories();
            } else {
                loadStoryHistory();
            }
        } else {
            alert(resData.detail || "Không thể xóa câu chuyện!");
        }
    } catch (err) {
        alert("Lỗi khi xóa câu chuyện: " + err.message);
    }
}

// ================= RENDER DỮ LIỆU CÂU CHUYỆN =================

function renderStoryData(data, style, age) {
    stopAudio();
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
    `;
}

// ================= LOGIC PHÁT ÂM THANH GIỌNG ĐỌC =================

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

    stopAudioStateOnly();

    currentPlayingSceneIndex = sceneIdx;
    let scene = currentStoryData.scenes[sceneIdx];
    let narrationText = scene.narration || scene.description || "";

    let cardEl = document.getElementById(`sceneCard_${sceneIdx}`);
    if (cardEl) {
        cardEl.scrollIntoView({ behavior: "smooth", block: "center" });
        cardEl.classList.add("active-narration");
    }

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

    const voices = window.speechSynthesis.getVoices();
    const viVoice = voices.find(v => 
        v.lang.toLowerCase().includes('vi') || 
        v.lang.toLowerCase().includes('vn') || 
        v.name.toLowerCase().includes('vietnam') ||
        v.name.toLowerCase().includes('hoaimy') ||
        v.name.toLowerCase().includes('namminh')
    );

    if (viVoice) {
        utterance.voice = viVoice;
    }

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
        setTimeout(() => {
            playSceneAudio(sceneIdx + 1);
        }, 500);
    } else {
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
