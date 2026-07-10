import React, { useState } from 'react';
import { KnowledgeDocument, KnowledgeType } from '../types';
import { BookOpen, FileText, Bookmark, Calendar, ChevronDown, ChevronUp, User } from 'lucide-react';

interface KnowledgeCardProps {
  doc: KnowledgeDocument;
}

export const KnowledgeCard: React.FC<KnowledgeCardProps> = ({ doc }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getDocTypeIcon = (type: KnowledgeType) => {
    switch (type) {
      case KnowledgeType.RUNBOOK: return BookOpen;
      case KnowledgeType.RCA: return FileText;
      default: return Bookmark;
    }
  };

  const getDocTypeColor = (type: KnowledgeType) => {
    switch (type) {
      case KnowledgeType.RUNBOOK: return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case KnowledgeType.RCA: return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700/80 transition-all shadow-xs select-none">
      {/* Summary Header */}
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-5 flex items-start justify-between gap-4 cursor-pointer hover:bg-slate-800/20 transition-colors"
      >
        <div className="space-y-2.5 flex-1">
          {/* Metadata Row */}
          <div className="flex flex-wrap items-center gap-2">
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border uppercase ${getDocTypeColor(doc.type)}`}>
              {doc.type}
            </span>
            {doc.status === 'QUARANTINED' && (
              <>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border uppercase bg-rose-500/10 text-rose-400 border-rose-500/20 flex items-center gap-1">
                  QUARANTINED
                </span>
              </>
            )}
            <span className="text-slate-700 font-sans text-xs">•</span>
            <span className="text-[10.5px] font-mono font-semibold text-slate-400">
              {doc.service}
            </span>
            <span className="text-slate-700 font-sans text-xs">•</span>
            <div className="flex items-center gap-1 text-slate-500 font-mono text-[10.5px]">
              <Calendar className="w-3.5 h-3.5" />
              <span>{new Date(doc.lastUpdated).toLocaleDateString()}</span>
            </div>
          </div>

          {/* Title */}
          <h4 className="font-sans font-bold text-slate-200 text-[14.5px] tracking-tight hover:text-slate-100 transition-colors">
            {doc.title}
          </h4>

          {/* Tag row */}
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {doc.tags.map(tag => (
              <span key={tag} className="text-[9.5px] font-mono text-slate-500 bg-slate-950 px-1.5 py-0.5 rounded-sm border border-slate-800/40">
                #{tag}
              </span>
            ))}
          </div>
        </div>

        {/* Action controllers */}
        <div className="flex items-center gap-2 pt-0.5">
          <span className="hidden sm:inline font-mono text-[10px] text-slate-500">
            {doc.vectorsCount || 1536} dimensions
          </span>
          <button className="p-1 hover:bg-slate-800 text-slate-400 rounded-lg transition-colors">
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Playbook Content Expansion */}
      {isExpanded && (
        <div className="p-5 border-t border-slate-800 bg-slate-950/40 font-sans text-xs text-slate-300 space-y-4">
          
          <div className="prose prose-invert max-w-none text-slate-300 leading-relaxed space-y-3">
            {doc.content.split('\n').map((line, idx) => {
              if (line.startsWith('# ')) {
                return <h1 key={idx} className="font-sans font-bold text-slate-100 text-sm border-b border-slate-800 pb-1 pt-2">{line.replace('# ', '')}</h1>;
              }
              if (line.startsWith('## ')) {
                return <h2 key={idx} className="font-sans font-semibold text-slate-200 text-xs pt-1.5">{line.replace('## ', '')}</h2>;
              }
              if (line.startsWith('### ')) {
                return <h3 key={idx} className="font-sans font-semibold text-slate-300 text-xs">{line.replace('### ', '')}</h3>;
              }
              if (line.startsWith('```')) {
                // If it is a code block start/end, don't output the ``` characters directly
                if (line === '```' || line.startsWith('```')) return null;
              }
              if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
                return (
                  <ul key={idx} className="list-disc list-inside pl-4 text-slate-400 space-y-1">
                    <li>{line.replace(/^[\s-*]+/, '')}</li>
                  </ul>
                );
              }
              if (line.trim().startsWith('1. ') || line.trim().startsWith('2. ') || line.trim().startsWith('3. ')) {
                return (
                  <ol key={idx} className="list-decimal list-inside pl-4 text-slate-400 space-y-1">
                    <li>{line.replace(/^\d+\.\s+/, '')}</li>
                  </ol>
                );
              }
              if (line.trim().includes('SELECT ') || line.trim().includes('kubectl ') || line.trim().includes('ALTER ')) {
                return (
                  <pre key={idx} className="bg-slate-950 border border-slate-800 rounded px-3 py-2 font-mono text-[10.5px] text-blue-400 overflow-x-auto my-2 select-all leading-tight">
                    {line.replace(/`/g, '')}
                  </pre>
                );
              }
              return <p key={idx} className="text-slate-400 leading-relaxed">{line}</p>;
            })}
          </div>

          <div className="flex justify-between items-center pt-3 border-t border-slate-800/80 text-[10.5px] font-mono text-slate-500">
            <div className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5" />
              <span>Authored by: <strong className="text-slate-400">{doc.author}</strong></span>
            </div>
            <span className="text-blue-400">Indexed in Qdrant Vector DB</span>
          </div>
        </div>
      )}
    </div>
  );
};
