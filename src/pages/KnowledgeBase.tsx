import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { KnowledgeCard } from '../components/KnowledgeCard';
import { SearchBar } from '../components/SearchBar';
import { KnowledgeType } from '../types';
import { BookOpen, Plus, Database, X } from 'lucide-react';

export const KnowledgeBase: React.FC = () => {
  const { knowledgeDocs, searchKB, addKBDoc, uploadKBDoc, systemOverview } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form states
  const [title, setTitle] = useState('');
  const [type, setType] = useState(KnowledgeType.RUNBOOK);
  const [service, setService] = useState('checkout-service');
  const [content, setContent] = useState('');
  const [tagsInput, setTagsInput] = useState('');

  const handleSearch = (val: string) => {
    setSearchQuery(val);
    searchKB(val);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    const tags = tagsInput.split(',')
      .map(t => t.trim().toLowerCase())
      .filter(t => t.length > 0);

    await addKBDoc({
      title,
      type,
      content,
      service,
      author: 'Elena Rostova',
      tags: [...tags, service]
    });

    setShowCreateModal(false);
    // Reset form
    setTitle('');
    setContent('');
    setTagsInput('');
    setService('checkout-service');
    setType(KnowledgeType.RUNBOOK);
  };

  return (
    <div className="space-y-6 pb-12 select-none animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="font-sans font-bold text-slate-100 text-lg leading-tight">Qdrant Knowledge Base</h3>
          <p className="text-slate-400 text-xs font-sans mt-0.5">Automated RAG vector storage index of cluster runbooks and resolved RCAs.</p>
        </div>

        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold px-3.5 py-2 rounded-lg border border-slate-700 transition-all cursor-pointer font-sans">
            <input type="file" className="hidden" accept=".txt,.md,.pdf,.docx" onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                uploadKBDoc(file);
                e.target.value = '';
              }
            }} />
            <BookOpen className="w-3.5 h-3.5" />
            Upload File
          </label>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg border border-blue-500 shadow-md shadow-blue-500/10 transition-all cursor-pointer font-sans"
          >
            <Plus className="w-3.5 h-3.5" />
            Author SOP/Runbook
          </button>
        </div>
      </div>

      {/* Stats/Search Row */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="flex items-center gap-3 font-mono text-xs text-slate-400 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2">
          <Database className="w-4 h-4 text-indigo-400" />
          <span>Vector Index Stats: <strong className="text-indigo-400">{systemOverview.ragVectorsIndexed}</strong> dimensions</span>
        </div>

        <SearchBar
          query={searchQuery}
          onChange={handleSearch}
          placeholder="Search runbooks, service guidelines, SOPs..."
        />
      </div>

      {/* Documents list */}
      <div className="space-y-4">
        {knowledgeDocs.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-slate-800 rounded-xl bg-slate-950/20">
            <BookOpen className="w-8 h-8 text-slate-600 mb-2.5" />
            <h4 className="font-sans font-bold text-slate-400 text-xs uppercase tracking-wider">No Guidelines Match Your Query</h4>
            <p className="text-[11px] text-slate-500 font-sans mt-0.5 max-w-xs mx-auto">
              Refine your text parameters or author a new runbook to populate the index.
            </p>
          </div>
        ) : (
          knowledgeDocs.map((doc) => (
            <KnowledgeCard key={doc.id} doc={doc} />
          ))
        )}
      </div>

      {/* Playbook Authoring Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-xl rounded-xl overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
              <h3 className="font-sans font-bold text-slate-200 text-sm">Author SOP Playbook</h3>
              <button 
                onClick={() => setShowCreateModal(false)}
                className="p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Document Type</label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono"
                  >
                    <option value={KnowledgeType.RUNBOOK}>RUNBOOK (Standard)</option>
                    <option value={KnowledgeType.SOP}>SOP (Policy)</option>
                    <option value={KnowledgeType.RCA}>RCA (Post-Mortem)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Target Service Scope</label>
                  <select
                    value={service}
                    onChange={(e) => setService(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono"
                  >
                    <option value="checkout-service">checkout-service</option>
                    <option value="auth-gateway">auth-gateway</option>
                    <option value="notification-worker">notification-worker</option>
                    <option value="api-gateway">api-gateway</option>
                    <option value="postgresql-primary">postgresql-primary</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Document Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Redis Cluster Lock Contention SOP"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-sans"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Keywords / Tags (comma separated)</label>
                <input
                  type="text"
                  placeholder="redis, cache, scaling, locking"
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Content Body (Markdown Supported)</label>
                <textarea
                  required
                  rows={8}
                  placeholder="# Playbook Name&#10;&#10;## Diagnostic steps&#10;1. run command...&#10;&#10;## Resolution&#10;ALTER SYSTEM SET..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono leading-relaxed"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 font-semibold hover:bg-slate-800 rounded-lg cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg border border-blue-500 shadow-md shadow-blue-500/10 transition-all cursor-pointer"
                >
                  Index SOP
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
