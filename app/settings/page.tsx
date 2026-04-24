'use client';

import { useState } from 'react';
import { Save, AlertTriangle, Shield, Bell, Sliders } from 'lucide-react';
import { UserSettings } from '@/types';

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings>({
    maxRiskPerTrade: 2,
    maxTradesPerDay: 5,
    tradeStyle: 'moderate',
    riskReminders: true,
  });

  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // In production, this would call /api/settings
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-terminal-muted text-sm mt-1">
          Configure your trading preferences and risk parameters
        </p>
      </div>

      {/* Risk Management */}
      <div className="bg-terminal-card border border-terminal-border rounded-lg p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-terminal-accent" />
          <h2 className="font-medium">Risk Management</h2>
        </div>

        <div className="space-y-6">
          {/* Max Risk Per Trade */}
          <div>
            <label className="text-sm text-terminal-muted block mb-2">
              Maximum Risk Per Trade (% of Capital)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0.5"
                max="5"
                step="0.5"
                value={settings.maxRiskPerTrade}
                onChange={(e) => setSettings({ ...settings, maxRiskPerTrade: Number(e.target.value) })}
                className="flex-1"
              />
              <span className="mono-nums text-lg font-medium w-16 text-right">
                {settings.maxRiskPerTrade}%
              </span>
            </div>
            <p className="text-xs text-terminal-muted mt-1">
              Recommended: 1-2% for conservative, 2-3% for moderate
            </p>
          </div>

          {/* Max Trades Per Day */}
          <div>
            <label className="text-sm text-terminal-muted block mb-2">
              Maximum Trades Per Day
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={settings.maxTradesPerDay}
                onChange={(e) => setSettings({ ...settings, maxTradesPerDay: Number(e.target.value) })}
                className="flex-1"
              />
              <span className="mono-nums text-lg font-medium w-16 text-right">
                {settings.maxTradesPerDay}
              </span>
            </div>
            <p className="text-xs text-terminal-muted mt-1">
              Limits overtrading. Quality over quantity.
            </p>
          </div>
        </div>
      </div>

      {/* Trade Style */}
      <div className="bg-terminal-card border border-terminal-border rounded-lg p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Sliders className="w-5 h-5 text-terminal-accent" />
          <h2 className="font-medium">Trade Style Preference</h2>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {(['conservative', 'moderate', 'aggressive'] as const).map((style) => (
            <button
              key={style}
              onClick={() => setSettings({ ...settings, tradeStyle: style })}
              className={`p-4 rounded-lg border text-center transition-colors ${
                settings.tradeStyle === style
                  ? 'border-terminal-accent bg-terminal-accent/10'
                  : 'border-terminal-border hover:border-terminal-muted'
              }`}
            >
              <div className="font-medium capitalize mb-1">{style}</div>
              <div className="text-xs text-terminal-muted">
                {style === 'conservative' && 'Lower risk, fewer trades'}
                {style === 'moderate' && 'Balanced approach'}
                {style === 'aggressive' && 'Higher risk tolerance'}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-terminal-card border border-terminal-border rounded-lg p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="w-5 h-5 text-terminal-accent" />
          <h2 className="font-medium">Notifications</h2>
        </div>

        <div className="space-y-4">
          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <div className="font-medium">Risk Reminders</div>
              <div className="text-sm text-terminal-muted">
                Show warnings when approaching daily limits
              </div>
            </div>
            <div
              onClick={() => setSettings({ ...settings, riskReminders: !settings.riskReminders })}
              className={`w-12 h-6 rounded-full transition-colors cursor-pointer ${
                settings.riskReminders ? 'bg-terminal-accent' : 'bg-terminal-border'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white mt-0.5 transition-transform ${
                  settings.riskReminders ? 'translate-x-6' : 'translate-x-0.5'
                }`}
              />
            </div>
          </label>
        </div>
      </div>

      {/* Risk Warning */}
      <div className="bg-terminal-warning/10 border border-terminal-warning/30 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-terminal-warning mt-0.5" />
          <div className="text-sm">
            <span className="font-medium text-terminal-warning">Important Reminder</span>
            <p className="text-terminal-muted mt-1">
              These settings help manage risk but do not guarantee profits. Always trade 
              with capital you can afford to lose. The system provides research-based 
              suggestions, not financial advice.
            </p>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-terminal-muted">
          Settings are stored locally and synced with backend on save
        </div>
        <button
          onClick={handleSave}
          className={`flex items-center gap-2 px-6 py-2 rounded font-medium transition-colors ${
            saved
              ? 'bg-terminal-success text-white'
              : 'bg-terminal-accent text-white hover:bg-terminal-accent/80'
          }`}
        >
          <Save className="w-4 h-4" />
          {saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
