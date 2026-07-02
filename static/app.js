let selectedId = null;
let selectedMeeting = null;
let activeTab = "mom";

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const text = await res.text();
    let message = text;
    try {
      const payload = JSON.parse(text);
      message = payload.detail || text;
    } catch {
    }
    throw new Error(message);
  }
  return res.json();
}

async function loadMeetings() {
  const rows = document.getElementById("rows");
  rows.replaceChildren();
  const meetings = await api("/meetings");
  for (const m of meetings) {
    const tr = document.createElement("tr");
    const status = m.status.length > 24 ? `${m.status.slice(0, 24)}...` : m.status;
    addCell(tr, m.id);
    addCell(tr, m.title);
    addCell(tr, m.platform);
    const statusCell = tr.insertCell();
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.title = m.status;
    chip.textContent = status;
    statusCell.appendChild(chip);
    const actionCell = tr.insertCell();
    const button = document.createElement("button");
    button.className = "rowBtn";
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
  const m = selectedMeeting;
  document.getElementById("detailTitle").textContent = `MOM: ${m.title}`;
  renderDetail();
}

function renderDetail() {
  if (!selectedMeeting) return;
  const text = activeTab === "mom" ? selectedMeeting.mom : selectedMeeting.transcript;
  document.getElementById("momBox").textContent = text || `${activeTab} not generated yet.`;
}

document.getElementById("meetingForm").onsubmit = async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  if (!data.starts_at) delete data.starts_at;
  await api("/meetings", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)});
  e.target.reset();
  loadMeetings();
};

document.getElementById("refreshBtn").onclick = loadMeetings;
document.getElementById("dueBtn").onclick = async () => {
  const r = await api("/calendar/run-due", {method:"POST"});
  alert(`Queued ${r.queued} meeting(s).`);
  loadMeetings();
};
document.getElementById("calendarBtn").onclick = async () => {
  try {
    const r = await api("/calendar/google/auth-url");
    location.href = r.auth_url;
  } catch (e) {
    alert(e.message);
  }
};
document.getElementById("importBtn").onclick = async () => {
  try {
    const r = await api("/calendar/google/import?days=7", {method:"POST"});
    alert(`Imported ${r.created} meeting(s).`);
    loadMeetings();
  } catch (e) {
    alert(e.message);
  }
};
document.getElementById("sendBtn").onclick = async () => {
  if (!selectedId) return alert("Select a meeting first.");
  await api(`/meetings/${selectedId}/send-mom`, {method:"POST"});
  alert("Email sent.");
};
document.getElementById("recordBtn").onclick = async () => {
  if (!selectedId) return alert("Select a meeting first.");
  await api(`/meetings/${selectedId}/record?duration_sec=60`, {method:"POST"});
  alert("Recording started.");
  loadMeetings();
};
document.getElementById("transcribeBtn").onclick = async () => {
  if (!selectedId) return alert("Select a meeting first.");
  await api(`/meetings/${selectedId}/transcribe?model_size=tiny`, {method:"POST"});
  await openMeeting(selectedId);
  loadMeetings();
};
document.getElementById("diarizeBtn").onclick = async () => {
  if (!selectedId) return alert("Select a meeting first.");
  try {
    selectedMeeting = await api(`/meetings/${selectedId}/diarize?model_size=tiny`, {method:"POST"});
    activeTab = "transcript";
    renderDetail();
    loadMeetings();
  } catch (e) {
    alert(e.message);
  }
};
document.getElementById("audioInput").onchange = async (e) => {
  if (!selectedId) return alert("Select a meeting first.");
  if (!e.target.files.length) return;
  const data = new FormData();
  data.append("file", e.target.files[0]);
  try {
    selectedMeeting = await api(`/meetings/${selectedId}/upload-audio?model_size=tiny`, {method:"POST", body:data});
    activeTab = "mom";
    renderDetail();
    loadMeetings();
  } catch (err) {
    alert(err.message);
  } finally {
    e.target.value = "";
  }
};
document.querySelectorAll(".tabs button").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".tabs button").forEach((x) => x.classList.remove("active"));
    btn.classList.add("active");
    activeTab = btn.dataset.tab;
    renderDetail();
  };
});

loadMeetings();
