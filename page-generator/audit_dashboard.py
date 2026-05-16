# ABOUTME: A lightweight server that provides a real-time progress report of the audit.
# ABOUTME: Includes a browseable list of identity errors and debunked facts.
import http.server
import json
import os
import re
import time
from pathlib import Path
from datetime import datetime

PORT = 63463
PROJECT_DIR = Path(__file__).parent.parent
LOG_PATH = PROJECT_DIR / "audit.log"
REPORT_PATH = PROJECT_DIR / "FACT_AUDIT_REPORT.md"
STATS_PATH = PROJECT_DIR / "stats_summary.json"

# Total players from stats_summary.json (read once)
try:
    with open(STATS_PATH, 'r') as f:
        TOTAL_PLAYERS = len(json.load(f))
except:
    TOTAL_PLAYERS = 189

def parse_report():
    failures = []
    if not REPORT_PATH.exists():
        return failures
    
    content = REPORT_PATH.read_text(encoding='utf-8')
    sections = content.split('### ❌ ')
    
    for section in sections[1:]: # Skip header
        lines = section.strip().split('\n')
        if not lines: continue
        
        # Player name and date
        header = lines[0]
        name_match = re.search(r"(.*?) \((.*?)\)", header)
        if not name_match: continue
        
        name = name_match.group(1)
        date = name_match.group(2)
        
        prediction = "Unknown"
        reasoning = ""
        debunked = []
        
        current_fact = None
        
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("- **Phase 1 Prediction:**"):
                prediction = line.replace("- **Phase 1 Prediction:**", "").strip()
            elif line.startswith("- **Phase 1 Reasoning:"):
                reasoning = line.replace("- **Phase 1 Reasoning:", "").replace("**", "").strip()
            elif line.startswith("- **Fact:**"):
                current_fact = {"text": line.replace("- **Fact:**", "").strip(), "reason": "", "source": ""}
                debunked.append(current_fact)
            elif line.startswith("- **Reason:**") and current_fact:
                current_fact["reason"] = line.replace("- **Reason:**", "").strip()
            elif line.startswith("- **Source:**") and current_fact:
                current_fact["source"] = line.replace("- **Source:**", "").strip()
        
        failures.append({
            "name": name,
            "date": date,
            "prediction": prediction,
            "reasoning": reasoning,
            "debunked": debunked
        })
    
    return failures

class AuditStatusHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            processed = 0
            current_player = "Waiting..."
            start_time = None
            
            if LOG_PATH.exists():
                with open(LOG_PATH, 'r') as f:
                    log_lines = f.readlines()
                    processed = sum(1 for line in log_lines if "Phase 1: Checking identity" in line)
                    for line in reversed(log_lines):
                        if "Phase 1: Checking identity for" in line:
                            match = re.search(r"for (.*?) \(", line)
                            if match:
                                current_player = match.group(1)
                                break
                    start_time = os.path.getmtime(LOG_PATH)

            failures_list = parse_report()
            
            elapsed = time.time() - start_time if start_time else 0
            if processed > 0:
                sec_per_player = elapsed / processed
                remaining_sec = sec_per_player * (TOTAL_PLAYERS - processed)
            else:
                remaining_sec = (TOTAL_PLAYERS * 13)
            
            status = {
                "processed": processed,
                "total": TOTAL_PLAYERS,
                "failures_count": len(failures_list),
                "failures": failures_list,
                "current_player": current_player,
                "percent": round((processed / TOTAL_PLAYERS) * 100, 1) if TOTAL_PLAYERS > 0 else 0,
                "eta_seconds": round(remaining_sec)
            }
            self.wfile.write(json.dumps(status).encode())
            
        elif self.path == '/raw':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            if REPORT_PATH.exists():
                self.wfile.write(REPORT_PATH.read_bytes())
            else:
                self.wfile.write(b"Report not found yet.")
                
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Audit Progress Dashboard</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f0f4f8; color: #2d3748; display: flex; flex-direction: column; align-items: center; padding: 40px; margin: 0; }
                    .container { width: 100%; max-width: 1000px; }
                    .card { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 30px; border: 1px solid #e2e8f0; }
                    h1 { margin-top: 0; color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; font-weight: 800; letter-spacing: -0.5px; }
                    .stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 25px 0; }
                    .stat-item { background: #f8fafc; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #edf2f7; }
                    .stat-value { font-size: 24px; font-weight: 800; color: #3182ce; line-height: 1.2; }
                    .stat-label { font-size: 11px; text-transform: uppercase; color: #718096; margin-top: 8px; font-weight: 600; letter-spacing: 0.5px; }
                    .progress-container { height: 16px; background: #e2e8f0; border-radius: 8px; overflow: hidden; margin: 25px 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); }
                    .progress-bar { height: 100%; background: linear-gradient(90deg, #48bb78, #38a169); width: 0%; transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }
                    .current { font-style: italic; color: #4a5568; font-size: 14px; text-align: center; font-weight: 500; }
                    
                    .error-list { margin-top: 30px; }
                    .error-card { border-left: 6px solid #e53e3e; background: white; padding: 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-top: 1px solid #fed7d7; border-right: 1px solid #fed7d7; border-bottom: 1px solid #fed7d7; }
                    .error-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }
                    .error-name { font-weight: 800; font-size: 22px; color: #1a365d; }
                    .error-date { font-size: 13px; color: #718096; font-family: monospace; background: #f7fafc; padding: 4px 8px; border-radius: 4px; border: 1px solid #edf2f7; }
                    .error-reasoning { font-size: 15px; color: #4a5568; margin-bottom: 20px; padding: 15px; background: #fffaf0; border-radius: 8px; border: 1px solid #feebc8; line-height: 1.5; overflow-wrap: break-word; }
                    .debunked-fact { font-size: 14px; margin-bottom: 15px; padding-left: 20px; border-left: 3px solid #feb2b2; position: relative; overflow-wrap: break-word; }
                    .fact-text { font-weight: 700; color: #2d3748; line-height: 1.4; margin-bottom: 8px; overflow-wrap: break-word; }
                    .fact-reason { color: #c53030; margin-top: 8px; background: #fff5f5; padding: 10px; border-radius: 6px; overflow-wrap: break-word; }
                    .fact-source { font-size: 12px; color: #3182ce; margin-top: 8px; display: block; word-break: break-all; text-decoration: none; font-weight: 500; }
                    .fact-source:hover { text-decoration: underline; }
                    
                    .badge { font-size: 11px; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; font-weight: 700; margin-left: 10px; vertical-align: middle; }
                    .badge-red { background: #fed7d7; color: #c53030; }
                    
                    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
                    .auditing-pulse { animation: pulse 2s infinite; color: #3182ce; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="card">
                        <h1>Audit Live Status</h1>
                        <div style="text-align: right; margin-top: -45px; margin-bottom: 25px;">
                            <a href="/raw" target="_blank" style="font-size: 12px; color: #3182ce; text-decoration: none; font-weight: 600;">View Raw Markdown</a>
                        </div>
                        <div class="progress-container">
                            <div id="bar" class="progress-bar"></div>
                        </div>
                        <div class="stat-grid">
                            <div class="stat-item">
                                <div id="processed" class="stat-value">0 / 0</div>
                                <div class="stat-label">Processed</div>
                            </div>
                            <div class="stat-item">
                                <div id="failures_count" class="stat-value" style="color: #e53e3e">0</div>
                                <div class="stat-label">Suspect Players</div>
                            </div>
                            <div class="stat-item">
                                <div id="percent" class="stat-value">0%</div>
                                <div class="stat-label">Complete</div>
                            </div>
                            <div class="stat-item">
                                <div id="eta" class="stat-value">--:--</div>
                                <div class="stat-label">Remaining</div>
                            </div>
                        </div>
                        <div id="current" class="current">Initializing...</div>
                    </div>

                    <h2 id="errors-title">Detected Inconsistencies (0)</h2>
                    <div id="error-list" class="error-list">
                        <!-- Populated by JS -->
                    </div>
                </div>

                <script>
                    function formatTime(seconds) {
                        if (seconds <= 0 || isNaN(seconds)) return "00:00";
                        const m = Math.floor(seconds / 60);
                        const s = Math.floor(seconds % 60);
                        return `${m}:${s.toString().padStart(2, '0')}`;
                    }

                    function createErrorCard(error) {
                        const debunkedHtml = error.debunked.map(f => `
                            <div class="debunked-fact">
                                <div class="fact-text">"${f.text}"</div>
                                <div class="fact-reason"><b>Fix:</b> ${f.reason}</div>
                                <a href="${f.source}" class="fact-source" target="_blank">${f.source}</a>
                            </div>
                        `).join('');

                        return `
                            <div class="error-card">
                                <div class="error-header">
                                    <span class="error-name">${error.name} <span class="badge badge-red">Suspect</span></span>
                                    <span class="error-date">${error.date}</span>
                                </div>
                                <div class="error-reasoning"><b>Phase 1 Discovery:</b> ${error.reasoning}</div>
                                <div class="debunked-list">
                                    ${debunkedHtml || '<div style="font-size: 12px; color: #718096">No specific facts debunked yet.</div>'}
                                </div>
                            </div>
                        `;
                    }

                    async function update() {
                        try {
                            const res = await fetch('/api/status');
                            const data = await res.json();
                            
                            document.getElementById('processed').textContent = `${data.processed} / ${data.total}`;
                            document.getElementById('failures_count').textContent = data.failures_count;
                            document.getElementById('percent').textContent = `${data.percent}%`;
                            document.getElementById('bar').style.width = `${data.percent}%`;
                            document.getElementById('current').innerHTML = `Auditing: <span class="auditing-pulse">${data.current_player}</span>`;
                            document.getElementById('eta').textContent = formatTime(data.eta_seconds);
                            document.getElementById('errors-title').textContent = `Detected Inconsistencies (${data.failures_count})`;

                            const errorList = document.getElementById('error-list');
                            // Sort by date descending
                            const sortedFailures = data.failures.reverse();
                            errorList.innerHTML = sortedFailures.map(createErrorCard).join('');
                            
                        } catch (e) { console.error("Update failed", e); }
                    }

                    setInterval(update, 3000);
                    update();
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), AuditStatusHandler)
    print(f"Dashboard serving at http://localhost:{PORT}")
    server.serve_forever()
