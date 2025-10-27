const reportEditor = document.querySelector('#report-editor');
const loadSampleBtn = document.querySelector('#load-sample');
const runAnalysisBtn = document.querySelector('#run-analysis');
const analysisOutput = document.querySelector('#analysis-output');
const chatHistory = document.querySelector('#chat-history');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const messageTemplate = document.querySelector('#message-template');

const state = {
  sessionId: null,
  isProcessing: false,
};

const formatJson = (data) => JSON.stringify(data, null, 2);

async function fetchSample() {
  toggleProcessing(true);
  try {
    const response = await fetch('/api/sample-report');
    if (!response.ok) {
      throw new Error('示例报告获取失败');
    }
    const payload = await response.json();
    reportEditor.value = formatJson(payload.report);
    resetAnalysis();
  } catch (error) {
    renderError(`无法载入示例：${error.message}`);
  } finally {
    toggleProcessing(false);
  }
}

function toggleProcessing(flag) {
  state.isProcessing = flag;
  runAnalysisBtn.disabled = flag;
  loadSampleBtn.disabled = flag;
}

function resetAnalysis() {
  analysisOutput.innerHTML = '<p class="empty">请运行分析以查看结果。</p>';
  chatHistory.innerHTML = '';
  state.sessionId = null;
}

function renderError(message) {
  analysisOutput.innerHTML = `<div class="error">${message}</div>`;
}

function renderAnalysis({ rule_outcomes: outcomes, narrative }) {
  if (!outcomes || outcomes.length === 0) {
    analysisOutput.innerHTML = '<p class="empty">规则未命中，请确认报告内容。</p>';
    return;
  }

  const listItems = outcomes
    .map((item) => {
      const recommendation = item.recommendation ? `<span class="recommendation">${item.recommendation}</span>` : '';
      return `<li><strong>${item.rule_id}</strong>：<span class="status">${item.status}</span> ${recommendation}</li>`;
    })
    .join('');

  const narrativeBlock = narrative
    ? `<section><h3>LLM 叙事</h3><div class="narrative">${narrative.response}</div></section>`
    : '';

  analysisOutput.innerHTML = `
    <section>
      <h3>规则命中情况</h3>
      <ul>${listItems}</ul>
    </section>
    ${narrativeBlock}
  `;
}

function appendMessage(role, content) {
  const node = messageTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector('.message-role').textContent = role === 'assistant' ? '顾问' : '用户';
  node.querySelector('.message-content').textContent = content;
  chatHistory.append(node);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function runAnalysis() {
  let parsed;
  try {
    parsed = JSON.parse(reportEditor.value);
  } catch (error) {
    renderError('JSON 解析失败，请检查格式。');
    return;
  }

  toggleProcessing(true);
  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ report: parsed, with_narrative: true }),
    });

    if (!response.ok) {
      const { detail } = await response.json();
      throw new Error(detail || '分析失败');
    }

    const payload = await response.json();
    state.sessionId = payload.session_id;
    renderAnalysis(payload.analysis);
    chatHistory.innerHTML = '';
    appendMessage('assistant', payload.intro_message);
  } catch (error) {
    renderError(`分析失败：${error.message}`);
  } finally {
    toggleProcessing(false);
  }
}

async function submitQuestion(event) {
  event.preventDefault();
  if (!state.sessionId) {
    appendMessage('assistant', '请先运行分析并建立对话会话。');
    return;
  }

  const question = chatInput.value.trim();
  if (!question) return;

  appendMessage('user', question);
  chatInput.value = '';

  try {
    const response = await fetch(`/api/conversations/${state.sessionId}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const { detail } = await response.json();
      throw new Error(detail || '对话失败');
    }

    const payload = await response.json();
    appendMessage('assistant', payload.response);
  } catch (error) {
    appendMessage('assistant', `对话失败：${error.message}`);
  }
}

loadSampleBtn?.addEventListener('click', fetchSample);
runAnalysisBtn?.addEventListener('click', runAnalysis);
chatForm?.addEventListener('submit', submitQuestion);

fetchSample();

