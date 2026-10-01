import { useState, useEffect } from "react";
import { Package, Zap, ChevronDown, ChevronUp, Loader2, Tag } from "lucide-react";

const fmt = (n) => `₹${Number(n).toLocaleString("en-IN")}`;

function StockBadge({ qty, threshold }) {
  if (qty <= 0) return <span className="px-2 py-0.5 text-[10px] font-semibold bg-red-500/20 text-red-400 rounded-full">Out of Stock</span>;
  if (qty <= threshold / 2) return <span className="px-2 py-0.5 text-[10px] font-semibold bg-red-500/15 text-red-400 rounded-full">Critical: {qty}</span>;
  if (qty <= threshold) return <span className="px-2 py-0.5 text-[10px] font-semibold bg-yellow-500/15 text-yellow-400 rounded-full">Low: {qty}</span>;
  return <span className="px-2 py-0.5 text-[10px] font-semibold bg-[#25D366]/10 text-[#25D366] rounded-full">{qty} units</span>;
}

function ListingResult({ listing }) {
  const [tab, setTab] = useState("amazon");
  if (!listing) return null;

  const amz = listing.amazon || {};
  const fk = listing.flipkart || {};
  const kwds = listing.seo_keywords || [];

  if (listing.raw) return (
    <div className="mt-4 p-4 bg-[#0f0f11] rounded-xl border border-[#27272a] text-sm text-zinc-300 whitespace-pre-wrap">{listing.raw}</div>
  );

  return (
    <div className="mt-4">
      <div className="flex gap-1 mb-3">
        {["amazon", "flipkart", "keywords"].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${tab === t ? "bg-[#27272a] text-white" : "text-zinc-500 hover:text-zinc-300"}`}>
            {t === "amazon" ? "🟠 Amazon" : t === "flipkart" ? "🟡 Flipkart" : "🔍 SEO Keywords"}
          </button>
        ))}
      </div>

      {tab === "amazon" && (
        <div className="space-y-3 text-sm">
          <div><div className="text-[10px] text-zinc-500 mb-1 uppercase tracking-wide">Title</div>
            <div className="p-3 bg-[#0f0f11] rounded-lg border border-[#27272a] text-zinc-200">{amz.title}</div></div>
          <div><div className="text-[10px] text-zinc-500 mb-1 uppercase tracking-wide">Bullet Points</div>
            <ul className="space-y-1">
              {(amz.bullet_points || []).map((b, i) => <li key={i} className="flex gap-2 text-zinc-300"><span className="text-[#25D366] shrink-0">•</span>{b}</li>)}
            </ul></div>
          {amz.backend_keywords && <div><div className="text-[10px] text-zinc-500 mb-1 uppercase tracking-wide">Backend Keywords</div>
            <div className="p-2 bg-[#0f0f11] rounded-lg border border-[#27272a] font-mono text-xs text-zinc-400">{amz.backend_keywords}</div></div>}
        </div>
      )}
      {tab === "flipkart" && (
        <div className="space-y-3 text-sm">
          <div><div className="text-[10px] text-zinc-500 mb-1 uppercase tracking-wide">Title</div>
            <div className="p-3 bg-[#0f0f11] rounded-lg border border-[#27272a] text-zinc-200">{fk.title}</div></div>
          <div><div className="text-[10px] text-zinc-500 mb-1 uppercase tracking-wide">Highlights</div>
            <ul className="space-y-1">
              {(fk.highlights || []).map((h, i) => <li key={i} className="flex gap-2 text-zinc-300"><span className="text-yellow-400 shrink-0">•</span>{h}</li>)}
            </ul></div>
          {fk.description && <div><div className="text-[10px] text-zinc-500 mb-1 uppercase tracking-wide">Description</div>
            <div className="p-3 bg-[#0f0f11] rounded-lg border border-[#27272a] text-zinc-300 leading-relaxed">{fk.description}</div></div>}
        </div>
      )}
      {tab === "keywords" && (
        <div className="flex flex-wrap gap-2">
          {kwds.map((kw, i) => <span key={i} className="px-2.5 py-1 bg-[#27272a] text-zinc-300 rounded-lg text-xs flex items-center gap-1"><Tag size={10} />{kw}</span>)}
        </div>
      )}
    </div>
  );
}

function ProductCard({ product }) {
  const [expanded, setExpanded] = useState(false);
  const [listing, setListing] = useState(null);
  const [generating, setGenerating] = useState(false);
  const margin = Math.round(((product.amazon_price - product.cost_price * 1.18) / product.amazon_price) * 100);

  const generateListing = async () => {
    setGenerating(true);
    try {
      const res = await fetch("/api/listing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_name: product.name, category: product.category, cost_price: product.cost_price }),
      });
      setListing(await res.json());
      setExpanded(true);
    } catch { alert("Failed to generate listing"); }
    finally { setGenerating(false); }
  };

  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-xl overflow-hidden">
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] px-2 py-0.5 bg-[#27272a] text-zinc-400 rounded-full">{product.category}</span>
              <StockBadge qty={product.stock_qty} threshold={product.reorder_threshold} />
            </div>
            <h3 className="text-sm font-semibold text-white truncate">{product.name}</h3>
            <p className="text-xs text-zinc-500 mt-0.5">{product.sku}</p>
          </div>
          <div className="text-right shrink-0">
            <div className="text-sm font-bold text-white">{fmt(product.amazon_price)}</div>
            <div className="text-xs text-zinc-500">🟠 Amazon</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-[#27272a]">
          <div><div className="text-[10px] text-zinc-600">Flipkart</div><div className="text-xs font-medium text-zinc-300">{fmt(product.flipkart_price)}</div></div>
          <div><div className="text-[10px] text-zinc-600">Cost</div><div className="text-xs font-medium text-zinc-300">{fmt(product.cost_price)}</div></div>
          <div><div className="text-[10px] text-zinc-600">Margin</div><div className={`text-xs font-medium ${margin > 30 ? "text-[#25D366]" : "text-yellow-400"}`}>{margin}%</div></div>
        </div>

        <div className="flex gap-2 mt-3">
          <button onClick={generateListing} disabled={generating}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-[#25D366]/10 border border-[#25D366]/20 text-[#25D366] text-xs font-medium rounded-lg hover:bg-[#25D366]/20 transition-colors disabled:opacity-50">
            {generating ? <Loader2 size={11} className="animate-spin" /> : <Zap size={11} />}
            {generating ? "Generating..." : "Optimise Listing"}
          </button>
          <button onClick={() => setExpanded(!expanded)}
            className="px-3 py-2 bg-[#27272a] text-zinc-400 rounded-lg hover:text-white transition-colors">
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {expanded && listing && (
        <div className="px-4 pb-4 border-t border-[#27272a] pt-4">
          <ListingResult listing={listing} />
        </div>
      )}
    </div>
  );
}

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newListing, setNewListing] = useState(null);
  const [form, setForm] = useState({ product_name: "", category: "Electronics", features: "", cost_price: "" });
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetch("/api/products").then(r => r.json()).then(d => { setProducts(d.products); setLoading(false); });
  }, []);

  const generateNew = async (e) => {
    e.preventDefault();
    setGenerating(true);
    try {
      const res = await fetch("/api/listing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, cost_price: Number(form.cost_price) || 0 }),
      });
      setNewListing(await res.json());
    } finally { setGenerating(false); }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2"><Package size={20} />Products</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Manage listings and optimise for Amazon & Flipkart</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-44 bg-[#18181b] rounded-xl animate-pulse" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {products.map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      )}

      {/* New listing generator */}
      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-5">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><Zap size={14} className="text-[#25D366]" />Generate New Listing</h2>
        <form onSubmit={generateNew} className="grid grid-cols-2 gap-3">
          <input required value={form.product_name} onChange={e => setForm(f => ({...f, product_name: e.target.value}))}
            placeholder="Product Name *" className="col-span-2 px-3 py-2.5 bg-[#0f0f11] border border-[#27272a] rounded-lg text-sm text-white placeholder-zinc-600 outline-none focus:border-[#25D366]/50" />
          <select value={form.category} onChange={e => setForm(f => ({...f, category: e.target.value}))}
            className="px-3 py-2.5 bg-[#0f0f11] border border-[#27272a] rounded-lg text-sm text-white outline-none focus:border-[#25D366]/50">
            {["Electronics", "Home & Kitchen", "Accessories", "Sports & Outdoors", "Fashion"].map(c => <option key={c}>{c}</option>)}
          </select>
          <input type="number" value={form.cost_price} onChange={e => setForm(f => ({...f, cost_price: e.target.value}))}
            placeholder="Cost Price (₹)" className="px-3 py-2.5 bg-[#0f0f11] border border-[#27272a] rounded-lg text-sm text-white placeholder-zinc-600 outline-none focus:border-[#25D366]/50" />
          <textarea value={form.features} onChange={e => setForm(f => ({...f, features: e.target.value}))}
            placeholder="Key features (optional)..." rows={2}
            className="col-span-2 px-3 py-2.5 bg-[#0f0f11] border border-[#27272a] rounded-lg text-sm text-white placeholder-zinc-600 outline-none focus:border-[#25D366]/50 resize-none" />
          <button type="submit" disabled={generating}
            className="col-span-2 flex items-center justify-center gap-2 py-2.5 bg-[#25D366] text-white text-sm font-medium rounded-lg hover:bg-[#22c55e] transition-colors disabled:opacity-50">
            {generating ? <><Loader2 size={14} className="animate-spin" />Generating...</> : <><Zap size={14} />Generate Listing</>}
          </button>
        </form>
        {newListing && <ListingResult listing={newListing} />}
      </div>
    </div>
  );
}
