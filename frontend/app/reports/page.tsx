"use client";
import { useState } from "react";
import { reportsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { FileBarChart2, Download, RefreshCw } from "lucide-react";

const fmt = (v: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(v);

export default function ReportsPage() {
  const [reportType, setReportType] = useState("GSTR-1");
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const r = await reportsApi.gstr({ report_type: reportType, month, year });
      setData(r.data);
    } catch (err: any) {
      toast.error(err.response?.data?.message || "Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = () => {
    const token = localStorage.getItem("token");
    const url = `${process.env.NEXT_PUBLIC_API_URL}/reports/gstr/pdf?report_type=${reportType}&month=${month}&year=${year}`;
    const a = document.createElement("a");
    a.href = url;
    a.download = `${reportType}_${year}_${String(month).padStart(2, "0")}.pdf`;
    document.body.appendChild(a);
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob())
      .then(blob => {
        const blobUrl = URL.createObjectURL(blob);
        a.href = blobUrl;
        a.click();
        URL.revokeObjectURL(blobUrl);
        document.body.removeChild(a);
      })
      .catch(() => toast.error("PDF download failed"));
  };

  const downloadExcel = () => {
    const token = localStorage.getItem("token");
    const url = `${process.env.NEXT_PUBLIC_API_URL}/reports/gstr/excel?report_type=${reportType}&month=${month}&year=${year}`;
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob())
      .then(blob => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${reportType}_${year}_${String(month).padStart(2, "0")}.xlsx`;
        a.click();
      })
      .catch(() => toast.error("Excel download failed"));
  };

  const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const years = [2023, 2024, 2025];

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl lg:text-2xl font-bold text-slate-900">GST Reports</h1>
        <p className="text-slate-500 text-xs lg:text-sm mt-1">Generate GSTR-1 and GSTR-3B simulation reports</p>
      </div>

      {/* Controls — stack on mobile */}
      <div className="card p-4 lg:p-5 flex flex-col sm:flex-row flex-wrap gap-3 lg:gap-4 items-stretch sm:items-end">
        <div className="flex-1 sm:flex-none">
          <label className="label">Report Type</label>
          <select value={reportType} onChange={e => setReportType(e.target.value)} className="input w-full sm:w-36">
            <option>GSTR-1</option>
            <option>GSTR-3B</option>
          </select>
        </div>
        <div className="flex-1 sm:flex-none">
          <label className="label">Month</label>
          <select value={month} onChange={e => setMonth(Number(e.target.value))} className="input w-full sm:w-40">
            {months.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
        </div>
        <div className="flex-1 sm:flex-none">
          <label className="label">Year</label>
          <select value={year} onChange={e => setYear(Number(e.target.value))} className="input w-full sm:w-28">
            {years.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <button onClick={fetchReport} disabled={loading} className="btn-primary flex items-center justify-center gap-2 py-2.5">
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileBarChart2 className="w-4 h-4" />}
          Generate
        </button>
      </div>

      {/* Report Output */}
      {data && (
        <div className="space-y-4">
          {/* Download buttons */}
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <button onClick={downloadPDF} className="btn-secondary flex items-center justify-center gap-2 text-sm">
              <Download className="w-4 h-4" /> Download PDF
            </button>
            <button onClick={downloadExcel} className="btn-secondary flex items-center justify-center gap-2 text-sm">
              <Download className="w-4 h-4" /> Download Excel
            </button>
          </div>

          {/* GSTR-1 Summary */}
          {reportType === "GSTR-1" && data.summary && (
            <>
              {/* Top 3 cards — 1 col mobile, 3 col sm+ */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 lg:gap-4">
                {[
                  { label: "Total Taxable Value", value: fmt(data.summary.total_taxable_value) },
                  { label: "Total Tax", value: fmt(data.summary.total_tax), highlight: true },
                  { label: "B2B Invoices", value: data.b2b_invoices?.length || 0 },
                ].map(c => (
                  <div key={c.label} className={`card p-4 ${c.highlight ? "bg-indigo-50 border-indigo-200" : ""}`}>
                    <p className="text-xs text-slate-500 uppercase tracking-wide">{c.label}</p>
                    <p className="text-xl font-bold text-slate-900 mt-1">{c.value}</p>
                  </div>
                ))}
              </div>

              {/* GST breakdown — 3 col always but smaller text on mobile */}
              <div className="grid grid-cols-3 gap-3 lg:gap-4">
                <div className="card p-3 lg:p-4">
                  <p className="text-xs text-slate-500">CGST</p>
                  <p className="text-base lg:text-lg font-bold text-slate-800 mt-1">{fmt(data.summary.total_cgst)}</p>
                </div>
                <div className="card p-3 lg:p-4">
                  <p className="text-xs text-slate-500">SGST</p>
                  <p className="text-base lg:text-lg font-bold text-slate-800 mt-1">{fmt(data.summary.total_sgst)}</p>
                </div>
                <div className="card p-3 lg:p-4">
                  <p className="text-xs text-slate-500">IGST</p>
                  <p className="text-base lg:text-lg font-bold text-slate-800 mt-1">{fmt(data.summary.total_igst)}</p>
                </div>
              </div>
            </>
          )}

          {/* GSTR-3B Summary */}
          {reportType === "GSTR-3B" && data["6_payment_of_tax"] && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 lg:gap-4">
              {[
                { label: "Output Tax Liability", value: fmt(data["6_payment_of_tax"].total_output_tax) },
                { label: "Input Tax Credit (ITC)", value: fmt(data["6_payment_of_tax"].total_itc) },
                { label: "Net GST Payable", value: fmt(data["6_payment_of_tax"].net_payable), highlight: true },
              ].map(c => (
                <div key={c.label} className={`card p-4 lg:p-5 ${c.highlight ? "bg-red-50 border-red-200" : ""}`}>
                  <p className="text-xs text-slate-500 uppercase tracking-wide">{c.label}</p>
                  <p className="text-xl lg:text-2xl font-bold text-slate-900 mt-1">{c.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* JSON Preview */}
          <div className="card p-4 lg:p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Report JSON Preview</h3>
            <pre className="bg-slate-900 text-slate-300 rounded-lg p-3 lg:p-4 text-xs overflow-auto max-h-64 font-mono">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}