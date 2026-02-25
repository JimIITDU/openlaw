import { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:8000";

// ---- API helpers ----
async function apiHealth() {
  const r = await fetch(`${API_BASE}/health`);
  return r.json();
}
async function apiQuery(question, include_sources = true) {
  const r = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, include_sources }),
  });
  return r.json();
}
async function apiSearch(query, k = 5) {
  const r = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, k }),
  });
  return r.json();
}
async function apiIngestFile(file) {
  const form = new FormData();
  form.append("file", file);
  const r = await fetch(`${API_BASE}/ingest`, { method: "POST", body: form });
  return r.json();
}
async function apiStats() {
  const r = await fetch(`${API_BASE}/stats`);
  return r.json();
}

// ---- Icons ----
const IconScale = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3v19M5 8l7-5 7 5M3 20h18"/>
    <path d="M5 8l-2 6h4L5 8zM19 8l-2 6h4L19 8z"/>
  </svg>
);
const IconSearch = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
  </svg>
);
const IconUpload = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);
const IconBook = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
  </svg>
);
const IconSend = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);
const IconLink = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
  </svg>
);
const IconStat = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
  </svg>
);

// ---- Sub-components ----
function ConfidenceBadge({ confidence }) {
  const map = {
    high: { label: "High Confidence", color: "#10b981", bg: "rgba(16,185,129,0.12)" },
    medium: { label: "Medium Confidence", color: "#f59e0b", bg: "rgba(245,158,11,0.12)" },
    low: { label: "Low Confidence", color: "#ef4444", bg: "rgba(239,68,68,0.12)" },
  };
  const c = map[confidence] || map.medium;
  return (
    <span style={{ fontSize: "0.7rem", fontFamily: "'IBM Plex Mono', monospace", padding: "2px 8px", borderRadius: "4px", color: c.color, background: c.bg, border: `1px solid ${c.color}40`, letterSpacing: "0.05em" }}>
      {c.label}
    </span>
  );
}

function SourceCard({ source, index }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(212,175,55,0.2)", borderRadius: "8px", overflow: "hidden", transition: "border-color 0.2s" }}
      onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(212,175,55,0.5)"}
      onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(212,175,55,0.2)"}>
      <button onClick={() => setOpen(o => !o)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: "10px", padding: "10px 14px", background: "none", border: "none", cursor: "pointer", color: "#d4af37", textAlign: "left" }}>
        <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.7rem", background: "rgba(212,175,55,0.15)", padding: "2px 7px", borderRadius: "4px", flexShrink: 0 }}>
          Art. {source.article_number}
        </span>
        <span style={{ fontSize: "0.8rem", color: "#a89060", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {source.article}
        </span>
        <span style={{ fontSize: "0.7rem", color: "rgba(212,175,55,0.5)", transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>▾</span>
      </button>
      {open && (
        <div style={{ padding: "0 14px 12px", fontSize: "0.8rem", color: "#8a7a5a", lineHeight: 1.7, borderTop: "1px solid rgba(212,175,55,0.1)" }}>
          <p style={{ margin: "10px 0 0" }}>{source.content}</p>
        </div>
      )}
    </div>
  );
}

function ChatMessage({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{ display: "flex", flexDirection: isUser ? "row-reverse" : "row", gap: "12px", alignItems: "flex-start", animation: "fadeUp 0.3s ease" }}>
      <div style={{ width: "32px", height: "32px", borderRadius: "50%", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center",
        background: isUser ? "rgba(212,175,55,0.2)" : "rgba(139,90,43,0.3)", border: isUser ? "1px solid rgba(212,175,55,0.4)" : "1px solid rgba(139,90,43,0.5)", fontSize: "0.8rem" }}>
        {isUser ? "👤" : "⚖️"}
      </div>
      <div style={{ maxWidth: "80%", display: "flex", flexDirection: "column", gap: "8px", alignItems: isUser ? "flex-end" : "flex-start" }}>
        <div style={{ padding: "12px 16px", borderRadius: isUser ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
          background: isUser ? "rgba(212,175,55,0.12)" : "rgba(20,16,10,0.8)",
          border: isUser ? "1px solid rgba(212,175,55,0.3)" : "1px solid rgba(139,90,43,0.3)",
          fontSize: "0.875rem", color: "#e8d5a3", lineHeight: 1.75, whiteSpace: "pre-wrap" }}>
          {msg.content}
        </div>
        {msg.confidence && <ConfidenceBadge confidence={msg.confidence} />}
        {msg.verified_citations?.length > 0 && (
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {msg.verified_citations.map(c => (
              <span key={c} style={{ fontSize: "0.68rem", fontFamily: "'IBM Plex Mono', monospace", padding: "2px 6px", borderRadius: "4px", background: "rgba(212,175,55,0.1)", color: "#d4af37", border: "1px solid rgba(212,175,55,0.25)" }}>
                <IconLink /> Art.{c}
              </span>
            ))}
          </div>
        )}
        {msg.sources?.length > 0 && (
          <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "6px" }}>
            <p style={{ margin: 0, fontSize: "0.7rem", color: "#6b5a3a", fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "0.08em" }}>SOURCES</p>
            {msg.sources.map((s, i) => <SourceCard key={i} source={s} index={i} />)}
          </div>
        )}
      </div>
    </div>
  );
}

// ---- Main App ----
export default function App() {
  const [tab, setTab] = useState("chat"); // chat | search | ingest | stats
  const [health, setHealth] = useState(null);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "As-salamu alaykum! I am ConstitutionBD — your expert guide to the People's Republic of Bangladesh Constitution. Ask me anything about fundamental rights, state structures, amendments, or any constitutional provision." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchK, setSearchK] = useState(5);
  const [searchLoading, setSearchLoading] = useState(false);
  const [ingestFile, setIngestFile] = useState(null);
  const [ingestStatus, setIngestStatus] = useState(null);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const chatEndRef = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => {
    apiHealth().then(setHealth).catch(() => setHealth({ status: "unreachable" }));
    apiStats().then(setStats).catch(() => {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages(m => [...m, { role: "user", content: question }]);
    setLoading(true);
    try {
      const res = await apiQuery(question);
      if (res.error) throw new Error(res.error);
      setMessages(m => [...m, {
        role: "assistant",
        content: res.answer,
        sources: res.sources,
        verified_citations: res.verified_citations,
        cross_references: res.cross_references,
        confidence: res.confidence,
      }]);
    } catch (e) {
      setMessages(m => [...m, { role: "assistant", content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    setSearchResults([]);
    try {
      const res = await apiSearch(searchQuery, searchK);
      setSearchResults(res.results || []);
    } catch (e) {
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }

  async function handleIngest() {
    if (!ingestFile) return;
    setIngestLoading(true);
    setIngestStatus(null);
    try {
      const res = await apiIngestFile(ingestFile);
      setIngestStatus(res);
      if (res.success) {
        apiHealth().then(setHealth);
        apiStats().then(setStats);
      }
    } catch (e) {
      setIngestStatus({ success: false, message: e.message });
    } finally {
      setIngestLoading(false);
    }
  }

  const statusColor = health?.status === "healthy" ? "#10b981" : health?.status === "degraded" ? "#f59e0b" : "#ef4444";

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=IBM+Plex+Mono:wght@400;500&family=Lora:wght@400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0d0a06; color: #e8d5a3; font-family: 'Lora', Georgia, serif; min-height: 100vh; }
        ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: rgba(212,175,55,0.3); border-radius: 4px; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes spin { to { transform: rotate(360deg); } }
        input, textarea { outline: none; }
        button { cursor: pointer; }
      `}</style>

      {/* Background texture */}
      <div style={{ position: "fixed", inset: 0, backgroundImage: `radial-gradient(ellipse at 20% 20%, rgba(139,90,43,0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(212,175,55,0.05) 0%, transparent 50%)`, pointerEvents: "none", zIndex: 0 }} />

      <div style={{ position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", flexDirection: "column", maxWidth: "900px", margin: "0 auto", padding: "0 16px" }}>

        {/* Header */}
        <header style={{ padding: "28px 0 20px", borderBottom: "1px solid rgba(212,175,55,0.15)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
              <div style={{ color: "#d4af37", opacity: 0.9 }}><IconScale /></div>
              <div>
                <h1 style={{ fontFamily: "'Cormorant Garamond', Georgia, serif", fontSize: "1.6rem", fontWeight: 600, letterSpacing: "0.02em", color: "#d4af37", lineHeight: 1 }}>
                  ConstitutionBD
                </h1>
                <p style={{ fontSize: "0.7rem", fontFamily: "'IBM Plex Mono', monospace", color: "#6b5a3a", letterSpacing: "0.1em", marginTop: "3px" }}>
                  BANGLADESH · CONSTITUTIONAL INTELLIGENCE
                </p>
              </div>
            </div>
            {/* Health indicator */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.72rem", fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: statusColor, animation: health?.status === "healthy" ? "none" : "pulse 1.5s infinite" }} />
              <span style={{ color: "#6b5a3a" }}>{health ? health.status.toUpperCase() : "CONNECTING…"}</span>
            </div>
          </div>

          {/* Tabs */}
          <nav style={{ display: "flex", gap: "4px", marginTop: "20px" }}>
            {[
              { id: "chat", label: "Ask", icon: "⚖️" },
              { id: "search", label: "Search Articles", icon: "🔍" },
              { id: "ingest", label: "Load Constitution", icon: "📄" },
              { id: "stats", label: "Stats", icon: "📊" },
            ].map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                style={{ padding: "7px 16px", borderRadius: "6px", border: "1px solid", fontSize: "0.78rem", fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "0.05em", transition: "all 0.2s",
                  borderColor: tab === t.id ? "rgba(212,175,55,0.5)" : "rgba(212,175,55,0.12)",
                  background: tab === t.id ? "rgba(212,175,55,0.1)" : "transparent",
                  color: tab === t.id ? "#d4af37" : "#6b5a3a" }}>
                {t.icon} {t.label}
              </button>
            ))}
          </nav>
        </header>

        {/* Content */}
        <main style={{ flex: 1, paddingTop: "24px", paddingBottom: "24px" }}>

          {/* ── CHAT TAB ── */}
          {tab === "chat" && (
            <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 220px)", minHeight: "400px" }}>
              <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "20px", paddingRight: "4px" }}>
                {messages.map((m, i) => <ChatMessage key={i} msg={m} />)}
                {loading && (
                  <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
                    <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "rgba(139,90,43,0.3)", border: "1px solid rgba(139,90,43,0.5)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem" }}>⚖️</div>
                    <div style={{ padding: "12px 16px", borderRadius: "4px 16px 16px 16px", background: "rgba(20,16,10,0.8)", border: "1px solid rgba(139,90,43,0.3)" }}>
                      <div style={{ display: "flex", gap: "5px", alignItems: "center" }}>
                        {[0, 1, 2].map(i => <span key={i} style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#d4af37", animation: `pulse 1s ${i * 0.2}s infinite` }} />)}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input bar */}
              <div style={{ marginTop: "16px", display: "flex", gap: "10px", padding: "14px", background: "rgba(20,16,10,0.9)", border: "1px solid rgba(212,175,55,0.2)", borderRadius: "12px", backdropFilter: "blur(10px)" }}>
                <textarea value={input} onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                  placeholder="Ask about the Bangladesh Constitution… (e.g. What are the fundamental rights?)"
                  rows={1} style={{ flex: 1, background: "none", border: "none", color: "#e8d5a3", fontSize: "0.875rem", fontFamily: "'Lora', Georgia, serif", resize: "none", lineHeight: 1.6, padding: "2px 0" }}
                />
                <button onClick={handleSend} disabled={loading || !input.trim()}
                  style={{ padding: "8px 16px", borderRadius: "8px", border: "1px solid rgba(212,175,55,0.4)", background: "rgba(212,175,55,0.12)", color: "#d4af37", display: "flex", alignItems: "center", gap: "6px", fontSize: "0.78rem", fontFamily: "'IBM Plex Mono', monospace", opacity: loading || !input.trim() ? 0.4 : 1, transition: "all 0.2s" }}>
                  <IconSend /> Ask
                </button>
              </div>
            </div>
          )}

          {/* ── SEARCH TAB ── */}
          {tab === "search" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div>
                <h2 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "1.4rem", fontWeight: 600, color: "#d4af37", marginBottom: "6px" }}>Search Articles</h2>
                <p style={{ fontSize: "0.82rem", color: "#6b5a3a" }}>Find specific articles using keyword search across the constitution.</p>
              </div>
              <div style={{ display: "flex", gap: "10px" }}>
                <div style={{ flex: 1, display: "flex", alignItems: "center", gap: "10px", padding: "11px 14px", background: "rgba(20,16,10,0.9)", border: "1px solid rgba(212,175,55,0.2)", borderRadius: "8px" }}>
                  <span style={{ color: "#6b5a3a" }}><IconSearch /></span>
                  <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleSearch()}
                    placeholder="Search e.g. fundamental rights, citizenship, parliament…"
                    style={{ flex: 1, background: "none", border: "none", color: "#e8d5a3", fontSize: "0.875rem", fontFamily: "'Lora', serif" }}
                  />
                </div>
                <select value={searchK} onChange={e => setSearchK(Number(e.target.value))}
                  style={{ padding: "0 12px", background: "rgba(20,16,10,0.9)", border: "1px solid rgba(212,175,55,0.2)", borderRadius: "8px", color: "#d4af37", fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.78rem" }}>
                  {[3,5,8,10].map(n => <option key={n} value={n}>{n} results</option>)}
                </select>
                <button onClick={handleSearch} disabled={searchLoading}
                  style={{ padding: "0 20px", background: "rgba(212,175,55,0.12)", border: "1px solid rgba(212,175,55,0.4)", borderRadius: "8px", color: "#d4af37", fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.78rem" }}>
                  {searchLoading ? "…" : "Search"}
                </button>
              </div>

              {searchResults.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <p style={{ fontSize: "0.72rem", fontFamily: "'IBM Plex Mono', monospace", color: "#6b5a3a", letterSpacing: "0.08em" }}>{searchResults.length} RESULTS FOUND</p>
                  {searchResults.map((r, i) => (
                    <div key={i} style={{ padding: "16px", background: "rgba(20,16,10,0.8)", border: "1px solid rgba(212,175,55,0.15)", borderRadius: "10px", animation: "fadeUp 0.3s ease" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
                        <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.72rem", background: "rgba(212,175,55,0.12)", color: "#d4af37", padding: "3px 8px", borderRadius: "5px" }}>Art. {r.article_number}</span>
                        <span style={{ fontSize: "0.82rem", color: "#a89060", fontStyle: "italic" }}>{r.article}</span>
                      </div>
                      <p style={{ fontSize: "0.82rem", color: "#8a7a5a", lineHeight: 1.75 }}>{r.content.slice(0, 400)}{r.content.length > 400 ? "…" : ""}</p>
                    </div>
                  ))}
                </div>
              )}
              {searchResults.length === 0 && !searchLoading && searchQuery && (
                <p style={{ textAlign: "center", color: "#6b5a3a", fontSize: "0.85rem", padding: "40px 0" }}>No results found. Try different keywords.</p>
              )}
            </div>
          )}

          {/* ── INGEST TAB ── */}
          {tab === "ingest" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
              <div>
                <h2 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "1.4rem", fontWeight: 600, color: "#d4af37", marginBottom: "6px" }}>Load Constitution</h2>
                <p style={{ fontSize: "0.82rem", color: "#6b5a3a" }}>Upload a .txt file of the Bangladesh Constitution to index it for querying.</p>
              </div>

              {health && (
                <div style={{ padding: "14px 18px", background: "rgba(20,16,10,0.8)", border: "1px solid rgba(212,175,55,0.15)", borderRadius: "10px", display: "flex", gap: "16px" }}>
                  {[
                    { label: "System", value: health.status?.toUpperCase(), ok: health.status === "healthy" },
                    { label: "Documents", value: health.documents_loaded ? "Loaded" : "Empty", ok: health.documents_loaded },
                    { label: "Gemini LLM", value: health.llm_available ? "Active" : "Unavailable", ok: health.llm_available },
                  ].map(item => (
                    <div key={item.label} style={{ flex: 1, textAlign: "center" }}>
                      <p style={{ fontSize: "0.65rem", fontFamily: "'IBM Plex Mono', monospace", color: "#6b5a3a", letterSpacing: "0.08em" }}>{item.label}</p>
                      <p style={{ fontSize: "0.85rem", color: item.ok ? "#10b981" : "#f59e0b", fontFamily: "'IBM Plex Mono', monospace", marginTop: "4px" }}>{item.value}</p>
                    </div>
                  ))}
                </div>
              )}

              <div onClick={() => fileRef.current?.click()}
                style={{ border: "2px dashed rgba(212,175,55,0.25)", borderRadius: "12px", padding: "40px", textAlign: "center", cursor: "pointer", transition: "all 0.2s" }}
                onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(212,175,55,0.5)"}
                onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(212,175,55,0.25)"}>
                <input ref={fileRef} type="file" accept=".txt" style={{ display: "none" }} onChange={e => setIngestFile(e.target.files[0])} />
                <div style={{ color: "#6b5a3a", marginBottom: "12px" }}><IconUpload /></div>
                <p style={{ color: "#d4af37", fontSize: "0.9rem", marginBottom: "6px" }}>{ingestFile ? ingestFile.name : "Click to select constitution .txt file"}</p>
                <p style={{ fontSize: "0.75rem", color: "#4a3a2a", fontFamily: "'IBM Plex Mono', monospace" }}>Only .txt files supported</p>
              </div>

              {ingestFile && (
                <button onClick={handleIngest} disabled={ingestLoading}
                  style={{ padding: "13px", background: "rgba(212,175,55,0.12)", border: "1px solid rgba(212,175,55,0.4)", borderRadius: "10px", color: "#d4af37", fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.85rem", letterSpacing: "0.08em", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", opacity: ingestLoading ? 0.6 : 1 }}>
                  {ingestLoading ? "INDEXING…" : <><IconBook /> INGEST CONSTITUTION</>}
                </button>
              )}

              {ingestStatus && (
                <div style={{ padding: "14px 18px", background: ingestStatus.success ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)", border: `1px solid ${ingestStatus.success ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`, borderRadius: "10px" }}>
                  <p style={{ color: ingestStatus.success ? "#10b981" : "#ef4444", fontSize: "0.85rem", fontFamily: "'IBM Plex Mono', monospace" }}>
                    {ingestStatus.success ? "✓ " : "✗ "}{ingestStatus.message}
                  </p>
                  {ingestStatus.documents_processed && (
                    <p style={{ color: "#6b5a3a", fontSize: "0.75rem", marginTop: "6px", fontFamily: "'IBM Plex Mono', monospace" }}>
                      {ingestStatus.documents_processed} document chunks indexed
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ── STATS TAB ── */}
          {tab === "stats" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
              <div>
                <h2 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "1.4rem", fontWeight: 600, color: "#d4af37", marginBottom: "6px" }}>System Statistics</h2>
                <p style={{ fontSize: "0.82rem", color: "#6b5a3a" }}>Current state of the ConstitutionBD RAG engine.</p>
              </div>

              {stats ? (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  {[
                    { label: "Documents Loaded", value: stats.documents_loaded, icon: "📄" },
                    { label: "Articles Indexed", value: stats.articles_indexed, icon: "📑" },
                    { label: "LLM Provider", value: stats.llm_provider?.toUpperCase(), icon: "🤖" },
                    { label: "Storage Type", value: stats.storage_type, icon: "💾" },
                    { label: "LLM Available", value: stats.llm_available ? "YES" : "NO", icon: "⚡", ok: stats.llm_available },
                  ].map(item => (
                    <div key={item.label} style={{ padding: "20px", background: "rgba(20,16,10,0.8)", border: "1px solid rgba(212,175,55,0.15)", borderRadius: "10px" }}>
                      <p style={{ fontSize: "1.4rem", marginBottom: "8px" }}>{item.icon}</p>
                      <p style={{ fontSize: "0.65rem", fontFamily: "'IBM Plex Mono', monospace", color: "#6b5a3a", letterSpacing: "0.08em", marginBottom: "6px" }}>{item.label}</p>
                      <p style={{ fontSize: "1.1rem", color: item.ok !== undefined ? (item.ok ? "#10b981" : "#ef4444") : "#d4af37", fontFamily: "'IBM Plex Mono', monospace", fontWeight: 500 }}>
                        {item.value ?? "—"}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "60px 0", color: "#6b5a3a", fontSize: "0.85rem" }}>
                  {health?.status === "unreachable" ? "Backend not reachable. Make sure the FastAPI server is running." : "Loading stats…"}
                </div>
              )}

              <div style={{ padding: "16px 20px", background: "rgba(20,16,10,0.8)", border: "1px solid rgba(212,175,55,0.1)", borderRadius: "10px" }}>
                <p style={{ fontSize: "0.65rem", fontFamily: "'IBM Plex Mono', monospace", color: "#6b5a3a", letterSpacing: "0.08em", marginBottom: "10px" }}>API ENDPOINTS</p>
                {["/health", "/query", "/search", "/ingest", "/stats"].map(ep => (
                  <div key={ep} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "6px 0", borderBottom: "1px solid rgba(212,175,55,0.06)" }}>
                    <span style={{ fontSize: "0.65rem", fontFamily: "'IBM Plex Mono', monospace", padding: "2px 6px", borderRadius: "3px", background: "rgba(16,185,129,0.12)", color: "#10b981" }}>GET/POST</span>
                    <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.8rem", color: "#a89060" }}>{API_BASE}{ep}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer style={{ borderTop: "1px solid rgba(212,175,55,0.1)", padding: "14px 0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ fontSize: "0.68rem", fontFamily: "'IBM Plex Mono', monospace", color: "#3a2a1a", letterSpacing: "0.08em" }}>
            CONSTITUTION OF THE PEOPLE'S REPUBLIC OF BANGLADESH · 1972
          </p>
          <p style={{ fontSize: "0.68rem", fontFamily: "'IBM Plex Mono', monospace", color: "#3a2a1a" }}>
            Powered by Gemini + RAG
          </p>
        </footer>
      </div>
    </>
  );
}