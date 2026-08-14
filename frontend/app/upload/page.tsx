"use client";
import { useCallback, useState } from "react";
import { uploadApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Upload, FileText, CheckCircle2, XCircle, Loader2, Eye } from "lucide-react";
import clsx from "clsx";

export default function UploadPage() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const processFile = async (file: File) => {
    if (!file) return;
    setUploading(true);
    setResult(null);
    try {
      const r = await uploadApi.upload(file);
      setResult(r.data);
      toast.success("File processed successfully!");
    } catch (err: any) {
      toast.error(err.response?.data?.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, []);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Upload & OCR</h1>
        <p className="text-slate-500 text-sm mt-1">Upload invoice images to automatically extract GST data using OCR + AI</p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={clsx(
          "card border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer",
          dragging ? "border-indigo-500 bg-indigo-50" : "border-slate-200 hover:border-indigo-300 hover:bg-slate-50"
        )}
        onClick={() => !uploading && document.getElementById("file-input")?.click()}
      >
        <input id="file-input" type="file" accept="image/*" className="hidden" onChange={onFileChange} />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
            <p className="text-slate-600 font-medium">Processing invoice…</p>
            <p className="text-slate-400 text-sm">Running OCR and AI extraction</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 bg-indigo-100 rounded-full flex items-center justify-center">
              <Upload className="w-7 h-7 text-indigo-600" />
            </div>
            <div>
              <p className="text-slate-700 font-medium">Drop invoice image here or click to browse</p>
              <p className="text-slate-400 text-sm mt-1">Supports JPG, PNG, WEBP, TIFF · Max 10MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Pipeline Info */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">How it works</h3>
        <div className="flex gap-4">
          {[
            { step: "1", label: "Upload", desc: "Image saved securely" },
            { step: "2", label: "OCR", desc: "Tesseract extracts text" },
            { step: "3", label: "Regex Parse", desc: "Pattern matching for GST fields" },
            { step: "4", label: "Gemini AI", desc: "Fallback for complex invoices" },
          ].map(s => (
            <div key={s.step} className="flex-1 text-center">
              <div className="w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold mx-auto mb-2">{s.step}</div>
              <p className="text-xs font-semibold text-slate-700">{s.label}</p>
              <p className="text-xs text-slate-400">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className="card p-6 space-y-4">
          {/* Header — stacks on mobile */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2 flex-wrap break-all">
              {result.ocr_status === "success" ? (
                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              )}
              OCR Result: {result.filename}
            </h3>
            <div className="flex gap-2 text-xs flex-wrap">
              <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded-full whitespace-nowrap">
                Method: {result.parsing_method || "—"}
              </span>
              {result.confidence && (
                <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full whitespace-nowrap">
                  Confidence: {(result.confidence * 100).toFixed(1)}%
                </span>
              )}
            </div>
          </div>

          {/* Parsed Fields */}
          {result.parsed_data && Object.keys(result.parsed_data).length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-3">Extracted Fields</h4>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(result.parsed_data).map(([k, v]) => (
                  <div key={k} className="bg-slate-50 rounded-lg px-3 py-2">
                    <p className="text-xs text-slate-400 uppercase tracking-wide">{k.replace(/_/g, " ")}</p>
                    <p className="text-sm font-medium text-slate-800 mt-0.5 break-all">{String(v)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Raw Text */}
          {result.ocr_text && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <Eye className="w-4 h-4" /> Raw OCR Text
              </h4>
              <pre className="bg-slate-900 text-slate-300 rounded-lg p-4 text-xs overflow-auto max-h-48 font-mono whitespace-pre-wrap">
                {result.ocr_text}
              </pre>
            </div>
          )}

          {result.ocr_status === "failed" && (
            <div className="bg-red-50 text-red-700 rounded-lg p-3 text-sm">
              OCR processing failed. Try a clearer image or ensure Tesseract is installed.
            </div>
          )}
        </div>
      )}
    </div>
  );
}