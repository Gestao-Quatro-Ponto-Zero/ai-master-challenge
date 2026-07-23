// Tab switching
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(`${tabId}-tab`).classList.add('active');
    event.target.classList.add('active');
    
    if(tabId === 'overview' && !window.chartsLoaded) {
        loadMetrics();
    }
}

// Load Metrics and Charts
async function loadMetrics() {
    try {
        const res = await fetch('/api/metrics');
        const data = await res.json();
        
        document.getElementById('kpi-churn').innerText = data.metrics.churn_rate;
        document.getElementById('kpi-mrr').innerText = data.metrics.avg_mrr;
        document.getElementById('kpi-usage').innerText = data.metrics.usage_avg;
        
        Plotly.newPlot('chart-ind', data.fig_ind.data, data.fig_ind.layout, {responsive: true, displayModeBar: false});
        Plotly.newPlot('chart-use', data.fig_use.data, data.fig_use.layout, {responsive: true, displayModeBar: false});
        
        window.chartsLoaded = true;
    } catch(e) {
        console.error("Error loading metrics", e);
    }
}

// Chat logic
function handleEnter(e) {
    if (e.key === 'Enter') sendMessage();
}

async function sendMessage() {
    const inputEl = document.getElementById('chat-input');
    const prompt = inputEl.value.trim();
    const apiKey = document.getElementById('api-key').value.trim();
    
    if(!prompt) return;
    
    if(!apiKey) {
        appendMessage("assistant", "⚠️ Por favor, insira a sua API Key da OpenAI no menu lateral primeiro.");
        return;
    }
    
    appendMessage("user", prompt);
    inputEl.value = '';
    
    const loadingId = appendMessage("assistant", "Analisando dados...");
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prompt: prompt, api_key: apiKey})
        });
        const data = await res.json();
        
        const loadingEl = document.getElementById(loadingId);
        if(res.ok) {
            loadingEl.innerText = data.response;
        } else {
            loadingEl.innerText = "❌ Erro: " + (data.error || "Falha na requisição");
        }
    } catch(e) {
        document.getElementById(loadingId).innerText = "❌ Erro de conexão com o servidor.";
    }
}

function appendMessage(role, text) {
    const history = document.getElementById('chat-history');
    const msgId = 'msg-' + Date.now();
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.id = msgId;
    div.innerText = text;
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
    return msgId;
}

// Load on start
document.addEventListener("DOMContentLoaded", () => {
    loadMetrics();
});
