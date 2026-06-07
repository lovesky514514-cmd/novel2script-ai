import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { getBackendDebug, getBackendVersion, getJobResult, getJobStatus, reviseScript, startConvertJob } from './api';
import './styles.css';

function ParticleBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let width = 0;
    let height = 0;
    let raf = 0;
    const mouse = { x: 0, y: 0, active: false };

    const particles = Array.from({ length: 86 }).map(() => ({
      x: Math.random(),
      y: Math.random(),
      r: Math.random() * 2 + 1,
      vx: (Math.random() - 0.5) * 0.0007,
      vy: (Math.random() - 0.5) * 0.0007
    }));

    function resize() {
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = width * window.devicePixelRatio;
      canvas.height = height * window.devicePixelRatio;
      ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    }

    function draw() {
      ctx.clearRect(0, 0, width, height);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > 1) p.vx *= -1;
        if (p.y < 0 || p.y > 1) p.vy *= -1;

        const px = p.x * width;
        const py = p.y * height;
        let ox = 0;
        let oy = 0;

        if (mouse.active) {
          const dx = px - mouse.x;
          const dy = py - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = Math.max(0, 150 - dist) / 150;
          ox = (dx / dist) * force * 16;
          oy = (dy / dist) * force * 16;
        }

        ctx.beginPath();
        ctx.fillStyle = 'rgba(84, 131, 179, 0.28)';
        ctx.arc(px + ox, py + oy, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(draw);
    }

    function onMove(event) {
      const rect = canvas.getBoundingClientRect();
      mouse.x = event.clientX - rect.left;
      mouse.y = event.clientY - rect.top;
      mouse.active = true;
    }

    function onLeave() {
      mouse.active = false;
    }

    resize();
    draw();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseleave', onLeave);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseleave', onLeave);
    };
  }, []);

  return <canvas ref={canvasRef} className="particleCanvas" />;
}

function Topbar({ page, setPage, locked, backendVersion }) {
  const items = [
    ['convert', '转换'],
    ['result', '结果'],
    ['features', '功能']
  ];

  return (
    <header
      className="topbar siteTopbarFull"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        width: '100vw',
        minWidth: '100vw',
        maxWidth: 'none',
        margin: 0,
        borderRadius: 0,
        background: '#1d1e24'
      }}
    >
      <div className="topbarInner">
        <button className="brand" type="button" onClick={() => !locked && setPage('convert')} aria-label="返回转换页">
          <span className="brandText">
            <strong>Novel2Script AI</strong>
            <small>小说转剧本工作台</small>
          </span>
        </button>

        <nav className="nav" aria-label="主导航">
          {items.map(([key, label]) => (
            <button
              type="button"
              key={key}
              className={page === key ? 'active' : ''}
              onClick={() => !locked && setPage(key)}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}

function estimateSeconds(text) {
  return Math.max(25, Math.min(Math.round(20 + text.trim().length / 800), 90));
}

function ConvertPage({ demand, setDemand, fileInfo, onUpload, onSubmit, onVoice, listening }) {
  return (
    <section className="convertPage pageInner">
      <div className="convertCenter">
        <p className="miniTag">AI 小说转剧本工具</p>
        <h1>把你的小说变成剧本</h1>

        <div className="mainPrompt">
          <button className="plusBtn" type="button" onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            onUpload();
          }}>+</button>
          <input
            value={demand}
            onChange={(event) => setDemand(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                onSubmit(event);
              }
            }}
            placeholder="上传小说文件，或补充改编要求"
          />
          <button
            className={`micBtn ${listening ? 'listening' : ''}`}
            type="button"
            onClick={onVoice}
          >
            {listening ? '录音中' : '语音'}
          </button>
          <button className="sendBtn" type="button" onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            onSubmit(event);
          }}>发送</button>
        </div>

        <p className="hintText">
          可补充要求：重点写某一章、保留某个伏笔、对白更自然、压缩支线；不填写也可以直接生成。
        </p>

        {fileInfo && (
          <div className="fileTag">
            <span>已上传</span>
            <b>{fileInfo.name}</b>
            <em>{fileInfo.count} 字</em>
          </div>
        )}
      </div>
    </section>
  );
}



function LoadingPage({ elapsedSeconds, fileName, jobState }) {
  return (
    <section className="loadingPage pageInner">
      <div className="loadingCard simpleLoading">
        <div className="spinner"><span /></div>
        <h2>正在生成...</h2>
        <p className="loadingStageText">{jobState?.stage_text || '正在启动知识库'}</p>
        <p className="loadingFileText">{fileName ? `正在处理《${fileName.replace(/\.[^.]+$/, '')}》` : '正在处理小说内容'}</p>
        <div className="progressTrack">
          <span style={{ width: `${Math.round((jobState?.progress || 0) * 100)}%` }} />
        </div>
      </div>
          <p className="elapsedUnderProgress">已用时 {elapsedSeconds} 秒</p>
    </section>
  );
}


function displayText(value) {
  if (value === undefined || value === null) return '-';
  const text = String(value).trim();
  if (!text || ['待识别', 'unknown', '主要场景', '暂无动作', '暂无对白'].includes(text)) return '-';
  return text;
}

function displayTime(value) {
  const text = displayText(value);
  return text;
}

function formatScene(scene, index) {
  const dialogue = scene.dialogue?.length ? scene.dialogue.map((item) => `${item.speaker || '-'}：${item.line || '-'}`).join('\n') : '-';
  return `第 ${index + 1} 场  ${scene.title || '未命名场景'}

地点：${displayText(scene.location)}
时间：${displayTime(scene.time)}
人物：${scene.characters?.length ? scene.characters.join('、') : '-'}

冲突：
${displayText(scene.conflict)}

动作：
${scene.action?.length ? scene.action.join('\n') : '-'}

对白：
${dialogue}

场景目的：
${displayText(scene.purpose)}`;
}

function ResultPage({ result, setResult, revisionText, setRevisionText, messages, setMessages, onDownloadYaml, onDownloadTxt, setPage }) {
  const [revising, setRevising] = useState(false);

  const sceneText = useMemo(() => {
    if (!result?.scenes?.length) return '';
    return result.scenes.map(formatScene).join('\n\n————————————\n\n');
  }, [result]);

  async function sendRevision() {
    const instruction = revisionText.trim();
    if (!instruction || !result || revising) return;

    const userMessage = { id: `u-${Date.now()}`, role: 'user', text: instruction };
    setMessages((old) => [...old, userMessage]);
    setRevisionText('');
    setRevising(true);

    try {
      const data = await reviseScript({
        result,
        instruction
      });

      setResult(data.result);
      setMessages((old) => [
        ...old,
        { id: `a-${Date.now()}`, role: 'assistant', text: data.message || '已根据修改要求更新剧本。' }
      ]);
    } catch (error) {
      console.error(error);
      setMessages((old) => [
        ...old,
        { id: `a-${Date.now()}`, role: 'assistant', text: '修改接口请求失败。请确认后端已启动，并存在 /api/revise-script。' }
      ]);
    } finally {
      setRevising(false);
    }
  }

  if (!result) {
    return (
      <section className="emptyResult pageInner">
        <div className="emptyCard">
          <h2>暂无生成结果</h2>
          <p>请先进入“转换”页上传小说文件。</p>
          <button type="button" onClick={() => setPage('convert')}>去转换</button>
        </div>
      </section>
    );
  }

  return (
    <section className="resultPage pageInner">
      <div className="resultGrid">
        <main className="scriptPanel">
          <div className="panelTop">
            <div>
              <p className="miniTag">Script Result</p>
              <h2>{result.title || '生成剧本'}</h2>
              <p className="detectedLine">系统已完成剧本初稿，可在右侧继续修改。</p>
              <p className="timeFormatHint">时间标记：日=白天，夜=夜晚，深夜=夜深以后。</p>
            </div>
            <span className="statusDot">已完成</span>
          </div>

          <div className="readableScript">
            {sceneText.split('\n').map((line, index) => {
              if (line.startsWith('第 ') && line.includes('场')) return <h3 key={index}>{line}</h3>;
              if (line === '————————————') return <hr key={index} />;
              if (['地点：', '时间：', '人物：', '冲突：', '动作：', '对白：', '场景目的：'].some((prefix) => line.startsWith(prefix))) {
                return <p className="labelLine" key={index}>{line}</p>;
              }
              return line ? <p key={index}>{line}</p> : <br key={index} />;
            })}
          </div>
        </main>

        <aside className="chatPanel">
          <div className="chatHeader">
            <h3>继续修改</h3>
            <p>可以要求调整对白、节奏、重点场次。</p>
          </div>

          <div className="chatBody">
            {messages.length === 0 && (
              <div className="emptyChat">输入修改要求后，系统会直接更新左侧剧本。</div>
            )}
            {messages.map((message) => (
              <div className={`bubble ${message.role}`} key={message.id}>{message.text}</div>
            ))}
            {revising && <div className="bubble assistant">正在修改剧本...</div>}
          </div>

          <div className="chatInput">
            <textarea
              value={revisionText}
              onChange={(event) => setRevisionText(event.target.value)}
              placeholder="例如：重点扩写第三章仓库戏，但不要改变父亲录音这个伏笔。"
            />
            <button type="button" onClick={sendRevision} disabled={revising}>
              {revising ? '修改中' : '发送'}
            </button>
          </div>

          <div className="downloadBox">
            <h4>下载文件</h4>
            <button type="button" onClick={onDownloadYaml}>下载 YAML</button>
            <button type="button" onClick={onDownloadTxt}>下载 TXT</button>
          </div>
        </aside>
      </div>
    </section>
  );
}

function FeaturesPage() {
  const capabilityItems = [
    ['小说上传与解析', '支持 TXT/MD/常见文本文件，自动读取正文并估算字数。'],
    ['章节与场景转换', '自动切章节，按章节事实生成分场剧本，输出更适合阅读的预览文本。'],
    ['事实保真', '记录人物、地点、时间、道具、伏笔，减少串场和前后信息污染。'],
    ['多地点拆场', '同一章节出现多个独立地点时，支持拆成多个可拍摄场景。'],
    ['结果继续修改', '生成后可在右侧继续输入要求，调整对白、节奏和重点场次。'],
    ['结构化导出', '支持 YAML / TXT 下载，便于后续接入剪辑、分镜或投稿流程。']
  ];

  const techItems = [
    ['双模型链路', 'Pro 负责 story_bible / chapter_facts / 校验，Chat 负责分场生成与润色。'],
    ['错误知识库', 'error_patterns.yaml 集中沉淀日期误判、道具污染、非现场人物等问题。'],
    ['Fact-bound Guard', '最终展示结果绑定 chapter_facts，避免后处理覆盖正确事实。'],
    ['可追踪输出', 'YAML 保留 model_trace、repair_questions、chapter_facts，方便排查。']
  ];

  const feedbackItems = [
    ['反馈记录', '规划：在结果页增加“反馈”入口，记录用户认为不准的场景和修改原因。'],
    ['服务器文档同步', '规划：把反馈同步到服务器文档目录，形成可复盘的样本库。'],
    ['定期导出', '规划：按天或按周生成反馈文件，方便继续更新错误知识库。']
  ];

  return (
    <section className="featuresPage pageInner">
      <div className="featureTitle">
        <p className="miniTag">Features</p>
        <h1>功能</h1>
        <p>先保证生成结果可读、可改、可追踪，再逐步沉淀用户反馈和错误知识库。</p>
      </div>

      <div className="featureSection">
        <div className="sectionHeading">
          <span>01</span>
          <div>
            <h2>能实现什么</h2>
            <p>围绕小说到剧本的核心流程，先把用户能直接感知的能力做清楚。</p>
          </div>
        </div>
        <div className="featureGrid capabilityGrid">
          {capabilityItems.map(([title, text]) => (
            <article key={title}>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="featureSection twoColumnFeature">
        <div className="techCard">
          <div className="sectionHeading compact">
            <span>02</span>
            <div>
              <h2>技术链路</h2>
              <p>后端不是单次生成，而是学习、抽取、生成、校验、修复的组合链路。</p>
            </div>
          </div>
          <div className="techList">
            {techItems.map(([title, text]) => (
              <div className="techItem" key={title}>
                <b>{title}</b>
                <p>{text}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="feedbackCard">
          <div className="sectionHeading compact">
            <span>03</span>
            <div>
              <h2>用户反馈设计</h2>
              <p>这部分先做前端规划，后续再接服务器文件同步。</p>
            </div>
          </div>
          <div className="feedbackMock">
            {feedbackItems.map(([title, text]) => (
              <div className="feedbackRow" key={title}>
                <strong>{title}</strong>
                <p>{text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function App() {
  const [page, setPage] = useState('convert');
  const [demand, setDemand] = useState('');
  const [novelText, setNovelText] = useState('');
  const [fileInfo, setFileInfo] = useState(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [jobState, setJobState] = useState({ stage_text: '正在启动知识库', progress: 0 });
  const [screenLock, setScreenLock] = useState(false);
  const [result, setResult] = useState(null);
  const [listening, setListening] = useState(false);
  const [revisionText, setRevisionText] = useState('');
  const [messages, setMessages] = useState([]);
  const [backendVersion, setBackendVersion] = useState('checking');

  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    getBackendVersion()
      .then((data) => setBackendVersion(data.version || 'unknown'))
      .catch(() => setBackendVersion('offline'));
  }, []);

  useEffect(() => {
    const preventFileNavigation = (event) => {
      event.preventDefault();
      event.stopPropagation();
    };

    window.addEventListener('dragover', preventFileNavigation);
    window.addEventListener('drop', preventFileNavigation);

    return () => {
      window.removeEventListener('dragover', preventFileNavigation);
      window.removeEventListener('drop', preventFileNavigation);
    };
  }, []);

  useEffect(() => {
    if (page !== 'loading') return;
    const timer = window.setInterval(() => {
      setElapsedSeconds((value) => value + 1);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [page]);

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    const lowerName = file.name.toLowerCase();
    if (lowerName.endsWith('.yaml') || lowerName.endsWith('.yml') || lowerName.endsWith('.json')) {
      alert('请上传小说正文文件（.txt / .md）。YAML 是生成结果，不适合作为小说输入。');
      event.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const content = String(reader.result || '');
      setNovelText(content);
      setFileInfo({
        name: file.name,
        count: content.length
      });
    };
    reader.readAsText(file, 'utf-8');
    event.target.value = '';
  }

  function toggleVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('当前浏览器暂不支持本地语音识别。建议使用 Chrome；稳定版可后续接入火山引擎/豆包 ASR。');
      return;
    }

    if (recognitionRef.current && listening) {
      recognitionRef.current.stop();
      setListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = false;
    recognition.interimResults = true;

    let finalText = '';
    recognition.onstart = () => setListening(true);
    recognition.onresult = (event) => {
      let interimText = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += transcript;
        else interimText += transcript;
      }
      setDemand(`${finalText}${interimText}`.trim());
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => {
      setListening(false);
      if (finalText.trim()) setDemand(finalText.trim());
    };

    recognitionRef.current = recognition;
    recognition.start();
  }

  
async function submitConvert(event) {
    event?.preventDefault?.();
    event?.stopPropagation?.();
    if (!novelText.trim()) {
      alert('请先点击 + 上传小说文本文件。');
      return;
    }

    setElapsedSeconds(0);
    setJobState({ stage_text: '正在启动知识库', progress: 0.05 });
    setScreenLock(true);
    setPage('loading');

    try {
      const startData = await startConvertJob({
        title: fileInfo?.name?.replace(/\.[^.]+$/, '') || '未命名作品',
        text: novelText,
        adaptation_style: 'auto',
        user_instruction: demand
      });

      const jobId = startData.job_id;
      let finished = false;

      while (!finished) {
        await new Promise((resolve) => setTimeout(resolve, 900));
        const status = await getJobStatus(jobId);
        setJobState(status);

        if (status.status === 'done') {
          const data = await getJobResult(jobId);
          if (data.status === 'quality_failed' || data.status === 'error') {
            throw new Error(data.error || '生成未通过质量校验。');
          }
          setResult(data);
          setMessages([]);
          setPage('result');
          setScreenLock(false);
          finished = true;
        }

        if (status.status === 'error') {
          throw new Error(status.error || 'job failed');
        }
      }
    } catch (error) {
      console.error(error);
      setPage('convert');
      setScreenLock(false);
      alert(`后端生成任务失败：${error?.message || '未知错误'}\n请先确认左上角版本为 day2_fullstack_polish，再打开 http://127.0.0.1:8000/api/debug/runtime 查看后端状态。`);
    }
  }

  function downloadFile(filename, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.style.display = 'none';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function downloadYaml() {
    if (!result?.yaml_text) return;
    downloadFile(`${result.title || 'novel2script'}.yaml`, result.yaml_text, 'text/yaml;charset=utf-8');
  }

  function downloadTxt() {
    if (!result?.scenes?.length) return;
    const text = result.scenes.map(formatScene).join('\n\n————————————\n\n');
    downloadFile(`${result.title || 'novel2script'}.txt`, text, 'text/plain;charset=utf-8');
  }

  function navSetPage(next) {
    if (screenLock) return;
    setPage(next);
  }

  return (
    <main className="app">
      <ParticleBackground />
      <Topbar page={page === 'loading' ? 'convert' : page} setPage={navSetPage} locked={screenLock} backendVersion={backendVersion} />

      <input
        ref={fileInputRef}
        className="hiddenFile"
        type="file"
        accept=".txt,.md,text/plain,text/markdown"
        onChange={handleFileChange}
      />

      <div className="pageShell">
        {page === 'convert' && (
          <ConvertPage
            demand={demand}
            setDemand={setDemand}
            fileInfo={fileInfo}
            onUpload={() => fileInputRef.current?.click()}
            onSubmit={submitConvert}
            onVoice={toggleVoice}
            listening={listening}
          />
        )}

        {page === 'loading' && <LoadingPage elapsedSeconds={elapsedSeconds} fileName={fileInfo?.name || ''} jobState={jobState} />}

        {page === 'result' && (
          <ResultPage
            result={result}
            setResult={setResult}
            revisionText={revisionText}
            setRevisionText={setRevisionText}
            messages={messages}
            setMessages={setMessages}
            onDownloadYaml={downloadYaml}
            onDownloadTxt={downloadTxt}
            setPage={setPage}
          />
        )}

        {page === 'features' && <FeaturesPage />}
      </div>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
