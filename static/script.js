// ==========================================
// Global State
// ==========================================
let currentWord = null;
let currentAudio = null;
const card = document.getElementById('card');
const loader = document.getElementById('loader');

// ==========================================
// Utility Functions
// ==========================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showLoader() {
    loader.classList.add('active');
}

function hideLoader() {
    loader.classList.remove('active');
}

function flipCard() {
    card.classList.add('is-flipped');
}

function unflipCard() {
    card.classList.remove('is-flipped');
}

// ==========================================
// Initialize Dropdowns
// ==========================================

async function loadVoices() {
    try {
        const response = await fetch('/api/voices');
        const data = await response.json();

        if (data.success && data.voices) {
            const select = document.getElementById('voiceSelect');
            select.innerHTML = '';

            data.voices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice.id;
                option.textContent = voice.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load voices:', error);
    }
}

async function loadLevels() {
    try {
        const response = await fetch('/api/levels');
        const data = await response.json();

        if (data.success && data.levels) {
            const select = document.getElementById('levelSelect');
            select.innerHTML = '';

            data.levels.forEach(level => {
                const option = document.createElement('option');
                option.value = level.id;
                option.textContent = `${level.name} (${level.count} words)`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load levels:', error);
    }
}

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();

        if (data.success && data.models) {
            // Load text models
            const textSelect = document.getElementById('textModelSelect');
            textSelect.innerHTML = '';
            data.models.text_models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                textSelect.appendChild(option);
            });

            // Load audio models
            const audioSelect = document.getElementById('audioModelSelect');
            audioSelect.innerHTML = '';
            data.models.audio_models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                audioSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

// ==========================================
// Word Card Generation
// ==========================================

async function generateWordCard(targetWord = null) {
    const voiceId = document.getElementById('voiceSelect').value;
    const level = document.getElementById('levelSelect').value;
    const textModel = document.getElementById('textModelSelect').value;
    const audioModel = document.getElementById('audioModelSelect').value;

    showLoader();

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                word: targetWord || '',
                voice_id: voiceId,
                level: level,
                text_model: textModel,
                audio_model: audioModel
            })
        });

        const data = await response.json();

        if (data.success) {
            currentWord = data.word;
            displayWordCard(data);
            flipCard();
            showToast('Word card generated!', 'success');
        } else {
            showToast(data.error || 'Failed to generate word card', 'error');
        }
    } catch (error) {
        console.error('Error generating word card:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        hideLoader();
    }
}

function displayWordCard(data) {
    // Set word title
    document.getElementById('wordTitle').textContent = data.word;

    // Set phonetic transcription (below title)
    const phoneticText = document.getElementById('phoneticText');
    const sections = data.sections || {};
    const phonetic = sections['Phonetic Transcription'] || '';

    if (phonetic) {
        // Remove any ** markdown and ensure format is [/phonetic/]
        let cleanPhonetic = phonetic.replace(/\*\*/g, '').trim();

        // Ensure it has brackets and slashes
        if (!cleanPhonetic.startsWith('[')) {
            cleanPhonetic = '[' + cleanPhonetic;
        }
        if (!cleanPhonetic.endsWith(']')) {
            cleanPhonetic = cleanPhonetic + ']';
        }
        // Ensure it has slashes inside brackets
        if (!cleanPhonetic.includes('/')) {
            cleanPhonetic = cleanPhonetic.replace('[', '[/').replace(']', '/]');
        }

        phoneticText.textContent = cleanPhonetic;
    } else {
        phoneticText.textContent = '';
    }

    // Set header image
    const header = document.getElementById('cardHeader');
    if (data.image_url) {
        header.style.backgroundImage = `url(${data.image_url})`;
    } else {
        header.style.backgroundImage = 'none';
    }

    // Build content sections
    const content = document.getElementById('cardContent');
    content.innerHTML = '';

    // Order of sections - must match backend keys exactly
    // Exclude Phonetic Transcription as it's displayed separately
    const sectionOrder = [
        'Definition',
        'Synonyms',
        'Antonyms',
        'Example Sentences',
        'Writing'
    ];

    sectionOrder.forEach(sectionName => {
        if (sections[sectionName]) {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'section';

            const heading = document.createElement('h3');
            heading.textContent = sectionName;

            const paragraph = document.createElement('p');
            paragraph.innerHTML = sections[sectionName];

            sectionDiv.appendChild(heading);
            sectionDiv.appendChild(paragraph);

            // Add audio button for Writing section
            if (sectionName === 'Writing' && data.explanation_audio_url) {
                const audioBtn = document.createElement('button');
                audioBtn.className = 'audio-btn';
                audioBtn.style.marginLeft = '10px';
                audioBtn.innerHTML = '<img src="https://api.iconify.design/solar:play-stream-bold.svg" alt="Play" class="play-icon" id="writingPlayIcon">';
                audioBtn.onclick = () => toggleAudio(data.explanation_audio_url, 'writingPlayIcon');
                heading.appendChild(audioBtn);
            }

            content.appendChild(sectionDiv);
        }
    });

    // Store audio URLs for playback
    currentWord = {
        word: data.word,
        audioUrl: data.word_audio_url,
        explanationAudioUrl: data.explanation_audio_url
    };

    // Reset audio state
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
}

// ==========================================
// Audio Playback
// ==========================================

let currentAudioUrl = null;
let currentIconId = null;

function toggleAudio(url, iconId) {
    if (!url) {
        showToast('Audio not available', 'error');
        return;
    }

    const icon = document.getElementById(iconId);

    // If this is the same audio and it's playing, pause it
    if (currentAudio && currentAudioUrl === url && !currentAudio.paused) {
        currentAudio.pause();
        if (icon) {
            icon.src = 'https://api.iconify.design/solar:play-stream-bold.svg';
        }
        return;
    }

    // If there's a different audio playing, stop it and reset its icon
    if (currentAudio && currentAudioUrl !== url) {
        currentAudio.pause();
        if (currentIconId && document.getElementById(currentIconId)) {
            document.getElementById(currentIconId).src = 'https://api.iconify.design/solar:play-stream-bold.svg';
        }
    }

    // If this is the same audio and it's paused, resume it
    if (currentAudio && currentAudioUrl === url && currentAudio.paused) {
        currentAudio.play().catch(error => {
            console.error('Audio playback failed:', error);
            showToast('Audio playback failed', 'error');
        });
        if (icon) {
            icon.src = 'https://api.iconify.design/solar:pause-bold.svg';
        }
        return;
    }

    // Create new audio and play
    currentAudio = new Audio(url);
    currentAudioUrl = url;
    currentIconId = iconId;

    currentAudio.play().catch(error => {
        console.error('Audio playback failed:', error);
        showToast('Audio playback failed', 'error');
        if (icon) {
            icon.src = 'https://api.iconify.design/solar:play-stream-bold.svg';
        }
    });

    // Update icon to pause
    if (icon) {
        icon.src = 'https://api.iconify.design/solar:pause-bold.svg';
    }

    // When audio ends, reset icon
    currentAudio.onended = () => {
        if (icon) {
            icon.src = 'https://api.iconify.design/solar:play-stream-bold.svg';
        }
        currentAudioUrl = null;
        currentIconId = null;
    };
}

function playAudio(url) {
    if (!url) {
        showToast('Audio not available', 'error');
        return;
    }

    // Stop current audio if playing
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
    }

    currentAudio = new Audio(url);
    currentAudio.play().catch(error => {
        console.error('Audio playback failed:', error);
        showToast('Audio playback failed', 'error');
    });
}

// ==========================================
// Chat Functionality
// ==========================================

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';

    // Get selected models
    const voiceId = document.getElementById('voiceSelect').value;
    const textModel = document.getElementById('textModelSelect').value;
    const audioModel = document.getElementById('audioModelSelect').value;

    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                voice_id: voiceId,
                text_model: textModel,
                audio_model: audioModel
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        // Create assistant message placeholder
        const messageDiv = addChatMessage('', 'assistant');
        const contentDiv = messageDiv.querySelector('.message-content') || messageDiv;
        let fullText = '';
        let audioUrl = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonData = JSON.parse(line.slice(6));

                    if (jsonData.error) {
                        showToast(jsonData.error, 'error');
                        break;
                    }

                    if (jsonData.chunk) {
                        fullText += jsonData.chunk;
                        contentDiv.textContent = fullText;
                        scrollChatToBottom();
                    }

                    if (jsonData.done && jsonData.audio_url) {
                        audioUrl = jsonData.audio_url;
                        // Add audio button
                        addAudioButton(messageDiv, audioUrl);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Chat error:', error);
        showToast('Chat error. Please try again.', 'error');
    }
}

function addChatMessage(text, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    scrollChatToBottom();

    return messageDiv;
}

function addAudioButton(messageDiv, audioUrl) {
    const audioBtn = document.createElement('button');
    audioBtn.className = 'chat-audio-btn';
    audioBtn.innerHTML = '<img src="https://api.iconify.design/solar:play-stream-bold.svg" alt="Play" style="width: 16px; height: 16px; filter: invert(45%) sepia(88%) saturate(1854%) hue-rotate(228deg) brightness(94%) contrast(91%);">';
    audioBtn.onclick = () => playAudio(audioUrl);
    messageDiv.appendChild(audioBtn);
}

function scrollChatToBottom() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ==========================================
// Event Listeners
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    // Load dropdown options
    loadVoices();
    loadLevels();
    loadModels();

    // Start Learning button
    document.getElementById('startBtn').addEventListener('click', () => {
        const wordInput = document.getElementById('wordInput');
        const targetWord = wordInput.value.trim();
        generateWordCard(targetWord || null);
    });

    // Word input - Enter key
    document.getElementById('wordInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const targetWord = e.target.value.trim();
            generateWordCard(targetWord || null);
        }
    });

    // Word audio button
    document.getElementById('wordAudioBtn').addEventListener('click', () => {
        if (currentWord && currentWord.audioUrl) {
            toggleAudio(currentWord.audioUrl, 'wordPlayIcon');
        } else {
            showToast('Please generate a word first', 'info');
        }
    });

    // Next word button
    document.getElementById('nextBtn').addEventListener('click', () => {
        generateWordCard(null);
    });

    // Home button
    document.getElementById('homeBtn').addEventListener('click', () => {
        unflipCard();
        document.getElementById('wordInput').value = '';
    });

    // Chat send button
    document.getElementById('sendBtn').addEventListener('click', sendChatMessage);

    // Chat input - Enter key
    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
});
