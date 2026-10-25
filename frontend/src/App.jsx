import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const suggestions = [
  {
    icon: "✦",
    title: "Find key information",
    description: "Search across your uploaded knowledge",
    prompt: "What are the most important points in my documents?",
  },
  {
    icon: "⌘",
    title: "Connect the dots",
    description: "Compare information across documents",
    prompt: "Summarize the key themes across my documents.",
  },
  {
    icon: "↗",
    title: "Get a quick summary",
    description: "Turn long PDFs into clear answers",
    prompt: "Give me a concise summary of my uploaded documents.",
  },
];

function Icon({ name, size = 20 }) {
  const paths = {
    menu: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
    plus: <path d="M12 5v14M5 12h14" />,
    search: <><circle cx="11" cy="11" r="7" /><path d="m16 16 4 4" /></>,
    file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M8 13h8M8 17h6" /></>,
    files: <><rect x="4" y="4" width="12" height="15" rx="2" /><path d="M8 2h10a2 2 0 0 1 2 2v13M7 9h6M7 13h6" /></>,
    history: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    send: <><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></>,
    trash: <><path d="M3 6h18M8 6V4h8v2m3 0-1 14H6L5 6" /><path d="M10 10v6m4-6v6" /></>,
    refresh: <><path d="M20 7v5h-5" /><path d="M4 17v-5h5" /><path d="M5.5 9a7 7 0 0 1 12-2L20 12" /><path d="M18.5 15a7 7 0 0 1-12 2L4 12" /></>,
    arrow: <path d="M7 17 17 7M7 7h10v10" />,
    close: <path d="m18 6-12 12M6 6l12 12" />,
    check: <path d="m5 12 4 4L19 6" />,
    shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" /><path d="m9 12 2 2 4-4" /></>,
    sparkles: <><path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3Z" /><path d="m19 14 1.1 2.9L23 18l-2.9 1.1L19 22l-1.1-2.9L15 18l2.9-1.1L19 14Z" /></>,
    alert: <><path d="M10.3 3.9 2.6 17.2A2 2 0 0 0 4.3 20h15.4a2 2 0 0 0 1.7-2.8L13.7 3.9a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4m0 3h.01" /></>,
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.sparkles}
    </svg>
  );
}

function BrandMark({ small = false }) {
  return (
    <span className={`brand-mark ${small ? "brand-mark-small" : ""}`} aria-hidden="true">
      <Icon name="sparkles" size={small ? 17 : 21} />
    </span>
  );
}

function formatFileSize(bytes = 0) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function Sidebar({ mobileOpen, onClose, onNewChat, onUpload, onShowDocuments }) {
  const nav = [
    { label: "New conversation", icon: "plus", action: onNewChat },
    { label: "Ask a question", icon: "search", action: () => {
      document.querySelector("#chat-input")?.focus();
      onClose();
    }},
    { label: "Upload a PDF", icon: "file", action: () => {
      onUpload();
      onClose();
    }},
    { label: "Knowledge base", icon: "files", action: () => {
      onShowDocuments();
      onClose();
    }},
  ];

  return (
    <>
      {mobileOpen && <button className="mobile-overlay" onClick={onClose} aria-label="Close navigation" />}
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <button className="sidebar-brand" onClick={onNewChat} title="Start a new chat">
          <BrandMark />
        </button>
        <div className="sidebar-label">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {nav.map((item, index) => (
            <button
              key={item.label}
              className={`sidebar-nav-item ${index === 0 ? "sidebar-nav-primary" : ""}`}
              onClick={item.action}
              title={item.label}
            >
              <Icon name={item.icon} size={19} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <div className="help-icon"><Icon name="shield" size={18} /></div>
            <div><strong>Your data stays local</strong><span>Private workspace</span></div>
          </div>
          <div className="workspace-user">
            <div className="user-avatar">R</div>
            <div className="workspace-user-copy"><strong>Research workspace</strong><span>Personal knowledge base</span></div>
          </div>
        </div>
      </aside>
    </>
  );
}

function SourceList({ sources }) {
  if (!sources?.length) return null;
  const uniqueSources = sources.filter((source, index, all) =>
    all.findIndex((item) => item.source === source.source && item.page === source.page) === index
  );

  return (
    <details className="sources-panel">
      <summary>
        <span className="sources-summary-icon"><Icon name="files" size={16} /></span>
        <span>Sources used</span>
        <span className="source-count">{uniqueSources.length}</span>
        <span className="source-chevron">⌄</span>
      </summary>
      <div className="source-list">
        {uniqueSources.map((source, index) => (
          <div className="source-item" key={`${source.source}-${source.page}-${index}`}>
            <div className="source-file-icon"><Icon name="file" size={17} /></div>
            <div className="source-item-copy">
              <div className="source-name">{source.source || "Unknown document"}</div>
              <div className="source-page">Page {source.page ?? "Unknown"}</div>
            </div>
          </div>
        ))}
      </div>
    </details>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";
  return (
    <article className={`message ${isUser ? "message-user" : "message-assistant"}`}>
      {isUser ? (
        <div className="user-avatar message-user-avatar">Y</div>
      ) : (
        <div className="message-avatar"><BrandMark small /></div>
      )}
      <div className="message-content">
        {!isUser && (
          <div className="message-meta">
            <strong>Knowledge Assistant</strong>
            <span className="answer-status"><span /> Answer generated</span>
          </div>
        )}
        {isUser ? (
          <div className="user-bubble">{message.content}</div>
        ) : (
          <>
            <div className="answer-text">{message.content}</div>
            <SourceList sources={message.sources} />
          </>
        )}
      </div>
    </article>
  );
}

function CurrentDocuments({
  documents, loading, refreshing, deleting, error, onRefresh, onDelete, onUpload,
}) {
  return (
    <section className="documents-panel" id="current-documents">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">YOUR KNOWLEDGE BASE</div>
          <h2>Indexed documents <span className="count-pill">{documents.length}</span></h2>
          <p>PDFs available to your assistant for retrieval.</p>
        </div>
        <div className="panel-actions">
          <button className="icon-button refresh-button" onClick={onRefresh} disabled={refreshing || loading} title="Refresh documents" aria-label="Refresh documents">
            <Icon name="refresh" size={17} />
          </button>
          <button className="secondary-button" onClick={onUpload} disabled={Boolean(deleting)}>
            <Icon name="plus" size={17} /><span>Add PDF</span>
          </button>
        </div>
      </div>

      {error && <div className="inline-error"><Icon name="alert" size={17} /><span>{error}</span></div>}

      {loading ? (
        <div className="documents-loading"><span className="spinner" /> Loading your knowledge base…</div>
      ) : documents.length === 0 ? (
        <div className="documents-empty">
          <div className="empty-illustration"><Icon name="files" size={27} /></div>
          <h3>Your knowledge base is waiting</h3>
          <p>Upload a PDF to index it and start asking questions grounded in your documents.</p>
          <button className="primary-button" onClick={onUpload}><Icon name="plus" size={17} /> Upload your first PDF</button>
        </div>
      ) : (
        <div className="documents-table">
          <div className="documents-table-header">
            <span>DOCUMENT</span><span>SIZE</span><span>TYPE</span><span className="actions-heading">ACTION</span>
          </div>
          {documents.map((document) => {
            const isDeleting = deleting === document.name;
            return (
              <div className="document-row" key={document.name}>
                <div className="document-cell document-main-cell">
                  <div className="pdf-icon"><span>PDF</span></div>
                  <div className="document-info">
                    <strong title={document.name}>{document.name}</strong>
                    <span>Indexed and ready to search</span>
                  </div>
                </div>
                <div className="document-cell document-size">{formatFileSize(document.size_bytes)}</div>
                <div className="document-cell"><span className="file-type-pill">PDF file</span></div>
                <div className="document-cell document-row-actions">
                  <button
                    type="button"
                    className="delete-button"
                    onClick={() => onDelete(document.name)}
                    disabled={Boolean(deleting)}
                    aria-label={`Delete ${document.name}`}
                    title={`Delete ${document.name}`}
                  >
                    {isDeleting ? <span className="delete-progress"><span className="spinner spinner-small" /> Deleting</span> : <><Icon name="trash" size={17} /><span>Remove</span></>}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
      <div className="panel-footnote"><Icon name="shield" size={15} /> Your files are stored in your local project workspace.</div>
    </section>
  );
}

function Composer({ input, setInput, onSubmit, onUpload, loading, uploading, conversation = false, inputRef }) {
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSubmit(event);
    }
  }

  return (
    <form className={`composer ${conversation ? "composer-conversation" : ""}`} onSubmit={onSubmit}>
      <button type="button" className="composer-attach" title="Upload a PDF" onClick={onUpload} disabled={uploading}>
        <Icon name="plus" size={20} />
      </button>
      <textarea
        id="chat-input"
        ref={inputRef}
        value={input}
        onChange={(event) => setInput(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={conversation ? "Ask a follow-up question…" : "Ask a question about your documents…"}
        rows={1}
        aria-label="Your question"
        maxLength={2000}
      />
      <div className="composer-footer">
        <div className="composer-hints">
          <span className="mini-status"><span /> RAG search</span>
          <span className="keyboard-hint">Enter to send · Shift + Enter for new line</span>
        </div>
        <button className="send-button" type="submit" disabled={!input.trim() || loading} aria-label="Send question">
          {loading ? <span className="spinner spinner-light" /> : <Icon name="send" size={18} />}
        </button>
      </div>
    </form>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsRefreshing, setDocumentsRefreshing] = useState(false);
  const [documentsError, setDocumentsError] = useState("");
  const [deleting, setDeleting] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(null);

  const inputRef = useRef(null);
  const fileRef = useRef(null);
  const bottomRef = useRef(null);
  const hasConversation = messages.length > 0;

  const refreshDocuments = useCallback(async (showRefreshing = true) => {
    if (showRefreshing) setDocumentsRefreshing(true);
    else setDocumentsLoading(true);
    setDocumentsError("");
    try {
      const response = await fetch(`${API_URL}/documents`);
      if (!response.ok) throw new Error(`Could not load documents (${response.status}).`);
      const result = await response.json();
      setDocuments(Array.isArray(result.documents) ? result.documents : []);
    } catch (err) {
      setDocumentsError(err instanceof TypeError
        ? "Cannot connect to FastAPI. Start your backend on 127.0.0.1:8000."
        : err.message);
    } finally {
      setDocumentsLoading(false);
      setDocumentsRefreshing(false);
    }
  }, []);

  useEffect(() => { refreshDocuments(false); }, [refreshDocuments]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  function showDocuments() {
    document.querySelector("#current-documents")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function newChat() {
    setMessages([]);
    setInput("");
    setError("");
    setMobileOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
    window.setTimeout(() => inputRef.current?.focus(), 50);
  }

  async function sendMessage(text = input) {
    const question = text.trim();
    if (!question || loading) return;
    setError("");
    setInput("");
    setMobileOpen(false);
    setMessages((previous) => [...previous, { role: "user", content: question }]);
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, k: 4 }),
      });
      if (!response.ok) {
        const details = await response.text();
        throw new Error(`API error ${response.status}: ${details.slice(0, 250)}`);
      }
      const data = await response.json();
      setMessages((previous) => [...previous, {
        role: "assistant",
        content: data.answer || "No answer was returned by the backend.",
        sources: Array.isArray(data.sources) ? data.sources : [],
      }]);
    } catch (err) {
      setError(err instanceof TypeError
        ? "Cannot connect to FastAPI. Check that the backend is running at http://127.0.0.1:8000."
        : err.message);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  async function uploadPDF(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("The PDF exceeds the 10 MB upload limit.");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);
    setError("");
    setUploading(true);
    try {
      const response = await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || `Upload failed with status ${response.status}.`);
      setMessages((previous) => [...previous, {
        role: "assistant",
        content: `Upload completed for "${file.name}". ${result.message || "The PDF was processed successfully and is ready to query."}`,
        sources: [],
      }]);
      await refreshDocuments();
    } catch (err) {
      setError(`Could not upload the PDF: ${err.message}`);
      await refreshDocuments();
    } finally {
      setUploading(false);
    }
  }

  async function deleteDocument(filename) {
    setConfirmDelete(null);
    setDeleting(filename);
    setDocumentsError("");
    try {
      const response = await fetch(`${API_URL}/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || `Deletion failed with status ${response.status}.`);
      setDocuments((previous) => previous.filter((document) => document.name !== filename));
      setMessages((previous) => [...previous, {
        role: "assistant",
        content: `Document "${filename}" was removed from your knowledge base. ${result.deleted_chunks ?? 0} indexed chunks were deleted.`,
        sources: [],
      }]);
    } catch (err) {
      setDocumentsError(err instanceof TypeError
        ? "Could not connect to the backend. Check that FastAPI is running and CORS allows DELETE."
        : err.message);
      await refreshDocuments();
    } finally {
      setDeleting("");
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage();
  }

  const commonDocumentsProps = {
    documents, loading: documentsLoading, refreshing: documentsRefreshing,
    deleting, error: documentsError,
    onRefresh: () => refreshDocuments(),
    onDelete: (filename) => setConfirmDelete(filename),
    onUpload: () => fileRef.current?.click(),
  };

  return (
    <div className="app-shell">
      <Sidebar
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
        onNewChat={newChat}
        onUpload={() => fileRef.current?.click()}
        onShowDocuments={showDocuments}
      />
      <input ref={fileRef} type="file" accept=".pdf,application/pdf" hidden onChange={uploadPDF} />

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Icon name="menu" /></button>
            <div className="mobile-brand"><BrandMark small /><span>RAG Workspace</span></div>
            <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{hasConversation ? "Conversation" : "Knowledge assistant"}</strong></div>
          </div>
          <div className="topbar-right">
            <span className="connection-status"><span className="connection-dot" /> Local API</span>
            <button className="topbar-new-chat" onClick={newChat}><Icon name="plus" size={17} /><span>New chat</span></button>
          </div>
        </header>

        {hasConversation ? (
          <section className="conversation-layout">
            <div className="conversation-column">
              <div className="conversation-title">
                <div className="eyebrow">YOUR SESSION</div>
                <h1>Knowledge conversation</h1>
                <p>Answers grounded in the documents you have indexed.</p>
              </div>
              <div className="conversation-messages">
                {messages.map((message, index) => <Message message={message} key={`${message.role}-${index}`} />)}
                {loading && (
                  <article className="message message-assistant">
                    <div className="message-avatar"><BrandMark small /></div>
                    <div className="message-content">
                      <div className="message-meta"><strong>Knowledge Assistant</strong><span className="thinking-label">Searching your knowledge base…</span></div>
                      <div className="thinking-indicator"><span /><span /><span /></div>
                    </div>
                  </article>
                )}
                <div ref={bottomRef} />
              </div>
              {error && <div className="error-banner"><Icon name="alert" size={17} /><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error"><Icon name="close" size={16} /></button></div>}
              {uploading && <div className="upload-notice"><span className="spinner" /> Uploading and indexing PDF…</div>}
              <div className="composer-dock">
                <Composer input={input} setInput={setInput} onSubmit={handleSubmit} onUpload={() => fileRef.current?.click()} loading={loading} uploading={uploading} conversation inputRef={inputRef} />
                <p className="disclaimer">AI-generated answers can be inaccurate. Verify important details against the cited sources.</p>
              </div>
              <div className="conversation-documents"><CurrentDocuments {...commonDocumentsProps} /></div>
            </div>
          </section>
        ) : (
          <section className="home-layout">
            <div className="hero">
              <div className="hero-badge"><span className="hero-badge-dot" /> PRIVATE DOCUMENT INTELLIGENCE</div>
              <div className="hero-mark"><BrandMark /></div>
              <h1>Make your documents<br /><span>work for you.</span></h1>
              <p className="hero-description">Ask questions, discover insights, and get grounded answers from your own knowledge base.</p>

              <div className="home-composer-wrap">
                <Composer input={input} setInput={setInput} onSubmit={handleSubmit} onUpload={() => fileRef.current?.click()} loading={loading} uploading={uploading} inputRef={inputRef} />
                <div className="composer-bottom-note"><Icon name="shield" size={14} /> Responses are based on your indexed documents.</div>
              </div>

              {error && <div className="error-banner"><Icon name="alert" size={17} /><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error"><Icon name="close" size={16} /></button></div>}
              {uploading && <div className="upload-notice"><span className="spinner" /> Uploading and indexing PDF…</div>}

              <div className="suggestions">
                <div className="suggestions-heading"><span>GET STARTED</span><span>Choose a prompt</span></div>
                <div className="suggestion-grid">
                  {suggestions.map((item) => (
                    <button key={item.title} className="suggestion-card" onClick={() => sendMessage(item.prompt)} disabled={loading}>
                      <span className="suggestion-card-icon">{item.icon}</span>
                      <strong>{item.title}</strong>
                      <span className="suggestion-description">{item.description}</span>
                      <span className="suggestion-prompt">{item.prompt}</span>
                      <span className="suggestion-arrow"><Icon name="arrow" size={16} /></span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="home-documents"><CurrentDocuments {...commonDocumentsProps} /></div>
            <footer className="page-footer"><span><BrandMark small /> Advanced RAG Assistant</span><span>Built for focused, source-grounded research</span></footer>
          </section>
        )}
      </main>

      {confirmDelete && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setConfirmDelete(null); }}>
          <section className="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="delete-title">
            <div className="confirm-modal-icon"><Icon name="trash" size={22} /></div>
            <h2 id="delete-title">Remove this document?</h2>
            <p><strong>{confirmDelete}</strong> and its indexed chunks will be deleted from your knowledge base. This action cannot be undone.</p>
            <div className="confirm-modal-actions">
              <button className="secondary-button" onClick={() => setConfirmDelete(null)}>Cancel</button>
              <button className="danger-button" onClick={() => deleteDocument(confirmDelete)}><Icon name="trash" size={16} /> Delete document</button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
