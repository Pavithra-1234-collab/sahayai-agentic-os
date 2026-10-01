import { useState, useEffect } from "react";
import { Star, MessageSquare, Loader2, CheckCircle } from "lucide-react";

function StarRating({ rating }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star key={i} size={11} className={i <= rating ? "text-yellow-400 fill-yellow-400" : "text-zinc-700"} />
      ))}
    </div>
  );
}

function ReviewCard({ review, onDraftResponse }) {
  const [drafting, setDrafting] = useState(false);
  const [draft, setDraft] = useState(null);

  const draftResponse = async () => {
    setDrafting(true);
    try {
      const res = await fetch("/api/reviews/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product: review.product, rating: review.rating, review_text: review.text, platform: review.platform }),
      });
      const d = await res.json();
      setDraft(d.response);
    } finally { setDrafting(false); }
  };

  const borderColor = review.rating >= 4 ? "border-l-[#25D366]" : review.rating === 3 ? "border-l-yellow-500" : "border-l-red-500";

  return (
    <div className={`bg-[#18181b] border border-[#27272a] border-l-2 ${borderColor} rounded-xl p-4`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <StarRating rating={review.rating} />
            <span className="text-[10px] text-zinc-600">{review.platform === "amazon" ? "🟠 Amazon" : "🟡 Flipkart"}</span>
          </div>
          <div className="text-xs font-medium text-white">{review.reviewer}</div>
          <div className="text-[10px] text-zinc-500">{review.product}</div>
        </div>
        {review.responded && (
          <span className="flex items-center gap-1 text-[10px] text-[#25D366] bg-[#25D366]/10 px-2 py-0.5 rounded-full shrink-0">
            <CheckCircle size={9} />Responded
          </span>
        )}
      </div>
      <p className="text-xs text-zinc-400 leading-relaxed mb-3">{review.text}</p>

      {review.rating <= 3 && !review.responded && (
        <button onClick={draftResponse} disabled={drafting}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#27272a] text-zinc-300 text-xs rounded-lg hover:text-white transition-colors disabled:opacity-50">
          {drafting ? <Loader2 size={10} className="animate-spin" /> : <MessageSquare size={10} />}
          {drafting ? "Drafting..." : "Draft Response"}
        </button>
      )}

      {draft && (
        <div className="mt-3 p-3 bg-[#25D366]/5 border border-[#25D366]/20 rounded-lg">
          <div className="text-[10px] text-[#25D366] mb-1 font-medium uppercase tracking-wide">AI Draft Response</div>
          <p className="text-xs text-zinc-300 leading-relaxed">{draft}</p>
        </div>
      )}
    </div>
  );
}

export default function Reviews() {
  const [data, setData] = useState(null);
  const [days, setDays] = useState(30);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/reviews?days=${days}`).then(r => r.json()).then(d => { setData(d); setLoading(false); });
  }, [days]);

  const summary = data?.summary || {};
  const total = summary.total || 1;
  const posPct = Math.round((summary.positive / total) * 100) || 0;
  const neuPct = Math.round((summary.neutral / total) * 100) || 0;
  const negPct = 100 - posPct - neuPct;

  const allReviews = data?.recent_reviews || [];
  const negativeReviews = data?.negative_reviews || [];
  const displayed = filter === "negative" ? negativeReviews : filter === "needs" ? negativeReviews.filter(r => !r.responded) : allReviews;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2"><Star size={20} />Reviews & Reputation</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Monitor sentiment and draft responses</p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))}
          className="px-3 py-2 bg-[#18181b] border border-[#27272a] text-sm text-zinc-300 rounded-lg outline-none">
          {[7, 14, 30, 60].map(d => <option key={d} value={d}>Last {d} days</option>)}
        </select>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: "Avg Rating", value: `${summary.avg_rating || 0}/5`, color: "text-yellow-400" },
          { label: "Total", value: summary.total || 0, color: "text-white" },
          { label: "Positive", value: summary.positive || 0, color: "text-[#25D366]" },
          { label: "Neutral", value: summary.neutral || 0, color: "text-yellow-400" },
          { label: "Negative", value: summary.negative || 0, color: "text-red-400" },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-[#18181b] border border-[#27272a] rounded-xl p-4 text-center">
            <div className={`text-xl font-bold ${color}`}>{value}</div>
            <div className="text-[10px] text-zinc-500 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Sentiment bar */}
      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
        <div className="text-xs text-zinc-500 mb-2">Sentiment breakdown</div>
        <div className="flex h-2 rounded-full overflow-hidden gap-0.5">
          <div className="bg-[#25D366] rounded-l-full transition-all" style={{ width: `${posPct}%` }} />
          <div className="bg-yellow-500 transition-all" style={{ width: `${neuPct}%` }} />
          <div className="bg-red-500 rounded-r-full transition-all" style={{ width: `${negPct}%` }} />
        </div>
        <div className="flex gap-4 mt-2">
          <span className="text-[10px] text-zinc-400">🟢 Positive {posPct}%</span>
          <span className="text-[10px] text-zinc-400">🟡 Neutral {neuPct}%</span>
          <span className="text-[10px] text-zinc-400">🔴 Negative {negPct}%</span>
        </div>
      </div>

      {/* Top complaints */}
      {data?.top_complaints?.length > 0 && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
          <div className="text-xs font-medium text-red-400 mb-2">Top Complaint Patterns</div>
          <div className="flex gap-2 flex-wrap">
            {data.top_complaints.map((c, i) => (
              <span key={i} className="px-2.5 py-1 bg-red-500/10 text-red-300 text-xs rounded-lg">"{c.issue}" ({c.count}×)</span>
            ))}
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-1">
        {[["all", "All Reviews"], ["negative", "Negative Only"], ["needs", "Needs Response"]].map(([v, l]) => (
          <button key={v} onClick={() => setFilter(v)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-colors ${filter === v ? "bg-[#27272a] text-white" : "text-zinc-500 hover:text-zinc-300"}`}>{l}</button>
        ))}
      </div>

      {/* Reviews grid */}
      {loading ? (
        <div className="grid grid-cols-2 gap-3">
          {[...Array(4)].map((_, i) => <div key={i} className="h-32 bg-[#18181b] rounded-xl animate-pulse" />)}
        </div>
      ) : displayed.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">No reviews for this filter.</div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {displayed.map((r, i) => <ReviewCard key={i} review={r} />)}
        </div>
      )}
    </div>
  );
}
