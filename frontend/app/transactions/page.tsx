"use client";
import { useEffect, useState } from "react";
import { transactionsApi } from "@/lib/api";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import {
  Plus, Search, Trash2, Edit3, X, ChevronLeft, ChevronRight,
} from "lucide-react";

const fmt = (v: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(v);

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

  const { register, handleSubmit, reset, formState: { errors } } = useForm<any>({
    defaultValues: { gst_type: "CGST", gst_rate: 18, transaction_type: "expense" },
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

  const openCreate = () => {
    setEditTxn(null);
    reset({ gst_type: "CGST", gst_rate: 18, transaction_type: "expense" });
    setShowModal(true);
  };

  const openEdit = (txn: any) => {
    setEditTxn(txn);
    reset({ ...txn });
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
    } catch {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="space-y-6">

      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Transactions</h1>
          <p className="text-slate-500 text-sm mt-0.5">{total} total records</p>
        </div>
        <button
          onClick={openCreate}
          className="btn-primary flex items-center gap-2 px-4 py-2.5 text-sm"
        >
          <Plus className="w-4 h-4" />
          Add Transaction
        </button>
      </div>

      {/* FILTERS */}
      <div className="card p-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search description, party, invoice..."
            className="input pl-9 w-full"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
          className="input sm:w-40"
        >
          <option value="">All Types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
      </div>

      {/* TABLE */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Description</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Party</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Amount</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">GST</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Total</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">ML Category</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-slate-400">
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600" />
                      Loading...
                    </div>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-slate-400">No transactions found</td>
                </tr>
              ) : (
                items.map((txn) => (
                  <tr key={txn.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{txn.transaction_date}</td>
                    <td className="px-4 py-3 text-slate-900 font-medium max-w-[180px] truncate">{txn.description}</td>
                    <td className="px-4 py-3 text-slate-500 max-w-[140px] truncate">{txn.party_name || "—"}</td>
                    <td className="px-4 py-3">
                      <span className={txn.transaction_type === "income" ? "badge-income" : "badge-expense"}>
                        {txn.transaction_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-900 whitespace-nowrap">{fmt(txn.amount)}</td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                      {txn.gst_amount ? `${fmt(txn.gst_amount)} (${txn.gst_rate}%)` : "—"}
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-900 whitespace-nowrap">
                      {fmt(txn.total_amount || txn.amount)}
                    </td>
                    <td className="px-4 py-3">
                      {txn.ml_category ? (
                        <span className="text-indigo-600 text-xs font-medium">{txn.ml_category}</span>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button onClick={() => openEdit(txn)} className="text-slate-400 hover:text-indigo-600 transition-colors">
                          <Edit3 size={15} />
                        </button>
                        <button onClick={() => handleDelete(txn.id)} className="text-slate-400 hover:text-red-500 transition-colors">
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* PAGINATION */}
        {pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
            <p className="text-sm text-slate-500">Page {page} of {pages}</p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary px-3 py-1.5 text-sm flex items-center gap-1 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" /> Prev
              </button>
              <button
                onClick={() => setPage(p => Math.min(pages, p + 1))}
                disabled={page === pages}
                className="btn-secondary px-3 py-1.5 text-sm flex items-center gap-1 disabled:opacity-40"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* MODAL */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-5 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">
                {editTxn ? "Edit Transaction" : "New Transaction"}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="p-5 space-y-4">
              <div>
                <label className="label">Description</label>
                <input {...register("description", { required: true })} className="input w-full" placeholder="Enter description" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Amount</label>
                  <input {...register("amount", { required: true })} type="number" className="input w-full" placeholder="0.00" />
                </div>
                <div>
                  <label className="label">Date</label>
                  <input {...register("transaction_date", { required: true })} type="date" className="input w-full" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Type</label>
                  <select {...register("transaction_type")} className="input w-full">
                    <option value="expense">Expense</option>
                    <option value="income">Income</option>
                  </select>
                </div>
                <div>
                  <label className="label">GST Rate</label>
                  <select {...register("gst_rate")} className="input w-full">
                    {GST_RATES.map(r => <option key={r} value={r}>{r}%</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="label">GST Type</label>
                <select {...register("gst_type")} className="input w-full">
                  {GST_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Party Name</label>
                <input {...register("party_name")} className="input w-full" placeholder="Vendor / Customer name" />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" className="btn-primary flex-1">Save Transaction</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}