"use client";
import { useState } from "react";
import { taxApi } from "@/lib/api";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { Calculator, IndianRupee, TrendingDown, Award } from "lucide-react";

const fmt = (v: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v);

export default function TaxAssistantPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, watch } = useForm<any>({
    defaultValues: { regime: "new", assessment_year: "2024-25", section_80c: 0, section_80d: 0, section_80g: 0, hra_exemption: 0 }
  });
  const regime = watch("regime");

  const onSubmit = async (data: any) => {
    setLoading(true);
    try {
      const r = await taxApi.calculate({
        ...data,
        gross_income: Number(data.gross_income),
        salary_income: Number(data.salary_income || 0),
        business_income: Number(data.business_income || 0),
        other_income: Number(data.other_income || 0),
        section_80c: Number(data.section_80c || 0),
        section_80d: Number(data.section_80d || 0),
        section_80g: Number(data.section_80g || 0),
        hra_exemption: Number(data.hra_exemption || 0)
      }, true);
      setResult(r.data);
    } catch (err: any) {
      toast.error(err.response?.data?.message || "Calculation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl lg:text-2xl font-bold text-slate-900">Tax Assistant</h1>
        <p className="text-slate-500 text-xs lg:text-sm mt-1">
          Calculate your Indian income tax liability for FY 2024-25 (Old vs New Regime)
        </p>
      </div>

      {/* Layout — stacked on mobile, side by side on lg */}
      <div className="flex flex-col lg:grid lg:grid-cols-5 gap-4 lg:gap-6">

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="lg:col-span-2 space-y-4">
          <div className="card p-4 lg:p-5 space-y-4">
            <h3 className="font-semibold text-slate-800">Income Details</h3>
            <div>
              <label className="label">Tax Regime *</label>
              <div className="flex gap-2">
                {["new", "old"].map(r => (
                  <label key={r} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg border cursor-pointer text-sm font-medium transition-all ${regime === r ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300"}`}>
                    <input type="radio" {...register("regime")} value={r} className="hidden" />
                    {r === "new" ? "New Regime" : "Old Regime"}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="label">Gross Annual Income (₹) *</label>
              <input {...register("gross_income", { required: true, min: 0 })} type="number" className="input" placeholder="1200000" />
            </div>
            <div>
              <label className="label">Salary Income (₹)</label>
              <input {...register("salary_income")} type="number" className="input" placeholder="1000000" />
            </div>
            <div>
              <label className="label">Business Income (₹)</label>
              <input {...register("business_income")} type="number" className="input" placeholder="200000" />
            </div>
            <div>
              <label className="label">Other Income (₹)</label>
              <input {...register("other_income")} type="number" className="input" placeholder="50000" />
            </div>
          </div>

          {regime === "old" && (
            <div className="card p-4 lg:p-5 space-y-4">
              <h3 className="font-semibold text-slate-800">Deductions (Old Regime)</h3>
              <div>
                <label className="label">Section 80C (max ₹1.5L)</label>
                <input {...register("section_80c")} type="number" max={150000} className="input" placeholder="150000" />
              </div>
              <div>
                <label className="label">Section 80D (Health Insurance)</label>
                <input {...register("section_80d")} type="number" className="input" placeholder="25000" />
              </div>
              <div>
                <label className="label">Section 80G (Donations)</label>
                <input {...register("section_80g")} type="number" className="input" placeholder="0" />
              </div>
              <div>
                <label className="label">HRA Exemption</label>
                <input {...register("hra_exemption")} type="number" className="input" placeholder="0" />
              </div>
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
            <Calculator className="w-4 h-4" />
            {loading ? "Calculating…" : "Calculate Tax"}
          </button>
        </form>

        {/* Results */}
        <div className="lg:col-span-3 space-y-4">
          {result ? (
            <>
              {/* Summary Cards — 1 col mobile, 2 col sm+ */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="card p-4 lg:p-5 bg-indigo-50 border-indigo-200">
                  <p className="text-xs font-semibold text-indigo-500 uppercase">Total Tax Liability</p>
                  <p className="text-2xl lg:text-3xl font-bold text-indigo-700 mt-1">{fmt(result.total_tax_liability)}</p>
                  <p className="text-xs text-indigo-500 mt-1">Effective Rate: {result.effective_tax_rate}%</p>
                </div>
                <div className="card p-4 lg:p-5">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Taxable Income</p>
                  <p className="text-2xl font-bold text-slate-800 mt-1">{fmt(result.taxable_income)}</p>
                  <p className="text-xs text-slate-400 mt-1">After deductions: {fmt(result.total_deductions)}</p>
                </div>
              </div>

              {/* Breakdown */}
              <div className="card p-4 lg:p-5 space-y-3">
                <h3 className="font-semibold text-slate-800">Tax Breakdown</h3>
                {[
                  { label: "Income Tax", value: result.income_tax },
                  { label: "Surcharge", value: result.surcharge },
                  { label: "Health & Education Cess (4%)", value: result.cess },
                ].map(r => (
                  <div key={r.label} className="flex justify-between text-sm py-1.5 border-b border-slate-100 last:border-0">
                    <span className="text-slate-600">{r.label}</span>
                    <span className="font-semibold text-slate-800">{fmt(r.value)}</span>
                  </div>
                ))}
                <div className="flex justify-between text-sm py-1.5 font-bold text-indigo-700">
                  <span>Total Tax Liability</span>
                  <span>{fmt(result.total_tax_liability)}</span>
                </div>
              </div>

              {/* Slab Breakdown */}
              {result.slab_breakdown?.length > 0 && (
                <div className="card p-4 lg:p-5">
                  <h3 className="font-semibold text-slate-800 mb-3">Slab-wise Breakdown</h3>
                  <div className="space-y-2 overflow-x-auto">
                    {result.slab_breakdown.map((s: any, i: number) => (
                      <div key={i} className="flex justify-between text-xs py-1.5 border-b border-slate-50 gap-2">
                        <span className="text-slate-500 flex-1">{s.slab}</span>
                        <span className="text-slate-600">{s.rate}% on {fmt(s.taxable_in_slab)}</span>
                        <span className="font-semibold text-slate-800">{fmt(s.tax_in_slab)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Regime Comparison */}
              {result.comparison && (
                <div className={`card p-4 lg:p-5 ${result.comparison.recommended === "current" ? "bg-green-50 border-green-200" : "bg-amber-50 border-amber-200"}`}>
                  <div className="flex items-start gap-3">
                    <Award className={`w-5 h-5 mt-0.5 flex-shrink-0 ${result.comparison.recommended === "current" ? "text-green-600" : "text-amber-600"}`} />
                    <div>
                      <p className="font-semibold text-slate-800">
                        {result.comparison.recommended === "current"
                          ? `✅ ${result.regime === "new" ? "New" : "Old"} Regime is better for you!`
                          : `💡 Switch to ${result.comparison.regime === "new" ? "New" : "Old"} Regime to save ${fmt(result.comparison.savings)}`
                        }
                      </p>
                      <p className="text-sm text-slate-600 mt-1">
                        {result.comparison.regime === "new" ? "New" : "Old"} regime tax: {fmt(result.comparison.total_tax_liability)}
                        {" "}({result.comparison.effective_tax_rate}% effective rate)
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="card p-10 lg:p-16 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-4">
                <Calculator className="w-8 h-8 text-indigo-500" />
              </div>
              <h3 className="font-semibold text-slate-700">Enter Income Details</h3>
              <p className="text-slate-400 text-sm mt-1 max-w-xs">
                Fill in your income details and click Calculate to see your tax liability with a regime comparison.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}