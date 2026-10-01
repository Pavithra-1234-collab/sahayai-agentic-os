import { useState, useRef, useEffect } from "react";
import { Mic, MicOff, Loader2, Volume2 } from "lucide-react";

/**
 * VoiceButton — records audio, sends to /api/voice/chat, plays back the response.
 *
 * Props:
 *   onTranscript(transcript)   — called with the transcribed text to show in chat
 *   onResponse({ response_native, response_english, language_name, audio_base64 })
 *   history                    — conversation history array for context
 *   className                  — optional extra classes on the button
 *   size                       — "sm" | "md" (default "md")
 */
export default function VoiceButton({ onTranscript, onResponse, history = [], className = "", size = "md" }) {
  const [state, setState] = useState("idle"); // idle | recording | processing | playing
  const [seconds, setSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioRef = useRef(null);

  useEffect(() => () => {
    clearInterval(timerRef.current);
    audioRef.current?.pause();
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Prefer webm; fall back to whatever the browser supports
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/mp4";

      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        clearInterval(timerRef.current);
        setSeconds(0);
        await sendAudio(new Blob(chunksRef.current, { type: mimeType }), mimeType);
      };

      recorder.start(250); // collect data every 250ms
      mediaRecorderRef.current = recorder;
      setState("recording");
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch (err) {
      if (err.name === "NotAllowedError") {
        alert("Microphone access denied. Please allow microphone permission and try again.");
      } else {
        alert(`Could not start recording: ${err.message}`);
      }
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setState("processing");
  };

  const sendAudio = async (blob, mimeType) => {
    try {
      const ext = mimeType.includes("mp4") ? "m4a" : "webm";
      const formData = new FormData();
      formData.append("audio", blob, `recording.${ext}`);
      formData.append("history", JSON.stringify(history));

      const res = await fetch("/api/voice/chat", { method: "POST", body: formData });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }

      const data = await res.json();

      // Notify parent components
      onTranscript?.(data.transcript);
      onResponse?.(data);

      // Auto-play the audio response
      if (data.audio_base64) {
        setState("playing");
        const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
        audioRef.current = audio;
        audio.onended = () => setState("idle");
        audio.onerror = () => setState("idle");
        audio.play().catch(() => setState("idle"));
      } else {
        setState("idle");
      }
    } catch (err) {
      alert(`Voice error: ${err.message}`);
      setState("idle");
    }
  };

  const handleClick = () => {
    if (state === "idle") startRecording();
    else if (state === "recording") stopRecording();
    else if (state === "playing") {
      audioRef.current?.pause();
      setState("idle");
    }
  };

  const fmtTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  const sizeClass = size === "sm"
    ? "w-8 h-8"
    : "w-10 h-10";

  const iconSize = size === "sm" ? 14 : 16;

  return (
    <div className="flex items-center gap-2">
      {state === "recording" && (
        <span className="text-xs text-red-400 font-mono tabular-nums">{fmtTime(seconds)}</span>
      )}
      <button
        onClick={handleClick}
        title={state === "idle" ? "Start voice input" : state === "recording" ? "Stop recording" : state === "playing" ? "Stop playback" : "Processing…"}
        className={`${sizeClass} rounded-full flex items-center justify-center shrink-0 transition-all ${
          state === "recording"
            ? "bg-red-500 hover:bg-red-600 animate-pulse shadow-lg shadow-red-500/30"
            : state === "processing"
            ? "bg-zinc-700 cursor-not-allowed"
            : state === "playing"
            ? "bg-[#25D366] hover:bg-[#22c55e] shadow-lg shadow-[#25D366]/30"
            : "bg-[#27272a] hover:bg-[#3f3f46] hover:text-white"
        } ${className}`}
      >
        {state === "idle" && <Mic size={iconSize} className="text-zinc-300" />}
        {state === "recording" && <MicOff size={iconSize} className="text-white" />}
        {state === "processing" && <Loader2 size={iconSize} className="text-zinc-400 animate-spin" />}
        {state === "playing" && <Volume2 size={iconSize} className="text-white" />}
      </button>
    </div>
  );
}
