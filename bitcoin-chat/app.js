const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api/bitcoin'
    : '/api/bitcoin';

const messagesEl = document.getElementById('messages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const nodeStatus = document.getElementById('nodeStatus');
const heightPill = document.getElementById('heightPill');
const chatPanel = document.querySelector('.chat-panel');

let sessionId = localStorage.getItem('bitcoinChatSessionId');

const starterMessage = {
    role: 'assistant',
    text: 'Ask me about the latest block, mempool fees, transaction confirmations, or node sync. I only use read-only blockchain queries.',
};

function addMessage({ role, text, data, warnings, toolsUsed, loading = false, error = false }) {
    const el = document.createElement('article');
    el.className = `message ${role}${loading ? ' loading' : ''}${error ? ' error' : ''}`;
    if (loading) {
        const loadingText = document.createElement('span');
        loadingText.textContent = text;
        const dots = document.createElement('span');
        dots.className = 'typing-dots';
        dots.setAttribute('aria-hidden', 'true');
        dots.innerHTML = '<span></span><span></span><span></span>';
        el.append(loadingText, dots);
    } else {
        el.textContent = text;
    }

    if (toolsUsed?.length || warnings?.length) {
        const meta = document.createElement('div');
        meta.className = 'meta';
        if (toolsUsed?.length) {
            const tools = document.createElement('span');
            tools.textContent = `Tools: ${toolsUsed.join(', ')}`;
            meta.appendChild(tools);
        }
        warnings?.forEach((warning) => {
            const warningEl = document.createElement('span');
            warningEl.textContent = warning;
            meta.appendChild(warningEl);
        });
        el.appendChild(meta);
    }

    if (data) {
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        const pre = document.createElement('pre');
        summary.textContent = 'Tool data';
        pre.textContent = JSON.stringify(data, null, 2);
        details.append(summary, pre);
        el.appendChild(details);
    }

    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
}

async function fetchJson(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}

async function refreshStatus() {
    try {
        const status = await fetchJson(`${API_BASE}/status`);
        const source = status.source === 'node' ? 'live node' : 'demo mode';
        nodeStatus.textContent = `${source} | ${status.chain || 'main'} | ${status.initial_block_download ? 'syncing' : 'synced'}`;
        heightPill.textContent = `Height ${status.blocks ?? '--'}`;
    } catch (error) {
        nodeStatus.textContent = 'Node status unavailable';
        heightPill.textContent = 'Height --';
    }
}

async function sendMessage(text) {
    addMessage({ role: 'user', text });
    const loadingEl = addMessage({ role: 'assistant', text: 'Checking the chain...', loading: true });
    setBusy(true);

    try {
        const payload = {
            message: text,
            session_id: sessionId,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        };
        const result = await fetchJson(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        sessionId = result.session_id;
        localStorage.setItem('bitcoinChatSessionId', sessionId);
        loadingEl.remove();
        addMessage({
            role: 'assistant',
            text: result.answer,
            data: result.data,
            warnings: result.warnings,
            toolsUsed: result.tools_used,
        });
        await refreshStatus();
    } catch (error) {
        loadingEl.remove();
        addMessage({ role: 'assistant', text: error.message, error: true });
    } finally {
        setBusy(false);
        messageInput.focus();
    }
}

function setBusy(isBusy) {
    chatForm.querySelector('button').disabled = isBusy;
    messageInput.disabled = isBusy;
}

function canScrollMessages() {
    return messagesEl.scrollHeight > messagesEl.clientHeight;
}

function shouldKeepNativeScroll(target) {
    return target.closest('.messages, textarea, pre, .suggestions');
}

function normalizeWheelDelta(event) {
    if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) {
        return event.deltaY * 32;
    }
    if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) {
        return event.deltaY * messagesEl.clientHeight;
    }
    return event.deltaY;
}

chatPanel.addEventListener('wheel', (event) => {
    if (!canScrollMessages() || shouldKeepNativeScroll(event.target)) return;
    event.preventDefault();
    messagesEl.scrollTop += normalizeWheelDelta(event) * 1.8;
}, { passive: false });

let touchStartY = null;

chatPanel.addEventListener('touchstart', (event) => {
    if (shouldKeepNativeScroll(event.target)) return;
    touchStartY = event.touches[0]?.clientY ?? null;
}, { passive: true });

chatPanel.addEventListener('touchmove', (event) => {
    if (touchStartY === null || !canScrollMessages() || shouldKeepNativeScroll(event.target)) return;
    const currentY = event.touches[0]?.clientY ?? touchStartY;
    const deltaY = touchStartY - currentY;
    if (deltaY === 0) return;
    event.preventDefault();
    messagesEl.scrollTop += deltaY;
    touchStartY = currentY;
}, { passive: false });

chatPanel.addEventListener('touchend', () => {
    touchStartY = null;
});

messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = `${messageInput.scrollHeight}px`;
});

messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});

chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const text = messageInput.value.trim();
    if (!text) return;
    messageInput.value = '';
    messageInput.style.height = 'auto';
    await sendMessage(text);
});

document.querySelectorAll('[data-prompt]').forEach((button) => {
    button.addEventListener('click', () => {
        sendMessage(button.dataset.prompt);
    });
});

addMessage(starterMessage);
refreshStatus();
