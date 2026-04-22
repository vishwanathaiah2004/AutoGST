"use client";
import { useEffect, useState } from "react";
import { transactionsApi } from "@/lib/api";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { Plus, Search, Trash2, Edit3, AlertTriangle, X, ChevronLeft, ChevronRight } from "lucide-react";
import clsx from "clsx";

const fmt = (v: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(v);
const GST_RATES = [0, 0.25, 3, 5, 12, 18, 28];
const GST_TYPES = ["CGST", "SGST", "IGST", "UTGST", "exempt"];

export default function TransactionsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editTxn, setEditTxn] = useState<any>(null);

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<any>({
    defaultValues: { gst_type: "CGST", gst_rate: 18, transaction_type: "expense" }
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: any = { page, size: 15 };
      if (search) params.search = search;
      if (typeFilter) params.transaction_type = typeFilter;
      const r = await transactionsApi.list(params);
      setItems(r.data.items);
      setTotal(r.data.total);
      setPages(r.data.pages);
    } catch {
      toast.error("Failed to load transactions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page, typeFilter]);
  useEffect(() => {
    const t = setTimeout(fetchData, 400);
    return () => clearTimeout(t);
  }, [search]);

  const openCreate = () => { setEditTxn(null); reset({ gst_type: "CGST", gst_rate: 18, transaction_type: "expense" }); setShowModal(true); };
  const openEdit = (txn: any) => {
    setEditTxn(txn);
    reset({ ...txn, transaction_date: txn.transaction_date });
    setShowModal(true);
  };

  const onSubmit = async (data: any) => {
    try {
      if (editTxn) {
        await transactionsApi.update(editTxn.id, data);
        toast.success("Transaction updated");
      } else {
        await transactionsApi.create(data);
        toast.success("Transaction created");
      }
      setShowModal(false);
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.message || "Failed to save");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this transaction?")) return;
    try {
      await transactionsApi.delete(id);
      toast.success("Deleted");
      fetchData();
    } catch { toast.error("Delete failed"); }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Transactions</h1>
          <p className="text-slate-500 text-sm">{total} total records</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Transaction
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Search description, party, invoice..." className="input pl-9" />
        </div>
        <select value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setPage(1); }} className="input w-40">
          <option value="">All Types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                {["Date", "Description", "Party", "Type", "Amount", "GST", "Total", "ML Category", ""].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={9} className="text-center py-12 text-slate-400">Loading…</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={9} className="text-center py-12 text-slate-400">No transactions found</td></tr>
              ) : items.map(txn => (
                <tr key={txn.id} className={clsx("hover:bg-slate-50 transition-colors", txn.is_anomaly && "bg-amber-50/50")}>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{txn.transaction_date}</td>
                  <td className="px-4 py-3 max-w-48">
                    <div className="flex items-center gap-1.5">
                      {txn.is_anomaly && <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" title="Anomaly detected" />}
                      <span className="truncate text-slate-800">{txn.description}</span>
                    </div>
                    {txn.invoice_number && <p className="text-xs text-slate-400">{txn.invoice_number}</p>}
                  </td>
                  <td className="px-4 py-3 text-slate-600 text-xs">{txn.party_name || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={txn.transaction_type === "income" ? "badge-income" : "badge-expense"}>
                      {txn.transaction_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-800 whitespace-nowrap">{fmt(txn.amount)}</td>
                  <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">{fmt(txn.total_gst)} ({txn.gst_rate}%)</td>
                  <td className="px-4 py-3 font-semibold whitespace-nowrap">{fmt(txn.total_amount)}</td>
                  <td className="px-4 py-3 text-xs text-indigo-600">
                    {txn.ml_category && (
                      <span className="bg-indigo-50 px-2 py-0.5 rounded-full">
                        {txn.ml_category} {txn.ml_confidence ? `(${(txn.ml_confidence * 100).toFixed(0)}%)` : ""}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => openEdit(txn)} className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"><Edit3 className="w-3.5 h-3.5" /></button>
                      <button onClick={() => handleDelete(txn.id)} className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
            <p className="text-sm text-slate-500">Page {page} of {pages}</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary py-1.5 px-3 flex items-center gap-1 text-xs disabled:opacity-40">
                <ChevronLeft className="w-3.5 h-3.5" /> Prev
              </button>
              <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages} className="btn-secondary py-1.5 px-3 flex items-center gap-1 text-xs disabled:opacity-40">
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold">{editTxn ? "Edit Transaction" : "New Transaction"}</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="label">Description *</label>
                  <input {...register("description", { required: true })} className="input" placeholder="e.g. Software development services" />
                </div>
                <div>
                  <label className="label">Amount (₹) *</label>
                  <input {...register("amount", { required: true, min: 0.01 })} type="number" step="0.01" className="input" placeholder="10000" />
                </div>
                <div>
                  <label className="label">Date *</label>
                  <input {...register("transaction_date", { required: true })} type="date" className="input" />
                </div>
                <div>
                  <label className="label">Type *</label>
                  <select {...register("transaction_type")} className="input">
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                  </select>
                </div>
                <div>
                  <label className="label">GST Rate (%)</label>
                  <select {...register("gst_rate")} className="input">
                    {GST_RATES.map(r => <option key={r} value={r}>{r}%</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">GST Type</label>
                  <select {...register("gst_type")} className="input">
                    {GST_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Party Name</label>
                  <input {...register("party_name")} className="input" placeholder="Vendor / Customer name" />
                </div>
                <div>
                  <label className="label">Party GSTIN</label>
                  <input {...register("party_gstin")} className="input" placeholder="27AAPFU0939F1ZV" />
                </div>
                <div>
                  <label className="label">Invoice Number</label>
                  <input {...register("invoice_number")} className="input" placeholder="INV-2024-001" />
                </div>
                <div>
                  <label className="label">HSN/SAC Code</label>
                  <input {...register("hsn_sac_code")} className="input" placeholder="9999" />
                </div>
                <div className="col-span-2">
                  <label className="label">Notes</label>
                  <textarea {...register("notes")} className="input" rows={2} placeholder="Optional notes..." />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" className="btn-primary flex-1">{editTxn ? "Update" : "Create"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
