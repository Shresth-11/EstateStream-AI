import React, { useState, useEffect, useRef } from 'react';
import { X, Mic, PhoneOff, PhoneCall, Bot, User, Wrench, Sparkles } from 'lucide-react';

// Seconds of caller silence (after Riya finishes speaking) before a silence turn is sent.
// The backend checks in once, then ends the call on the second consecutive silence.
const SILENCE_TIMEOUT_MS = 9000;

// Words shared between what the mic heard and what Riya is saying. Used to drop
// speaker echo (laptop speakers -> mic) so Riya doesn't interrupt or answer herself.
function looksLikeEcho(heard, agentText) {
  if (!heard || !agentText) return false;
  const norm = (t) => t.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(Boolean);
  const h = norm(heard);
  if (h.length === 0) return false;
  const agentWords = new Set(norm(agentText));
  const overlap = h.filter((w) => agentWords.has(w)).length / h.length;
  return overlap >= 0.7;
}

export default function VoiceTestModal({ isOpen, onClose, onCallCompleted }) {
  const [inCall, setInCall] = useState(false);
  const [status, setStatus] = useState('Ready to connect');
  const [messages, setMessages] = useState([]);
  const [audioVolume, setAudioVolume] = useState(0);
  const [speechSupported] = useState(
    () => typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  );
  const [typedText, setTypedText] = useState('');

  const wsRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const speechRecRef = useRef(null);
  const currentAudioSourceRef = useRef(null);
  const transcriptEndRef = useRef(null);
  // Refs (not state) for values read inside long-lived callbacks. The old code read
  // `inCall` state inside recognition.onend, which was always the stale `false`, so
  // the mic never restarted after Chrome ended recognition on the first pause.
  const inCallRef = useRef(false);
  const agentSpeakingRef = useRef(false);
  const agentTextRef = useRef('');
  const silenceTimerRef = useRef(null);
  const rafRef = useRef(null);

  const clearSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  };

  const armSilenceTimer = () => {
    clearSilenceTimer();
    if (!inCallRef.current) return;
    silenceTimerRef.current = setTimeout(() => {
      if (inCallRef.current && !agentSpeakingRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'user_speech', text: '' }));
      }
    }, SILENCE_TIMEOUT_MS);
  };

  const stopAgentAudio = () => {
    if (currentAudioSourceRef.current) {
      try { currentAudioSourceRef.current.stop(); } catch (e) {}
      currentAudioSourceRef.current = null;
    }
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    agentSpeakingRef.current = false;
  };

  const onAgentFinishedSpeaking = () => {
    agentSpeakingRef.current = false;
    if (!inCallRef.current) {
      // Call already ended server-side; release audio once the goodbye has played.
      if (audioCtxRef.current) {
        audioCtxRef.current.close().catch(() => {});
        audioCtxRef.current = null;
      }
      return;
    }
    armSilenceTimer();
  };

  const cleanup = () => {
    inCallRef.current = false;
    clearSilenceTimer();
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (speechRecRef.current) {
      const sr = speechRecRef.current;
      speechRecRef.current = null;
      try { sr.stop(); } catch (e) {}
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    stopAgentAudio();
    if (audioCtxRef.current) {
      // Browsers cap live AudioContexts; leaking one per call eventually breaks audio.
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    setAudioVolume(0);
  };

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (e) {}
      }
      cleanup();
    };
  }, []);

  const sendUserText = (text) => {
    const clean = (text || '').trim();
    if (!clean) return;
    clearSilenceTimer();
    stopAgentAudio();
    setMessages((prev) => [...prev, { role: 'user', text: clean }]);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'user_speech', text: clean }));
    }
  };

  const buildWsUrl = () => {
    if (import.meta.env.VITE_WS_URL) return `${import.meta.env.VITE_WS_URL.replace(/\/$/, '')}/ws/browser-audio`;
    if (import.meta.env.VITE_API_URL) {
      const base = import.meta.env.VITE_API_URL.replace(/\/$/, '').replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
      return `${base}/ws/browser-audio`;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws/browser-audio`;
  };

  const startVoiceCall = async () => {
    if (!window.isSecureContext) {
      setStatus('Microphone needs HTTPS or localhost');
      return;
    }
    try {
      setInCall(true);
      inCallRef.current = true;
      setStatus('Connecting to Riya...');
      setMessages([]);

      // 1. Microphone capture & visualizer
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      mediaStreamRef.current = stream;

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioCtxRef.current = audioCtx;
      // Created after an await, so some browsers start it suspended -> no playback.
      if (audioCtx.state === 'suspended') await audioCtx.resume();
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
        setAudioVolume(sum / dataArray.length / 255);
        rafRef.current = requestAnimationFrame(updateVolume);
      };
      updateVolume();

      // 2. WebSocket Connection
      const ws = new WebSocket(buildWsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus(speechSupported ? 'Call Active • Speaking with Riya' : 'Call Active • Type below (voice input needs Chrome/Edge)');
        if (speechSupported) initSpeechRecognition();
      };

      ws.onerror = () => {
        setStatus('Could not reach the voice server');
      };

      ws.onmessage = (event) => {
        let data;
        try {
          data = JSON.parse(event.data);
        } catch (e) {
          console.error('Bad message from server', e);
          return;
        }
        if (data.type === 'agent_speech') {
          setMessages((prev) => [...prev, { role: 'assistant', text: data.text, tools: data.tools_called }]);
          agentTextRef.current = data.text || '';
          clearSilenceTimer();
          if (data.audio) {
            playAgentAudio(data.audio, data.text);
          } else {
            speakLocally(data.text);
          }
        } else if (data.type === 'call_summary') {
          setStatus(`Call Ended: ${data.outcome}`);
          if (onCallCompleted) onCallCompleted();
        }
      };

      ws.onclose = () => {
        // Server closes after call_ended (goodbye / escalation / silence). Let the
        // final sentence finish, then release the mic.
        inCallRef.current = false;
        clearSilenceTimer();
        setInCall(false);
        setStatus((s) => (s.startsWith('Call Ended') ? s : 'Call Ended'));
        if (speechRecRef.current) {
          const sr = speechRecRef.current;
          speechRecRef.current = null;
          try { sr.stop(); } catch (e) {}
        }
        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach((t) => t.stop());
          mediaStreamRef.current = null;
        }
        setAudioVolume(0);
      };
    } catch (err) {
      console.error(err);
      setStatus(err && err.name === 'NotAllowedError' ? 'Microphone permission denied' : 'Could not start the call');
      cleanup();
      setInCall(false);
    }
  };

  const initSpeechRecognition = () => {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;

    const sr = new SpeechRec();
    sr.continuous = true;
    sr.interimResults = true; // interim results enable real barge-in mid-sentence
    sr.lang = 'en-US';

    sr.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const text = result[0].transcript.trim();
        if (!text) continue;

        if (agentSpeakingRef.current && looksLikeEcho(text, agentTextRef.current)) {
          continue; // Riya's own voice coming back through the mic
        }
        if (!result.isFinal) {
          // Caller started talking over Riya: stop her immediately (barge-in).
          if (agentSpeakingRef.current && text.split(/\s+/).length >= 2) {
            stopAgentAudio();
            wsRef.current?.readyState === WebSocket.OPEN &&
              wsRef.current.send(JSON.stringify({ type: 'interruption' }));
          }
          clearSilenceTimer();
          continue;
        }
        sendUserText(text);
      }
    };

    sr.onerror = (e) => {
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
        setStatus('Speech recognition blocked. Type below instead.');
        speechRecRef.current = null;
      } else if (e.error !== 'no-speech' && e.error !== 'aborted') {
        console.error('Speech recognition error:', e.error);
      }
    };

    // Chrome ends "continuous" recognition after pauses; restart while the call is live.
    sr.onend = () => {
      if (speechRecRef.current === sr && inCallRef.current) {
        try { sr.start(); } catch (e) {}
      }
    };

    speechRecRef.current = sr;
    try { sr.start(); } catch (e) { console.error(e); }
  };

  const playAgentAudio = async (base64, text) => {
    const ctx = audioCtxRef.current;
    if (!ctx) return;
    try {
      const binary = atob(base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const buffer = await ctx.decodeAudioData(bytes.buffer);
      stopAgentAudio();
      const src = ctx.createBufferSource();
      src.buffer = buffer;
      src.connect(ctx.destination);
      src.onended = () => {
        if (currentAudioSourceRef.current === src) {
          currentAudioSourceRef.current = null;
          onAgentFinishedSpeaking();
        }
      };
      currentAudioSourceRef.current = src;
      agentSpeakingRef.current = true;
      src.start(0);
    } catch (e) {
      console.error('Audio decode error, falling back to browser voice:', e);
      speakLocally(text);
    }
  };

  const speakLocally = (text) => {
    if (!text || !('speechSynthesis' in window)) {
      onAgentFinishedSpeaking();
      return;
    }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.05;
    u.onend = onAgentFinishedSpeaking;
    u.onerror = onAgentFinishedSpeaking;
    agentSpeakingRef.current = true;
    window.speechSynthesis.speak(u);
  };

  const endVoiceCall = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Server persists the call and replies with call_summary, then closes the socket.
      wsRef.current.send(JSON.stringify({ type: 'end_call' }));
      const ws = wsRef.current;
      setTimeout(() => { try { ws.close(); } catch (e) {} }, 3000);
    }
    cleanup();
    setInCall(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#191512]/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-xl bg-[#ffffff] border border-[#ede5da] rounded-3xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#ede5da] flex items-center justify-between bg-[#fbf8f3]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#d94336] flex items-center justify-center text-white shadow-sm">
              <Mic className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-extrabold text-[#191512] text-sm">Live Voice Qualification Call</h3>
              <p className="text-xs text-[#78716c]">Speaking with Riya (EstateStream AI)</p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <span className="flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-[#f4ede4] border border-[#e8dfd2]">
              <span className={`w-2 h-2 rounded-full ${inCall ? 'bg-emerald-500 animate-pulse' : 'bg-stone-400'}`}></span>
              <span className="text-[#191512]">{status}</span>
            </span>
            <button
              onClick={() => { endVoiceCall(); onClose(); }}
              className="p-1.5 text-[#78716c] hover:text-[#191512] rounded-xl bg-[#ffffff] border border-[#ede5da] hover:bg-[#f4ede4]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Smartphone Call Simulator Banner */}
        <div className="px-6 py-4 bg-[#fbf8f3] border-b border-[#ede5da] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-[#feece8] border border-[#fbd2ca] flex items-center justify-center text-[#d94336]">
              <PhoneCall className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-extrabold text-[#191512]">EstateStream Voice Prototype</div>
              <div className="text-[11px] text-[#78716c]">English • Web Speech STT • ElevenLabs / Browser TTS</div>
            </div>
          </div>

          {/* Audio Waveform Meter */}
          <div className="flex items-center gap-1 h-6">
            {Array.from({ length: 18 }).map((_, i) => {
              const h = inCall ? Math.max(4, Math.min(22, audioVolume * 30 * Math.sin((i / 18) * Math.PI) + 4)) : 4;
              return (
                <div
                  key={i}
                  className="w-1 bg-[#d94336] rounded-full transition-all duration-75"
                  style={{ height: `${h}px` }}
                />
              );
            })}
          </div>
        </div>

        {/* Live Conversation Stream */}
        <div className="flex-1 p-6 overflow-y-auto max-h-[340px] space-y-3 bg-[#ffffff]">
          {messages.length === 0 ? (
            <div className="text-center py-12 text-[#78716c] text-xs space-y-2">
              <div className="w-12 h-12 rounded-full bg-[#f4ede4] flex items-center justify-center mx-auto text-[#d94336]">
                <Mic className="w-5 h-5" />
              </div>
              <p className="font-bold text-[#191512] text-sm">Click "Start Voice Call" below to test</p>
              <p className="max-w-xs mx-auto text-[#78716c]">
                Speak naturally as a prospective home buyer. Example: <em>"I'm looking for a 3 BHK in Downtown under $800,000."</em>
              </p>
            </div>
          ) : (
            messages.map((m, idx) => (
              <div key={idx} className="space-y-1.5">
                <div
                  className={`p-3.5 rounded-2xl text-xs leading-relaxed max-w-[85%] ${
                    m.role === 'assistant'
                      ? 'bg-[#fff5f3] border border-[#fbd2ca] text-[#191512] mr-auto'
                      : 'bg-[#f4ede4] border border-[#e8dfd2] text-[#191512] ml-auto'
                  }`}
                >
                  <div className="font-extrabold mb-1 flex items-center gap-1 text-[11px] text-[#78716c]">
                    {m.role === 'assistant' ? <Bot className="w-3.5 h-3.5 text-[#d94336]" /> : <User className="w-3.5 h-3.5 text-[#6b635b]" />}
                    <span>{m.role === 'assistant' ? 'Riya' : 'You'}</span>
                  </div>
                  <p className="font-normal">{m.text}</p>
                </div>

                {m.tools && m.tools.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 justify-center py-1">
                    {m.tools.map((t, ti) => (
                      <span
                        key={ti}
                        className="px-2.5 py-0.5 rounded-full bg-[#fef3c7] border border-[#fde68a] text-[#92400e] text-[11px] font-bold flex items-center gap-1"
                      >
                        <Wrench className="w-3 h-3 text-[#d97706]" />
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

        {/* Typed input: works in every browser and is handy for demos in noisy rooms */}
        {inCall && (
          <form
            className="px-4 pt-3 bg-[#fbf8f3] border-t border-[#ede5da] flex gap-2"
            onSubmit={(e) => { e.preventDefault(); sendUserText(typedText); setTypedText(''); }}
          >
            <input
              value={typedText}
              onChange={(e) => setTypedText(e.target.value)}
              placeholder={speechSupported ? 'Or type a message…' : 'Type your message to Riya…'}
              className="flex-1 px-3 py-2 text-xs rounded-xl border border-[#ede5da] bg-white focus:outline-none focus:border-[#d94336]"
            />
            <button type="submit" className="px-4 py-2 text-xs font-bold rounded-xl bg-[#191512] text-white">Send</button>
          </form>
        )}

        {/* Footer Controls */}
        <div className="p-4 border-t border-[#ede5da] bg-[#fbf8f3] flex items-center justify-center gap-4">
          {!inCall ? (
            <button
              onClick={startVoiceCall}
              className="flex items-center gap-2 px-6 py-3 bg-[#d94336] hover:bg-[#c43529] text-white font-extrabold text-xs rounded-xl shadow-md shadow-[#d94336]/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <PhoneCall className="w-4 h-4" />
              <span>Start Voice Call</span>
            </button>
          ) : (
            <button
              onClick={endVoiceCall}
              className="flex items-center gap-2 px-6 py-3 bg-stone-900 hover:bg-black text-white font-extrabold text-xs rounded-xl shadow-md transition-all hover:scale-[1.02] active:scale-[0.98]"
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
