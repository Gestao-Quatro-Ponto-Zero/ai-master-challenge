import { useState, useRef, useCallback } from 'react';
import {
  X, Globe, Upload, FileText, Loader2, Check,
  Link, Tag as TagIcon, FolderOpen, AlertCircle,
  Clipboard, ChevronDown, ChevronUp,
} from 'lucide-react';
import {
  ingestManual, ingestUrl, ingestFile,
  detectClientFormat, type IngestFormat,
} from '../../services/ingestionService';
import { type KnowledgeSource, type KnowledgeCategory, type KnowledgeTag, type DocumentType } from '../../services/knowledgeService';

type IngestTab = 'paste' | 'url' | 'file';

const DOC_TYPES: DocumentType[] = ['article', 'faq', 'policy', 'procedure', 'guide'];
const FORMAT_LABELS: Record<IngestFormat, string> = {
  text:     'Plain Text',
  html:     'HTML',
  markdown: 'Markdown',
  json:     'JSON',
};
const FORMAT_COLORS: Record<IngestFormat, string> = {
  text:     'text-slate-400',
  html:     'text-orange-400',
  markdown: 'text-blue-400',
  json:     'text-emerald-400',
};

const ACCEPTED_EXTENSIONS = '.txt,.md,.markdown,.html,.htm,.json';

interface Props {
  sources:    KnowledgeSource[];
  categories: KnowledgeCategory[];
  tags:       KnowledgeTag[];
  onClose:    () => void;
  onSuccess:  (docId: string, title: string) => void;
}

interface MetaFields {
  title:        string;
  source_id:    string;
  category_id:  string;
  document_type: DocumentType;
  tag_ids:      string[];
}

const EMPTY_META: MetaFields = {
  title: '', source_id: '', category_id: '', document_type: 'article', tag_ids: [],
};

export default function DocumentIngestionPanel({ sources, categories, tags, onClose, onSuccess }: Props) {
  const [activeTab, setActiveTab] = useState<IngestTab>('paste');

  const [pasteContent, setPasteContent] = useState('');
  const [pasteFormat, setPasteFormat]   = useState<IngestFormat>('text');
  const [autoDetected, setAutoDetected] = useState(false);

  const [importUrl, setImportUrl] = useState('');

  const [file,        setFile]        = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState('');
  const [isDragging,  setIsDragging]  = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [meta,      setMeta]     = useState<MetaFields>(EMPTY_META);
  const [showMeta,  setShowMeta] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result,    setResult]   = useState<{ id: string; title: string } | null>(null);
  const [error,     setError]    = useState('');

  function updatePasteContent(val: string) {
    setPasteContent(val);
    if (val.length > 30) {
      const detected = detectClientFormat(val);
      setPasteFormat(detected);
      setAutoDetected(true);
    } else {
      setAutoDetected(false);
    }
  }

  function toggleTag(id: string) {
    setMeta((m) => ({
      ...m,
      tag_ids: m.tag_ids.includes(id) ? m.tag_ids.filter((t) => t !== id) : [...m.tag_ids, id],
    }));
  }

  function handleFileSelect(f: File) {
    setFile(f);
    setError('');
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = (e.target?.result as string) ?? '';
      setFilePreview(text.slice(0, 400));
    };
    reader.readAsText(f);
    if (!meta.title) {
      setMeta((m) => ({ ...m, title: f.name.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ') }));
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFileSelect(dropped);
  }, []);

  async function submit() {
    setError(''); setSubmitting(true);
    try {
      const shared = {
        title:         meta.title,
        source_id:     meta.source_id  || undefined,
        category_id:   meta.category_id || undefined,
        document_type: meta.document_type,
        tag_ids:       meta.tag_ids.length ? meta.tag_ids : undefined,
      };

      let res;
      if (activeTab === 'paste') {
        if (!pasteContent.trim()) { setError('Please enter some content'); setSubmitting(false); return; }
        if (!meta.title.trim())   { setError('Title is required');           setSubmitting(false); return; }
        res = await ingestManual({ ...shared, content: pasteContent, format: pasteFormat });
      } else if (activeTab === 'url') {
        if (!importUrl.trim()) { setError('Please enter a URL'); setSubmitting(false); return; }
        res = await ingestUrl({ ...shared, url: importUrl });
      } else {
        if (!file) { setError('Please select a file'); setSubmitting(false); return; }
        res = await ingestFile({ ...shared, file });
      }

      setResult({ id: res.document_id, title: res.title });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <div className="w-full max-w-md bg-slate-900 border border-white/10 rounded-2xl p-8 text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mx-auto mb-4">
            <Check className="w-7 h-7 text-emerald-400" />
          </div>
          <h2 className="text-lg font-semibold text-white mb-1">Document Ingested</h2>
          <p className="text-sm text-slate-400 mb-1">
            <span className="text-white font-medium">{result.title}</span> was created as a draft.
          </p>
          <p className="text-xs text-slate-600 mb-6">Open the document in the editor to review, edit, and publish.</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => { onSuccess(result.id, result.title); onClose(); }}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm text-white font-medium transition-colors">
              Open in Editor
            </button>
            <button onClick={() => { setResult(null); setMeta(EMPTY_META); setPasteContent(''); setImportUrl(''); setFile(null); setFilePreview(''); }}
              className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-sm text-white font-medium transition-colors">
              Ingest Another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full sm:max-w-2xl bg-slate-900 border border-white/10 sm:rounded-2xl flex flex-col max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/6 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <Upload className="w-4 h-4 text-blue-400" />
            </div>
            <h2 className="text-sm font-semibold text-white">Ingest Document</h2>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl text-slate-500 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-1 px-6 py-3 border-b border-white/6 shrink-0 bg-slate-900/60">
          {([
            { id: 'paste' as IngestTab, label: 'Paste Content', icon: Clipboard },
            { id: 'url'   as IngestTab, label: 'Import URL',    icon: Link      },
            { id: 'file'  as IngestTab, label: 'Upload File',   icon: Upload    },
          ] as const).map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => { setActiveTab(id); setError(''); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === id ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-white'}`}>
              <Icon className="w-3.5 h-3.5" />{label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {activeTab === 'paste' && (
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs text-slate-500">Content *</label>
                  {autoDetected && (
                    <span className={`text-xs font-mono ${FORMAT_COLORS[pasteFormat]}`}>
                      {FORMAT_LABELS[pasteFormat]} detected
                    </span>
                  )}
                </div>
                <textarea value={pasteContent} onChange={(e) => updatePasteContent(e.target.value)}
                  rows={10} placeholder="Paste your text, HTML, Markdown, or JSON here…"
                  className="w-full bg-slate-800/60 border border-white/8 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/30 font-mono leading-relaxed" />
                <div className="flex items-center justify-between mt-1.5">
                  <div className="flex gap-1">
                    {(['text', 'html', 'markdown', 'json'] as IngestFormat[]).map((f) => (
                      <button key={f} onClick={() => { setPasteFormat(f); setAutoDetected(false); }}
                        className={`px-2 py-0.5 rounded-md text-xs transition-colors ${pasteFormat === f ? `${FORMAT_COLORS[f]} bg-white/6` : 'text-slate-600 hover:text-white'}`}>
                        {FORMAT_LABELS[f]}
                      </button>
                    ))}
                  </div>
                  <span className="text-xs text-slate-700">{pasteContent.length.toLocaleString()} chars</span>
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">Title *</label>
                <input value={meta.title} onChange={(e) => setMeta((m) => ({ ...m, title: e.target.value }))}
                  placeholder="Document title"
                  className="w-full bg-slate-800/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
              </div>
            </div>
          )}

          {activeTab === 'url' && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">Web Page URL *</label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none" />
                  <input value={importUrl} onChange={(e) => setImportUrl(e.target.value)}
                    type="url" placeholder="https://example.com/help-article"
                    className="w-full bg-slate-800/60 border border-white/8 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
                </div>
                <p className="text-xs text-slate-700 mt-1.5">The page will be fetched server-side and its text extracted automatically.</p>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">Title override <span className="text-slate-700">(auto-detected if blank)</span></label>
                <input value={meta.title} onChange={(e) => setMeta((m) => ({ ...m, title: e.target.value }))}
                  placeholder="Leave blank to use page title"
                  className="w-full bg-slate-800/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
              </div>
            </div>
          )}

          {activeTab === 'file' && (
            <div className="space-y-3">
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed py-10 px-6 cursor-pointer transition-all ${isDragging ? 'border-blue-500/60 bg-blue-500/5' : 'border-white/10 hover:border-white/20 hover:bg-white/2'}`}>
                <input ref={fileInputRef} type="file" accept={ACCEPTED_EXTENSIONS} className="hidden"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }} />
                {file ? (
                  <>
                    <FileText className="w-8 h-8 text-blue-400 mb-2" />
                    <p className="text-sm font-medium text-white">{file.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{(file.size / 1024).toFixed(1)} KB</p>
                  </>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-slate-600 mb-2" />
                    <p className="text-sm text-slate-400">Drop a file here or <span className="text-blue-400">click to browse</span></p>
                    <p className="text-xs text-slate-600 mt-1">.txt · .md · .html · .json</p>
                  </>
                )}
              </div>

              {filePreview && (
                <div className="bg-slate-800/40 border border-white/6 rounded-xl px-4 py-3">
                  <p className="text-xs text-slate-600 mb-1.5">Preview</p>
                  <p className="text-xs text-slate-400 font-mono leading-relaxed whitespace-pre-wrap break-words">{filePreview}{filePreview.length >= 400 ? '…' : ''}</p>
                </div>
              )}

              <div>
                <label className="block text-xs text-slate-500 mb-1.5">Title override <span className="text-slate-700">(auto-detected from filename if blank)</span></label>
                <input value={meta.title} onChange={(e) => setMeta((m) => ({ ...m, title: e.target.value }))}
                  placeholder="Leave blank to use filename"
                  className="w-full bg-slate-800/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
              </div>
            </div>
          )}

          <button onClick={() => setShowMeta((v) => !v)}
            className="flex items-center gap-2 text-xs text-slate-500 hover:text-white transition-colors w-full pt-1">
            {showMeta ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{showMeta ? 'Hide' : 'Show'} metadata options</span>
          </button>

          {showMeta && (
            <div className="space-y-3 bg-slate-800/30 border border-white/6 rounded-2xl p-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">Category</label>
                  <select value={meta.category_id} onChange={(e) => setMeta((m) => ({ ...m, category_id: e.target.value }))}
                    className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40">
                    <option value="">— None —</option>
                    {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">Source</label>
                  <select value={meta.source_id} onChange={(e) => setMeta((m) => ({ ...m, source_id: e.target.value }))}
                    className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40">
                    <option value="">— None —</option>
                    {sources.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">Document Type</label>
                <div className="flex gap-1.5 flex-wrap">
                  {DOC_TYPES.map((t) => (
                    <button key={t} onClick={() => setMeta((m) => ({ ...m, document_type: t }))}
                      className={`px-3 py-1 rounded-lg text-xs capitalize transition-colors ${meta.document_type === t ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-white bg-slate-800/40'}`}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              {tags.length > 0 && (
                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">Tags</label>
                  <div className="flex flex-wrap gap-1.5">
                    {tags.map((tag) => {
                      const sel = meta.tag_ids.includes(tag.id);
                      return (
                        <button key={tag.id} onClick={() => toggleTag(tag.id)}
                          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs transition-colors border ${sel ? 'text-white border-transparent' : 'border-white/8 text-slate-500 hover:text-white'}`}
                          style={sel ? { backgroundColor: tag.color + '33', borderColor: tag.color + '66', color: tag.color } : {}}>
                          <TagIcon className="w-2.5 h-2.5" />{tag.name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2.5 bg-rose-500/10 border border-rose-500/20 rounded-xl px-4 py-3">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <p className="text-sm text-rose-300">{error}</p>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-white/6 shrink-0 flex items-center justify-between">
          <p className="text-xs text-slate-600">
            {activeTab === 'paste' && 'Content will be normalised and saved as draft.'}
            {activeTab === 'url'   && 'Text will be extracted from the page server-side.'}
            {activeTab === 'file'  && 'File content will be extracted and normalised.'}
          </p>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">Cancel</button>
            <button onClick={submit} disabled={submitting}
              className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-xl text-sm text-white font-medium transition-colors">
              {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              {submitting ? 'Ingesting…' : 'Ingest Document'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
