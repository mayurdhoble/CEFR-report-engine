import { useState, useRef } from "react";
import axios from "axios";

// In production (Railway) VITE_API_URL = backend Railway URL
// In local dev it is empty string so the Vite proxy handles /upload and /report
const API = import.meta.env.VITE_API_URL || "";

const CEFR_COLOR = {
  BelowA2: "#B0BEC5",
  A1: "#90CAF9",
  A2: "#64B5F6",
  B1: "#4A90D9",
  B2: "#2C6DB5",
  "B2+": "#1E4FA0",
  C1: "#1A237E",
  C2: "#0D0D3D",
};

function Badge({ level }) {
  return (
    <span
      style={{
        background: CEFR_COLOR[level] || "#4A90D9",
        color: "#fff",
        borderRadius: 6,
        padding: "2px 10px",
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {level}
    </span>
  );
}

export default function App() {
  const [file, setFile]           = useState(null);
  const [dragging, setDragging]   = useState(false);
  const [status, setStatus]       = useState("idle"); // idle | uploading | done | error
  const [rows, setRows]           = useState([]);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [errorMsg, setErrorMsg]   = useState("");
  const inputRef = useRef();

  // ── parse X-Results header + blob to build table rows ──────────────────────
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

      // Create download URL for the returned Excel
      const blob = new Blob([res.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      setDownloadUrl(URL.createObjectURL(blob));

      // Read the Excel to populate the results table
      // We re-upload just to parse — alternatively the backend can return JSON too.
      // For now we parse the filename from header and show success.
      setStatus("done");

      // Re-read rows from the blob using SheetJS if available, else show generic message
      if (window.XLSX) {
        const ab = await blob.arrayBuffer();
        const wb = window.XLSX.read(ab, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const data = window.XLSX.utils.sheet_to_json(ws);
        const parsed = data.map((r) => ({
          name:        r["Employee_Full_Name"] || "—",
          id:          r["Employee_ID"] || "—",
          cefr:        r["Reading (B2-C1)_Candidate_Score"] != null ? "—" : "—",
          report_link: r["Report_Link"] || "",
        }));
        setRows(parsed);
      } else {
        setRows([{ name: "Upload complete", id: "—", cefr: "—", report_link: "" }]);
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

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <header style={{
        background: "#fff",
        borderBottom: "1px solid #E5E7EB",
        padding: "14px 40px",
        display: "flex",
        alignItems: "center",
        gap: 14,
      }}>
        <span style={{ fontSize: 22, color: "#FF6B35" }}>⬡</span>
        <span style={{ fontWeight: 700, fontSize: 18, color: "#6B4EFF" }}>iMocha</span>
        <span style={{ color: "#9CA3AF", fontSize: 14, marginLeft: 8 }}>
          CEFR Report Engine
        </span>
      </header>

      {/* Body */}
      <main style={{ flex: 1, padding: "40px 40px" }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4, color: "#1F1F3D" }}>
          Generate CEFR Reading Reports
        </h1>
        <p style={{ color: "#6B7280", marginBottom: 28, fontSize: 14 }}>
          Upload your iMocha CSV export. The engine will score each candidate's
          Reading section, generate a PDF per candidate, and return the file with
          report links appended.
        </p>

        {/* Drop zone */}
        <div
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          style={{
            border: `2px dashed ${dragging ? "#6B4EFF" : "#D1D5DB"}`,
            borderRadius: 12,
            padding: "48px 24px",
            textAlign: "center",
            cursor: "pointer",
            background: dragging ? "#F0EDFF" : "#FAFAFA",
            transition: "all 0.2s",
            marginBottom: 20,
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            style={{ display: "none" }}
            onChange={(e) => setFile(e.target.files[0])}
          />
          <div style={{ fontSize: 36, marginBottom: 12 }}>📄</div>
          {file ? (
            <p style={{ fontWeight: 600, color: "#6B4EFF" }}>{file.name}</p>
          ) : (
            <>
              <p style={{ fontWeight: 600, color: "#374151" }}>
                Drag & drop your CSV / Excel file here
              </p>
              <p style={{ color: "#9CA3AF", fontSize: 13, marginTop: 4 }}>
                or click to browse
              </p>
            </>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 12, marginBottom: 32 }}>
          <button
            onClick={handleUpload}
            disabled={!file || status === "uploading"}
            style={{
              background: "#6B4EFF",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "10px 28px",
              fontWeight: 600,
              fontSize: 14,
              cursor: file && status !== "uploading" ? "pointer" : "not-allowed",
              opacity: !file || status === "uploading" ? 0.6 : 1,
            }}
          >
            {status === "uploading" ? "Processing…" : "Generate Reports"}
          </button>

          {status !== "idle" && (
            <button
              onClick={reset}
              style={{
                background: "#F3F4F6",
                color: "#374151",
                border: "none",
                borderRadius: 8,
                padding: "10px 20px",
                fontWeight: 500,
                fontSize: 14,
                cursor: "pointer",
              }}
            >
              Reset
            </button>
          )}

          {downloadUrl && (
            <a
              href={downloadUrl}
              download="cefr_reports_with_links.xlsx"
              style={{
                background: "#10B981",
                color: "#fff",
                borderRadius: 8,
                padding: "10px 20px",
                fontWeight: 600,
                fontSize: 14,
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              ⬇ Download Excel with Links
            </a>
          )}
        </div>

        {/* Status banners */}
        {status === "uploading" && (
          <div style={bannerStyle("#EEF2FF", "#6B4EFF")}>
            Processing candidates and generating PDFs…
          </div>
        )}
        {status === "error" && (
          <div style={bannerStyle("#FEF2F2", "#DC2626")}>
            Error: {errorMsg}
          </div>
        )}
        {status === "done" && (
          <div style={bannerStyle("#ECFDF5", "#059669")}>
            Reports generated successfully. Download the Excel file above — each
            row now has a <strong>Report_Link</strong> column. Share those links
            with candidates to let them view their PDF.
          </div>
        )}

        {/* Results table */}
        {rows.length > 0 && (
          <div style={{
            background: "#fff",
            borderRadius: 12,
            border: "1px solid #E5E7EB",
            overflow: "hidden",
            marginTop: 24,
          }}>
            <div style={{
              padding: "14px 20px",
              borderBottom: "1px solid #E5E7EB",
              fontWeight: 600,
              fontSize: 14,
              color: "#1F1F3D",
            }}>
              Results — {rows.length} candidate{rows.length !== 1 ? "s" : ""}
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#F9FAFB" }}>
                  {["Candidate Name", "ID", "CEFR Level", "Report Link"].map((h) => (
                    <th key={h} style={thStyle}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} style={{ borderTop: "1px solid #F3F4F6" }}>
                    <td style={tdStyle}>{r.name}</td>
                    <td style={tdStyle}>{r.id}</td>
                    <td style={tdStyle}>{r.cefr ? <Badge level={r.cefr} /> : "—"}</td>
                    <td style={tdStyle}>
                      {r.report_link ? (
                        <a href={r.report_link} target="_blank" rel="noreferrer"
                          style={{ color: "#6B4EFF", fontSize: 12 }}>
                          View Report
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
        textAlign: "center",
        padding: "16px",
        fontSize: 12,
        color: "#9CA3AF",
        borderTop: "1px solid #E5E7EB",
        background: "#fff",
      }}>
        iMocha CEFR Report Engine — Reading Module
      </footer>
    </div>
  );
}

const bannerStyle = (bg, color) => ({
  background: bg,
  color,
  borderRadius: 8,
  padding: "12px 16px",
  fontSize: 13,
  marginBottom: 16,
  fontWeight: 500,
});

const thStyle = {
  padding: "10px 16px",
  textAlign: "left",
  fontSize: 12,
  fontWeight: 600,
  color: "#6B7280",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
};

const tdStyle = {
  padding: "12px 16px",
  fontSize: 13,
  color: "#374151",
};
