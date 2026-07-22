// ── Tab Switcher (Login/Signup) ───────────────────
function switchTab(tab) {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const buttons = document.querySelectorAll('.tab-btn');

    if (tab === 'login') {
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
        buttons[0].classList.add('active');
        buttons[1].classList.remove('active');
    } else {
        signupForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
        buttons[1].classList.add('active');
        buttons[0].classList.remove('active');
    }
}

let chatHistory = [];

// ── Chat Logic ────────────────────────────────────
async function sendQuestion() {
    const input = document.getElementById('question-input');
    const chatBox = document.getElementById('chat-box');
    const question = input.value.trim();
    
    // We allow sending just the image, or text + image
    if (!question && !window.attachedImage) return;

    // Show user bubble (include image if attached)
    let imgHtml = '';
    if (window.attachedImage) {
        imgHtml = `<img src="data:${window.attachedImage.mime_type};base64,${window.attachedImage.data}" class="chat-sent-img" alt="Scanned question">`;
    }

    chatBox.innerHTML += `
    <div class="message user-msg">
      <span>🎓</span>
      <div class="bubble">
        ${imgHtml}
        <div>${escapeHtml(question || "Scanned Question Image")}</div>
      </div>
    </div>`;
    input.value = '';
    scrollBottom();

    // Hold a local reference to the image to send, then clear from the UI
    const imgToSend = window.attachedImage;
    if (window.removeImage) {
        window.removeImage();
    }

    // Typing dots
    const typingId = 'typing-' + Date.now();
    chatBox.innerHTML += `
    <div class="message bot-msg" id="${typingId}">
      <span>🤖</span>
      <div class="bubble">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>`;
    scrollBottom();

    // Call backend
    try {
        chatHistory.push({ role: 'User', content: question || "Scanned Image" });
        
        const payload = { question, history: chatHistory };
        if (imgToSend) {
            payload.image = imgToSend;
        }

        const res = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error('Server returned error status');
        }

        const typingEl = document.getElementById(typingId);
        const bubbleEl = typingEl ? typingEl.querySelector('.bubble') : null;
        if (bubbleEl) {
            // Clear typing dots
            bubbleEl.innerHTML = '';
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let done = false;
        let buffer = '';
        let accumulatedAnswer = '';

        while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;
            buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith('data: ')) {
                    try {
                        const jsonData = JSON.parse(trimmed.slice(6));
                        if (jsonData.text) {
                            accumulatedAnswer += jsonData.text;
                            if (bubbleEl) {
                                simulateTyping(bubbleEl, accumulatedAnswer);
                            }
                            scrollBottom();
                        } else if (jsonData.error) {
                            if (bubbleEl) {
                                bubbleEl.innerHTML = `⚠️ Error: ${escapeHtml(jsonData.error)}`;
                            }
                        }
                    } catch (e) {
                        console.error('Error parsing stream chunk:', e, 'Line:', trimmed);
                        if (bubbleEl && !accumulatedAnswer) {
                            bubbleEl.innerHTML = "⚠️ Error displaying response.";
                        }
                    }
                }
            }
        }
        
        if (accumulatedAnswer) {
            chatHistory.push({ role: 'AI', content: accumulatedAnswer });
        }
    } catch (err) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) {
            typingEl.querySelector('.bubble').textContent = '⚠️ Connection error.';
        }
    }
    scrollBottom();
}

function scrollBottom() {
    const chatBox = document.getElementById('chat-box');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function simulateTyping(element, rawText) {
    if (!rawText) {
        element.innerHTML = "<em>Empty response</em>";
        return;
    }
    
    // If it's called again while already typing (e.g. if streaming is re-enabled),
    // instantly render the updated text to avoid overlapping timeouts.
    if (element.dataset.typing) {
        element.innerHTML = marked.parse(rawText);
        scrollBottom();
        return;
    }
    
    element.dataset.typing = "true";
    let index = 0;
    const speed = 10; // ms per frame
    const charsPerFrame = 4;

    function typeWriter() {
        if (index < rawText.length) {
            index += charsPerFrame;
            if (index > rawText.length) index = rawText.length;
            element.innerHTML = marked.parse(rawText.substring(0, index));
            scrollBottom();
            setTimeout(typeWriter, speed);
        } else {
            element.innerHTML = marked.parse(rawText);
            scrollBottom();
            delete element.dataset.typing;
        }
    }
    
    typeWriter();
}

function exportChat() {
    if (chatHistory.length === 0) {
        alert("No chat history to export.");
        return;
    }
    let exportText = "# MARSHAI Chat Export\n\n";
    for (let msg of chatHistory) {
        exportText += `**${msg.role}**:\n${msg.content}\n\n---\n\n`;
    }
    const blob = new Blob([exportText], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'marshai-chat-export.md';
    a.click();
    URL.revokeObjectURL(url);
}