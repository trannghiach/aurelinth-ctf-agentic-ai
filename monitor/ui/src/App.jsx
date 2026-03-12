import { useState, useEffect, useRef } from "react"

const API = "http://localhost:8000"

const eventColor = {
    agent_start:  "#a3a3a3",
    agent_done:   "#4ade80",
    agent_failed: "#f87171",
    tool_call:    "#60a5fa",
    tool_result:  "#6b7280",
    agent_reason: "#c084fc",
    supervisor_decision: "#f59e0b",
    flag_found:          "#faff00",
}

export default function App() {
  const [target, setTarget] = useState("")
  const [notes, setNotes] = useState("")
  const [events, setEvents] = useState([])
  const [agents, setAgents] = useState({})
  const logRef = useRef(null)
  const [flagBanner, setFlagBanner] = useState(null)

  // Load history on mount
  useEffect(() => {
    fetch(`${API}/events/history`)
      .then(r => r.json())
      .then(d => {
        setEvents(d.events || [])
        d.events?.forEach(e => updateAgent(e.type, e.data))
      })
  }, [])

  // SSE stream
  useEffect(() => {
    const es = new EventSource(`${API}/stream`)

    es.addEventListener("agent_start", e => {
      const data = JSON.parse(e.data)
      setEvents(prev => [...prev, { type: "agent_start", data }])
      updateAgent("agent_start", data)
    })

    es.addEventListener("agent_done", e => {
      const data = JSON.parse(e.data)
      setEvents(prev => [...prev, { type: "agent_done", data }])
      updateAgent("agent_done", data)
    })

    es.addEventListener("agent_failed", e => {
      const data = JSON.parse(e.data)
      setEvents(prev => [...prev, { type: "agent_failed", data }])
      updateAgent("agent_failed", data)
    })

    es.addEventListener("tool_call", e => {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, { type: "tool_call", data }])
    })

    es.addEventListener("tool_result", e => {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, { type: "tool_result", data }])
    })

    es.addEventListener("agent_reason", e => {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, { type: "agent_reason", data }])
    })

    es.addEventListener("supervisor_decision", e => {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, { type: "supervisor_decision", data }])
    })

    es.addEventListener("flag_found", e => {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, { type: "flag_found", data }])
    })

    es.addEventListener("pipeline_complete", e => {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, { type: "pipeline_complete", data }])
        if (data.flag) setFlagBanner(data)
    })

    return () => es.close()
  }, [])

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current)
      logRef.current.scrollTop = logRef.current.scrollHeight
  }, [events])

  function updateAgent(type, data) {
    if (!data.task_id) return
    setAgents(prev => ({
      ...prev,
      [data.task_id]: {
        agent: data.agent || prev[data.task_id]?.agent || data.task_id,
        status: type === "agent_start" ? "running"
               : type === "agent_done" ? "done"
               : "failed"
      }
    }))
  }

  function run() {
    if (!target) return
    fetch(`${API}/run?target=${encodeURIComponent(target)}&notes=${encodeURIComponent(notes)}`, {
      method: "POST"
    })
    setEvents([])
    setAgents({})
  }

  const statusColor = { running: "#facc15", done: "#4ade80", failed: "#f87171", pending: "#6b7280" }

  return (
    <div style={{ fontFamily: "monospace", padding: 24, background: "#0f0f0f", minHeight: "100vh", color: "#e5e5e5" }}>
      <h2 style={{ margin: "0 0 16px", color: "#fff" }}>aurelinth</h2>

      {/* Control */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        <input
          value={target}
          onChange={e => setTarget(e.target.value)}
          placeholder="target URL"
          style={{ flex: 2, padding: "6px 10px", background: "#1a1a1a", border: "1px solid #333", color: "#e5e5e5", borderRadius: 4 }}
        />
        <input
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="notes (optional)"
          style={{ flex: 1, padding: "6px 10px", background: "#1a1a1a", border: "1px solid #333", color: "#e5e5e5", borderRadius: 4 }}
        />
        <button
          onClick={run}
          style={{ padding: "6px 16px", background: "#fff", color: "#000", border: "none", borderRadius: 4, cursor: "pointer" }}
        >
          run
        </button>
      </div>

      {/* Agent status */}
      {Object.keys(agents).length > 0 && (
        <div style={{ marginBottom: 24, display: "flex", gap: 12, flexWrap: "wrap" }}>
          {Object.entries(agents).map(([id, { agent, status }]) => (
            <div key={id} style={{ padding: "4px 12px", border: `1px solid ${statusColor[status]}`, borderRadius: 4, color: statusColor[status], fontSize: 13 }}>
              {agent} — {status}
            </div>
          ))}
        </div>
      )}

      {flagBanner && (
          <div style={{
              margin: "16px 0",
              padding: "16px 24px",
              background: "#0a0a0a",
              border: "2px solid #faff00",
              borderRadius: 4,
              color: "#faff00",
              fontFamily: "monospace"
          }}>
              <div style={{ fontSize: 11, opacity: 0.6 }}>FLAG CAPTURED</div>
              <div style={{ fontSize: 22, fontWeight: "bold", margin: "4px 0" }}>{flagBanner.flag}</div>
              <div style={{ fontSize: 11, opacity: 0.6 }}>
                  {flagBanner.target} — {flagBanner.total_time}s — {flagBanner.agents_run} agents
              </div>
              <button
                  onClick={() => setFlagBanner(null)}
                  style={{ marginTop: 8, padding: "2px 8px", background: "transparent", border: "1px solid #faff00", color: "#faff00", cursor: "pointer", fontSize: 11 }}
              >
                  dismiss
              </button>
          </div>
      )}

      {/* Event log */}
      <div
        ref={logRef}
        style={{ height: 480, overflowY: "auto", background: "#1a1a1a", borderRadius: 4, padding: 12, fontSize: 12, lineHeight: 1.6 }}
      >
        {events.length === 0 && <span style={{ color: "#555" }}>waiting for events...</span>}
        {events.map((e, i) => (
          <div key={i} style={{ color: eventColor[e.type] || "#a3a3a3" }}>
            [{e.type}] {JSON.stringify(e.data)}
          </div>
        ))}
      </div>
    </div>
  )
}