import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { apiRequest } from '../services/api';
import { 
  Sparkles, 
  Send, 
  Terminal, 
  FileText, 
  Database, 
  ShieldCheck, 
  ShieldAlert, 
  Copy, 
  Check, 
  ArrowRight, 
  Loader2, 
  Cpu, 
  RefreshCw,
  ExternalLink
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  referencedIncident?: Record<string, any> | null;
  retrievedDocuments?: Array<Record<string, any>>;
  guardrailStatus?: Record<string, any>;
}

export const AICopilot: React.FC = () => {
  const { incidents } = useApp();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "### Welcome to Mastra Sentinel SRE Copilot\n\nI am connected to the **Qdrant Vector database** and **Gemini reasoning modules** to act as your expert on-call partner. I can help you analyze outages, run similarity searches on SRE runbooks, explain autonomous agent decisions, or formulate safe mitigation recipes.\n\nHere are some operations we can perform together:",
      timestamp: new Date().toISOString(),
      guardrailStatus: { inputStatus: 'PASSED', outputStatus: 'PASSED', inputThreats: [], outputThreats: [] }
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [contextData, setContextData] = useState<{
    suggestedQuestions: Array<{text: string, icon: string}>;
    activeAlerts: number;
    recentIncidents: Array<{id: string, title: string}>;
  }>({
    suggestedQuestions: [
      { text: "Explain Incident INC-2026-001 in depth", icon: "ShieldAlert" },
      { text: "Find PostgreSQL connection pool saturation SOPs", icon: "Database" },
      { text: "Why was INC-2026-002 classified as infrastructure overload?", icon: "Cpu" },
      { text: "Formulate a safe rollback recipe for product-catalog", icon: "Terminal" }
    ],
    activeAlerts: 0,
    recentIncidents: []
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  useEffect(() => {
    // Load context on mount
    const fetchContext = async () => {
      try {
        const response = await apiRequest<any>('/api/v1/copilot/context');
        if (response.data) {
          setContextData(response.data);
        }
      } catch (err) {
        console.error("Failed to load Copilot context", err);
      }
    };
    fetchContext();
  }, []);

  const handleCopyCode = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const parseMessageContent = (content: string, messageId: string) => {
    const parts = content.split(/(```[\s\S]*?```)/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('```')) {
        const lines = part.split('\n');
        const firstLine = lines[0].replace('```', '').trim();
        const codeType = firstLine || 'bash';
        const codeContent = lines.slice(1, lines.length - 1).join('\n');
        const blockId = `${messageId}-code-${index}`;

        return (
          <div key={blockId} className="my-3 border border-slate-800 rounded-lg overflow-hidden bg-slate-950 shadow-inner">
            <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800 text-xs font-mono text-slate-400">
              <span className="flex items-center gap-1.5 uppercase font-bold text-blue-400">
                <Terminal className="w-3.5 h-3.5" />
                {codeType}
              </span>
              <button
                onClick={() => handleCopyCode(codeContent, blockId)}
                className="flex items-center gap-1 hover:text-slate-200 transition-colors cursor-pointer"
              >
                {copiedId === blockId ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
            <pre className="p-4 overflow-x-auto font-mono text-xs text-slate-300 leading-relaxed max-w-full">
              <code>{codeContent}</code>
            </pre>
          </div>
        );
      }

      // Simple Markdown rendering simulation
      const textLines = part.split('\n');
      return textLines.map((line, lIdx) => {
        if (line.startsWith('### ')) {
          return <h4 key={lIdx} className="text-slate-100 font-sans font-bold text-sm mt-3 mb-1.5">{line.substring(4)}</h4>;
        } else if (line.startsWith('#### ')) {
          return <h5 key={lIdx} className="text-slate-200 font-sans font-semibold text-xs mt-2.5 mb-1">{line.substring(5)}</h5>;
        } else if (line.startsWith('- ') || line.startsWith('* ')) {
          return <li key={lIdx} className="text-slate-300 font-sans text-xs ml-4 list-disc mt-1 leading-relaxed">{line.substring(2)}</li>;
        } else if (line.trim().length === 0) {
          return <div key={lIdx} className="h-2" />;
        }
        
        // Inline code highlights
        const segments = line.split(/(`[^`]+`)/g);
        return (
          <p key={lIdx} className="text-slate-300 font-sans text-xs leading-relaxed mt-1">
            {segments.map((seg, sIdx) => {
              if (seg.startsWith('`') && seg.endsWith('`')) {
                return (
                  <code key={sIdx} className="bg-slate-950 border border-slate-800 text-blue-400 px-1.5 py-0.5 rounded-md font-mono text-[10.5px]">
                    {seg.substring(1, seg.length - 1)}
                  </code>
                );
              }
              // Bold words
              const boldSegments = seg.split(/(\*\*[^*]+\*\*)/g);
              return boldSegments.map((bSeg, bIdx) => {
                if (bSeg.startsWith('**') && bSeg.endsWith('**')) {
                  return <strong key={bIdx} className="font-bold text-slate-100">{bSeg.substring(2, bSeg.length - 2)}</strong>;
                }
                return bSeg;
              });
            })}
          </p>
        );
      });
    });
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isGenerating) return;

    setInput('');
    const userMsgId = `msg-${Date.now()}`;
    const newUserMessage: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };

    const assistantMsgId = `assistant-${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newUserMessage, initialAssistantMsg]);
    setIsGenerating(true);

    try {
      const chatHistoryPayload = messages
        .filter(m => m.id !== 'welcome')
        .map(m => ({
          role: m.role,
          content: m.content
        }));

      // We use native fetch for SSE support instead of apiRequest wrapper
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/copilot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          message: text,
          incidentId: selectedIncidentId || null,
          chatHistory: chatHistoryPayload
        })
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let doneReading = false;
      let buffer = '';

      while (!doneReading) {
        const { value, done } = await reader.read();
        if (done) {
          doneReading = true;
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (part.startsWith('data: ')) {
            const dataStr = part.substring(6);
            try {
              const data = JSON.parse(dataStr);
              
              setMessages(prev => prev.map(msg => {
                if (msg.id === assistantMsgId) {
                  return {
                    ...msg,
                    content: msg.content + (data.chunk || ''),
                    referencedIncident: data.referencedIncident || msg.referencedIncident,
                    retrievedDocuments: data.retrievedDocuments || msg.retrievedDocuments,
                    guardrailStatus: data.guardrailStatus || msg.guardrailStatus
                  };
                }
                return msg;
              }));

              if (data.done) {
                doneReading = true;
              }
            } catch (e) {
              console.error("SSE parse error", e, dataStr);
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMsgId) {
           return {
             ...msg,
             content: `### ⚠️ SRE Pipeline Gateway Timeout\n\nCould not resolve Gemini connection channel. Ensure the core FastAPI backend services and port forwardings are fully initialized.\n\n*Detailed Error log: ${err?.message || "Connection Refused"}*`,
             guardrailStatus: { inputStatus: 'PASSED', outputStatus: 'FAILED', inputThreats: [], outputThreats: ['Connection Fail'] }
           };
        }
        return msg;
      }));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(input);
  };

  return (
    <div className="space-y-6 pb-12 select-none animate-fadeIn h-[calc(100vh-140px)] flex flex-col">
      {/* Copilot Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-blue-600/15 text-blue-400 rounded-lg border border-blue-500/20">
              <Sparkles className="w-4 h-4 animate-pulse" />
            </div>
            <h3 className="font-sans font-bold text-slate-100 text-lg leading-none">Autonomous SRE Copilot</h3>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-1.5">Direct natural language chat connecting Gemini with indexed standard operating procedures and diagnostic runs.</p>
        </div>

        {/* Incident Context Selector */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
          <span className="text-[11px] font-mono font-bold text-slate-400">Context:</span>
          <select
            value={selectedIncidentId}
            onChange={(e) => setSelectedIncidentId(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-md px-2 py-0.5 text-xs text-slate-300 font-bold focus:outline-hidden cursor-pointer max-w-[200px]"
          >
            <option value="">No Active Incident</option>
            {incidents.map(inc => (
              <option key={inc.id} value={inc.id}>{inc.id} - {inc.title.substring(0, 20)}...</option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Chat Deck */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        {/* Chat Stream (8 cols) */}
        <div className="lg:col-span-8 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col overflow-hidden h-full">
          
          {/* Chat log body */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5 custom-scrollbar bg-slate-950/20">
            {messages.map((msg) => {
              const isAssistant = msg.role === 'assistant';
              const isToxAlert = msg.guardrailStatus?.inputStatus === 'ALERT' || msg.guardrailStatus?.outputStatus === 'ALERT';

              return (
                <div key={msg.id} className={`flex gap-4 ${isAssistant ? 'justify-start' : 'justify-end'}`}>
                  {/* Icon */}
                  {isAssistant && (
                    <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                      <Cpu className="w-4 h-4" />
                    </div>
                  )}

                  {/* Message bubble */}
                  <div className={`max-w-[85%] rounded-xl p-4 border space-y-2 ${
                    isAssistant 
                      ? 'bg-slate-900 border-slate-800/80 text-slate-200' 
                      : 'bg-blue-600/10 border-blue-500/30 text-slate-100'
                  }`}>
                    <div className="flex items-center justify-between gap-10 border-b border-slate-800/60 pb-1.5 mb-1.5 text-[10px] font-mono text-slate-500">
                      <span className="font-bold tracking-wider uppercase">
                        {isAssistant ? 'Mastra Sentinel Copilot' : 'SRE OPERATOR'}
                      </span>
                      <span>
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    {/* Content */}
                    <div className="space-y-1">
                      {parseMessageContent(msg.content, msg.id)}
                    </div>

                    {/* Enkrypt Badges */}
                    {isAssistant && msg.guardrailStatus && (
                      <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-slate-800/60 mt-3 text-[10px] font-mono">
                        <span className="text-slate-500">Enkrypt Guardrails:</span>
                        {isToxAlert ? (
                          <span className="flex items-center gap-1 bg-rose-500/15 border border-rose-500/30 text-rose-400 px-1.5 py-0.5 rounded-md font-bold">
                            <ShieldAlert className="w-3 h-3" />
                            ALERT SCAN TRIGGERED
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 px-1.5 py-0.5 rounded-md font-bold">
                            <ShieldCheck className="w-3 h-3" />
                            SHIELD PASSED (SAFE)
                          </span>
                        )}
                        {msg.guardrailStatus.inputThreats?.length > 0 && (
                          <span className="text-rose-400" title="Threats detected in query">
                            ({msg.guardrailStatus.inputThreats[0]})
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isGenerating && (
              <div className="flex gap-4 justify-start">
                <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                  <Cpu className="w-4 h-4 animate-spin" />
                </div>
                <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-4 text-slate-400 flex items-center gap-3 text-xs font-mono">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                  <span>Synthesizing logs and runbooks with Gemini reasoning model...</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Form input row */}
          <form onSubmit={handleSubmit} className="p-4 bg-slate-950/40 border-t border-slate-800 flex items-center gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isGenerating}
              placeholder={selectedIncidentId ? `Ask anything about active context ${selectedIncidentId}...` : "Ask a question, find runbooks, or explain incident details..."}
              className="flex-1 bg-slate-950 border border-slate-800 focus:border-blue-500 focus:outline-hidden rounded-xl px-4 py-3 text-xs text-slate-100 placeholder:text-slate-500 leading-none transition-colors"
            />
            <button
              type="submit"
              disabled={isGenerating || !input.trim()}
              className="p-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl border border-blue-500 shadow-md shadow-blue-500/15 disabled:opacity-40 transition-all cursor-pointer flex items-center justify-center shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Suggested Queries & Source Citations (4 cols) */}
        <div className="lg:col-span-4 space-y-6 overflow-y-auto custom-scrollbar h-full pr-1">
          {/* SRE Suggested Scenarios */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Suggested Scenarios</h4>
            <div className="space-y-2.5">
              {contextData.suggestedQuestions.map((q) => {
                let QIcon = FileText;
                if (q.icon === "ShieldAlert") QIcon = ShieldAlert;
                if (q.icon === "Cpu") QIcon = Cpu;
                if (q.icon === "Database") QIcon = Database;
                if (q.icon === "Terminal") QIcon = Terminal;

                return (
                  <button
                    key={q.text}
                    onClick={() => handleSendMessage(q.text)}
                    disabled={isGenerating}
                    className="w-full flex items-center gap-3 text-left p-3 rounded-lg bg-slate-950/40 border border-slate-800/80 hover:bg-slate-900 hover:border-slate-700 transition-all cursor-pointer group text-xs text-slate-300 hover:text-slate-100 disabled:opacity-40"
                  >
                    <div className="p-1.5 rounded-md bg-slate-900 group-hover:bg-blue-500/10 text-slate-500 group-hover:text-blue-400 border border-slate-800 group-hover:border-blue-500/25 transition-colors shrink-0">
                      <QIcon className="w-3.5 h-3.5" />
                    </div>
                    <span className="font-sans leading-snug">{q.text}</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-auto text-slate-600 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all shrink-0" />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Context Citations */}
          {messages.length > 1 && messages[messages.length - 1].role === 'assistant' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 animate-fadeIn">
              <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Active Copilot Citations</h4>
              
              {/* Document references */}
              {messages[messages.length - 1].retrievedDocuments && messages[messages.length - 1].retrievedDocuments!.length > 0 ? (
                <div className="space-y-3">
                  <span className="block text-[10px] font-mono text-slate-500">RETRIEVED RUNBOOKS:</span>
                  {messages[messages.length - 1].retrievedDocuments!.map((doc, idx) => (
                    <div key={idx} className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-sans font-bold text-xs text-slate-200 truncate">{doc.title}</span>
                        <span className="font-mono text-[9px] font-bold text-indigo-400 bg-indigo-500/15 border border-indigo-500/30 px-1.5 py-0.5 rounded-md shrink-0">
                          {doc.doc_id}
                        </span>
                      </div>
                      <p className="text-[10.5px] text-slate-400 leading-relaxed font-sans truncate-2-lines italic">
                        "{doc.content}"
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No historical SOP playbooks referenced in current retrieval context.</p>
              )}

              {/* Incident References */}
              {messages[messages.length - 1].referencedIncident && (
                <div className="space-y-3 pt-3 border-t border-slate-800/80">
                  <span className="block text-[10px] font-mono text-slate-500">REFERENCED INCIDENT ENTITY:</span>
                  <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg space-y-2">
                    <div className="flex items-center justify-between gap-2 text-xs font-mono font-bold">
                      <span className="text-rose-400">{messages[messages.length - 1].referencedIncident!.id}</span>
                      <span className="text-blue-400">{messages[messages.length - 1].referencedIncident!.service}</span>
                    </div>
                    <span className="block font-sans font-bold text-xs text-slate-200">
                      {messages[messages.length - 1].referencedIncident!.title}
                    </span>
                    <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                      <span>Status: <strong className="text-indigo-400">{messages[messages.length - 1].referencedIncident!.status}</strong></span>
                      <span>Sev: <strong className="text-rose-400">{messages[messages.length - 1].referencedIncident!.severity}</strong></span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
