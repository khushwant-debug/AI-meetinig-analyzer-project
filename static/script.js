// ======================================================
// AI Meeting Analyzer - Optimized JS (Phase 1 Polish)
// ======================================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("JS Loaded ✅");


    // ======================================================
    // ELEMENTS
    // ======================================================
    const loader = document.getElementById("loader");

    const analyzeBtn = document.getElementById("analyze-btn");
    const clearBtn = document.getElementById("clear-btn");

    const copyBtn = document.getElementById("copy-summary");
    const downloadBtn = document.getElementById("download-summary");
    const pdfBtn = document.getElementById("download-pdf");

    const toggleBtn = document.getElementById("theme-toggle");

    const notesInput = document.getElementById("meeting-notes");
    const titleInput = document.getElementById("meeting-title");
    const typeInput = document.getElementById("meeting-type");


    // ======================================================
    // DARK MODE (saved in localStorage)
    // ======================================================
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark");
    }

    toggleBtn?.addEventListener("click", () => {
        document.body.classList.toggle("dark");

        localStorage.setItem(
            "theme",
            document.body.classList.contains("dark") ? "dark" : "light"
        );
    });



    // ======================================================
    // HELPERS
    // ======================================================
    function showLoader() {
        loader.classList.remove("hidden");
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "Analyzing...";
    }

    function hideLoader() {
        loader.classList.add("hidden");
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze Meeting";
    }

    function scrollToResults() {
        document.querySelector(".output-section")
            ?.scrollIntoView({ behavior: "smooth" });
    }



    // ======================================================
    // ANALYZE
    // ======================================================
    analyzeBtn?.addEventListener("click", async () => {

        const notes = notesInput.value.trim();
        const title = titleInput.value.trim();
        const type = typeInput.value;

        if (!notes) {
            alert("Please paste some meeting notes first!");
            return;
        }

        showLoader();

        try {

            const res = await fetch("/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    meeting_text: notes,
                    meeting_title: title || "Untitled Meeting",
                    meeting_type: type
                })
            });

            const data = await res.json();


            // ================= Fill UI =================
            document.getElementById("meeting-title-output").innerText = data.meeting_title;
            document.getElementById("summary-text").innerText = data.summary;

            document.getElementById("key-points-list").innerHTML =
                data.key_points.map(p => `<li>${p}</li>`).join("");

            document.getElementById("decisions-list").innerHTML =
                data.decisions.map(d => `<li>${d}</li>`).join("");

            document.getElementById("action-items-list").innerHTML =
                data.action_items.map(a => `<li>${a}</li>`).join("");

            document.getElementById("confidence-score").innerText =
                `Confidence: ${data.confidence}%`;


            // Show cards animation
            document.querySelectorAll(".card").forEach(c => {
                c.classList.add("show");
            });

            scrollToResults();

        } catch (err) {
            console.error(err);
            alert("Backend error. Check Flask server.");
        }

        hideLoader();
    });

// ======================================================
// 🎤 LIVE SPEECH TO TEXT (Web Speech API)
// ======================================================

const startRecordBtn = document.getElementById("start-record");
const stopRecordBtn = document.getElementById("stop-record");
const notesBox = document.getElementById("meeting-notes");

let recognition;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();

    recognition.continuous = true;        // keep listening
    recognition.interimResults = true;    // show live typing
    recognition.lang = "hi-IN";           // change to hi-IN for Hindi

    recognition.onresult = (event) => {

        let transcript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }

        notesBox.value += " " + transcript;
    };

    recognition.onerror = () => {
        console.log("Speech recognition error");
    };
}


// Start
startRecordBtn?.addEventListener("click", () => {
    recognition?.start();
    startRecordBtn.textContent = "Listening...";
});


// Stop
stopRecordBtn?.addEventListener("click", () => {
    recognition?.stop();
    startRecordBtn.textContent = "🎤 Start Live";
});


// ============================
// WHISPER TRANSCRIPTION
// ============================

const audioInput = document.getElementById("audio-upload");
const transcribeBtn = document.getElementById("transcribe-btn");

transcribeBtn?.addEventListener("click", async () => {

    if (!audioInput.files.length) {
        alert("Upload audio first");
        return;
    }

    const formData = new FormData();
    formData.append("audio", audioInput.files[0]);

    transcribeBtn.textContent = "Transcribing...";

    const res = await fetch("/transcribe", {
        method: "POST",
        body: formData
    });

    const data = await res.json();

   
    // textarea me text daal do
    document.getElementById("meeting-notes").value = data.text;

    transcribeBtn.textContent = "Transcribe Audio";
});



    // ======================================================
    // CLEAR
    // ======================================================
    clearBtn?.addEventListener("click", () => {

        notesInput.value = "";
        titleInput.value = "";

        document.getElementById("summary-text").innerText = "AI output will appear here";
        document.getElementById("key-points-list").innerHTML = "";
        document.getElementById("decisions-list").innerHTML = "";
        document.getElementById("action-items-list").innerHTML = "";
        document.getElementById("confidence-score").innerText = "";

        document.getElementById("meeting-title-output").innerText = "";

        document.querySelectorAll(".card").forEach(c => {
            c.classList.remove("show");
        });

        notesInput.focus();
    });



    // ======================================================
    // COPY SUMMARY
    // ======================================================
    copyBtn?.addEventListener("click", async () => {

        const text = document.getElementById("summary-text").innerText;

        await navigator.clipboard.writeText(text);

        // better UX than alert
        copyBtn.textContent = "Copied ✓";

        setTimeout(() => {
            copyBtn.textContent = "Copy";
        }, 1500);
    });



    // ======================================================
    // DOWNLOAD TXT
    // ======================================================
    downloadBtn?.addEventListener("click", () => {

        const text = document.getElementById("summary-text").innerText;

        const blob = new Blob([text], { type: "text/plain" });

        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "meeting-summary.txt";
        link.click();
    });



    // ======================================================
    // DOWNLOAD PDF
    // ======================================================
    pdfBtn?.addEventListener("click", async () => {

        try {

            const payload = {
                summary: document.getElementById("summary-text").innerText
            };

            const res = await fetch("/export-pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error();

            const blob = await res.blob();

            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = "meeting_report.pdf";
            document.body.appendChild(a);
            a.click();
            a.remove();

        } catch {
            alert("PDF download failed");
        }
    });

});

// ======================================================
// 💬 CHATBOT FEATURE
// ======================================================

const chatBox = document.getElementById("chat-box");
const chatInput = document.getElementById("chat-question");
const sendBtn = document.getElementById("send-chat");

function addMessage(text, type) {

    const msg = document.createElement("div");
    msg.className = `msg ${type}-msg`;
    msg.textContent = text;

    chatBox.appendChild(msg);

    chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn?.addEventListener("click", async () => {

    const question = chatInput.value.trim();
    const notes = document.getElementById("meeting-notes").value.trim();

    if (!question) return;

    addMessage(question, "user");
    chatInput.value = "";

    addMessage("Thinking...", "ai");

    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            question: question,
            notes: notes
        })
    });

    const data = await res.json();

    chatBox.lastChild.remove(); // remove thinking

    addMessage(data.answer, "ai");
});

// enter key support
chatInput?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendBtn.click();
});

