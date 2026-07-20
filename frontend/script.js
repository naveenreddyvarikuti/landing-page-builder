// "Try it yourself" swaps the showcase for the chat/preview workspace.
const showcaseView = document.getElementById("showcase-view");
const workspaceView = document.getElementById("workspace-view");
const tryBtn = document.getElementById("try-btn");

tryBtn.addEventListener("click", () => {
    showcaseView.hidden = true;
    workspaceView.hidden = false;
    messageInput.focus();
});

// ---- chat -> backend wiring ----
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const timeline = document.getElementById("timeline");
const previewFrame = document.getElementById("preview-frame");
const previewPlaceholder = document.getElementById("preview-placeholder");

// load the built website into the preview panel
function showPreview() {
    previewPlaceholder.hidden = true;
    previewFrame.hidden = false;
    // the ?t=... forces the iframe to reload fresh content after a rebuild
    previewFrame.src = `/api/sessions/${sessionId}/preview/index.html?t=${Date.now()}`;
}

// add one line of text to the timeline panel
function addLine(text) {
    const placeholder = timeline.querySelector(".placeholder");
    if (placeholder) placeholder.remove();
    const line = document.createElement("p");
    line.className = "timeline-line";
    line.textContent = text;
    timeline.appendChild(line);
    timeline.scrollTop = timeline.scrollHeight; // keep the newest line in view
}

// turn one event into a short, readable line ("" = skip it)
function eventToText(data) {
    if (data.type === "orchestrator") return `Planning ${data.tasks} task(s)...`;
    if (data.type === "task_start") return `Building: ${data.question}`;
    if (data.type === "coder_step") return `Coder: ${data.summary}`;
    if (data.type === "review") {
        return data.passed ? "Reviewer: looks good" : `Reviewer: needs changes — ${data.feedback}`;
    }
    if (data.type === "task_failed") return "Gave up after too many tries.";
    if (data.type === "done") return "Done!";
    if (data.type === "error") return `Error: ${data.message}`;
    return "";
}

let sessionId = null; // created on first send, then reused
let socket = null; // the open WebSocket, reused across messages

// Create a session (once) and open the WebSocket to it.
async function ensureConnection() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        return; // already connected
    }

    // POST /api/sessions -> { session_id }
    const resp = await fetch("/api/sessions", { method: "POST" });
    if (!resp.ok) {
        // guardrail hit (e.g. 429 too many sessions, 503 at capacity) — show it on the page
        const data = await resp.json().catch(() => ({}));
        addLine("Notice: " + (data.detail || "Could not start a session."));
        return;
    }
    const data = await resp.json();
    sessionId = data.session_id;

    // open the live pipe to this session
    const wsProtocol = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${wsProtocol}//${location.host}/api/sessions/${sessionId}/ws`);

    // show each event the server streams back as a line in the timeline
    socket.addEventListener("message", (event) => {
        const data = JSON.parse(event.data);
        const text = eventToText(data);
        if (text) addLine(text);
        if (data.type === "done") showPreview();
    });
    socket.addEventListener("close", () => console.log("socket closed"));
    socket.addEventListener("error", (e) => console.error("socket error:", e));

    // wait until the socket is actually open before returning
    await new Promise((resolve) => socket.addEventListener("open", resolve, { once: true }));
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) {
        return; // nothing to send
    }
    addLine("You: " + text);
    messageInput.value = "";
    await ensureConnection();
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(text);
    }
}

sendBtn.addEventListener("click", sendMessage);
