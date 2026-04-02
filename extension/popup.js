function refresh() {
  chrome.runtime.sendMessage({ type: 'STATUS' }, (data) => {
    if (!data) return;

    const agentEl = document.getElementById('agent-status');
    const tokenEl = document.getElementById('token-status');
    const statsEl = document.getElementById('stats');

    agentEl.className = `status ${data.agentConnected ? 'connected' : 'disconnected'}`;
    agentEl.textContent = data.agentConnected ? '✅ Agent connected' : '❌ Agent disconnected';

    tokenEl.className = `status ${data.flowKeyPresent ? 'connected' : 'disconnected'}`;
    const age = data.tokenAge ? `${Math.round(data.tokenAge / 60000)}m ago` : '—';
    tokenEl.textContent = data.flowKeyPresent ? `🔑 Token captured (${age})` : '❌ No token — open Flow tab';

    const m = data.metrics || {};
    const stats = [
      ['State', data.state],
      ['Requests', m.requestCount || 0],
      ['Success', m.successCount || 0],
      ['Failed', m.failedCount || 0],
      ['Last error', m.lastError || '—'],
    ];
    statsEl.textContent = '';
    for (const [label, value] of stats) {
      const div = document.createElement('div');
      div.className = 'stat';
      const labelSpan = document.createElement('span');
      labelSpan.className = 'label';
      labelSpan.textContent = label;
      const valueSpan = document.createElement('span');
      valueSpan.className = 'value';
      valueSpan.textContent = value;
      div.appendChild(labelSpan);
      div.appendChild(valueSpan);
      statsEl.appendChild(div);
    }
  });
}

document.getElementById('btn-test').addEventListener('click', () => {
  const btn = document.getElementById('btn-test');
  btn.textContent = '⏳ Solving...';
  btn.disabled = true;
  chrome.runtime.sendMessage({ type: 'TEST_CAPTCHA' }, (r) => {
    btn.textContent = r?.token ? '✅ Token OK' : `❌ ${r?.error || 'Failed'}`;
    btn.disabled = false;
    setTimeout(() => { btn.textContent = '🧪 Test Captcha'; }, 3000);
  });
});

document.getElementById('btn-flow').addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'OPEN_FLOW_TAB' });
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'STATUS_PUSH') refresh();
});

refresh();
