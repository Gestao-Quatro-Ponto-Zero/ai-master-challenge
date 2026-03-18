import { useState, useEffect } from 'react';
import { ThumbsUp, ThumbsDown, Minus, Loader2, Check, MessageSquare, X } from 'lucide-react';
import {
  collectFeedback, getTicketFeedback,
  type KnowledgeFeedback,
} from '../../services/feedbackService';

interface Props {
  ticketId:        string;
  conversationId?: string | null;
}

const QUICK = [
  { label: 'Helpful',   icon: ThumbsUp,   rating: 5, cls: 'hover:border-emerald-500/40 hover:bg-emerald-500/8 hover:text-emerald-400' },
  { label: 'Partial',   icon: Minus,      rating: 3, cls: 'hover:border-amber-500/40 hover:bg-amber-500/8 hover:text-amber-400'       },
  { label: 'Not helpful', icon: ThumbsDown, rating: 1, cls: 'hover:border-rose-500/40 hover:bg-rose-500/8 hover:text-rose-400'          },
] as const;

const RATING_LABEL: Record<number, { label: string; cls: string }> = {
  5: { label: 'Excellent',  cls: 'text-emerald-400' },
  4: { label: 'Good',       cls: 'text-emerald-300' },
  3: { label: 'Partial',    cls: 'text-amber-400'   },
  2: { label: 'Incomplete', cls: 'text-orange-400'  },
  1: { label: 'Not helpful',cls: 'text-rose-400'    },
};

function StarRow({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const [hover, setHover] = useState(0);
  const display = hover || value;

  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          onClick={() => onChange(n)}
          onMouseEnter={() => setHover(n)}
          onMouseLeave={() => setHover(0)}
          className={`w-6 h-6 flex items-center justify-center rounded transition-colors ${
            n <= display ? 'text-amber-400' : 'text-slate-700 hover:text-slate-500'
          }`}
        >
          <svg viewBox="0 0 16 16" className="w-4 h-4 fill-current">
            <path d="M8 12.3L3.1 15l.9-5.4L.4 6l5.5-.8L8 .3l2.1 4.9 5.5.8-4 3.9.9 5.4z" />
          </svg>
        </button>
      ))}
      {value > 0 && (
        <span className={`text-xs ml-1 ${RATING_LABEL[value]?.cls ?? 'text-slate-400'}`}>
          {RATING_LABEL[value]?.label}
        </span>
      )}
    </div>
  );
}

function ExistingFeedback({ fb }: { fb: KnowledgeFeedback }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-0.5">
          {[1, 2, 3, 4, 5].map((n) => (
            <svg key={n} viewBox="0 0 16 16" className={`w-3 h-3 fill-current ${n <= fb.rating ? 'text-amber-400' : 'text-slate-700'}`}>
              <path d="M8 12.3L3.1 15l.9-5.4L.4 6l5.5-.8L8 .3l2.1 4.9 5.5.8-4 3.9.9 5.4z" />
            </svg>
          ))}
        </div>
        <span className={`text-xs font-medium ${RATING_LABEL[fb.rating]?.cls ?? 'text-slate-400'}`}>
          {RATING_LABEL[fb.rating]?.label}
        </span>
      </div>
      {fb.feedback_text && (
        <p className="text-xs text-slate-500 leading-relaxed italic">"{fb.feedback_text}"</p>
      )}
      <p className="text-xs text-slate-700">
        {new Date(fb.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
      </p>
    </div>
  );
}

export default function AnswerFeedback({ ticketId, conversationId }: Props) {
  const [existing,   setExisting]   = useState<KnowledgeFeedback | null>(null);
  const [loadingEx,  setLoadingEx]  = useState(true);
  const [rating,     setRating]     = useState(0);
  const [text,       setText]       = useState('');
  const [showText,   setShowText]   = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted,  setSubmitted]  = useState(false);
  const [error,      setError]      = useState('');

  useEffect(() => {
    getTicketFeedback(ticketId)
      .then(setExisting)
      .catch(() => void 0)
      .finally(() => setLoadingEx(false));
  }, [ticketId]);

  async function handleSubmit() {
    if (!rating) { setError('Please select a rating'); return; }
    setSubmitting(true); setError('');
    try {
      await collectFeedback({
        ticket_id:       ticketId,
        conversation_id: conversationId ?? null,
        rating,
        feedback_text:   text.trim(),
        feedback_source: 'operator',
      });
      setSubmitted(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingEx) return null;

  if (existing) {
    return (
      <section>
        <div className="flex items-center gap-2 mb-2.5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">AI Response Quality</p>
          <Check className="w-3 h-3 text-emerald-500" />
        </div>
        <ExistingFeedback fb={existing} />
      </section>
    );
  }

  if (submitted) {
    return (
      <section>
        <div className="flex items-center gap-2 mb-2.5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">AI Response Quality</p>
        </div>
        <div className="flex items-center gap-2 py-2">
          <div className="w-6 h-6 rounded-full bg-emerald-500/15 flex items-center justify-center">
            <Check className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <span className="text-xs text-emerald-400">Feedback submitted</span>
        </div>
      </section>
    );
  }

  return (
    <section>
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2.5">AI Response Quality</p>

      <div className="space-y-3">
        <div className="flex flex-wrap gap-1.5">
          {QUICK.map(({ label, icon: Icon, rating: r, cls }) => (
            <button
              key={r}
              onClick={() => { setRating(r); setShowText(true); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                rating === r
                  ? r >= 4
                    ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
                    : r === 3
                    ? 'border-amber-500/40 bg-amber-500/10 text-amber-400'
                    : 'border-rose-500/40 bg-rose-500/10 text-rose-400'
                  : `border-gray-200 text-gray-400 bg-white ${cls}`
              }`}
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>

        {rating > 0 && (
          <StarRow value={rating} onChange={setRating} />
        )}

        {showText && (
          <div className="relative">
            <MessageSquare className="absolute left-3 top-3 w-3 h-3 text-gray-300 pointer-events-none" />
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Optional comment…"
              rows={2}
              className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-8 pr-8 py-2.5 text-xs text-gray-700 placeholder-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
            {text && (
              <button
                onClick={() => setText('')}
                className="absolute right-2.5 top-2.5 text-gray-300 hover:text-gray-500"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        )}

        {error && <p className="text-xs text-red-400">{error}</p>}

        {rating > 0 && (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-xs font-medium text-gray-700 transition-colors"
          >
            {submitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
            Submit Feedback
          </button>
        )}
      </div>
    </section>
  );
}
