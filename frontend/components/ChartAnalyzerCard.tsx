import { useState, useRef } from "react";
import { analyzeChart, ChartAnalysis } from "@/lib/api";

export default function ChartAnalyzerCard() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChartAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const response = await analyzeChart(file);
      setResult(response.data);
    } catch (err) {
      setError("Failed to analyze chart. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-4 flex flex-col h-full">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <span>🔍</span> Stock Analyzer
        </h2>
        {file && !loading && (
          <button 
            onClick={handleClear}
            className="text-[10px] uppercase text-[var(--text-muted)] hover:text-white px-2 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-default)] transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      <div className="flex-1 flex flex-col gap-4">
        {/* Upload Area */}
        {!file && (
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 min-h-[120px] border-2 border-dashed border-[var(--border-default)] rounded-lg flex flex-col items-center justify-center p-4 cursor-pointer hover:border-[var(--accent-blue)]/50 hover:bg-[var(--accent-blue)]/5 transition-all group"
          >
            <span className="text-2xl mb-2 opacity-50 group-hover:opacity-100 transition-opacity">📈</span>
            <span className="text-xs text-[var(--text-muted)] group-hover:text-white transition-colors">Click to upload chart image</span>
            <input 
              type="file" 
              accept="image/*" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleFileChange}
            />
          </div>
        )}

        {/* Preview Area */}
        {preview && (
          <div className="relative rounded-lg overflow-hidden border border-[var(--border-default)] bg-[var(--bg-primary)]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={preview} alt="Chart preview" className="w-full h-auto max-h-[200px] object-contain" />
            
            {!result && !loading && (
              <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                <button 
                  onClick={handleAnalyze}
                  className="bg-[var(--accent-blue)] text-white px-4 py-2 rounded text-xs font-bold tracking-wider hover:bg-[var(--accent-blue-dark)] transition-colors shadow-lg shadow-[var(--accent-blue)]/20"
                >
                  ANALYZE PATTERN
                </button>
              </div>
            )}

            {loading && (
              <div className="absolute inset-0 bg-black/80 flex flex-col items-center justify-center">
                <span className="relative flex h-8 w-8 mb-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent-blue)] opacity-50"></span>
                  <span className="relative inline-flex rounded-full h-8 w-8 bg-[var(--accent-blue)]"></span>
                </span>
                <span className="text-[10px] text-[var(--accent-blue)] uppercase tracking-widest font-bold">Scanning Image...</span>
              </div>
            )}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-xs text-[var(--accent-red)] bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 p-2 rounded text-center">
            {error}
          </div>
        )}

        {/* Analysis Results */}
        {result && (
          <div className="mt-2 space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="flex justify-between items-start gap-4 pb-3 border-b border-[var(--border-default)]/50">
              <div>
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block mb-0.5">Detected Pattern</span>
                <span className="text-sm font-bold text-white uppercase">{result.pattern}</span>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block mb-0.5">Strength</span>
                <div className="flex items-center gap-2 justify-end">
                  <span className={`text-lg font-mono font-bold ${
                    result.strength >= 80 ? 'text-[var(--accent-green)]' : 
                    result.strength >= 50 ? 'text-[var(--accent-yellow)]' : 
                    'text-[var(--accent-red)]'
                  }`}>{result.strength}</span>
                  <span className="text-[10px] text-[var(--text-muted)]">/100</span>
                </div>
              </div>
            </div>
            
            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block mb-1">Prediction</span>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{result.prediction}</p>
            </div>
          </div>
        )}

        {/* Quick Action when file is selected but not analyzed */}
        {file && !result && !loading && (
          <button 
            onClick={handleAnalyze}
            className="w-full bg-[var(--bg-secondary)] hover:bg-[var(--accent-blue)]/20 text-[var(--accent-blue)] border border-[var(--accent-blue)]/30 px-4 py-2.5 rounded text-xs font-bold tracking-wider transition-all"
          >
            RUN AI ANALYSIS
          </button>
        )}
      </div>
    </div>
  );
}
