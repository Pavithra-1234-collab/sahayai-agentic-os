import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { BarChart2, Loader2, FileText, TrendingUp, TrendingDown } from "lucide-react";

const fmt = (n) => `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const fmtK = (n) => n >= 100000 ? `₹${(n / 100000).toFixed(1)}L` : n >= 1000 ? `₹${(n / 1000).toFixed(1)}K` : `₹${n}`;
const PLATFORM_COLORS = ["#FF9900", "#F7D000"];

export default function Analytics() {
  const [data, setData] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/analytics?days=${days}`).then(r => r.json()).then(d => { setData(d); setLoading(false); });
  }, [days]);

  const generateReport = async () => {
    setGenerating(true);
    try {
      const res = await fetch("/api/analytics/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days }),
      });
      setReport((await res.json()).report);
    } finally { setGenerating(false); }
  };

  if (loading) return (
    <div className="p-6 space-y-4">
      <div className="h-8 bg-[#18181b] rounded w-40 animate-pulse" />
      <div className="grid grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-[#18181b] rounded-xl animate-pulse" />)}</div>
    </div>
  );

  const dailyData = Object.entries(data?.daily_revenue || {}).map(([date, revenue]) => ({ date: date.slice(5), revenue }));
  const platformData = [
    { name: "Amazon.in", value: data?.amazon_revenue || 0 },
    { name: "Flipkart", value: data?.flipkart_revenue || 0 },
  ];
  const growth = data?.revenue_growth_pct || 0;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2"><BarChart2 size={20} />Analytics</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Deep dive into your sales performance</p>
        </div>
        <div className="flex gap-2">
          <select value={days} onChange={e => setDays(Number(e.target.value))}
            className="px-3 py-2 bg-[#18181b] border border-[#27272a] text-sm text-zinc-300 rounded-lg outline-none">
            {[7, 14, 30, 60, 90].map(d => <option key={d} value={d}>Last {d} days</option>)}
          </select>
          <button onClick={generateReport} disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-[#25D366] text-white text-sm font-medium rounded-lg hover:bg-[#22c55e] transition-colors disabled:opacity-60">
            {generating ? <Loader2 size={13} className="animate-spin" /> : <FileText size={13} />}
            {generating ? "Generating..." : "AI Report"}
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Revenue", value: fmtK(data.total_revenue), sub: `${growth > 0 ? "+" : ""}${growth}% growth`, trend: growth > 0 ? "up" : "down" },
          { label: "Total Orders", value: data.total_orders?.toLocaleString("en-IN"), sub: `AOV ${fmt(data.avg_order_value)}` },
          { label: "Return Rate", value: `${data.return_rate_pct}%`, sub: "of orders returned", trend: data.return_rate_pct > 10 ? "down" : null },
          { label: "Amazon Revenue", value: fmtK(data.amazon_revenue), sub: `Flipkart: ${fmtK(data.flipkart_revenue)}` },
        ].map(({ label, value, sub, trend }) => (
          <div key={label} className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
            <div className="text-[10px] text-zinc-500 uppercase tracking-wide mb-2">{label}</div>
            <div className="text-xl font-bold text-white">{value}</div>
            {sub && <div className={`flex items-center gap-1 text-xs mt-1 ${trend === "up" ? "text-[#25D366]" : trend === "down" ? "text-red-400" : "text-zinc-500"}`}>
              {trend === "up" && <TrendingUp size={10} />}{trend === "down" && <TrendingDown size={10} />}{sub}
            </div>}
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-[#18181b] border border-[#27272a] rounded-xl p-5">
          <div className="text-sm font-semibold text-white mb-4">Daily Revenue</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={dailyData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} interval={4} />
              <YAxis tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false}
                tickFormatter={v => `₹${(v / 1000).toFixed(0)}K`} width={45} />
              <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, fontSize: 12 }}
                formatter={v => [fmt(v), "Revenue"]} />
              <Bar dataKey="revenue" fill="#25D366" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-5">
          <div className="text-sm font-semibold text-white mb-3">Platform Split</div>
          <ResponsiveContainer width="100%" height={130}>
            <PieChart>
              <Pie data={platformData} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value" strokeWidth={0}>
                {platformData.map((_, i) => <Cell key={i} fill={PLATFORM_COLORS[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, fontSize: 12 }} formatter={v => fmt(v)} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-1">
            {platformData.map((p, i) => (
              <div key={p.name} className="flex justify-between text-xs">
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full" style={{ background: PLATFORM_COLORS[i] }} /><span className="text-zinc-400">{p.name}</span></div>
                <span className="text-white font-medium">{fmtK(p.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top products + states */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-5">
          <div className="text-sm font-semibold text-white mb-3">🏆 Top Products</div>
          {(data.top_products || []).map((p, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-[#27272a] last:border-0">
              <span className="text-xs text-zinc-300 truncate max-w-[65%]"><span className="text-zinc-600 mr-2">{i + 1}.</span>{p.name}</span>
              <span className="text-xs font-medium text-white">{fmtK(p.revenue)}</span>
            </div>
          ))}
        </div>
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-5">
          <div className="text-sm font-semibold text-white mb-3">📍 Top Customer States</div>
          {(data.top_states || []).map((s, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-[#27272a] last:border-0">
              <span className="text-xs text-zinc-300">{s.state}</span>
              <span className="text-xs text-zinc-500">{s.orders} orders</span>
            </div>
          ))}
        </div>
      </div>

      {/* AI Report */}
      {report && (
        <div className="bg-[#18181b] border border-[#25D366]/20 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <FileText size={14} className="text-[#25D366]" />
            <span className="text-sm font-semibold text-white">AI-Generated Report</span>
          </div>
          <div className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{report}</div>
        </div>
      )}
    </div>
  );
}
