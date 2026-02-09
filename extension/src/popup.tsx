import React, { useEffect, useState } from 'react';
import { PanelRightOpen, LogIn, CheckCircle, ExternalLink } from 'lucide-react';
import { api, type User } from './lib/api';
import { STORAGE_KEYS } from './lib/config';
import './styles/globals.css';

function Popup() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await api.getUser();
        setUser(userData);
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleOpenSidePanel = async () => {
    try {
      // Get current window and tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab?.windowId) {
        // Open side panel
        await chrome.sidePanel.open({ windowId: tab.windowId });
        // Close popup
        window.close();
      }
    } catch (error) {
      console.error('Failed to open side panel:', error);
    }
  };

  const handleLogin = () => {
    chrome.tabs.create({ url: api.getLoginUrl() });
    window.close();
  };

  const handleLogout = async () => {
    await api.clearAuth();
    setUser(null);
  };

  if (isLoading) {
    return (
      <div className="w-[280px] p-4 bg-white">
        <div className="flex items-center justify-center py-8">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-[280px] bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500 flex items-center justify-center">
            <svg 
              viewBox="0 0 24 24" 
              className="w-6 h-6 text-white"
              fill="currentColor"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
            </svg>
          </div>
          <div>
            <h1 className="text-base font-semibold text-dark-text">Contentry.ai</h1>
            <p className="text-xs text-dark-tertiary">Content Analysis Co-pilot</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {user ? (
          <div className="space-y-4">
            {/* User Info */}
            <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-green-800 truncate">
                  {user.full_name || user.email}
                </p>
                <p className="text-xs text-green-600 truncate">{user.email}</p>
              </div>
            </div>

            {/* Open Side Panel Button */}
            <button
              onClick={handleOpenSidePanel}
              className="w-full py-3 px-4 rounded-xl bg-brand-500 hover:bg-brand-600 
                         text-white font-semibold text-sm transition-all duration-200
                         flex items-center justify-center gap-2"
            >
              <PanelRightOpen className="w-4 h-4" />
              Open Analysis Panel
            </button>

            {/* Dashboard Link */}
            <a
              href="https://contentry.ai/contentry/dashboard"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full py-2.5 px-4 rounded-lg border border-gray-200 
                         text-dark-secondary font-medium text-sm transition-all duration-200
                         flex items-center justify-center gap-2 hover:bg-gray-50"
            >
              <ExternalLink className="w-4 h-4" />
              Open Dashboard
            </a>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="w-full py-2 text-xs text-dark-tertiary hover:text-red-500 transition-colors"
            >
              Sign out
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-dark-secondary text-center">
              Sign in to analyze content on any webpage in real-time.
            </p>

            <button
              onClick={handleLogin}
              className="w-full py-3 px-4 rounded-xl bg-brand-500 hover:bg-brand-600 
                         text-white font-semibold text-sm transition-all duration-200
                         flex items-center justify-center gap-2"
            >
              <LogIn className="w-4 h-4" />
              Sign in to Contentry.ai
            </button>

            <p className="text-xs text-center text-dark-tertiary">
              Don't have an account?{' '}
              <a 
                href="https://contentry.ai/contentry/auth" 
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-500 hover:underline"
              >
                Sign up free
              </a>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Popup;
