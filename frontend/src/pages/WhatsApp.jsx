import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Phone, Video, MoreVertical, ArrowLeft, Check, Mic, MicOff, Play, Pause, Download, FileText } from "lucide-react";

const SUGGESTIONS = [
  "Kitna stock bacha hai?",
  "Show me this week's sales",
  "Create a listing for wireless earbuds",
  "Which products need reorder?",
  "Summarise my customer reviews",
  "Price advice for Bluetooth speaker",
];

const ONDC_ORDER = {
  role: "assistant",
  isOndcAlert: true,
  content: "🛍️ *New Order via PhonePe (ONDC)*\n\nProduct: Bluetooth Speaker SWP-001\nQty: 2 × ₹1,095\nTotal: *₹2,190*\nBuyer: Rahul S., Indore (MP)\nOrder ID: ONDC-PPE-20260321-8842\n\n_Fulfilled via ONDC · Buyer on PhonePe_",
};

// ── Voice note bubble (WhatsApp style) ────────────────────────────────────
function VoiceNoteBubble({ isUser, audioB64, duration, transcript, nativeText, languageName, time }) {
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef(null);
  const intervalRef = useRef(null);

  const togglePlay = () => {
    if (!audioB64) return;
    if (playing) {
      audioRef.current?.pause();
      clearInterval(intervalRef.current);
      setPlaying(false);
    } else {
      const audio = new Audio(`data:audio/mp3;base64,${audioB64}`);
      audioRef.current = audio;
      audio.onended = () => { setPlaying(false); setProgress(0); clearInterval(intervalRef.current); };
      audio.play();
      setPlaying(true);
      intervalRef.current = setInterval(() => {
        if (audio.duration) setProgress((audio.currentTime / audio.duration) * 100);
      }, 100);
    }
  };

  return (
    <div className={`max-w-[70%] rounded-2xl shadow-sm overflow-hidden ${isUser ? "bg-[#005C4B] rounded-br-sm" : "bg-[#202C33] rounded-bl-sm"}`}>
      {/* Voice note row */}
      <div className="flex items-center gap-2.5 px-3 py-2.5">
        <button onClick={togglePlay}
          className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${isUser ? "bg-[#25D366]/40 hover:bg-[#25D366]/60" : "bg-[#25D366]/30 hover:bg-[#25D366]/50"} transition-colors`}>
          {playing ? <Pause size={13} className="text-white" /> : <Play size={13} className="text-white ml-0.5" />}
        </button>
        {/* Waveform bars */}
        <div className="flex items-center gap-0.5 flex-1">
          {[...Array(20)].map((_, i) => {
            const h = [3, 5, 8, 12, 9, 6, 14, 10, 7, 11, 8, 13, 6, 9, 11, 7, 5, 10, 8, 4][i];
            const filled = progress > (i / 20) * 100;
            return <div key={i} className={`rounded-full w-1 transition-colors ${filled ? "bg-[#25D366]" : "bg-[#8696A0]"}`} style={{ height: h }} />;
          })}
        </div>
        <div className="w-7 h-7 rounded-full bg-[#8696A0]/30 flex items-center justify-center shrink-0">
          <Mic size={11} className="text-[#8696A0]" />
        </div>
      </div>
      {/* Transcript / native text */}
      {(transcript || nativeText) && (
        <div className="px-3 pb-2.5 border-t border-white/5">
          {nativeText && nativeText !== transcript && (
            <p className="text-[12px] text-[#E9EDEF] leading-snug mt-2">{nativeText}</p>
          )}
          {transcript && (
            <p className="text-[10px] text-[#8696A0] mt-1 leading-snug italic">{transcript}</p>
          )}
          {languageName && <span className="text-[9px] text-[#25D366] mt-0.5 block">{languageName}</span>}
        </div>
      )}
      <div className={`flex items-center gap-1 px-3 pb-1.5 ${isUser ? "justify-end" : "justify-start"}`}>
        <span className="text-[10px] text-[#8696A0]">{time}</span>
        {isUser && <Check size={11} className="text-[#53BDEB]" />}
      </div>
    </div>
  );
}

// ── Regular text bubble ───────────────────────────────────────────────────
function WaMessage({ role, content, time, isVoice, audioB64, nativeContent, languageName, transcript }) {
  const isUser = role === "user";

  if (isVoice) {
    return (
      <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-1.5`}>
        <VoiceNoteBubble
          isUser={isUser}
          audioB64={audioB64}
          transcript={isUser ? content : transcript}
          nativeText={isUser ? null : nativeContent}
          languageName={isUser ? null : languageName}
          time={time}
        />
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-1.5`}>
      <div className={`max-w-[72%] px-3 py-2 rounded-2xl text-sm leading-relaxed shadow-sm ${
        isUser ? "bg-[#005C4B] text-[#E9EDEF] rounded-br-sm" : "bg-[#202C33] text-[#E9EDEF] rounded-bl-sm"
      }`}>
        <div className="whitespace-pre-wrap text-[13px]">{content}</div>
        <div className={`flex items-center gap-1 mt-0.5 ${isUser ? "justify-end" : "justify-start"}`}>
          <span className="text-[10px] text-[#8696A0]">{time}</span>
          {isUser && <Check size={12} className="text-[#53BDEB]" />}
        </div>
      </div>
    </div>
  );
}

// ── Voice recorder for input bar ──────────────────────────────────────────
function WaVoiceRecorder({ onTranscript, onResponse, history, disabled }) {
  const [state, setState] = useState("idle"); // idle | recording | processing
  const [seconds, setSeconds] = useState(0);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => () => clearInterval(timerRef.current), []);

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true }).catch((e) => {
      alert("Microphone access denied. Please allow mic permission."); throw e;
    });
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : "audio/webm";
    const recorder = new MediaRecorder(stream, { mimeType });
    chunksRef.current = [];
    recorder.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data);
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      clearInterval(timerRef.current);
      setSeconds(0);
      setState("processing");
      const blob = new Blob(chunksRef.current, { type: mimeType });
      const ext = mimeType.includes("mp4") ? "m4a" : "webm";
      const formData = new FormData();
      formData.append("audio", blob, `voice.${ext}`);
      formData.append("history", JSON.stringify(history));

      try {
        const res = await fetch("/api/voice/chat", { method: "POST", body: formData });
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || "Server error"); }
        const data = await res.json();
        onTranscript?.(data.transcript);
        onResponse?.(data);
      } catch (e) {
        alert(`Voice error: ${e.message}`);
      } finally {
        setState("idle");
      }
    };
    recorder.start(250);
    recorderRef.current = recorder;
    setState("recording");
    timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
  };

  const stop = () => { recorderRef.current?.stop(); };
  const fmt = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  if (state === "recording") return (
    <div className="flex items-center gap-2 flex-1">
      <div className="flex-1 flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-full px-4 py-2">
        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        <span className="text-xs text-red-400 font-mono">{fmt(seconds)}</span>
        <div className="flex gap-0.5 items-center flex-1">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-red-400 rounded-full w-0.5 animate-pulse" style={{ height: Math.random() * 10 + 4, animationDelay: `${i * 100}ms` }} />
          ))}
        </div>
        <span className="text-[10px] text-red-400">Slide to cancel</span>
      </div>
      <button onClick={stop}
        className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center hover:bg-red-600 transition-colors">
        <MicOff size={16} className="text-white" />
      </button>
    </div>
  );

  if (state === "processing") return (
    <div className="flex-1 flex items-center justify-center gap-2 text-xs text-zinc-500">
      <Loader2 size={13} className="animate-spin text-[#25D366]" />
      Processing voice…
    </div>
  );

  return (
    <button onClick={start} disabled={disabled}
      className="w-9 h-9 rounded-full bg-[#00A884] flex items-center justify-center hover:bg-[#25D366] transition-colors disabled:opacity-40">
      <Mic size={15} className="text-white" />
    </button>
  );
}

// ── Document attachment bubble (WhatsApp-style) ───────────────────────────
function DocBubble({ filename, reportId, time }) {
  const [downloading, setDownloading] = useState(false);

  const download = async () => {
    setDownloading(true);
    try {
      const res = await fetch(`/api/report/temp/${reportId}`);
      const html = await res.text();
      const blob = new Blob([html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex justify-start mb-1.5">
      <div className="max-w-[72%] bg-[#202C33] rounded-2xl rounded-bl-sm overflow-hidden shadow-sm">
        <button onClick={download} disabled={downloading}
          className="flex items-center gap-3 px-3 py-3 w-full hover:bg-white/5 transition-colors text-left">
          <div className="w-10 h-10 rounded-xl bg-[#25D366]/20 flex items-center justify-center shrink-0">
            {downloading
              ? <Loader2 size={18} className="text-[#25D366] animate-spin" />
              : <FileText size={18} className="text-[#25D366]" />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-medium text-[#E9EDEF] truncate">{filename}</div>
            <div className="text-[11px] text-[#8696A0]">HTML Report · Tap to download</div>
          </div>
          <Download size={14} className="text-[#25D366] shrink-0" />
        </button>
        <div className="flex items-center gap-1 px-3 pb-2">
          <span className="text-[10px] text-[#8696A0]">{time}</span>
          <Check size={12} className="text-[#53BDEB]" />
          <Check size={12} className="text-[#53BDEB] -ml-2" />
        </div>
      </div>
    </div>
  );
}


// ── Main WhatsApp Page ────────────────────────────────────────────────────
export default function WhatsApp() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const now = () => new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

  const sendText = async (text) => {
    if (!text.trim() || loading) return;
    const time = now();
    setMessages((m) => [...m, { role: "user", content: text, time }]);
    setHistory((h) => [...h, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history }),
      });
      const rawText = await res.text();
      let data;
      try { data = JSON.parse(rawText); } catch { data = { response: "Sorry, the server returned an unexpected error. Please try again." }; }
      const t = now();
      setMessages((m) => {
        const next = [...m, { role: "assistant", content: data.response, time: t }];
        // If the AI generated a report, append a document bubble
        if (data.report) {
          next.push({ role: "assistant", isDoc: true, reportId: data.report.report_id, filename: data.report.filename, time: t });
        }
        return next;
      });
      setHistory((h) => [...h, { role: "assistant", content: data.response }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Connection error.", time: now() }]);
    } finally { setLoading(false); }
  };

  const handleVoiceTranscript = (transcript) => {
    setMessages((m) => [...m, { role: "user", content: transcript, time: now(), isVoice: true }]);
    setHistory((h) => [...h, { role: "user", content: transcript }]);
  };

  const handleVoiceResponse = (data) => {
    setMessages((m) => [...m, {
      role: "assistant",
      content: data.response_english,
      time: now(),
      isVoice: true,
      audioB64: data.audio_base64,
      nativeContent: data.response_native,
      languageName: data.language_name,
      transcript: data.response_english,
    }]);
    setHistory((h) => [...h, { role: "assistant", content: data.response_english }]);
  };

  const handleKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendText(input); } };

  return (
    <div className="p-6 h-screen flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">WhatsApp Interface</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Real phone UI — voice notes in any Indian language</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => setMessages((m) => [...m, { ...ONDC_ORDER, time: now() }])}
            className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 text-xs text-blue-400 rounded-full hover:bg-blue-500/20 transition-colors font-medium">
            📦 Simulate ONDC Order (PhonePe)
          </button>
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => sendText(s)}
              className="px-3 py-1.5 bg-[#18181b] border border-[#27272a] text-xs text-zinc-400 rounded-full hover:border-[#25D366]/40 hover:text-white transition-colors">
              {s.length > 30 ? s.slice(0, 30) + "…" : s}
            </button>
          ))}
        </div>
      </div>

      {/* Phone frame */}
      <div className="flex-1 flex justify-center">
        <div className="w-[390px] rounded-[44px] border-4 border-[#27272a] bg-black shadow-2xl shadow-black/70 overflow-hidden flex flex-col" style={{ height: 640 }}>
          {/* iOS status bar */}
          <div className="bg-[#0b141a] px-6 pt-3 pb-1 flex items-center justify-between shrink-0">
            <span className="text-[11px] text-white font-semibold">9:41</span>
            <div className="w-24 h-5 bg-black rounded-full" />
            <div className="flex gap-1 items-center">
              {[3, 4, 5].map(h => <div key={h} className="w-0.5 bg-white rounded-sm" style={{ height: h * 2 }} />)}
              <div className="w-4 h-2 border border-white rounded-sm ml-1 relative">
                <div className="absolute inset-0.5 bg-white rounded-sm" style={{ width: "70%" }} />
              </div>
            </div>
          </div>

          {/* WA Header */}
          <div className="bg-[#202C33] px-3 py-2.5 flex items-center gap-2.5 shrink-0">
            <ArrowLeft size={18} className="text-[#aebac1]" />
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#25D366] to-[#128C7E] flex items-center justify-center text-lg shrink-0">🤖</div>
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-semibold text-[#E9EDEF]">AI Business Manager</div>
              <div className="text-[11px] text-[#25D366]">online</div>
            </div>
            <Video size={19} className="text-[#aebac1]" />
            <Phone size={18} className="text-[#aebac1] ml-1" />
            <MoreVertical size={18} className="text-[#aebac1] ml-1" />
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-3 py-3 wa-pattern">
            {messages.length === 0 && (
              <div className="flex justify-center mt-3">
                <div className="bg-[#182229] px-4 py-2 rounded-xl text-center">
                  <p className="text-[11px] text-[#8696A0]">🔒 End-to-end encrypted</p>
                  <p className="text-[10px] text-[#8696A0] mt-1">Tap the 🎤 mic to send a voice note in Hindi, Tamil, or any Indian language</p>
                </div>
              </div>
            )}
            {messages.length > 0 && (
              <div className="flex justify-center mb-3">
                <span className="bg-[#182229] text-[#8696A0] text-[10px] px-3 py-1 rounded-full">Today</span>
              </div>
            )}
            {messages.map((m, i) =>
              m.isDoc
                ? <DocBubble key={i} filename={m.filename} reportId={m.reportId} time={m.time} />
                : m.isOndcAlert
                ? (
                  <div key={i} className="flex justify-start mb-1.5">
                    <div className="max-w-[80%] bg-[#1a2e22] border border-[#25D366]/30 rounded-2xl rounded-bl-sm px-3 py-2.5 shadow-sm">
                      <div className="text-[11px] text-[#25D366] font-bold mb-1 flex items-center gap-1">🟢 ONDC · via PhonePe</div>
                      <pre className="text-[12px] text-[#E9EDEF] whitespace-pre-wrap font-sans leading-relaxed">{m.content}</pre>
                      <div className="flex items-center gap-1 mt-1">
                        <span className="text-[10px] text-[#8696A0]">{m.time}</span>
                      </div>
                    </div>
                  </div>
                )
                : <WaMessage key={i} {...m} />
            )}
            {loading && (
              <div className="flex justify-start mb-1.5">
                <div className="bg-[#202C33] px-4 py-2.5 rounded-2xl rounded-bl-sm">
                  <div className="flex gap-1 items-center">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="w-1.5 h-1.5 bg-[#8696A0] rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input bar */}
          <div className="bg-[#202C33] px-2 py-2 flex items-center gap-2 shrink-0">
            {voiceMode ? (
              <WaVoiceRecorder
                onTranscript={handleVoiceTranscript}
                onResponse={handleVoiceResponse}
                history={history}
                disabled={loading}
              />
            ) : (
              <>
                <div className="flex-1 bg-[#2a3942] rounded-full px-4 py-2 flex items-center gap-2 min-w-0">
                  <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
                    placeholder="Message" className="flex-1 bg-transparent text-[13px] text-[#E9EDEF] placeholder-[#8696A0] outline-none min-w-0" />
                </div>
                {input.trim() ? (
                  <button onClick={() => sendText(input)}
                    className="w-9 h-9 rounded-full bg-[#00A884] flex items-center justify-center hover:bg-[#25D366] transition-colors shrink-0">
                    <Send size={14} className="text-white ml-0.5" />
                  </button>
                ) : (
                  <button onClick={() => setVoiceMode(true)}
                    className="w-9 h-9 rounded-full bg-[#00A884] flex items-center justify-center hover:bg-[#25D366] transition-colors shrink-0">
                    <Mic size={15} className="text-white" />
                  </button>
                )}
              </>
            )}
            {voiceMode && (
              <button onClick={() => setVoiceMode(false)} className="text-[10px] text-zinc-500 hover:text-zinc-300 ml-1 shrink-0">✕</button>
            )}
          </div>
        </div>
      </div>

      {messages.length > 0 && (
        <div className="flex justify-center">
          <button onClick={() => { setMessages([]); setHistory([]); }} className="text-xs text-zinc-600 hover:text-zinc-400 transition-colors">Clear conversation</button>
        </div>
      )}
    </div>
  );
}
