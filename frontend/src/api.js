const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

async function request(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let detail = `${path} failed: ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch (error) {}
    throw new Error(detail);
  }

  return response.json();
}

export function startConvertJob(payload) {
  return request('/api/convert-ai/start', payload);
}

export async function getJobStatus(jobId) {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}/status`);
  if (!response.ok) {
    throw new Error(`job status failed: ${response.status}`);
  }
  return response.json();
}

export async function getJobResult(jobId) {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}/result`);
  if (!response.ok) {
    throw new Error(`job result failed: ${response.status}`);
  }
  return response.json();
}

export function convertNovel(payload) {
  return request('/api/convert-ai', payload);
}

export function reviseScript(payload) {
  return request('/api/revise-script', payload);
}


export async function getBackendVersion() {
  const response = await fetch(`${API_BASE}/api/version`);
  if (!response.ok) return { version: 'unknown' };
  return response.json();
}


export async function getBackendDebug() {
  const response = await fetch(`${API_BASE}/api/debug/runtime`);
  if (!response.ok) return { error: `debug failed: ${response.status}` };
  return response.json();
}
