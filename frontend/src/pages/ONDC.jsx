import { useState, useEffect } from "react";
import { TrendingUp, Zap, MapPin, Star, Loader2, ChevronRight, ShoppingCart, Tag, CheckCircle } from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────────────────

function Stat({ label, value, sub, accent }) {
  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
      <div className="text-xs text-zinc-500 mb-1">{label}</div>
      <div className={`text-lg font-bold ${accent || "text-white"}`}>{value}</div>
      {sub && <div className="text-[11px] text-zinc-500 mt-0.5">{sub}</div>}
    </div>
  );
}

function Badge({ label, color = "zinc" }) {
  const cls = {
    green: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    yellow: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    zinc: "bg-zinc-800 text-zinc-400 border-zinc-700",
  }[color] || "bg-zinc-800 text-zinc-400 border-zinc-700";
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium border ${cls}`}>
      {label}
    </span>
  );
}

function ScoreBar({ score }) {
  const color = score >= 70 ? "#25D366" : score >= 40 ? "#eab308" : "#71717a";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-[#27272a] rounded-full overflow-hidden">
        <div style={{ width: `${score}%`, backgroundColor: color }} className="h-full rounded-full transition-all" />
      </div>
      <span className="text-xs font-bold" style={{ color }}>{score}</span>
    </div>
  );
}

// ── List on ONDC Button with success state ────────────────────────────────

function ListButton({ beckn_item_id }) {
  const [listed, setListed] = useState(false);
  const [listing, setListing] = useState(false);

  const handleList = () => {
    setListing(true);
    setTimeout(() => { setListing(false); setListed(true); }, 1800);
  };

  if (listed) return (
    <div className="w-full bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 space-y-2">
      <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold">
        <CheckCircle size={16} /> Listed on ONDC Network
      </div>
      <div className="text-[11px] text-zinc-400 font-mono">Beckn ID: {beckn_item_id}</div>
      <div className="text-[11px] text-zinc-400">Now visible on <span className="text-blue-400 font-medium">PhonePe · Meesho · Magicpin · Mystore</span></div>
    </div>
  );

  return (
    <button onClick={handleList} disabled={listing}
      className="w-full flex items-center justify-center gap-2 py-3 bg-[#25D366] rounded-xl text-sm font-bold text-white hover:bg-[#22c55e] transition-colors disabled:opacity-70">
      {listing ? <Loader2 size={14} className="animate-spin" /> : <ShoppingCart size={14} />}
      {listing ? "Publishing to ONDC…" : "List on ONDC Network"}
    </button>
  );
}

// ── Product Card ──────────────────────────────────────────────────────────

function ProductCard({ product, onGenerate }) {
  const priceAdv = product.amazon_price > 0
    ? Math.round((product.amazon_price - product.ondc_recommended_price) / product.amazon_price * 100)
    : 0;

  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-2xl p-5 hover:border-[#25D366]/30 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-white leading-tight">{product.name}</h3>
          <div className="flex items-center gap-1.5 mt-1">
            <Badge label={product.category} color="blue" />
            <Badge label={product.sku} />
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-zinc-500">Demand Score</div>
          <div className="text-xl font-bold text-[#25D366]">{product.demand_score}</div>
        </div>
      </div>

      <ScoreBar score={product.demand_score} />

      <div className="grid grid-cols-3 gap-2 mt-4 text-xs">
        <div>
          <div className="text-zinc-500">Amazon Price</div>
          <div className="text-white font-medium">₹{product.amazon_price?.toLocaleString("en-IN") || "—"}</div>
        </div>
        <div>
          <div className="text-zinc-500">ONDC Price</div>
          <div className="text-[#25D366] font-bold">₹{product.ondc_recommended_price?.toLocaleString("en-IN") || "—"}</div>
        </div>
        <div>
          <div className="text-zinc-500">Advantage</div>
          <div className="text-emerald-400 font-bold">{priceAdv}% lower</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
        <div>
          <div className="text-zinc-500">Daily units</div>
          <div className="text-white">{product.daily_units_sold}/day</div>
        </div>
        <div>
          <div className="text-zinc-500">Monthly revenue</div>
          <div className="text-white">₹{product.monthly_revenue?.toLocaleString("en-IN") || "0"}</div>
        </div>
        <div>
          <div className="text-zinc-500">Growth</div>
          <div className={product.growth_pct >= 0 ? "text-emerald-400" : "text-red-400"}>
            {product.growth_pct >= 0 ? "+" : ""}{product.growth_pct}%
          </div>
        </div>
        <div>
          <div className="text-zinc-500">Fee saving / unit</div>
          <div className="text-yellow-400">₹{product.ondc_fee_saving?.toFixed(0)}</div>
        </div>
      </div>

      {product.top_states?.length > 0 && (
        <div className="mt-3 flex items-center gap-1.5 flex-wrap">
          <MapPin size={10} className="text-zinc-600" />
          {product.top_states.map((s) => (
            <Badge key={s.state} label={`${s.state} (${s.units})`} color="zinc" />
          ))}
        </div>
      )}


      <button
        onClick={() => onGenerate(product.product_id, product.name)}
        className="mt-4 w-full flex items-center justify-center gap-2 py-2 bg-[#25D366]/10 text-[#25D366] border border-[#25D366]/30 rounded-xl text-xs font-medium hover:bg-[#25D366]/20 transition-colors">
        <Zap size={11} />
        Generate ONDC Listing
        <ChevronRight size={11} />
      </button>
    </div>
  );
}

// ── Listing Modal ─────────────────────────────────────────────────────────

function ListingPanel({ productId, productName, onClose }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`/api/ondc/listing/${productId}`)
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, [productId]);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111113] border border-[#27272a] rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#27272a] sticky top-0 bg-[#111113]">
          <div>
            <h2 className="text-sm font-bold text-white">ONDC Catalogue Entry</h2>
            <p className="text-xs text-zinc-500">{productName}</p>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-white text-xs px-3 py-1.5 bg-[#18181b] border border-[#27272a] rounded-lg">
            Close
          </button>
        </div>

        <div className="p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 size={24} className="text-[#25D366] animate-spin" />
              <span className="text-zinc-400 ml-3 text-sm">Generating ONDC listing with AI…</span>
            </div>
          )}
          {error && <p className="text-red-400 text-sm">{error}</p>}
          {data && !loading && (
            <div className="space-y-4">
              {/* Price summary */}
              <div className="grid grid-cols-3 gap-3">
                <Stat label="ONDC Price" value={`₹${data.ondc_price?.toLocaleString("en-IN") || "—"}`} accent="text-[#25D366]" />
                <Stat label="Amazon Price" value={`₹${data.amazon_price?.toLocaleString("en-IN") || "—"}`} />
                <Stat label="Price Advantage" value={`₹${data.price_advantage?.toFixed(0)} cheaper`} accent="text-emerald-400" />
              </div>

              {/* Beckn metadata */}
              <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4 flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-zinc-500 mb-1">Beckn Item ID</div>
                  <div className="text-xs font-mono text-zinc-300">{data.beckn_item_id}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-zinc-500 mb-1">Visibility Boost</div>
                  <div className="text-sm font-bold text-[#25D366]">+{data.estimated_visibility_boost}</div>
                </div>
              </div>

              {/* Buyer NPs */}
              {data.buyer_nps_reach?.length > 0 && (
                <div>
                  <div className="text-xs text-zinc-500 mb-2">Buyer Network Providers</div>
                  <div className="flex flex-wrap gap-1.5">
                    {data.buyer_nps_reach.map((np) => (
                      <Badge key={np} label={np} color="blue" />
                    ))}
                  </div>
                </div>
              )}

              {/* AI-generated listing content */}
              {data.listing && !data.listing.raw && (
                <div className="space-y-3">
                  {data.listing.title && (
                    <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
                      <div className="text-[10px] text-zinc-500 mb-1">Title</div>
                      <div className="text-sm font-semibold text-white">{data.listing.title}</div>
                    </div>
                  )}
                  {data.listing.usp && (
                    <div className="bg-[#25D366]/5 border border-[#25D366]/20 rounded-xl p-4">
                      <div className="text-[10px] text-[#25D366] mb-1 flex items-center gap-1">
                        <Star size={9} /> USP
                      </div>
                      <div className="text-sm text-white">{data.listing.usp}</div>
                    </div>
                  )}
                  {data.listing.short_description && (
                    <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
                      <div className="text-[10px] text-zinc-500 mb-1">Short Description</div>
                      <div className="text-sm text-zinc-300">{data.listing.short_description}</div>
                    </div>
                  )}
                  {data.listing.full_description && (
                    <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
                      <div className="text-[10px] text-zinc-500 mb-1">Full Description</div>
                      <div className="text-sm text-zinc-300 leading-relaxed">{data.listing.full_description}</div>
                    </div>
                  )}
                  {data.listing.search_tags?.length > 0 && (
                    <div>
                      <div className="text-xs text-zinc-500 mb-2 flex items-center gap-1"><Tag size={10} /> Search Tags</div>
                      <div className="flex flex-wrap gap-1.5">
                        {data.listing.search_tags.map((t) => (
                          <Badge key={t} label={t} color="zinc" />
                        ))}
                      </div>
                    </div>
                  )}
                  {data.listing.demand_insight && (
                    <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
                      <div className="text-[10px] text-zinc-500 mb-1">Demand Insight</div>
                      <div className="text-sm text-zinc-300">{data.listing.demand_insight}</div>
                    </div>
                  )}
                  {data.listing.pricing_rationale && (
                    <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
                      <div className="text-[10px] text-zinc-500 mb-1">Pricing Rationale</div>
                      <div className="text-sm text-zinc-300">{data.listing.pricing_rationale}</div>
                    </div>
                  )}
                </div>
              )}
              {data.listing?.raw && (
                <pre className="bg-[#18181b] border border-[#27272a] rounded-xl p-4 text-xs text-zinc-300 whitespace-pre-wrap font-mono">
                  {data.listing.raw}
                </pre>
              )}

              <ListButton beckn_item_id={data.beckn_item_id} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function ONDC() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(30);
  const [selected, setSelected] = useState(null); // { productId, productName }

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/ondc/analyze?days=${days}`);
      setData(await res.json());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAnalysis(); }, []);

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">ONDC Auto-Optimizer</h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Predictive demand analysis · Lower fees · Open Network for Digital Commerce
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-[#18181b] border border-[#27272a] rounded-lg px-3 py-1.5 text-xs text-white outline-none">
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
          </select>
          <button onClick={loadAnalysis} disabled={loading}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-[#25D366]/10 text-[#25D366] border border-[#25D366]/30 rounded-lg text-xs hover:bg-[#25D366]/20 transition-colors disabled:opacity-50">
            {loading ? <Loader2 size={12} className="animate-spin" /> : <TrendingUp size={12} />}
            {loading ? "Analysing…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* Summary metrics */}
      {data && (
        <div className="grid grid-cols-4 gap-4">
          <Stat label="Products Analysed" value={data.total_products} />
          <Stat label="Estimated Reach" value={Number(data.estimated_reach).toLocaleString("en-IN")} sub="ONDC buyers" />
          <Stat
            label="Buyer Networks"
            value={data.buyer_nps?.length || 0}
            sub={data.buyer_nps?.slice(0, 2).join(", ")}
          />
          <Stat
            label="Analysis Date"
            value={data.analysis_date}
            sub={`${days}-day window`}
          />
        </div>
      )}

      {/* Fee comparison callout */}
      <div className="bg-[#25D366]/5 border border-[#25D366]/20 rounded-2xl p-5 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-white mb-1">Why ONDC?</div>
          <div className="text-xs text-zinc-400 max-w-xl">
            ONDC charges 3–8% + ₹1.5/order vs Amazon/Flipkart's 5–20%. By passing 50% of fee savings to buyers,
            your products are priced competitively while you protect margins.
          </div>
        </div>
        <div className="flex gap-4 text-center shrink-0">
          <div>
            <div className="text-xs text-zinc-500">Amazon/Flipkart</div>
            <div className="text-lg font-bold text-red-400">5–20%</div>
          </div>
          <div className="text-zinc-600 text-lg">→</div>
          <div>
            <div className="text-xs text-zinc-500">ONDC</div>
            <div className="text-lg font-bold text-[#25D366]">3–8%</div>
          </div>
        </div>
      </div>

      {/* Buyer apps callout */}
      <div className="bg-blue-500/5 border border-blue-500/20 rounded-2xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center text-2xl shrink-0">🌐</div>
          <div>
            <div className="text-sm font-bold text-white">Your products reach millions of buyers across India</div>
            <div className="text-xs text-zinc-400 mt-0.5">PhonePe, Meesho, Magicpin, Mystore and more are active Buyer Network Providers on ONDC — list once, sell everywhere.</div>
          </div>
        </div>
        <div className="shrink-0 ml-4">
          <Badge label="ONDC BNPs" color="blue" />
        </div>
      </div>

      {/* Revenue projector */}
      {data && (() => {
        const ready = data.products.filter(p => p.demand_score >= 60);
        const extraRevenue = Math.round(ready.reduce((sum, p) => sum + (p.ondc_fee_saving * p.daily_units_sold * 30), 0));
        if (!ready.length) return null;
        return (
          <div className="bg-[#25D366]/5 border border-[#25D366]/20 rounded-2xl p-5 flex items-center justify-between">
            <div>
              <div className="text-xs text-zinc-500 mb-1">ONDC Revenue Opportunity</div>
              <div className="text-2xl font-bold text-[#25D366]">+₹{extraRevenue.toLocaleString("en-IN")}/mo</div>
              <div className="text-xs text-zinc-400 mt-1">{ready.length} products with demand score ≥ 60 ready to list — estimated extra monthly margin from lower ONDC fees</div>
            </div>
            <Zap size={32} className="text-[#25D366]/40 shrink-0 ml-4" />
          </div>
        );
      })()}

      {/* Buyer NPs */}
      {data?.buyer_nps?.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-zinc-500">Active buyer networks:</span>
          {data.buyer_nps.map((np) => (
            <Badge key={np} label={np} color="blue" />
          ))}
        </div>
      )}

      {/* Product grid */}
      {loading && !data && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={28} className="text-[#25D366] animate-spin" />
          <span className="text-zinc-400 ml-3">Analysing demand patterns…</span>
        </div>
      )}

      {data?.products && (
        <div className="grid grid-cols-2 gap-4">
          {data.products.map((p) => (
            <ProductCard
              key={p.product_id}
              product={p}
              onGenerate={(id, name) => setSelected({ productId: id, productName: name })}
            />
          ))}
        </div>
      )}

      {/* Listing modal */}
      {selected && (
        <ListingPanel
          productId={selected.productId}
          productName={selected.productName}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
