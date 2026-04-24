'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import ChatPanel from '@/components/ChatPanel';
import ImageUploadAnalyzer from '@/components/ImageUploadAnalyzer';

function ChatContent() {
  const searchParams = useSearchParams();
  const stock = searchParams.get('stock');
  const initialMessage = stock ? `Tell me more about ${stock}` : '';

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 h-[calc(100vh-4rem)]">
      <div className="grid grid-cols-3 gap-6 h-full">
        {/* Chat Panel */}
        <div className="col-span-2 bg-terminal-card border border-terminal-border rounded-lg overflow-hidden flex flex-col">
          <div className="p-4 border-b border-terminal-border">
            <h1 className="text-lg font-semibold">Research Assistant</h1>
            <p className="text-sm text-terminal-muted">
              Ask about stocks, compare picks, or explain market conditions
            </p>
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatPanel initialMessage={initialMessage} />
          </div>
        </div>

        {/* Side Panel */}
        <div className="space-y-4">
          {/* Chart Upload */}
          <ImageUploadAnalyzer />

          {/* Quick Actions */}
          <div className="bg-terminal-card border border-terminal-border rounded-lg p-4">
            <div className="text-xs text-terminal-muted uppercase tracking-wider mb-3">Quick Questions</div>
            <div className="space-y-2">
              {[
                'What is the market regime today?',
                'Which sectors are strongest?',
                'Explain the risk in current picks',
                'Why was INFY marked as SHORT?',
                'Compare banking stocks',
              ].map((question) => (
                <button
                  key={question}
                  className="w-full text-left text-sm px-3 py-2 bg-terminal-bg rounded hover:bg-terminal-border transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>

          {/* API Status */}
          <div className="bg-terminal-card border border-terminal-border rounded-lg p-4">
            <div className="text-xs text-terminal-muted uppercase tracking-wider mb-3">API Status</div>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-terminal-muted">/api/chat</span>
                <span className="text-terminal-success">● Ready</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-terminal-muted">/api/chart-analysis</span>
                <span className="text-terminal-success">● Ready</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-4">Loading...</div>}>
      <ChatContent />
    </Suspense>
  );
}
