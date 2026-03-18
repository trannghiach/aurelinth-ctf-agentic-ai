import { useState, useEffect, useRef } from "react"

const API = "http://localhost:8000"

const eventColor = {
    agent_start:          "#a3a3a3",
    agent_done:           "#4ade80",
    agent_failed:         "#f87171",
    tool_call:            "#60a5fa",
    tool_result:          "#6b7280",
    agent_reason:         "#c084fc",
    supervisor_decision:  "#f59e0b",
    flag_found:           "#faff00",
    pipeline_complete:    "#4ade80",
    unexpected_finding:   "#fb923c",
}

const agentColor = {
    web_recon:               "#60a5fa",
    sqli_hunter:             "#f87171",
    xss_hunter:              "#fb923c",
    auth_bypasser:           "#a78bfa",
    lfi_hunter:              "#34d399",
    ssti_hunter:             "#f472b6",
    idor_hunter:             "#facc15",
    file_upload_hunter:      "#38bdf8",
    flag_extractor:          "#faff00",
    code_reader:             "#60a5fa",
    dep_checker:             "#94a3b8",
    vuln_reasoner:           "#c084fc",
    sqli_auditor:            "#f87171",
    xss_auditor:             "#fb923c",
    auth_auditor:            "#a78bfa",
    lfi_auditor:             "#34d399",
    ssti_auditor:            "#f472b6",
    access_control_auditor:  "#facc15",
    upload_auditor:          "#38bdf8",
    race_condition_auditor:  "#e879f9",
    crypto_auditor:          "#4ade80",
    deserialization_auditor: "#f43f5e",
    crypto_hunter:           "#f0abfc",
}

const statusColor = {
    running: "#facc15",
    done:    "#4ade80",
    failed:  "#f87171",
}

const inp = {
    padding: "7px 10px",
    background: "#111",
    border: "1px solid #222",
    color: "#e5e5e5",
    borderRadius: 4,
    fontFamily: "monospace",
    fontSize: 12,
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
}

export default function App() {
    const [mode, setMode]               = useState("blackbox")
    const [target, setTarget]           = useState("")
    const [localTarget, setLocalTarget] = useState("")
    const [sourceCode, setSourceCode]   = useState("")
    const [notes, setNotes]             = useState("")
    const [flagFormat, setFlagFormat]   = useState("")
    const [events, setEvents]           = useState([])
    const [agents, setAgents]           = useState({})
    const [flagBanner, setFlagBanner]   = useState(null)
    const [running, setRunning]         = useState(false)
    const [spinnerIdx, setSpinnerIdx]   = useState(0)
    const logRef = useRef(null)
    const spinnerFrames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    useEffect(() => {
        if (!running) return
        const t = setInterval(() => setSpinnerIdx(i => (i + 1) % spinnerFrames.length), 100)
        return () => clearInterval(t)
    }, [running])

    useEffect(() => {
        fetch(`${API}/events/history`)
            .then(r => r.json())
            .then(d => {
                setEvents(d.events || [])
                d.events?.forEach(e => updateAgent(e.type, e.data))
            })
    }, [])

    useEffect(() => {
        const es = new EventSource(`${API}/stream`)
        const on = (type, fn) => es.addEventListener(type, e => {
            const data = JSON.parse(e.data)
            setEvents(prev => [...prev, { type, data }])
            fn?.(data)
        })
        on("agent_start",        d => updateAgent("agent_start", d))
        on("agent_done",         d => updateAgent("agent_done", d))
        on("agent_failed",       d => updateAgent("agent_failed", d))
        on("tool_call")
        on("tool_result")
        on("agent_reason")
        on("supervisor_decision")
        on("unexpected_finding")
        on("flag_found",         d => { if (d.flag) setFlagBanner(d) })
        on("pipeline_complete",  d => { if (d.flag) setFlagBanner(d); setRunning(false) })
        return () => es.close()
    }, [])

    useEffect(() => {
        if (logRef.current)
            logRef.current.scrollTop = logRef.current.scrollHeight
    }, [events])

    function updateAgent(type, data) {
        if (!data.task_id) return
        setAgents(prev => {
            const existing = prev[data.task_id] || {}
            const startedAt = type === "agent_start" ? Date.now() : existing.startedAt
            const elapsed = (type === "agent_done" || type === "agent_failed") && existing.startedAt
                ? Math.round((Date.now() - existing.startedAt) / 1000)
                : existing.elapsed
            return {
                ...prev,
                [data.task_id]: {
                    agent:     data.agent || existing.agent || data.task_id,
                    status:    type === "agent_start" ? "running" : type === "agent_done" ? "done" : "failed",
                    startedAt,
                    elapsed,
                    summary:   data.summary || existing.summary,
                }
            }
        })
    }

    function run() {
        if (!target || running) return
        const p = new URLSearchParams({ target, notes, flag_format: flagFormat })
        if (mode === "whitebox") {
            p.set("local_target", localTarget)
            p.set("source_code", sourceCode)
        }
        fetch(`${API}/run?${p}`, { method: "POST" })
        setEvents([])
        setAgents({})
        setFlagBanner(null)
        setRunning(true)
    }

    function clear() {
        fetch(`${API}/clear`, { method: "POST" })
        setEvents([])
        setAgents({})
        setFlagBanner(null)
        setRunning(false)
    }

    return (
        <div style={{
            fontFamily: "monospace",
            background: "#0a0a0a",
            minHeight: "100vh",
            width: "100%",
            boxSizing: "border-box",
            padding: "20px 28px",
            color: "#e5e5e5",
        }}>

            {/* Header */}
            <div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
                <span style={{ fontSize: 15, fontWeight: "bold", color: "#fff" }}>aurelinth</span>
                <span style={{ fontSize: 11, color: running ? "#facc15" : "#333", marginLeft: 10 }}>
                    {running ? `${spinnerFrames[spinnerIdx]} running` : "idle"}
                </span>
                <button onClick={clear} disabled={running} style={{
                    marginLeft: 12, padding: "2px 10px", borderRadius: 3,
                    fontFamily: "monospace", fontSize: 11,
                    background: "transparent",
                    border: "1px solid #222",
                    color: running ? "#222" : "#444",
                    cursor: running ? "not-allowed" : "pointer",
                }}>clear</button>
                <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
                    {["blackbox", "whitebox"].map(m => (
                        <button key={m} onClick={() => setMode(m)} style={{
                            padding: "3px 14px", borderRadius: 3,
                            cursor: "pointer", fontFamily: "monospace", fontSize: 11,
                            background: mode === m ? "#e5e5e5" : "transparent",
                            color: mode === m ? "#000" : "#444",
                            border: `1px solid ${mode === m ? "#e5e5e5" : "#222"}`,
                        }}>{m}</button>
                    ))}
                </div>
            </div>

            {/* Inputs */}
            <div style={{ display: "grid", gap: 8, marginBottom: 14, width: "100%" }}>
                <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr", gap: 8 }}>
                    <input value={target} onChange={e => setTarget(e.target.value)}
                        placeholder="real target URL" style={inp} />
                    <input value={flagFormat} onChange={e => setFlagFormat(e.target.value)}
                        placeholder="flag format  picoCTF{...}" style={inp} />
                </div>

                {mode === "whitebox" && (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                        <input value={localTarget} onChange={e => setLocalTarget(e.target.value)}
                            placeholder="local target  http://localhost:8888" style={inp} />
                        <input value={sourceCode} onChange={e => setSourceCode(e.target.value)}
                            placeholder="source code path  ~/challenges/app/src" style={inp} />
                    </div>
                )}

                <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}>
                    <input value={notes} onChange={e => setNotes(e.target.value)}
                        placeholder="notes (optional)" style={inp} />
                    <button onClick={run} disabled={running || !target} style={{
                        padding: "7px 28px", borderRadius: 4, whiteSpace: "nowrap",
                        fontFamily: "monospace", fontSize: 12,
                        background: running || !target ? "#111" : "#e5e5e5",
                        color: running || !target ? "#333" : "#000",
                        border: `1px solid ${running || !target ? "#222" : "#e5e5e5"}`,
                        cursor: running || !target ? "not-allowed" : "pointer",
                    }}>{running ? "running..." : "run"}</button>
                </div>
            </div>

            {/* Agent pills */}
            {Object.keys(agents).length > 0 && (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                    {Object.entries(agents).map(([id, { agent, status, elapsed, summary }]) => (
                        <div key={id} title={summary || ""} style={{
                            padding: "3px 10px", borderRadius: 3, fontSize: 11,
                            border: `1px solid ${statusColor[status] || "#222"}`,
                            color: agentColor[agent] || "#a3a3a3",
                            background: status === "running" ? "#0f0f00" : "transparent",
                            whiteSpace: "nowrap", cursor: summary ? "help" : "default",
                        }}>
                            {agent}
                            <span style={{ color: statusColor[status], marginLeft: 5, fontSize: 10 }}>
                                {status === "running" ? spinnerFrames[spinnerIdx] : status === "done" ? "✓" : "✗"}
                            </span>
                            {elapsed != null && status !== "running" &&
                                <span style={{ color: "#333", marginLeft: 4, fontSize: 10 }}>{elapsed}s</span>
                            }
                        </div>
                    ))}
                </div>
            )}

            {/* Flag banner */}
            {flagBanner && (
                <div style={{
                    marginBottom: 12, padding: "14px 20px",
                    background: "#080800", border: "1px solid #faff00", borderRadius: 4,
                }}>
                    <div style={{ fontSize: 10, color: "#555", letterSpacing: 2, marginBottom: 4 }}>FLAG CAPTURED</div>
                    <div style={{ fontSize: 20, fontWeight: "bold", color: "#faff00", marginBottom: 4 }}>
                        {flagBanner.flag}
                    </div>
                    <div style={{ fontSize: 11, color: "#444" }}>
                        {flagBanner.target}
                        {flagBanner.agent && <> — <span style={{ color: "#666" }}>{flagBanner.agent}</span></>}
                        {flagBanner.total_time && <> — {flagBanner.total_time}s</>}
                        {flagBanner.agents_run && <> — {flagBanner.agents_run} agents</>}
                    </div>
                    <button onClick={() => setFlagBanner(null)} style={{
                        marginTop: 10, padding: "2px 10px",
                        background: "transparent", border: "1px solid #2a2a2a",
                        color: "#555", cursor: "pointer",
                        fontFamily: "monospace", fontSize: 11, borderRadius: 3,
                    }}>dismiss</button>
                </div>
            )}

            {/* Event log */}
            <div ref={logRef} style={{
                height: "calc(100vh - 260px)",
                minHeight: 200,
                overflowY: "auto",
                background: "#0d0d0d",
                border: "1px solid #191919",
                borderRadius: 4,
                padding: "10px 14px",
                fontSize: 12,
                lineHeight: 1.75,
                width: "100%",
                boxSizing: "border-box",
            }}>
                {events.length === 0
                    ? <span style={{ color: "#222" }}>waiting for events...</span>
                    : events.map((e, i) => (
                        <div key={i} style={{ display: "flex", gap: 10 }}>
                            <span style={{ color: "#3a3a3a", flexShrink: 0, userSelect: "none" }}>[{e.type}]</span>
                            <span style={{ color: eventColor[e.type] || "#a3a3a3", wordBreak: "break-all" }}>
                                {renderEvent(e)}
                            </span>
                        </div>
                    ))
                }
            </div>
        </div>
    )
}

function renderEvent({ type, data }) {
    switch (type) {
        case "agent_start":
            return <span style={{ color: "#444" }}>{data.agent} starting</span>

        case "agent_done":
            return <><span style={{ color: "#4ade80" }}>{data.agent} done</span>
                {data.summary && <span style={{ color: "#2d4a2d" }}> — {data.summary.slice(0, 120)}</span>}</>

        case "agent_failed":
            return <span style={{ color: "#f87171" }}>{data.agent} failed — {data.error}</span>

        case "tool_call":
            return <><span style={{ color: "#60a5fa" }}>🔧 {data.agent} → {data.tool}</span>
                <span style={{ color: "#4a6a7a" }}> {data.cmd}</span></>

        case "tool_result":
            return <span style={{ color: "#374151" }}>✓ [{data.status}] {data.output}</span>

        case "agent_reason":
            return <span style={{ color: "#c084fc" }}>{data.agent}: {data.text}</span>

        case "supervisor_decision":
            return <><span style={{ color: "#f59e0b" }}>
                iter {data.iteration} → {data.next ? <strong>{data.next}</strong> : <span style={{ color: "#444" }}>stop</span>}
            </span><span style={{ color: "#2a2a2a" }}> — {data.reason}</span></>

        case "flag_found":
            return <span style={{ color: "#faff00", fontWeight: "bold" }}>
                🚩 {data.flag} <span style={{ color: "#666", fontWeight: "normal" }}>by {data.agent}</span>
            </span>

        case "unexpected_finding":
            return <span style={{ color: "#fb923c" }}>⚠ {data.agent}: {data.finding}</span>

        case "pipeline_complete":
            return <><span style={{ color: "#4ade80" }}>
                complete — {data.mode} — {data.total_time}s — {data.done}/{data.agents_run} agents
            </span>{data.flag && <span style={{ color: "#faff00" }}> 🚩 {data.flag}</span>}</>

        default:
            return <span style={{ color: "#2a2a2a" }}>{JSON.stringify(data)}</span>
    }
}