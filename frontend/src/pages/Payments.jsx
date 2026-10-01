import { useState } from "react";
import {
  FileText, Upload, CheckCircle, Building2, IndianRupee,
  Loader2, Receipt
} from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────────────────

function Stat({ label, value, sub }) {
  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
      <div className="text-xs text-zinc-500 mb-1">{label}</div>
      <div className="text-lg font-bold text-white">{value}</div>
      {sub && <div className="text-[11px] text-zinc-500 mt-0.5">{sub}</div>}
    </div>
  );
}

function Badge({ label, color = "zinc" }) {
  const cls = {
    green: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    yellow: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    zinc: "bg-zinc-800 text-zinc-400 border-zinc-700",
  }[color] || "bg-zinc-800 text-zinc-400 border-zinc-700";
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium border ${cls}`}>
      {label}
    </span>
  );
}

// ── Section: Invoice Scanner ──────────────────────────────────────────────

function InvoiceScanner({ onScanned }) {
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);

  const loadDemo = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/invoice/demo");
      const data = await res.json();
      onScanned(data);
    } finally {
      setLoading(false);
    }
  };

  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append("image", file);
      const res = await fetch("/api/invoice/scan", { method: "POST", body: form });
      const data = await res.json();
      onScanned(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Receipt size={16} className="text-[#25D366]" />
        <h2 className="text-sm font-semibold text-white">Invoice Scanner (OCR)</h2>
        <Badge label="Groq Vision" color="blue" />
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]); }}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
          ${dragging ? "border-[#25D366]/60 bg-[#25D366]/5" : "border-[#27272a] hover:border-zinc-600"}`}
        onClick={() => document.getElementById("inv-upload").click()}
      >
        <input id="inv-upload" type="file" accept="image/*" className="hidden"
          onChange={(e) => handleFile(e.target.files[0])} />
        <Upload size={28} className="mx-auto text-zinc-600 mb-2" />
        <p className="text-sm text-zinc-400">Drop invoice image or click to upload</p>
        <p className="text-xs text-zinc-600 mt-1">Supports JPG, PNG, PDF screenshots</p>
      </div>

      <div className="mt-3 flex justify-center">
        <button onClick={loadDemo} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-[#25D366]/10 text-[#25D366] border border-[#25D366]/30 rounded-lg text-sm hover:bg-[#25D366]/20 transition-colors disabled:opacity-50">
          {loading ? <Loader2 size={13} className="animate-spin" /> : <FileText size={13} />}
          {loading ? "Processing…" : "Load Demo Invoice"}
        </button>
      </div>
    </div>
  );
}

// ── Section: Invoice Details ───────────────────────────────────────────────

function InvoiceDetails({ invoice, onFile }) {
  const [filing, setFiling] = useState(false);
  const [gstnResult, setGstnResult] = useState(null);

  const fileGstn = async () => {
    setFiling(true);
    try {
      const res = await fetch("/api/invoice/gstn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(invoice),
      });
      const data = await res.json();
      setGstnResult(data);
      onFile(data);
    } finally {
      setFiling(false);
    }
  };

  const fmt = (n) => n ? `₹${Number(n).toLocaleString("en-IN")}` : "—";

  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText size={16} className="text-[#25D366]" />
          <h2 className="text-sm font-semibold text-white">Invoice Details</h2>
        </div>
        <Badge label={invoice.status || "scanned"} color="green" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Stat label="Invoice No." value={invoice.invoice_number || "—"} />
        <Stat label="Invoice Date" value={invoice.invoice_date || "—"} />
        <Stat label="Seller" value={invoice.seller_name || "—"} sub={invoice.seller_gstin} />
        <Stat label="Buyer" value={invoice.buyer_name || "—"} sub={invoice.buyer_gstin} />
        <Stat label="Total Amount" value={fmt(invoice.total_amount)} sub={`GST: ${fmt(invoice.total_gst)}`} />
        <Stat label="Due Date" value={invoice.due_date || "—"} sub={invoice.payment_terms} />
      </div>

      {invoice.line_items?.length > 0 && (
        <div>
          <div className="text-xs text-zinc-500 mb-2">Line Items</div>
          <div className="space-y-1.5">
            {invoice.line_items.map((item, i) => (
              <div key={i} className="flex justify-between items-center bg-[#111113] rounded-lg px-3 py-2 text-xs">
                <span className="text-zinc-300">{item.description}</span>
                <span className="text-zinc-500">{item.quantity} × {fmt(item.rate)}</span>
                <span className="text-white font-medium">{fmt(item.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!gstnResult ? (
        <button onClick={fileGstn} disabled={filing}
          className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#25D366] rounded-xl text-sm font-semibold text-white hover:bg-[#22c55e] transition-colors disabled:opacity-50">
          {filing ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
          {filing ? "Filing to GSTN…" : "File e-Invoice to GSTN IRP"}
        </button>
      ) : (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold">
            <CheckCircle size={14} /> e-Invoice Registered Successfully
          </div>
          <div className="text-xs text-zinc-400 font-mono break-all">IRN: {gstnResult.irn}</div>
          <div className="text-xs text-zinc-400">Ack No: {gstnResult.ack_no} · {gstnResult.ack_date}</div>
          {gstnResult.eway_bill && (
            <div className="text-xs text-yellow-400">E-Way Bill: {gstnResult.eway_bill.number} (valid till {gstnResult.eway_bill.valid_till})</div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Section: TReDS Financing ───────────────────────────────────────────────

function TReDSOffers({ invoice, irn }) {
  const [loading, setLoading] = useState(false);
  const [offers, setOffers] = useState(null);

  const fetchOffers = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/invoice/treds", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ invoice_data: invoice, irn }),
      });
      const data = await res.json();
      setOffers(data);
    } finally {
      setLoading(false);
    }
  };

  const fmt = (n) => `₹${Number(n).toLocaleString("en-IN")}`;

  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Building2 size={16} className="text-[#25D366]" />
        <h2 className="text-sm font-semibold text-white">TReDS Invoice Discounting</h2>
        <Badge label="RBI Regulated" color="yellow" />
      </div>

      {!offers ? (
        <div className="text-center py-6">
          <p className="text-xs text-zinc-500 mb-4">Get instant financing from SBI, HDFC, Axis, ICICI, Kotak via RXIL / M1Xchange / NTREBIA</p>
          <button onClick={fetchOffers} disabled={loading || !irn}
            className="flex items-center gap-2 mx-auto px-5 py-2.5 bg-[#25D366]/10 text-[#25D366] border border-[#25D366]/30 rounded-xl text-sm hover:bg-[#25D366]/20 transition-colors disabled:opacity-40">
            {loading ? <Loader2 size={13} className="animate-spin" /> : <IndianRupee size={13} />}
            {loading ? "Fetching bids…" : "Get Financing Offers"}
          </button>
          {!irn && <p className="text-[11px] text-zinc-600 mt-2">File e-invoice first to get IRN</p>}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2 mb-2">
            <Badge label={`${offers.offers.length} financiers bid`} color="green" />
            <span className="text-xs text-zinc-500">Invoice: {fmt(offers.invoice_amount)}</span>
          </div>
          {offers.offers.map((o, i) => (
            <div key={i} className={`rounded-xl p-3.5 border ${i === 0 ? "border-[#25D366]/40 bg-[#25D366]/5" : "border-[#27272a] bg-[#111113]"}`}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-sm font-semibold text-white">{o.financier}</span>
                  <span className="text-[11px] text-zinc-500 ml-2">{o.platform}</span>
                </div>
                <div className="flex items-center gap-2">
                  {i === 0 && <Badge label="Best Offer" color="green" />}
                  <span className="text-sm font-bold text-[#25D366]">{o.annual_rate_pct}% p.a.</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <span className="text-zinc-500">Advance ({o.advance_rate_pct}%)</span>
                  <div className="text-white font-medium">{fmt(o.advance_amount)}</div>
                </div>
                <div>
                  <span className="text-zinc-500">Discount cost</span>
                  <div className="text-red-400 font-medium">-{fmt(o.discount_cost)}</div>
                </div>
                <div>
                  <span className="text-zinc-500">Net proceeds</span>
                  <div className="text-emerald-400 font-bold">{fmt(o.net_proceeds)}</div>
                </div>
              </div>
              <div className="text-[10px] text-zinc-600 mt-1">{o.tenor_days} days · maturity {o.maturity_date}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function Payments() {
  const [invoice, setInvoice] = useState(null);
  const [irn, setIrn] = useState("");

  const handleScanned = (data) => {
    setInvoice(data);
    setIrn("");
  };

  const handleFiled = (gstnResult) => {
    setIrn(gstnResult.irn || "");
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-white">Smart Invoicing & Financing</h1>
        <p className="text-sm text-zinc-500 mt-0.5">OCR · GSTN e-Invoice · TReDS Discounting</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          <InvoiceScanner onScanned={handleScanned} />
          {invoice && <InvoiceDetails invoice={invoice} onFile={handleFiled} />}
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {invoice && <TReDSOffers invoice={invoice} irn={irn} />}
          {!invoice && (
            <div className="bg-[#18181b] border border-[#27272a] rounded-2xl p-8 text-center">
              <FileText size={36} className="mx-auto text-zinc-700 mb-3" />
              <p className="text-sm text-zinc-500">Scan or load a demo invoice to get started</p>
              <p className="text-xs text-zinc-600 mt-2">TReDS offers and UPI links will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
