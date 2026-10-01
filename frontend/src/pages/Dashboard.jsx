import { useEffect, useState } from "react";
import { AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { TrendingUp, TrendingDown, ShoppingBag, Package, Bell, AlertTriangle, Zap, IndianRupee, Globe, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

const fmt = (n) => `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const fmtK = (n) => n >= 100000 ? `₹${(n / 100000).toFixed(1)}L` : n >= 1000 ? `₹${(n / 1000).toFixed(1)}K` : `₹${n}`;

function MetricCard({ title, value, sub, icon: Icon, trend, color = "zinc" }) {
  const colors = {
    green: "text-[#25D366] bg-[#25D366]/10",
    yellow: "text-yellow-400 bg-yellow-400/10",
    red: "text-red-400 bg-red-400/10",
    blue: "text-blue-400 bg-blue-400/10",
    zinc: "text-zinc-400 bg-zinc-400/10",
  };
  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-5">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-zinc-500 font-medium uppercase tracking-wide">{title}</span>
        <span className={`p-1.5 rounded-lg ${colors[color]}`}>
          <Icon size={14} />
        </span>
      </div>
      <div className="text-2xl font-bold text-white tracking-tight mb-1">{value}</div>
      {sub && (
        <div className={`flex items-center gap-1 text-xs ${trend === "up" ? "text-[#25D366]" : trend === "down" ? "text-red-400" : "text-zinc-500"}`}>
          {trend === "up" && <TrendingUp size={11} />}
          {trend === "down" && <TrendingDown size={11} />}
          {sub}
        </div>
      )}
    </div>
  );
}

const PLATFORM_COLORS = ["#FF9900", "#F7D000"];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ondcData, setOndcData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("/api/dashboard")
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
    fetch("/api/ondc/analyze?days=30")
      .then((r) => r.json())
      .then((d) => setOndcData(d))
      .catch(() => {});
  }, []);

  if (loading) return (
    <div className="p-8 space-y-4">
      <div className="h-8 bg-[#18181b] rounded-lg w-48 animate-pulse" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-[#18181b] rounded-xl animate-pulse" />)}
      </div>
    </div>
  );

  if (!data) return <div className="p-8 text-zinc-500">Failed to load dashboard.</div>;

  const { metrics, daily_revenue, top_products, alerts, low_stock } = data;
  const platformData = [
    { name: "Amazon.in", value: metrics.amazon_revenue },
    { name: "Flipkart", value: metrics.flipkart_revenue },
  ];

  const revGrowth = metrics.revenue_growth_pct;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Business Dashboard</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Last 30 days performance</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Total Revenue"
          value={fmtK(metrics.total_revenue)}
          sub={`${revGrowth > 0 ? "+" : ""}${revGrowth}% vs prev period`}
          icon={IndianRupee}
          trend={revGrowth > 0 ? "up" : "down"}
          color="green"
        />
        <MetricCard
          title="Total Orders"
          value={metrics.total_orders.toLocaleString("en-IN")}
          sub={`AOV ${fmt(metrics.avg_order_value)}`}
          icon={ShoppingBag}
          color="blue"
        />
        <MetricCard
          title="Active Products"
          value={metrics.active_products}
          sub="on Amazon & Flipkart"
          icon={Package}
          color="zinc"
        />
        <MetricCard
          title="Active Alerts"
          value={metrics.active_alerts}
          sub={`${metrics.urgent_alerts} urgent`}
          icon={Bell}
          trend={metrics.urgent_alerts > 0 ? "down" : null}
          color={metrics.urgent_alerts > 0 ? "red" : "zinc"}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Revenue chart */}
        <div className="col-span-2 bg-[#18181b] border border-[#27272a] rounded-xl p-5">
          <div className="text-sm font-semibold text-white mb-4">Revenue — Last 30 Days</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={daily_revenue} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#25D366" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#25D366" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false}
                tickFormatter={(v) => v.slice(5)} interval={4} />
              <YAxis tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false}
                tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} width={45} />
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: "#71717a" }}
                formatter={(v) => [fmt(v), "Revenue"]}
              />
              <Area type="monotone" dataKey="revenue" stroke="#25D366" strokeWidth={2} fill="url(#revGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Platform donut */}
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-5">
          <div className="text-sm font-semibold text-white mb-4">Platform Split</div>
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={platformData} cx="50%" cy="50%" innerRadius={45} outerRadius={65}
                dataKey="value" strokeWidth={0}>
                {platformData.map((_, i) => <Cell key={i} fill={PLATFORM_COLORS[i]} />)}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, fontSize: 12 }}
                formatter={(v) => fmt(v)}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-2">
            {platformData.map((p, i) => (
              <div key={p.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: PLATFORM_COLORS[i] }} />
                  <span className="text-zinc-400">{p.name}</span>
                </div>
                <span className="text-white font-medium">{fmtK(p.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ONDC Opportunity Banner */}
      {ondcData && (() => {
        const ready = ondcData.products?.filter(p => p.demand_score >= 60) || [];
        const extraRevenue = Math.round(ready.reduce((sum, p) => sum + (p.ondc_fee_saving * p.daily_units_sold * 30), 0));
        if (!ready.length) return null;
        return (
          <button onClick={() => navigate("/ondc")}
            className="w-full bg-[#25D366]/5 border border-[#25D366]/20 rounded-xl p-4 flex items-center justify-between hover:bg-[#25D366]/10 transition-colors text-left">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#25D366]/20 flex items-center justify-center shrink-0">
                <Globe size={16} className="text-[#25D366]" />
              </div>
              <div>
                <div className="text-sm font-semibold text-white">
                  {ready.length} products ready for ONDC — potential <span className="text-[#25D366]">+₹{extraRevenue.toLocaleString("en-IN")}/mo</span>
                </div>
                <div className="text-xs text-zinc-500 mt-0.5">List on PhonePe, Meesho & Magicpin via ONDC at just 3% fees vs Amazon's 18%</div>
              </div>
            </div>
            <ChevronRight size={16} className="text-[#25D366] shrink-0 ml-2" />
          </button>
        );
      })()}

      {/* Bottom row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Top products */}
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-5">
          <div className="text-sm font-semibold text-white mb-4">Top Products</div>
          <div className="space-y-3">
            {top_products.map((p, i) => {
              const max = top_products[0]?.revenue || 1;
              const pct = Math.round((p.revenue / max) * 100);
              return (
                <div key={i}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-zinc-300 truncate max-w-[70%]">{p.name}</span>
                    <span className="text-white font-medium">{fmtK(p.revenue)}</span>
                  </div>
                  <div className="h-1.5 bg-[#27272a] rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-[#25D366]" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={14} className="text-[#25D366]" />
            <span className="text-sm font-semibold text-white">AI Insights</span>
          </div>
          <div className="space-y-2.5">
            {low_stock.slice(0, 2).map((item, i) => (
              <div key={i} className={`flex gap-3 p-3 rounded-lg text-xs ${item.status === "critical" ? "bg-red-500/10 border border-red-500/20" : "bg-yellow-500/10 border border-yellow-500/20"}`}>
                <AlertTriangle size={13} className={item.status === "critical" ? "text-red-400 shrink-0 mt-0.5" : "text-yellow-400 shrink-0 mt-0.5"} />
                <span className="text-zinc-300">
                  <span className="text-white font-medium">{item.name}</span>
                  {" "}has only {item.status === "critical" ? "🔴" : "🟡"} <span className="font-medium">{item.stock_qty} units</span> left — ~{item.days_until_stockout} days of stock.
                </span>
              </div>
            ))}
            {alerts.filter(a => a.type === "pricing_opportunity").slice(0, 1).map((a, i) => (
              <div key={i} className="flex gap-3 p-3 rounded-lg text-xs bg-[#25D366]/10 border border-[#25D366]/20">
                <TrendingUp size={13} className="text-[#25D366] shrink-0 mt-0.5" />
                <span className="text-zinc-300">{a.message}</span>
              </div>
            ))}
            {revGrowth > 10 && (
              <div className="flex gap-3 p-3 rounded-lg text-xs bg-blue-500/10 border border-blue-500/20">
                <TrendingUp size={13} className="text-blue-400 shrink-0 mt-0.5" />
                <span className="text-zinc-300">Revenue grew <span className="text-white font-medium">+{revGrowth}%</span> vs the previous period. Strong momentum!</span>
              </div>
            )}
            <div className="flex gap-3 p-3 rounded-lg text-xs bg-purple-500/10 border border-purple-500/20">
              <Zap size={13} className="text-purple-400 shrink-0 mt-0.5" />
              <span className="text-zinc-300">Festival season approaching — stock up 30% extra for <span className="text-white font-medium">Diwali & Amazon Great Indian Festival</span>.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
