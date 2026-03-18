import { useState } from 'react';
import { X, Upload, Loader2, FileText, Link } from 'lucide-react';
import { addDocument } from '../../services/knowledgeService';

interface Props {
  onClose: () => void;
  onSuccess: () => void;
}

export default function DocumentUploadModal({ onClose, onSuccess }: Props) {
  const [title, setTitle] = useState('');
  const [source, setSource] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const charCount = content.length;
  const estimatedChunks = Math.max(1, Math.ceil(charCount / 550));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setLoading(true);
    setError('');
    try {
      await addDocument({ title: title.trim(), source: source.trim(), content: content.trim() });
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <Upload className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold">Add Document</h2>
              <p className="text-xs text-slate-500">Document will be chunked and embedded automatically</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/6 text-slate-500 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                <FileText className="w-3 h-3 inline mr-1" />
                Title <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Refund Policy, Getting Started Guide…"
                required
                className="w-full bg-slate-800 border border-white/8 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                <Link className="w-3 h-3 inline mr-1" />
                Source <span className="text-slate-600">(optional)</span>
              </label>
              <input
                type="text"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="e.g. https://docs.example.com/refund-policy"
                className="w-full bg-slate-800 border border-white/8 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-slate-400">
                  Content <span className="text-rose-400">*</span>
                </label>
                <span className="text-xs text-slate-600">{charCount.toLocaleString()} chars</span>
              </div>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste the full document text here. It will be automatically split into semantic chunks and indexed for vector search."
                required
                rows={12}
                className="w-full bg-slate-800 border border-white/8 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors leading-relaxed"
              />
            </div>

            {charCount > 0 && (
              <div className="flex items-center gap-4 px-4 py-3 rounded-xl bg-slate-800/60 border border-white/6 text-xs text-slate-500">
                <span>~{estimatedChunks} chunks</span>
                <span>·</span>
                <span>~{estimatedChunks} embeddings to generate</span>
                <span>·</span>
                <span>Vector(384) per chunk</span>
              </div>
            )}

            {error && (
              <div className="px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
                {error}
              </div>
            )}
          </div>

          <div className="px-6 py-4 border-t border-white/6 flex items-center justify-end gap-3">
            <button type="button" onClick={onClose} disabled={loading} className="px-4 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/6 text-sm font-medium transition-colors disabled:opacity-40">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !title.trim() || !content.trim()}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              {loading ? 'Uploading & embedding…' : 'Upload Document'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
