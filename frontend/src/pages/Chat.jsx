import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Mic, Volume2, Globe } from "lucide-react";
import VoiceButton from "../components/VoiceButton";

const SUGGESTIONS = [
  { icon: "📦", label: "Check Inventory", prompt: "Show me products with low stock" },
  { icon: "💰", label: "Pricing Advice", prompt: "Give me pricing advice for my products" },
  { icon: "📝", label: "Create Listing", prompt: "Create an Amazon listing for Bluetooth Speaker" },
  { icon: "📊", label: "Weekly Report", prompt: "Show me my sales report for the last 7 days" },
  { icon: "⭐", label: "Review Summary", prompt: "Summarise my recent customer reviews" },
  { icon: "📈", label: "Growth Insights", prompt: "How is my business performing this month?" },
];

function Bubble({ role, content, isVoice, nativeContent, languageName, audioB64 }) {
  const isUser = role === "user";
  const [showNative, setShowNative] = useState(true);
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef(null);

  const playAudio = () => {
    if (!audioB64) return;
    if (playing) { audioRef.current?.pause(); setPlaying(false); return; }
    const audio = new Audio(`data:audio/mp3;base64,${audioB64}`);
    audioRef.current = audio;
    audio.onended = () => setPlaying(false);
    audio.play();
    setPlaying(true);
  };

  const displayContent = isVoice && nativeContent && showNative ? nativeContent : content;

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-7 h-7 rounded-full shrink-0 flex items-center justify-center mt-0.5 ${isUser ? "bg-[#25D366]/20" : "bg-[#27272a]"}`}>
        {isUser
          ? (isVoice ? <Mic size={13} className="text-[#25D366]" /> : <User size={13} className="text-[#25D366]" />)
          : <Bot size={13} className="text-zinc-400" />}
      </div>
      <div className={`max-w-[78%] rounded-2xl text-sm leading-relaxed ${
        isUser
          ? "bg-[#25D366]/15 text-white rounded-tr-sm border border-[#25D366]/20"
          : "bg-[#18181b] text-zinc-200 rounded-tl-sm border border-[#27272a]"
      }`}>
        <div className="px-4 py-3 whitespace-pre-wrap">{displayContent}</div>

        {/* Voice response controls */}
        {!isUser && isVoice && (
          <div className="px-4 pb-3 flex items-center gap-2 border-t border-[#27272a] pt-2">
            {audioB64 && (
              <button onClick={playAudio}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs transition-colors ${playing ? "bg-[#25D366]/20 text-[#25D366]" : "bg-[#27272a] text-zinc-400 hover:text-white"}`}>
                <Volume2 size={11} />
                {playing ? "Playing…" : "Play audio"}
              </button>
            )}
            {nativeContent && nativeContent !== content && (
              <button onClick={() => setShowNative(!showNative)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-[#27272a] text-zinc-400 hover:text-white transition-colors">
                <Globe size={11} />
                {showNative ? "Show English" : `Show ${languageName || "Native"}`}
              </button>
            )}
            {languageName && (
              <span className="ml-auto text-[10px] text-zinc-600">{languageName}</span>
            )}
          </div>
        )}

        {/* User voice transcription label */}
        {isUser && isVoice && (
          <div className="px-4 pb-2 text-[10px] text-[#25D366]/60 flex items-center gap-1">
            <Mic size={9} />voice
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addMessages = (userMsg, assistantMsg) => {
    setMessages((m) => [...m, userMsg, assistantMsg]);
    setHistory((h) => [...h, { role: "user", content: userMsg.content }, { role: "assistant", content: assistantMsg.content }]);
  };

  const send = async (text) => {
    if (!text.trim() || loading) return;
    const userMsg = { role: "user", content: text };
    setMessages((m) => [...m, userMsg]);
    setHistory((h) => [...h, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history }),
      });
      const text2 = await res.text();
      let data;
      try { data = JSON.parse(text2); } catch { data = { response: "Sorry, the server returned an unexpected error. Please try again." }; }
      const assistantMsg = { role: "assistant", content: data.response || "Sorry, something went wrong." };
      setMessages((m) => [...m, assistantMsg]);
      setHistory((h) => [...h, { role: "assistant", content: data.response }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceTranscript = (transcript) => {
    // Show the transcribed text as user bubble immediately
    setMessages((m) => [...m, { role: "user", content: transcript, isVoice: true }]);
    setHistory((h) => [...h, { role: "user", content: transcript }]);
    setLoading(true);
  };

  const handleVoiceResponse = (data) => {
    const assistantMsg = {
      role: "assistant",
      content: data.response_english,
      isVoice: true,
      nativeContent: data.response_native,
      languageName: data.language_name,
      audioB64: data.audio_base64,
    };
    setMessages((m) => [...m, assistantMsg]);
    setHistory((h) => [...h, { role: "assistant", content: data.response_english }]);
    setLoading(false);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#27272a] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#25D366]/10 flex items-center justify-center">
            <Bot size={15} className="text-[#25D366]" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">AI Business Manager</div>
            <div className="text-xs text-[#25D366]">● online</div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-zinc-600 bg-[#18181b] px-3 py-1.5 rounded-full border border-[#27272a]">
          <Mic size={10} />
          <span>Voice available — responds in your language</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center pb-20">
            <div className="w-14 h-14 rounded-2xl bg-[#25D366]/10 flex items-center justify-center mb-4">
              <Bot size={24} className="text-[#25D366]" />
            </div>
            <h2 className="text-lg font-semibold text-white mb-1">Namaste! 🙏</h2>
            <p className="text-zinc-500 text-sm max-w-sm mb-1">
              I'm your AI Business Manager for Amazon.in & Flipkart.
            </p>
            <p className="text-zinc-600 text-xs max-w-xs">
              Type your question or <span className="text-[#25D366]">tap the mic</span> to speak in Hindi, Tamil, Telugu, Kannada, or any Indian language — I'll reply in the same language.
            </p>
            <div className="grid grid-cols-3 gap-2 mt-6 w-full max-w-lg">
              {SUGGESTIONS.map((s) => (
                <button key={s.label} onClick={() => send(s.prompt)}
                  className="flex items-center gap-2 px-3 py-2.5 bg-[#18181b] border border-[#27272a] rounded-xl text-xs text-zinc-300 hover:border-[#25D366]/40 hover:text-white transition-all text-left">
                  <span>{s.icon}</span>
                  <span>{s.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => <Bubble key={i} {...m} />)}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-[#27272a] flex items-center justify-center">
              <Bot size={13} className="text-zinc-400" />
            </div>
            <div className="px-4 py-3 bg-[#18181b] border border-[#27272a] rounded-2xl rounded-tl-sm">
              <Loader2 size={14} className="text-[#25D366] animate-spin" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-[#27272a]">
        <div className="flex gap-2 items-end bg-[#18181b] border border-[#27272a] rounded-xl px-4 py-3 focus-within:border-[#25D366]/50 transition-colors">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Type or tap 🎤 to speak in any Indian language…"
            rows={1}
            className="flex-1 bg-transparent text-sm text-white placeholder-zinc-600 resize-none outline-none leading-relaxed"
            style={{ maxHeight: 120 }}
          />
          <VoiceButton
            onTranscript={handleVoiceTranscript}
            onResponse={handleVoiceResponse}
            history={history}
            size="sm"
          />
          <button
            onClick={() => send(input)}
            disabled={!input.trim() || loading}
            className="w-8 h-8 rounded-lg bg-[#25D366] disabled:opacity-30 flex items-center justify-center shrink-0 hover:bg-[#22c55e] transition-colors"
          >
            {loading ? <Loader2 size={13} className="animate-spin text-white" /> : <Send size={13} className="text-white" />}
          </button>
        </div>
        <p className="text-[10px] text-zinc-700 mt-2 text-center">Enter to send · Shift+Enter new line · 🎤 speak in Hindi/Tamil/Telugu/Kannada/etc.</p>
      </div>
    </div>
  );
}
