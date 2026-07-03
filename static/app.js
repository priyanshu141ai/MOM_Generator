let selectedId = null;
let selectedMeeting = null;
let activeTab = "dashboard";
let currentView = "meetings";

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const text = await res.text();
    let message = text;
    try {
      const payload = JSON.parse(text);
      message = payload.detail || text;
    } catch {}
    throw new Error(message);
  }
  return res.json();
}

// View switching
function showView(viewName) {
  currentView = viewName;
  document.querySelectorAll(".view-panel").forEach(p => p.style.display = "none");
  document.querySelectorAll("aside nav button").forEach(b => b.classList.remove("active"));
  
  if (viewName === "meetings") {
    document.getElementById("viewMeetings").style.display = "block";
    document.getElementById("navMeetings").classList.add("active");
    loadMeetings();
  } else if (viewName === "search") {
    document.getElementById("viewSearch").style.display = "block";
    document.getElementById("navSearch").classList.add("active");
  } else if (viewName === "calendar") {
    document.getElementById("viewCalendar").style.display = "block";
    document.getElementById("navCalendar").classList.add("active");
    loadCalendarStatus();
  } else if (viewName === "insights") {
    document.getElementById("viewInsights").style.display = "block";
    document.getElementById("navInsights").classList.add("active");
    loadWorkspaceInsights();
  }
}

document.getElementById("navMeetings").onclick = () => showView("meetings");
document.getElementById("navSearch").onclick = () => showView("search");
document.getElementById("navCalendar").onclick = () => showView("calendar");
document.getElementById("navInsights").onclick = () => showView("insights");

async function loadMeetings() {
  const rows = document.getElementById("rows");
  rows.replaceChildren();
  const meetings = await api("/meetings");
  for (const m of meetings) {
    const tr = document.createElement("tr");
    tr.style.cursor = "pointer";
    tr.onclick = (e) => {
      if (e.target.tagName !== "BUTTON") {
        openMeeting(m.id);
      }
    };
    
    addCell(tr, m.id);
    addCell(tr, m.title);
    addCell(tr, m.platform.replace("_", " "));
    
    const statusCell = tr.insertCell();
    const chip = document.createElement("span");
    chip.className = `chip ${m.status.includes('failed') ? 'failed' : m.status}`;
    chip.textContent = m.status.replace("_", " ");
    statusCell.appendChild(chip);
    
    const actionCell = tr.insertCell();
    const button = document.createElement("button");
    button.textContent = "Open";
    button.onclick = () => openMeeting(m.id);
    actionCell.appendChild(button);
    
    rows.appendChild(tr);
  }
}

function addCell(row, value) {
  const td = row.insertCell();
  td.textContent = value ?? "";
}

async function openMeeting(id) {
  selectedId = id;
  selectedMeeting = await api(`/meetings/${id}`);
  document.getElementById("meetingDetailSection").style.display = "block";
  document.getElementById("detailTitle").textContent = `Meeting: ${selectedMeeting.title}`;
  renderTabs();
  // Scroll to detail section smoothly
  document.getElementById("meetingDetailSection").scrollIntoView({ behavior: 'smooth' });
}

// Parse diarized transcript format (e.g. "0.0-5.2: Speaker 0: Hello")
function parseTranscript(text) {
  if (!text) return [];
  const lines = text.split('\n');
  const results = [];
  const regex = /^([\d.]+)-([\d.]+):\s*([^:]+):\s*(.*)$/;
  for (const line of lines) {
    const match = line.match(regex);
    if (match) {
      results.push({
        start: parseFloat(match[1]),
        end: parseFloat(match[2]),
        speaker: match[3].trim(),
        text: match[4].trim()
      });
    } else if (line.trim()) {
      // Fallback for lines without speaker/time
      results.push({
        start: 0,
        end: 0,
        speaker: "Unknown",
        text: line.trim()
      });
    }
  }
  return results;
}

// Compute client-side analytics
function computeAnalytics(transcriptText) {
  const segments = parseTranscript(transcriptText);
  if (segments.length === 0) {
    return { talkTime: {}, speakers: [], fillerWords: {}, speechSpeed: {} };
  }

  const talkTime = {};
  const wordsCount = {};
  const fillerCount = {};
  let totalDuration = 0;
  
  const fillerPatterns = /\b(um|uh|like|so|you know|basically|actually)\b/gi;

  segments.forEach(seg => {
    const dur = seg.end - seg.start;
    if (dur > 0) {
      talkTime[seg.speaker] = (talkTime[seg.speaker] || 0) + dur;
      totalDuration += dur;
    }
    
    const wordList = seg.text.split(/\s+/).filter(Boolean);
    wordsCount[seg.speaker] = (wordsCount[seg.speaker] || 0) + wordList.length;
    
    // Count fillers
    const fillers = seg.text.match(fillerPatterns);
    if (fillers) {
      fillerCount[seg.speaker] = (fillerCount[seg.speaker] || 0) + fillers.length;
    } else {
      fillerCount[seg.speaker] = fillerCount[seg.speaker] || 0;
    }
  });

  const speakers = Object.keys(talkTime);
  const speechSpeed = {};
  speakers.forEach(spk => {
    const minutes = talkTime[spk] / 60;
    speechSpeed[spk] = minutes > 0 ? Math.round(wordsCount[spk] / minutes) : 0;
  });

  return { talkTime, totalDuration, speakers, fillerCount, speechSpeed };
}

function renderTabs() {
  if (!selectedMeeting) return;
  
  // Hide all tab contents
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
  
  // Show active tab content
  const activeContent = document.getElementById(`tab-${activeTab}`);
  if (activeContent) activeContent.classList.add("active");
  
  // Format MOM text (basic markdown parsing for lists and headers)
  if (activeTab === "mom") {
    const momBox = document.getElementById("momBox");
    if (selectedMeeting.mom) {
      momBox.innerHTML = formatMarkdown(selectedMeeting.mom);
      
      // Bind interactive checkbox clicks
      momBox.querySelectorAll(".task-checkbox").forEach(chk => {
        chk.onchange = async () => {
          const lineIndex = parseInt(chk.dataset.line);
          const lines = selectedMeeting.mom.split('\n');
          const isChecked = chk.checked;
          
          if (isChecked) {
            lines[lineIndex] = lines[lineIndex].replace(/\[ \]/, '[x]');
          } else {
            lines[lineIndex] = lines[lineIndex].replace(/\[[xX]\]/, '[ ]');
          }
          
          const newMom = lines.join('\n');
          try {
            selectedMeeting = await api(`/meetings/${selectedId}/mom`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ mom: newMom })
            });
            renderTabs();
          } catch (e) {
            alert("Failed to update task: " + e.message);
            chk.checked = !isChecked; // Revert checkbox in case of error
          }
        };
      });
      
    } else {
      momBox.textContent = "MOM summary not generated yet. Click Transcribe or Diarize.";
    }
  } 
  // Transcript Bubble UI
  else if (activeTab === "transcript") {
    const box = document.getElementById("transcriptBox");
    box.replaceChildren();
    if (!selectedMeeting.transcript) {
      box.textContent = "Transcript not generated yet.";
      return;
    }
    
    const segments = parseTranscript(selectedMeeting.transcript);
    segments.forEach(seg => {
      const bubble = document.createElement("div");
      bubble.className = "transcript-bubble";
      
      const avatar = document.createElement("div");
      avatar.className = "transcript-avatar";
      avatar.textContent = seg.speaker.slice(0, 2).toUpperCase();
      
      const body = document.createElement("div");
      body.className = "transcript-body";
      
      const header = document.createElement("div");
      header.className = "transcript-header";
      
      const name = document.createElement("span");
      name.className = "transcript-speaker";
      name.textContent = seg.speaker;
      name.title = "Click to rename speaker";
      name.onclick = () => renameSpeakerPrompt(seg.speaker);
      
      const time = document.createElement("span");
      time.className = "transcript-time";
      time.textContent = `${formatTime(seg.start)} - ${formatTime(seg.end)}`;
      
      header.appendChild(name);
      header.appendChild(time);
      
      const text = document.createElement("div");
      text.className = "transcript-text";
      text.textContent = seg.text;
      
      body.appendChild(header);
      body.appendChild(text);
      
      bubble.appendChild(avatar);
      bubble.appendChild(body);
      box.appendChild(bubble);
    });
  } 
  // Dashboard Metrics
  else if (activeTab === "dashboard") {
    const metrics = computeAnalytics(selectedMeeting.transcript);
    document.getElementById("statSpeakers").textContent = metrics.speakers.length || "0";
    
    // Simple sentiment estimate
    let sentiment = "Neutral";
    if (selectedMeeting.transcript) {
      const pos = (selectedMeeting.transcript.match(/\b(good|great|awesome|excellent|perfect|agree|yes)\b/gi) || []).length;
      const neg = (selectedMeeting.transcript.match(/\b(bad|issue|problem|delay|error|no|difficult)\b/gi) || []).length;
      sentiment = pos > neg ? "Positive" : neg > pos ? "Negative" : "Neutral";
    }
    document.getElementById("statSentiment").textContent = sentiment;
    
    // Engagement Score
    const engagement = metrics.speakers.length > 1 ? "88%" : selectedMeeting.transcript ? "50%" : "--";
    document.getElementById("statEngagement").textContent = engagement;
    
    const container = document.getElementById("talkTimeContainer");
    container.replaceChildren();
    if (metrics.speakers.length === 0) {
      container.textContent = "No analytics available yet.";
      return;
    }
    
    metrics.speakers.forEach(spk => {
      const pct = Math.round((metrics.talkTime[spk] / metrics.totalDuration) * 100);
      const row = document.createElement("div");
      row.className = "metric-row";
      row.innerHTML = `
        <div class="metric-label-row">
          <span>${spk}</span>
          <span>${pct}% (${Math.round(metrics.talkTime[spk])}s)</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" style="width: ${pct}%"></div>
        </div>
      `;
      container.appendChild(row);
    });
  }
  // Speaker Coach Recommendations
  else if (activeTab === "coach") {
    const grid = document.getElementById("coachGrid");
    grid.replaceChildren();
    
    const metrics = computeAnalytics(selectedMeeting.transcript);
    if (metrics.speakers.length === 0) {
      grid.textContent = "No analytics available yet.";
      return;
    }
    
    metrics.speakers.forEach(spk => {
      const wpm = metrics.speechSpeed[spk] || 0;
      const fillers = metrics.fillerCount[spk] || 0;
      
      let speedFeedback = "Pace: Normal (110-150 WPM)";
      if (wpm > 150) speedFeedback = "Pace: Fast (>150 WPM) - Try to slow down.";
      if (wpm > 0 && wpm < 110) speedFeedback = "Pace: Slow (<110 WPM) - Keep it concise.";
      
      let fillerFeedback = fillers > 5 ? "High filler word usage. Practice pauses." : "Low filler word usage. Great job!";
      
      const card = document.createElement("div");
      card.className = "coach-card";
      card.innerHTML = `
        <h4>🎓 ${spk} Coaching</h4>
        <div style="display: flex; flex-direction: column; gap: 12px; font-size: 14px;">
          <div><strong>Speech Rate:</strong> ${wpm} WPM</div>
          <div style="color: var(--text-secondary); font-size: 13px;">${speedFeedback}</div>
          <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 4px 0;">
          <div><strong>Filler Words:</strong> ${fillers} used</div>
          <div style="color: var(--text-secondary); font-size: 13px;">${fillerFeedback}</div>
        </div>
      `;
      grid.appendChild(card);
    });
  }
}

async function renameSpeakerPrompt(oldName) {
  const newName = prompt(`Rename speaker "${oldName}" to:`, oldName);
  if (!newName || newName === oldName) return;
  
  try {
    const payload = await api(`/meetings/${selectedId}/rename-speaker`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ old_name: oldName, new_name: newName })
    });
    selectedMeeting = payload;
    renderTabs();
  } catch (e) {
    alert(e.message);
  }
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function formatMarkdown(text) {
  const lines = text.split('\n');
  const result = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Checklist checkbox parsing
    const checkboxRegex = /^\s*-\s*\[([ xX])\]\s*(.*)$/;
    const checkboxMatch = line.match(checkboxRegex);
    if (checkboxMatch) {
      const isChecked = checkboxMatch[1].toLowerCase() === 'x';
      const taskText = checkboxMatch[2];
      result.push(`<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 14px;">
        <input type="checkbox" class="task-checkbox" data-line="${i}" ${isChecked ? 'checked' : ''} style="width: 16px; height: 16px; margin: 0; cursor: pointer;">
        <span style="${isChecked ? 'text-decoration: line-through; color: var(--text-muted);' : ''}">${taskText}</span>
      </div>`);
      continue;
    }
    
    let parsedLine = line
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^\s*-\s*(.*$)/gim, '<li>$1</li>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      
    result.push(parsedLine);
  }
  
  return result.join('<br>');
}

// Wiring Tabs Click
document.querySelectorAll(".tabs button").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".tabs button").forEach(x => x.classList.remove("active"));
    btn.classList.add("active");
    activeTab = btn.dataset.tab;
    renderTabs();
  };
});

// New Meeting Form
document.getElementById("meetingForm").onsubmit = async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  if (!data.starts_at) delete data.starts_at;
  await api("/meetings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  e.target.reset();
  loadMeetings();
};

document.getElementById("refreshBtn").onclick = loadMeetings;

// Action Trigger APIs
document.getElementById("recordBtn").onclick = async () => {
  if (!selectedId) return alert("Select a meeting first.");
  await api(`/meetings/${selectedId}/record?duration_sec=60`, { method: "POST" });
  alert("Recording started (60 seconds).");
  loadMeetings();
};

document.getElementById("transcribeBtn").onclick = async () => {
  if (!selectedId) return alert("Select a meeting first.");
  document.getElementById("transcribeBtn").disabled = true;
  document.getElementById("transcribeBtn").textContent = "Transcribing...";
  try {
    await api(`/meetings/${selectedId}/transcribe`, { method: "POST" });
    await openMeeting(selectedId);
  } catch (err) {
    alert(err.message);
  } finally {
    document.getElementById("transcribeBtn").disabled = false;
    document.getElementById("transcribeBtn").textContent = "🎙️ Transcribe";
  }
};

document.getElementById("diarizeBtn").onclick = async () => {
  if (!selectedId) return alert("Select a meeting first.");
  document.getElementById("diarizeBtn").disabled = true;
  document.getElementById("diarizeBtn").textContent = "Diarizing...";
  try {
    selectedMeeting = await api(`/meetings/${selectedId}/diarize?model_size=tiny`, { method: "POST" });
    activeTab = "transcript";
    renderTabs();
  } catch (err) {
    alert(err.message);
  } finally {
    document.getElementById("diarizeBtn").disabled = false;
    document.getElementById("diarizeBtn").textContent = "👥 Diarize";
  }
};

document.getElementById("sendBtn").onclick = async () => {
  if (!selectedId) return alert("Select a meeting first.");
  await api(`/meetings/${selectedId}/send-mom`, { method: "POST" });
  alert("Email sent to recipient.");
};

// Upload Audio
document.getElementById("audioInput").onchange = async (e) => {
  if (!selectedId) return alert("Select a meeting first.");
  if (!e.target.files.length) return;
  const data = new FormData();
  data.append("file", e.target.files[0]);
  try {
    selectedMeeting = await api(`/meetings/${selectedId}/upload-audio`, { method: "POST", body: data });
    activeTab = "mom";
    renderTabs();
    loadMeetings();
  } catch (err) {
    alert(err.message);
  } finally {
    e.target.value = "";
  }
};

// Search Copilot
async function runSearch() {
  const q = document.getElementById("searchInput").value.trim();
  if (!q) return;
  const results = await api(`/meetings/search?q=${encodeURIComponent(q)}`);
  const box = document.getElementById("searchResults");
  box.replaceChildren();
  
  if (results.length === 0) {
    box.textContent = "No matching meetings or transcripts found.";
    return;
  }
  
  results.forEach(item => {
    const card = document.createElement("div");
    card.className = "search-item";
    card.onclick = () => {
      showView("meetings");
      openMeeting(item.id);
    };
    
    card.innerHTML = `
      <h4>${item.title} (${item.platform.replace("_", " ")})</h4>
      <div class="search-match-snippet">... ${item.snippet} ...</div>
    `;
    box.appendChild(card);
  });
}
document.getElementById("searchBtn").onclick = runSearch;
document.getElementById("searchInput").onkeydown = (e) => {
  if (e.key === "Enter") runSearch();
};

// Calendar Sync Actions
async function loadCalendarStatus() {
  const status = await api("/calendar/google/status");
  const el = document.getElementById("calendarStatusText");
  if (status.configured && status.token_file) {
    el.textContent = "Connected. Google Calendar integrations are fully operational.";
  } else {
    el.textContent = "Not connected. Connect Google account in configuration client credentials.";
  }
}
document.getElementById("calendarBtn").onclick = async () => {
  try {
    const r = await api("/calendar/google/auth-url");
    location.href = r.auth_url;
  } catch (e) {
    alert(e.message);
  }
};
document.getElementById("importBtn").onclick = async () => {
  const r = await api("/calendar/google/import?days=7", { method: "POST" });
  alert(`Imported ${r.created} meeting(s).`);
};
document.getElementById("dueBtn").onclick = async () => {
  const r = await api("/calendar/run-due", { method: "POST" });
  alert(`Queued ${r.queued} meeting(s).`);
};

async function loadWorkspaceInsights() {
  try {
    const meetings = await api("/meetings");
    
    let totalMeetings = meetings.length;
    let totalDuration = 0;
    let totalWPM = 0;
    let meetingsWithWPM = 0;
    let totalFillers = 0;
    let meetingsWithFillers = 0;
    
    const globalTalkTime = {};
    const globalFillers = {};
    
    meetings.forEach(m => {
      if (!m.transcript) return;
      const analytics = computeAnalytics(m.transcript);
      
      // Sum duration
      if (analytics.totalDuration) {
        totalDuration += analytics.totalDuration;
      }
      
      // Sum global speaker talk time
      analytics.speakers.forEach(spk => {
        const dur = analytics.talkTime[spk] || 0;
        globalTalkTime[spk] = (globalTalkTime[spk] || 0) + dur;
        
        const fillers = analytics.fillerCount[spk] || 0;
        globalFillers[spk] = (globalFillers[spk] || 0) + fillers;
      });
      
      // Aggregate WPM averages
      let meetingWPMs = Object.values(analytics.speechSpeed).filter(w => w > 0);
      if (meetingWPMs.length > 0) {
        const avgMeetingWPM = meetingWPMs.reduce((a, b) => a + b, 0) / meetingWPMs.length;
        totalWPM += avgMeetingWPM;
        meetingsWithWPM++;
      }
      
      // Aggregate Filler word totals
      let meetingFillers = Object.values(analytics.fillerCount).reduce((a, b) => a + b, 0);
      if (analytics.speakers.length > 0) {
        totalFillers += meetingFillers;
        meetingsWithFillers++;
      }
    });
    
    // Format statistics values
    document.getElementById("globalTotalMeetings").textContent = totalMeetings;
    document.getElementById("globalTotalTime").textContent = `${Math.round(totalDuration / 60)}m`;
    
    const avgWPM = meetingsWithWPM > 0 ? Math.round(totalWPM / meetingsWithWPM) : 0;
    document.getElementById("globalAvgWPM").textContent = avgWPM ? `${avgWPM} WPM` : "--";
    
    const avgFillers = meetingsWithFillers > 0 ? Math.round(totalFillers / meetingsWithFillers) : 0;
    document.getElementById("globalAvgFillers").textContent = avgFillers || "--";
    
    // Render Top Speakers
    const spkContainer = document.getElementById("globalSpeakersContainer");
    spkContainer.replaceChildren();
    const sortedSpeakers = Object.keys(globalTalkTime).sort((a, b) => globalTalkTime[b] - globalTalkTime[a]);
    const maxTalkTime = sortedSpeakers.length > 0 ? globalTalkTime[sortedSpeakers[0]] : 1;
    
    if (sortedSpeakers.length === 0) {
      spkContainer.textContent = "No workspace insights available yet.";
    } else {
      sortedSpeakers.forEach(spk => {
        const dur = globalTalkTime[spk];
        const pct = Math.round((dur / maxTalkTime) * 100);
        const row = document.createElement("div");
        row.className = "metric-row";
        row.innerHTML = `
          <div class="metric-label-row">
            <span>${spk}</span>
            <span>${Math.round(dur / 60)} mins</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar" style="width: ${pct}%"></div>
          </div>
        `;
        spkContainer.appendChild(row);
      });
    }
    
    // Render Filler Word Distribution
    const fillerContainer = document.getElementById("globalFillersContainer");
    fillerContainer.replaceChildren();
    const sortedFillers = Object.keys(globalFillers).sort((a, b) => globalFillers[b] - globalFillers[a]);
    const maxFillers = sortedFillers.length > 0 ? globalFillers[sortedFillers[0]] : 1;
    
    if (sortedFillers.length === 0) {
      fillerContainer.textContent = "No workspace insights available yet.";
    } else {
      sortedFillers.forEach(spk => {
        const count = globalFillers[spk];
        const pct = maxFillers > 0 ? Math.round((count / maxFillers) * 100) : 0;
        const row = document.createElement("div");
        row.className = "metric-row";
        row.innerHTML = `
          <div class="metric-label-row">
            <span>${spk}</span>
            <span>${count} times</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar" style="width: ${pct}%; background: linear-gradient(90deg, #ef4444, #f59e0b);"></div>
          </div>
        `;
        fillerContainer.appendChild(row);
      });
    }
  } catch (err) {
    console.error("Error loading insights:", err);
  }
}

// Start default view
showView("meetings");
