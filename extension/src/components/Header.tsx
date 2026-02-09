import React from 'react';
import { LogOut, Settings, ExternalLink } from 'lucide-react';
import type { User } from '~/lib/api';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

export function Header({ user, onLogout }: HeaderProps) {
  return (
    <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-white">
      <div className="flex items-center gap-3">
        {/* Logo */}
        <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
          <svg 
            viewBox="0 0 24 24" 
            className="w-5 h-5 text-white"
            fill="currentColor"
          >
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
          </svg>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-dark-text">Contentry.ai</h1>
          <p className="text-xs text-dark-tertiary">Content Co-pilot</p>
        </div>
      </div>

      {user && (
        <div className="flex items-center gap-2">
          <a
            href="https://contentry.ai/contentry/dashboard"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Open Dashboard"
          >
            <ExternalLink className="w-4 h-4 text-dark-tertiary" />
          </a>
          <button
            onClick={onLogout}
            className="p-2 rounded-lg hover:bg-red-50 transition-colors group"
            title="Sign out"
          >
            <LogOut className="w-4 h-4 text-dark-tertiary group-hover:text-red-500" />
          </button>
        </div>
      )}
    </div>
  );
}
