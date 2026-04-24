'use client';

import { useState } from 'react';
import { Send, Loader2, Bot, User } from 'lucide-react';
import { ChatMessage } from '@/types';

interface ChatPanelProps {
  initialMessage?: string;
}

export default function ChatPanel({ initialMessage }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome to the Trading Research Assistant. I can help you understand stock picks, compare stocks, explain market conditions, and analyze risk. What would you like to know?',
      timestamp: new Date().toISOString(),
    }
  ]);
  const [input, setInput] = useState(initialMessage || '');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    // Simulated AI response - in production, this calls /api/chat
    await new Promise(resolve => setTimeout(resolve, 1500));

    const responses: Record<string, string> = {
      default: `Based on the current market analysis:\n\n**Market Context:**\n- NIFTY showing mild bullish bias with support at 21,750\n- Banking sector leading with strong FII inflows\n- VIX at comfortable levels suggesting low fear\n\n**Risk Assessment:**\nCurrent picks are aligned with the broader market trend. However, always maintain strict stop-losses as outlined in each pick card.\n\nWould you like me to elaborate on any specific stock or sector?`,
    };

    const assistantMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: responses.default,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, assistantMessage]);
    setLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-terminal-accent/20 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-terminal-accent" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-terminal-accent text-white'
                  : 'bg-terminal-card border border-terminal-border'
              }`}
            >
              <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              <div className={`text-xs mt-1 ${
                message.role === 'user' ? 'text-white/60' : 'text-terminal-muted'
              }`}>
                {new Date(message.timestamp).toLocaleTimeString('en-IN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
            {message.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-terminal-border flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-terminal-accent/20 flex items-center justify-center">
              <Bot className="w-4 h-4 text-terminal-accent" />
            </div>
            <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
              <Loader2 className="w-4 h-4 animate-spin text-terminal-accent" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-terminal-border">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about stocks, compare picks, or explain risk..."
            className="flex-1 bg-terminal-bg border border-terminal-border rounded-lg px-4 py-2 text-sm resize-none focus:outline-none focus:border-terminal-accent"
            rows={2}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="px-4 bg-terminal-accent text-white rounded-lg hover:bg-terminal-accent/80 transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex gap-2 mt-2">
          {['Why is ICICIBANK selected?', 'Compare HDFC vs ICICI', "Explain today's risk"].map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => setInput(suggestion)}
              className="text-xs px-2 py-1 bg-terminal-border rounded hover:bg-terminal-muted/30 transition-colors"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
