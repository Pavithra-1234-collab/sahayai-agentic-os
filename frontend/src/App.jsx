import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { LayoutDashboard, MessageSquare, Package, Star, BarChart2, Smartphone, TrendingUp, Receipt, Globe } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Products from "./pages/Products";
import Reviews from "./pages/Reviews";
import Analytics from "./pages/Analytics";
import WhatsApp from "./pages/WhatsApp";
import Payments from "./pages/Payments";
import ONDC from "./pages/ONDC";

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/chat", icon: MessageSquare, label: "AI Chat" },
  { to: "/products", icon: Package, label: "Products" },
  { to: "/reviews", icon: Star, label: "Reviews" },
  { to: "/analytics", icon: BarChart2, label: "Analytics" },
  { to: "/payments", icon: Receipt, label: "Payments" },
  { to: "/ondc", icon: Globe, label: "ONDC" },
  { to: "/whatsapp", icon: Smartphone, label: "WhatsApp" },
];

function Sidebar() {
  return (
    <aside className="w-56 shrink-0 bg-[#111113] border-r border-[#27272a] flex flex-col h-screen sticky top-0 z-10">
      <div className="px-5 py-4 border-b border-[#27272a]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#25D366] flex items-center justify-center shadow-lg shadow-[#25D366]/20">
            <TrendingUp size={15} className="text-white" strokeWidth={2.5} />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none tracking-tight">BizManager</div>
            <div className="text-[10px] text-zinc-500 mt-0.5">AI Business Co-pilot</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all ${
                isActive
                  ? "bg-[#25D366]/10 text-[#25D366] font-medium"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              }`
            }
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-[#27272a]">
        <div className="px-2 text-[10px] text-zinc-600 leading-relaxed">
          Powered by Groq<br />LLaMA 3.3 70B · Amazon.in + Flipkart
        </div>
      </div>
    </aside>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex w-full min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/products" element={<Products />} />
            <Route path="/reviews" element={<Reviews />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/ondc" element={<ONDC />} />
            <Route path="/whatsapp" element={<WhatsApp />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
