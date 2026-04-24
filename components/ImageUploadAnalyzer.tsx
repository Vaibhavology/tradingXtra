'use client';

import { useState, useRef } from 'react';
import { Upload, X, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { ChartAnalysis } from '@/types';

interface ImageUploadAnalyzerProps {
  onAnalysisComplete?: (analysis: ChartAnalysis) => void;
}

export default function ImageUploadAnalyzer({ onAnalysisComplete }: ImageUploadAnalyzerProps) {
  const [image, setImage] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<ChartAnalysis | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImage(e.target?.result as string);
        setAnalysis(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImage(e.target?.result as string);
        setAnalysis(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeChart = async () => {
    setAnalyzing(true);
    
    // Simulated AI analysis - in production, this calls /api/chart-analysis
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const mockAnalysis: ChartAnalysis = {
      pattern: 'Ascending Triangle',
      timeframe: 'Daily',
      suggestedEntry: { low: 1520, high: 1545 },
      suggestedSL: 1485,
      suggestedTP: [1610, 1680],
      confidence: 72,
      notes: 'Pattern shows higher lows with horizontal resistance. Volume declining in consolidation - typical for this pattern. Breakout above 1550 would confirm.',
      isAIAssisted: true,
    };
    
    setAnalysis(mockAnalysis);
    setAnalyzing(false);
    onAnalysisComplete?.(mockAnalysis);
  };

  const clearImage = () => {
    setImage(null);
    setAnalysis(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-lg p-4">
      <div className="text-xs text-terminal-muted uppercase tracking-wider mb-3">Chart Snapshot Analysis</div>
      
      {!image ? (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-terminal-border rounded-lg p-8 text-center cursor-pointer hover:border-terminal-accent/50 transition-colors"
        >
          <Upload className="w-8 h-8 mx-auto mb-2 text-terminal-muted" />
          <p className="text-sm text-terminal-muted">Drop chart image or click to upload</p>
          <p className="text-xs text-terminal-muted mt-1">PNG, JPG up to 5MB</p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Image Preview */}
          <div className="relative">
            <img
              src={image}
              alt="Chart snapshot"
              className="w-full rounded-lg border border-terminal-border"
            />
            <button
              onClick={clearImage}
              className="absolute top-2 right-2 p-1 bg-terminal-bg/80 rounded hover:bg-terminal-danger/20 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Analyze Button */}
          {!analysis && (
            <button
              onClick={analyzeChart}
              disabled={analyzing}
              className="w-full py-2 bg-terminal-accent text-white rounded font-medium hover:bg-terminal-accent/80 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {analyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                'Analyze Chart'
              )}
            </button>
          )}

          {/* Analysis Results */}
          {analysis && (
            <div className="bg-terminal-bg border border-terminal-border rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-terminal-success" />
                  <span className="text-sm font-medium">Analysis Complete</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-terminal-warning">
                  <AlertCircle className="w-3 h-3" />
                  AI-Assisted
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-terminal-muted">Pattern: </span>
                  <span className="font-medium">{analysis.pattern}</span>
                </div>
                <div>
                  <span className="text-terminal-muted">Timeframe: </span>
                  <span>{analysis.timeframe}</span>
                </div>
                <div>
                  <span className="text-terminal-muted">Entry: </span>
                  <span className="mono-nums text-terminal-accent">
                    ₹{analysis.suggestedEntry.low} - ₹{analysis.suggestedEntry.high}
                  </span>
                </div>
                <div>
                  <span className="text-terminal-muted">Confidence: </span>
                  <span className="mono-nums text-terminal-accent">{analysis.confidence}%</span>
                </div>
                <div>
                  <span className="text-terminal-muted">SL: </span>
                  <span className="mono-nums text-terminal-danger">₹{analysis.suggestedSL}</span>
                </div>
                <div>
                  <span className="text-terminal-muted">Targets: </span>
                  <span className="mono-nums text-terminal-success">
                    {analysis.suggestedTP.map(t => `₹${t}`).join(', ')}
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-terminal-border">
                <div className="text-xs text-terminal-muted mb-1">Notes</div>
                <p className="text-sm">{analysis.notes}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
