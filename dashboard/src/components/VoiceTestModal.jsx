import React, { useState, useEffect, useRef } from 'react';
import { X, Mic, PhoneOff, PhoneCall, Bot, User, Wrench, Sparkles } from 'lucide-react';

export default function VoiceTestModal({ isOpen, onClose, onCallCompleted }) {
  const [inCall, setInCall] = useState(false);
  const [status, setStatus] = useState('Ready to connect');
  const [messages, setMessages] = useState([]);
  const [audioVolume, setAudioVolume] = useState(0);

  const wsRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const speechRecRef = useRef(null);
  const currentAudioSourceRef = useRef(null);
  const transcriptEndRef = useRef(null);

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

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  const startVoiceCall = async () => {
    try {
      setInCall(true);
      setStatus('Connecting to Riya...');
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
        setStatus('Call Active • Speaking with Riya');
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
        setStatus('Call Ended');
        setInCall(false);
      };
    } catch (err) {
      console.error(err);
      setStatus('Mic permission needed / Error');
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
              <p className="text-xs text-[#78716c]">Speaking with Riya (Placeholder Realty)</p>
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
              <div className="text-xs font-extrabold text-[#191512]">EstateStream Voice AI</div>
              <div className="text-[11px] text-[#78716c]">English • Nova-2 STT • ElevenLabs Voice</div>
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
