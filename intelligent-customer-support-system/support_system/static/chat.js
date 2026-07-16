const messagesEl = document.getElementById('messages');
const form = document.getElementById('composer-form');
const input = document.getElementById('composer-input');
const sendBtn = document.getElementById('send-btn');
const sessionId = window.__SESSION_ID__;

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function confidenceRing(confidence) {
  // confidence: 0..1
  const pct = Math.max(0, Math.min(1, confidence));
  const radius = 12;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct);
  const color = pct >= 0.35 ? '#4cae7d' : '#e15554';
  return `
    <svg width="30" height="30">
      <circle cx="15" cy="15" r="${radius}" stroke="#2c3542" stroke-width="2.5" fill="none" />
      <circle cx="15" cy="15" r="${radius}" stroke="${color}" stroke-width="2.5" fill="none"
        stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" stroke-linecap="round" />
    </svg>
    <span>${Math.round(pct * 100)}</span>
  `;
}

function appendUserMessage(text) {
  const div = document.createElement('div');
  div.className = 'msg user';
  div.innerHTML = `<div class="bubble"></div>`;
  div.querySelector('.bubble').textContent = text;
  messagesEl.appendChild(div);
  scrollToBottom();
}

function appendBotMessage({ response, confidence, escalated, intent }) {
  const div = document.createElement('div');
  div.className = 'msg bot';

  const confDiv = document.createElement('div');
  confDiv.className = 'confidence';
  confDiv.innerHTML = confidenceRing(confidence);

  const bubbleWrap = document.createElement('div');
  const bubble = document.createElement('div');
  bubble.className = 'bubble' + (escalated ? ' escalated' : '');
  bubble.textContent = response;

  const meta = document.createElement('div');
  meta.className = 'meta-line';
  meta.innerHTML = `<span>${intent ? 'intent: ' + intent : 'intent: unmatched'}</span>` +
    (escalated ? `<span class="escalate-tag">● escalated to agent</span>` : '');

  bubbleWrap.appendChild(bubble);
  bubbleWrap.appendChild(meta);

  div.appendChild(confDiv);
  div.appendChild(bubbleWrap);
  messagesEl.appendChild(div);
  scrollToBottom();
}

function showTyping() {
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.id = 'typing-indicator';
  div.innerHTML = '<span></span><span></span><span></span>';
  messagesEl.appendChild(div);
  scrollToBottom();
}

function hideTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

async function sendMessage(text) {
  appendUserMessage(text);
  input.value = '';
  sendBtn.disabled = true;
  showTyping();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    const data = await res.json();
    hideTyping();
    // small delay so the typing indicator feels natural
    setTimeout(() => appendBotMessage(data), 150);
  } catch (err) {
    hideTyping();
    appendBotMessage({
      response: "Something went wrong reaching the server. Please try again.",
      confidence: 0,
      escalated: true,
      intent: null,
    });
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  sendMessage(text);
});

document.querySelectorAll('.topic-chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    sendMessage(chip.dataset.prompt);
  });
});

// Greet on load
window.addEventListener('DOMContentLoaded', () => {
  appendBotMessage({
    response: "Hi! I'm your support assistant. Ask me about orders, returns, payments, your account, or products.",
    confidence: 1,
    escalated: false,
    intent: 'greeting',
  });
});
