import { useState, useRef } from "react";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "";

// ── Brand tokens (matches iMocha Analytics palette) ───────────────────────────
const C = {
  orange:      "#F47920",
  orangeLight: "#FFF4EC",
  orangeMid:   "#FDE8D4",
  sidebar:     "#FFFFFF",
  bg:          "#F5F6FA",
  white:       "#FFFFFF",
  border:      "#E8EAF0",
  text:        "#1A1A2E",
  sub:         "#6B7280",
  purple:      "#6B4EFF",
  blue:        "#2563EB",
  green:       "#059669",
  red:         "#DC2626",
};

const CEFR_COLOR = {
  BelowA2: "#94A3B8", A1: "#64B5F6", A2: "#4A90D9",
  B1: "#2563EB", B2: "#1E40AF", "B2+": "#1E3A8A",
  C1: "#1A237E", C2: "#0D0D3D",
};

// ── Small reusable pieces ──────────────────────────────────────────────────────
function Logo() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <polygon points="14,2 26,8 26,20 14,26 2,20 2,8"
          fill={C.orange} />
        <polygon points="14,6 22,10 22,18 14,22 6,18 6,10"
          fill="white" opacity="0.25" />
      </svg>
      <span style={{ fontWeight: 800, fontSize: 17, color: C.orange, letterSpacing: "-0.3px" }}>
        iMocha
      </span>
    </div>
  );
}

function NavItem({ icon, label, active }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "9px 16px", borderRadius: 8, cursor: "pointer",
      background: active ? C.orangeLight : "transparent",
      color: active ? C.orange : C.sub,
      fontWeight: active ? 600 : 400,
      fontSize: 14,
    }}>
      <span style={{ fontSize: 16 }}>{icon}</span>
      {label}
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: C.white, border: `1px solid ${C.border}`,
      borderRadius: 12, padding: "20px 24px", flex: 1, minWidth: 0,
    }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: C.sub,
        textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>
        {label}
      </div>
      <div style={{ fontSize: 30, fontWeight: 800, color: color || C.orange }}>
        {value}
      </div>
    </div>
  );
}

function Badge({ level }) {
  return (
    <span style={{
      background: CEFR_COLOR[level] || C.blue,
      color: "#fff", borderRadius: 5,
      padding: "2px 9px", fontSize: 11, fontWeight: 700,
    }}>
      {level}
    </span>
  );
}

// ── Main app ───────────────────────────────────────────────────────────────────
export default function App() {
  const [file, setFile]         = useState(null);
  const [dragging, setDragging] = useState(false);
  const [status, setStatus]     = useState("idle");
  const [rows, setRows]         = useState([]);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [totalProcessed, setTotalProcessed] = useState(0);
  const inputRef = useRef();

  async function handleUpload() {
    if (!file) return;
    setStatus("uploading");
    setRows([]);
    setDownloadUrl(null);
    setErrorMsg("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API}/upload`, formData, {
        responseType: "blob",
        headers: { "Content-Type": "multipart/form-data" },
      });

      const blob = new Blob([res.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      setDownloadUrl(URL.createObjectURL(blob));
      setStatus("done");

      if (window.XLSX) {
        const ab = await blob.arrayBuffer();
        const wb = window.XLSX.read(ab, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const data = window.XLSX.utils.sheet_to_json(ws);
        const parsed = data.map((r) => ({
          name:        r["Employee_Full_Name"] || "—",
          id:          r["Employee_ID"] || "—",
          report_link: r["Report_Link"] || "",
        }));
        setRows(parsed);
        setTotalProcessed(t => t + parsed.length);
      } else {
        setRows([{ name: "Upload complete", id: "—", report_link: "" }]);
        setTotalProcessed(t => t + 1);
      }
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.response?.data?.detail || err.message || "Upload failed.");
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }

  function reset() {
    setFile(null);
    setStatus("idle");
    setRows([]);
    setDownloadUrl(null);
    setErrorMsg("");
  }

  const isDone = status === "done";

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "'Inter', 'Segoe UI', sans-serif", background: C.bg }}>

      {/* ── Sidebar ─────────────────────────────────────────────────────────── */}
      <aside style={{
        width: 220, background: C.sidebar, borderRight: `1px solid ${C.border}`,
        display: "flex", flexDirection: "column", padding: "20px 12px",
        position: "fixed", top: 0, left: 0, bottom: 0,
      }}>
        <div style={{ padding: "4px 4px 24px" }}>
          <Logo />
          <div style={{ fontSize: 11, color: C.sub, marginTop: 4, marginLeft: 36 }}>
            Analytics
          </div>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <NavItem icon="▤" label="Overview" active={true} />
        </nav>

        <div style={{ flex: 1 }} />
      </aside>

      {/* ── Main content ────────────────────────────────────────────────────── */}
      <div style={{ marginLeft: 220, flex: 1, display: "flex", flexDirection: "column" }}>

        {/* Top bar */}
        <header style={{
          background: C.white, borderBottom: `1px solid ${C.border}`,
          padding: "14px 32px", display: "flex", alignItems: "center",
          justifyContent: "space-between",
        }}>
          <span style={{ fontWeight: 700, fontSize: 18, color: C.text }}>
            CEFR Report Engine
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {downloadUrl && (
              <a
                href={downloadUrl}
                download="cefr_reports_with_links.xlsx"
                style={{
                  background: C.orange, color: "#fff", borderRadius: 8,
                  padding: "8px 18px", fontWeight: 600, fontSize: 13,
                  textDecoration: "none", display: "inline-flex",
                  alignItems: "center", gap: 6,
                }}>
                ↓ Download Excel
              </a>
            )}
            <button
              onClick={handleUpload}
              disabled={!file || status === "uploading"}
              style={{
                background: file && status !== "uploading" ? C.text : C.border,
                color: file && status !== "uploading" ? "#fff" : C.sub,
                border: "none", borderRadius: 8, padding: "8px 18px",
                fontWeight: 600, fontSize: 13,
                cursor: file && status !== "uploading" ? "pointer" : "not-allowed",
              }}>
              {status === "uploading" ? "Processing…" : "Generate Reports"}
            </button>
          </div>
        </header>

        <main style={{ flex: 1, padding: "28px 32px" }}>

          {/* Page title */}
          <div style={{ marginBottom: 24 }}>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: C.text, margin: 0 }}>
              Overview
            </h1>
            <p style={{ fontSize: 13, color: C.sub, marginTop: 4 }}>
              Upload iMocha assessment exports to generate CEFR candidate reports.
            </p>
          </div>

          {/* Stat cards */}
          <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
            <StatCard label="Total Reports Generated"
              value={isDone ? rows.length : "—"} color={C.orange} />
            <StatCard label="Candidates Processed"
              value={isDone ? rows.length : "—"} color={C.purple} />
            <StatCard label="Skills Scored"
              value={isDone ? "Reading · Listening" : "—"} color={C.blue} />
            <StatCard label="Status"
              value={isDone ? "Complete" : status === "uploading" ? "Processing" : "Idle"}
              color={isDone ? C.green : C.sub} />
          </div>

          {/* Upload zone */}
          {!isDone && (
            <div
              onClick={() => inputRef.current.click()}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              style={{
                border: `2px dashed ${dragging ? C.orange : C.border}`,
                borderRadius: 12, padding: "44px 24px", textAlign: "center",
                cursor: "pointer",
                background: dragging ? C.orangeLight : C.white,
                marginBottom: 20,
              }}>
              <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls"
                style={{ display: "none" }}
                onChange={(e) => setFile(e.target.files[0])} />
              <div style={{ fontSize: 32, marginBottom: 10 }}>📂</div>
              {file ? (
                <p style={{ fontWeight: 600, color: C.orange, fontSize: 14 }}>
                  {file.name}
                </p>
              ) : (
                <>
                  <p style={{ fontWeight: 600, color: C.text, fontSize: 14, margin: 0 }}>
                    Drag & drop your CSV / Excel export here
                  </p>
                  <p style={{ color: C.sub, fontSize: 12, marginTop: 6 }}>
                    or click to browse &nbsp;·&nbsp; .csv, .xlsx supported
                  </p>
                </>
              )}
            </div>
          )}

          {/* Status banners */}
          {status === "uploading" && (
            <Banner bg="#EEF2FF" color={C.purple}>
              Scoring candidates and generating PDF reports…
            </Banner>
          )}
          {status === "error" && (
            <Banner bg="#FEF2F2" color={C.red}>
              Error: {errorMsg}
            </Banner>
          )}
          {isDone && (
            <Banner bg="#ECFDF5" color={C.green}>
              Reports generated. Download the Excel file — each row contains a
              unique <strong>Report_Link</strong> to share with candidates.
            </Banner>
          )}

          {/* Results table */}
          {rows.length > 0 && (
            <div style={{
              background: C.white, borderRadius: 12,
              border: `1px solid ${C.border}`, overflow: "hidden", marginTop: 20,
            }}>
              <div style={{
                padding: "14px 20px", borderBottom: `1px solid ${C.border}`,
                display: "flex", alignItems: "center", justifyContent: "space-between",
              }}>
                <span style={{ fontWeight: 700, fontSize: 14, color: C.text }}>
                  Candidate Reports
                </span>
                <span style={{
                  background: C.orangeLight, color: C.orange,
                  borderRadius: 20, padding: "2px 12px",
                  fontSize: 12, fontWeight: 600,
                }}>
                  {rows.length} candidate{rows.length !== 1 ? "s" : ""}
                </span>
              </div>

              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#F9FAFB" }}>
                    {["#", "Candidate Name", "Employee ID", "Report"].map((h) => (
                      <th key={h} style={TH}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i} style={{
                      borderTop: `1px solid ${C.border}`,
                      background: i % 2 === 0 ? C.white : "#FAFAFA",
                    }}>
                      <td style={{ ...TD, color: C.sub, width: 40 }}>{i + 1}</td>
                      <td style={{ ...TD, fontWeight: 500 }}>{r.name}</td>
                      <td style={{ ...TD, color: C.sub }}>{r.id}</td>
                      <td style={TD}>
                        {r.report_link ? (
                          <a href={r.report_link} target="_blank" rel="noreferrer"
                            style={{
                              color: C.orange, fontSize: 12, fontWeight: 600,
                              textDecoration: "none", border: `1px solid ${C.orange}`,
                              borderRadius: 6, padding: "3px 10px",
                            }}>
                            View PDF →
                          </a>
                        ) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer style={{
          borderTop: `1px solid ${C.border}`, background: C.white,
          padding: "12px 32px", fontSize: 12, color: C.sub,
          display: "flex", justifyContent: "space-between",
        }}>
          <span>iMocha · CEFR Report Engine</span>
          <span>Reading &amp; Listening Module</span>
        </footer>
      </div>
    </div>
  );
}

function Banner({ bg, color, children }) {
  return (
    <div style={{
      background: bg, color, borderRadius: 8,
      padding: "11px 16px", fontSize: 13, fontWeight: 500, marginBottom: 16,
    }}>
      {children}
    </div>
  );
}

const TH = {
  padding: "10px 16px", textAlign: "left", fontSize: 11,
  fontWeight: 700, color: "#6B7280", textTransform: "uppercase",
  letterSpacing: "0.05em",
};

const TD = {
  padding: "11px 16px", fontSize: 13, color: "#374151",
};
