// Navigation
function showSection(id) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.currentTarget.classList.add('active');
}

function formatMessage(text) {
    if (!text) return '';

    // Convert **bold** to <strong>
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert *italic* to <em>
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert ### headings
    text = text.replace(/^### (.*$)/gm, '<h4 style="color:#fff;margin:10px 0 4px">$1</h4>');

    // Convert ## headings
    text = text.replace(/^## (.*$)/gm, '<h3 style="color:#4ade80;margin:12px 0 6px">$1</h3>');

    // Convert bullet points - to li
    text = text.replace(/^\- (.*$)/gm, '<li style="margin:4px 0;color:#cbd5e1">$1</li>');

    // Convert numbered lists
    text = text.replace(/^\d+\. (.*$)/gm, '<li style="margin:4px 0;color:#cbd5e1">$1</li>');

    // Wrap consecutive li items in ul
    text = text.replace(/(<li.*<\/li>\n?)+/g, '<ul style="padding-left:18px;margin:8px 0">$&</ul>');

    // Convert line breaks to <br>
    text = text.replace(/\n\n/g, '<br><br>');
    text = text.replace(/\n/g, '<br>');

    return text;
}
// Run Agent via WebSocket
async function runAgent(agentId) {
    const logEl = document.getElementById(`log-${agentId}`) ||
                  document.getElementById(`log-${agentId}-pub`);

    if (!logEl) return;

    logEl.style.display = 'block';
    logEl.textContent   = '';

    const btn = event.currentTarget;
    btn.disabled    = true;
    btn.textContent = '⏳ Running...';

    const agentNames = {
        '1': 'Creative Head',
        '2': 'Visual Designer',
        '3': 'Analytics Manager',
        '4': 'Executive Reporter',
        '5': 'Auto Publisher'
    };

    logEl.textContent = `Starting Agent ${agentId} — ${agentNames[agentId] || ''}...\n`;
    logEl.textContent += `Please wait, this may take 30–90 seconds...\n`;

    // Animate dots while waiting
    let dots = 0;
    const timer = setInterval(() => {
        dots++;
        logEl.textContent = logEl.textContent.replace(/\n⏳.*/, '');
        logEl.textContent += `\n⏳ Running${'...'.slice(0, dots % 4)}`;
        logEl.scrollTop = logEl.scrollHeight;
    }, 1000);

    try {
        const response = await fetch(`/api/run-agent/${agentId}`, {
            method: 'POST'
        });

        clearInterval(timer);
        const data = await response.json();

        if (data.status === 'success') {
            logEl.textContent += `\n\n✅ ${data.message}`;
            logEl.textContent += `\n🔄 Refresh the page to see updated data.`;
        } else {
            logEl.textContent += `\n\n❌ Error: ${data.detail}`;
        }

    } catch (err) {
        clearInterval(timer);
        logEl.textContent += `\n\n❌ Failed to connect: ${err.message}`;
    }

    btn.disabled    = false;
    btn.textContent = `▶ Run Agent ${agentId}`;
    logEl.scrollTop = logEl.scrollHeight;
}

// Send chat message
async function sendChat(agentNum) {
    const input   = document.getElementById(`chat-input-${agentNum}`);
    const chatBox = document.getElementById(`chat-box-${agentNum}`);
    const message = input.value.trim();

    if (!message) return;

    // Show user message
    chatBox.innerHTML += `
        <div class="chat-msg user">${message}</div>
    `;
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    chatBox.innerHTML += `
        <div class="chat-msg agent" id="${typingId}">
            <div class="sender">Agent ${agentNum}</div>
            <span>Thinking...</span>
        </div>
    `;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch(`/api/chat/agent${agentNum}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        // Remove typing indicator
        document.getElementById(typingId)?.remove();

        // Show agent reply
        chatBox.innerHTML += `
            <div class="chat-msg agent">
                <div class="sender">Agent ${agentNum}</div>
                ${formatMessage(data.reply || data.error)}
            </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
        document.getElementById(typingId)?.remove();
        chatBox.innerHTML += `
            <div class="chat-msg agent">
                <div class="sender">Agent ${agentNum}</div>
                Error connecting to agent. Make sure it's running.
            </div>
        `;
    }
}

// Send report
async function sendReport() {
    const status = document.getElementById('report-status');
    status.textContent = '⏳ Sending report...';
    try {
        const ws = new WebSocket('ws://localhost:8000/ws/agent/4');
        ws.onmessage = (e) => {
            if (e.data.startsWith('DONE::')) {
                status.textContent = '✅ Report sent successfully!';
                ws.close();
            }
        };
    } catch (err) {
        status.textContent = '❌ Error sending report.';
    }
}

// Refresh report iframe
function loadReport() {
    document.getElementById('report-frame').src = '/api/report?' + Date.now();
}

// Copy text to clipboard
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    });
}