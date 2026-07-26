import React, { useState, useEffect, useRef } from 'react';
import { X, Mic, PhoneOff, Bot, User, Wrench, Sparkles, Volume2 } from 'lucide-react';

export default function VoiceTestModal({ isOpen, onClose, onCallCompleted }) {
  const [inCall, setInCall] = useState(false);
  const [status, setStatus] = useState('Disconnected');
  const [messages, setMessages] = useState([]);
  const [audioVolume, setAudioVolume] = useState(0);

  const wsRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const speechRecRef = useRef(null);
  const currentAudioSourceRef = useRef(null);
  const transcriptEndRef = useRef(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  if (!isOpen) return null;

  const startVoiceCall = async () => {
    try {
      setInCall(true);
      setStatus('Requesting Microphone...');
      setMessages([]);

      // 1. Microphone capture & visualizer
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateVolume = () => {
        if (!mediaStreamRef.current) return;
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        const avg = sum / dataArray.length / 255;
        setAudioVolume(avg);
        requestAnimationFrame(updateVolume);
      };
      updateVolume();

      // 2. WebSocket Connection
      let wsUrl = '';
      if (import.meta.env.VITE_WS_URL) {
        wsUrl = `${import.meta.env.VITE_WS_URL}/ws/browser-audio`;
      } else if (import.meta.env.VITE_API_URL) {
        const cleanHost = import.meta.env.VITE_API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
        wsUrl = `${cleanHost}/ws/browser-audio`;
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${protocol}//${window.location.host}/ws/browser-audio`;
      }
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('Connected with Riya');
        initSpeechRecognition();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'agent_speech') {
            setMessages((prev) => [
              ...prev,
              {
                role: 'assistant',
                text: data.text,
                tools: data.tools_called,
              },
            ]);

            if (data.audio) {
              playAgentAudio(data.audio);
            } else {
              speakLocally(data.text);
            }

            if (data.call_ended) {
              setTimeout(() => endVoiceCall(), 4000);
            }
          } else if (data.type === 'call_summary') {
            setStatus(`Call Ended: ${data.outcome}`);
            if (onCallCompleted) onCallCompleted();
          }
        } catch (e) {
          console.error(e);
        }
      };

      ws.onclose = () => {
        setStatus('Call Disconnected');
        setInCall(false);
      };
    } catch (err) {
      console.error(err);
      setStatus('Mic permission denied / Error');
      setInCall(false);
    }
  };

  const initSpeechRecognition = () => {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;

    const sr = new SpeechRec();
    sr.continuous = true;
    sr.interimResults = false;
    sr.lang = 'en-US';

    sr.onresult = (event) => {
      const last = event.results.length - 1;
      const text = event.results[last][0].transcript.trim();
      if (text) {
        // Interruption handling: stop agent audio
        if (currentAudioSourceRef.current) {
          try { currentAudioSourceRef.current.stop(); } catch(e){}
        }
        if (window.speechSynthesis) {
          window.speechSynthesis.cancel();
        }

        setMessages((prev) => [...prev, { role: 'user', text }]);
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'user_speech', text }));
        }
      }
    };

    sr.onerror = (e) => {
      if (e.error !== 'no-speech') console.error('Speech recognition error:', e);
    };

    sr.onend = () => {
      if (speechRecRef.current && inCall) {
        try { speechRecRef.current.start(); } catch (e) {}
      }
    };

    speechRecRef.current = sr;
    sr.start();
  };

  const playAgentAudio = (base64) => {
    try {
      const binary = atob(base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

      audioCtxRef.current?.decodeAudioData(bytes.buffer, (buffer) => {
        if (currentAudioSourceRef.current) {
          try { currentAudioSourceRef.current.stop(); } catch (e) {}
        }
        const src = audioCtxRef.current.createBufferSource();
        src.buffer = buffer;
        src.connect(audioCtxRef.current.destination);
        currentAudioSourceRef.current = src;
        src.start(0);
      });
    } catch (e) {
      console.error('Audio decode error:', e);
    }
  };

  const speakLocally = (text) => {
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.05;
      window.speechSynthesis.speak(u);
    }
  };

  const endVoiceCall = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end_call' }));
      setTimeout(() => wsRef.current?.close(), 300);
    }
    cleanup();
    setInCall(false);
  };

  const cleanup = () => {
    if (speechRecRef.current) {
      try { speechRecRef.current.stop(); } catch (e) {}
      speechRecRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    if (currentAudioSourceRef.current) {
      try { currentAudioSourceRef.current.stop(); } catch (e) {}
      currentAudioSourceRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setAudioVolume(0);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-2xl bg-[#0c1322] border border-indigo-500/30 rounded-3xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/70">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-emerald-500 flex items-center justify-center text-white">
              <Mic className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Live Microphone Voice Session</h3>
              <p className="text-xs text-slate-400">Persona: Riya (Placeholder Realty)</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700">
              <span className={`w-2 h-2 rounded-full ${inCall ? 'bg-emerald-500 animate-pulse' : 'bg-slate-500'}`}></span>
              <span className="text-slate-300">{status}</span>
            </span>
            <button
              onClick={() => { endVoiceCall(); onClose(); }}
              className="p-1.5 text-slate-400 hover:text-white rounded-xl bg-slate-800 hover:bg-slate-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Audio Visualizer Bar */}
        <div className="px-6 py-3 bg-slate-950/40 border-b border-slate-800/80 flex items-center justify-center gap-1.5 h-12">
          {Array.from({ length: 24 }).map((_, i) => {
            const h = inCall ? Math.max(4, Math.min(32, audioVolume * 40 * Math.sin((i / 24) * Math.PI) + 4)) : 4;
            return (
              <div
                key={i}
                className="w-1.5 bg-indigo-500 rounded-full transition-all duration-75"
                style={{ height: `${h}px` }}
              />
            );
          })}
        </div>

        {/* Transcript Box */}
        <div className="flex-1 p-6 overflow-y-auto max-h-[380px] space-y-3">
          {messages.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              Press "Start Voice Call" below to test the agent with your microphone.
            </div>
          ) : (
            messages.map((m, idx) => (
              <div key={idx} className="space-y-1.5">
                <div
                  className={`p-3.5 rounded-2xl text-xs leading-relaxed max-w-[85%] ${
                    m.role === 'assistant'
                      ? 'bg-indigo-950/40 border border-indigo-500/30 text-indigo-100 mr-auto'
                      : 'bg-emerald-950/40 border border-emerald-500/30 text-emerald-100 ml-auto'
                  }`}
                >
                  <div className="font-bold mb-1 opacity-70 flex items-center gap-1">
                    {m.role === 'assistant' ? <Bot className="w-3.5 h-3.5" /> : <User className="w-3.5 h-3.5" />}
                    <span>{m.role === 'assistant' ? 'Riya' : 'You'}</span>
                  </div>
                  <p>{m.text}</p>
                </div>

                {m.tools && m.tools.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 justify-center py-1">
                    {m.tools.map((t, ti) => (
                      <span
                        key={ti}
                        className="px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px] font-medium flex items-center gap-1"
                      >
                        <Wrench className="w-3 h-3" />
                        <span>{t.name}: {Array.isArray(t.result) ? `${t.result.length} matches` : 'Executed'}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={transcriptEndRef} />
        </div>

        {/* Footer Controls */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-center gap-4">
          {!inCall ? (
            <button
              onClick={startVoiceCall}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-emerald-600/30 transition-all"
            >
              <Mic className="w-4 h-4" />
              <span>Start Voice Call</span>
            </button>
          ) : (
            <button
              onClick={endVoiceCall}
              className="flex items-center gap-2 px-6 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-rose-600/30 transition-all"
            >
              <PhoneOff className="w-4 h-4" />
              <span>End Call</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
