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

  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackMessages, setFeedbackMessages] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('n2s_feedback_queue') || '[]');
    } catch {
      return [];
    }
  });
  const [feedbackStatus, setFeedbackStatus] = useState('');

  async function sendFeedback() {
    const message = feedbackText.trim();

    if (!message) {
      setFeedbackStatus('请先写下反馈内容。');
      return;
    }

    const record = {
      id: Date.now(),
      text: message,
      created_at: new Date().toLocaleString(),
      status: '同步中'
    };

    const nextMessages = [...feedbackMessages, record];
    setFeedbackMessages(nextMessages);
    setFeedbackText('');
    setFeedbackStatus('正在同步到服务器...');

    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: '',
          contact: '',
          category: '功能建议',
          message,
          page: 'features',
          user_agent: navigator.userAgent
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const syncedMessages = nextMessages.map((item) =>
        item.id === record.id ? { ...item, status: '已同步' } : item
      );

      setFeedbackMessages(syncedMessages);
      localStorage.setItem('n2s_feedback_queue', JSON.stringify(syncedMessages));
      setFeedbackStatus('已同步到服务器反馈文档。');
    } catch (error) {
      console.error(error);

      const failedMessages = nextMessages.map((item) =>
        item.id === record.id ? { ...item, status: '同步失败，已暂存' } : item
      );

      setFeedbackMessages(failedMessages);
      localStorage.setItem('n2s_feedback_queue', JSON.stringify(failedMessages));
      setFeedbackStatus('服务器同步失败，已先暂存在本机。');
    }
  }

  function clearFeedbackDrafts() {
    setFeedbackMessages([]);
    localStorage.removeItem('n2s_feedback_queue');
    setFeedbackStatus('本机暂存反馈已清空。');
  }

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
              <h2>用户反馈</h2>
              <p>把生成不准、体验问题或功能建议直接写在这里。</p>
            </div>
          </div>

          <div className="feedbackChatBox">
            <div className="feedbackChatBody">
              {feedbackMessages.length === 0 ? (
                <div className="feedbackEmpty">
                  暂无反馈。可以像聊天一样写下问题，例如“第三章人物关系不准”或“希望支持导出 Word”。
                </div>
              ) : (
                feedbackMessages.map((item) => (
                  <div className="feedbackBubble" key={item.id}>
                    <p>{item.text}</p>
                    <span>{item.created_at} · {item.status}</span>
                  </div>
                ))
              )}
            </div>

            <div className="feedbackChatInput">
              <textarea
                value={feedbackText}
                onChange={(event) => setFeedbackText(event.target.value)}
                placeholder="写下你的反馈，例如：对白不自然、事实错误、生成太慢、想要新增导出格式……"
              />
              <div className="feedbackChatActions">
                <button type="button" onClick={sendFeedback}>发送反馈</button>
                {feedbackMessages.length > 0 && (
                  <button type="button" className="ghostBtn" onClick={clearFeedbackDrafts}>清空暂存</button>
                )}
              </div>
            </div>

            {feedbackStatus && <p className="feedbackMiniStatus">{feedbackStatus}</p>}
          </div>
        </div>
      </div>
    </section>
  );
}