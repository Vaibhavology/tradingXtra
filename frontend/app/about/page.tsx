"use client";

import Link from "next/link";
import { Github, Linkedin, Mail, Globe, ExternalLink, Terminal } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="max-w-[1000px] mx-auto space-y-12 pb-20 animate-fade-in">

      {/* Header Banner */}
      <div className="relative terminal-card rounded-2xl p-10 border border-[var(--border-default)] shadow-2xl overflow-hidden group">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--accent-blue)]/5 rounded-full blur-[100px] group-hover:bg-[var(--accent-blue)]/10 transition-colors duration-1000" />
        <div className="absolute -bottom-20 -left-20 w-72 h-72 bg-purple-500/5 rounded-full blur-[80px]" />

        <div className="relative z-10 flex flex-col md:flex-row items-center md:items-start gap-8">
          {/* Avatar / Profile */}
          <div className="w-32 h-32 rounded-full border-4 border-[var(--bg-secondary)] shadow-xl overflow-hidden bg-gradient-to-br from-[var(--accent-blue)]/20 to-purple-500/20 flex items-center justify-center shrink-0">
            <span className="text-5xl">💻</span>
          </div>

          <div className="text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent-blue)]/10 border border-[var(--accent-blue)]/20 text-[var(--accent-blue)] text-xs font-mono font-bold tracking-widest mb-4">
              <span className="w-2 h-2 rounded-full bg-[var(--accent-blue)] animate-pulse" />
              SYSTEM ARCHITECT
            </div>
            <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight mb-4">
              Vaibhav
            </h1>
            <p className="text-[var(--text-secondary)] text-lg max-w-2xl leading-relaxed">
              Full-Stack Developer & Quantitative Systems Architect. I build high-performance trading algorithms, AI-driven intelligence engines, and scalable web applications.
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto">

        {/* Connect & Links */}
        <div className="terminal-card rounded-2xl p-8 border border-[var(--border-default)] shadow-xl bg-gradient-to-br from-[var(--bg-card)] to-[var(--bg-secondary)]/30">
          <h2 className="text-sm font-black uppercase tracking-widest text-white mb-6 flex items-center gap-3">
            <Globe className="w-5 h-5 text-purple-400" />
            Connect & Portfolio
          </h2>

          <div className="space-y-4">
            {/* Portfolio Link */}
            <Link href="https://vaibhavology.vercel.app" target="_blank" className="flex items-center justify-between p-4 bg-[var(--bg-primary)]/50 hover:bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-xl transition-all duration-300 group relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/5 rounded-full blur-2xl group-hover:bg-green-500/10 transition-colors" />
              <div className="flex items-center gap-4 relative z-10">
                <div className="w-10 h-10 rounded-lg bg-green-900/30 flex items-center justify-center">
                  <Globe className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white group-hover:text-green-400 transition-colors">Personal Portfolio</div>
                  <div className="text-xs text-[var(--text-muted)]">View my other projects</div>
                </div>
              </div>
              <ExternalLink className="w-4 h-4 text-[var(--text-muted)] group-hover:text-green-400 relative z-10" />
            </Link>
            <Link href="https://github.com/vaibhavology" target="_blank" className="flex items-center justify-between p-4 bg-[var(--bg-primary)]/50 hover:bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-xl transition-all duration-300 group">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center">
                  <Github className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white group-hover:text-[var(--accent-blue)] transition-colors">GitHub</div>
                  <div className="text-xs text-[var(--text-muted)]">github.com/vaibhav</div>
                </div>
              </div>
              <ExternalLink className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--accent-blue)]" />
            </Link>

            <Link href="https://linkedin.com/in/vaibhavology/" target="_blank" className="flex items-center justify-between p-4 bg-[var(--bg-primary)]/50 hover:bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-xl transition-all duration-300 group">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-blue-900/30 flex items-center justify-center">
                  <Linkedin className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors">LinkedIn</div>
                  <div className="text-xs text-[var(--text-muted)]">linkedin.com/in/vaibhavology</div>
                </div>
              </div>
              <ExternalLink className="w-4 h-4 text-[var(--text-muted)] group-hover:text-blue-400" />
            </Link>

            <Link href="mailto:vaibhavsu24@gmail.com" className="flex items-center justify-between p-4 bg-[var(--bg-primary)]/50 hover:bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-xl transition-all duration-300 group">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-red-900/30 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white group-hover:text-red-400 transition-colors">Email</div>
                  <div className="text-xs text-[var(--text-muted)]">Get in touch</div>
                </div>
              </div>
              <ExternalLink className="w-4 h-4 text-[var(--text-muted)] group-hover:text-red-400" />
            </Link>
          </div>
        </div>

      </div>

      {/* Project Philosophy */}
      <div className="p-8 border border-[var(--border-default)]/50 bg-[var(--bg-secondary)]/20 rounded-2xl text-center">
        <h3 className="text-lg font-bold text-white mb-2 tracking-tight">About TradingXtra</h3>
        <p className="text-sm text-[var(--text-muted)] max-w-3xl mx-auto leading-relaxed">
          TradingXtra was built to bridge the gap between institutional quantitative analysis and retail trading. By combining real-time data ingestion, strict mathematical expected value (EV) thresholds, and AI-driven narrative intelligence, it provides a strictly "Decision-First" framework that eliminates emotional trading.
        </p>
      </div>

    </div>
  );
}
