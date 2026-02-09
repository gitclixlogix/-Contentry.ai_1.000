import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, FileText, AlertCircle } from 'lucide-react';
import { api, type User, type StrategicProfile, type AnalysisResult } from './lib/api';
import { STORAGE_KEYS, ANALYSIS_DEBOUNCE_MS } from './lib/config';
import { Header } from './components/Header';
import { LoginPrompt } from './components/LoginPrompt';
import { ProfileSelector } from './components/ProfileSelector';
import { ScoreGrid } from './components/ScoreCard';
import { RecommendationList } from './components/RecommendationList';
import { LoadingState, AnalyzingState, EmptyState } from './components/LoadingState';
import './styles/globals.css';

function SidePanel() {
  // Auth state
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  // Profile state
  const [profiles, setProfiles] = useState<StrategicProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [isProfilesLoading, setIsProfilesLoading] = useState(false);

  // Content & Analysis state
  const [currentContent, setCurrentContent] = useState<string>('');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [lastAnalyzedContent, setLastAnalyzedContent] = useState<string>('');

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await api.getUser();
        setUser(userData);
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsAuthLoading(false);
      }
    };

    checkAuth();

    // Listen for auth changes from storage
    const handleStorageChange = (changes: { [key: string]: chrome.storage.StorageChange }) => {
      if (changes[STORAGE_KEYS.USER_DATA]) {
        const newUser = changes[STORAGE_KEYS.USER_DATA].newValue;
        setUser(newUser || null);
      }
    };

    chrome.storage.onChanged.addListener(handleStorageChange);
    return () => chrome.storage.onChanged.removeListener(handleStorageChange);
  }, []);

  // Load profiles when authenticated
  useEffect(() => {
    if (!user) return;

    const loadProfiles = async () => {
      setIsProfilesLoading(true);
      try {
        const fetchedProfiles = await api.getStrategicProfiles();
        setProfiles(fetchedProfiles);

        // Load saved profile selection
        const savedProfileId = await api.getSelectedProfile();
        if (savedProfileId && fetchedProfiles.some(p => p.id === savedProfileId)) {
          setSelectedProfileId(savedProfileId);
        } else if (fetchedProfiles.length > 0) {
          // Auto-select first profile
          setSelectedProfileId(fetchedProfiles[0].id);
        }
      } catch (error) {
        console.error('Failed to load profiles:', error);
      } finally {
        setIsProfilesLoading(false);
      }
    };

    loadProfiles();
  }, [user]);

  // Listen for content updates from content script
  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.type === 'CONTENT_UPDATED') {
        setCurrentContent(message.payload.content || '');
      }
    };

    chrome.runtime.onMessage.addListener(handleMessage);
    
    // Also request current content from active tab
    const requestContent = async () => {
      try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab?.id) {
          chrome.tabs.sendMessage(tab.id, { type: 'GET_ACTIVE_CONTENT' });
        }
      } catch (error) {
        console.log('Could not request content:', error);
      }
    };
    
    requestContent();

    return () => chrome.runtime.onMessage.removeListener(handleMessage);
  }, []);

  // Debounced analysis
  useEffect(() => {
    if (!user || !currentContent || currentContent.length < 10) return;
    if (currentContent === lastAnalyzedContent) return;

    const timeoutId = setTimeout(() => {
      runAnalysis();
    }, ANALYSIS_DEBOUNCE_MS);

    return () => clearTimeout(timeoutId);
  }, [currentContent, user, selectedProfileId]);

  const runAnalysis = useCallback(async () => {
    if (!currentContent || currentContent.length < 10) {
      setAnalysisError('Please enter at least 10 characters to analyze');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const result = await api.analyzeContent(currentContent, selectedProfileId || undefined);
      if (result) {
        setAnalysisResult(result);
        setLastAnalyzedContent(currentContent);
      } else {
        setAnalysisError('Analysis failed. Please try again.');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      setAnalysisError('Failed to analyze content. Please check your connection.');
    } finally {
      setIsAnalyzing(false);
    }
  }, [currentContent, selectedProfileId]);

  const handleProfileSelect = async (profileId: string) => {
    setSelectedProfileId(profileId);
    await api.setSelectedProfile(profileId);
    // Re-analyze with new profile if we have content
    if (currentContent && currentContent.length >= 10) {
      setLastAnalyzedContent(''); // Force re-analysis
    }
  };

  const handleLogout = async () => {
    await api.clearAuth();
    setUser(null);
    setProfiles([]);
    setSelectedProfileId(null);
    setAnalysisResult(null);
    setCurrentContent('');
  };

  const handleRefresh = () => {
    setLastAnalyzedContent(''); // Force re-analysis
    runAnalysis();
  };

  // Loading state
  if (isAuthLoading) {
    return (
      <div className="w-full h-full min-h-screen bg-white">
        <LoadingState message="Loading..." />
      </div>
    );
  }

  // Not authenticated
  if (!user) {
    return (
      <div className="w-full h-full min-h-screen bg-white">
        <LoginPrompt onLoginSuccess={() => {
          // Reload user data
          api.getUser().then(setUser);
        }} />
      </div>
    );
  }

  // Parse violations and recommendations from analysis result
  const violations = analysisResult?.violations || [];
  const recommendations = analysisResult?.recommendations || [];
  const scores = {
    compliance: analysisResult?.compliance_score || 0,
    cultural: analysisResult?.cultural_sensitivity_score || 0,
    accuracy: analysisResult?.accuracy_score || 0,
    overall: analysisResult?.overall_score || 0,
  };

  return (
    <div className="w-full min-h-screen bg-gray-50 flex flex-col">
      <Header user={user} onLogout={handleLogout} />

      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* Profile Selector */}
          <ProfileSelector
            profiles={profiles}
            selectedId={selectedProfileId}
            onSelect={handleProfileSelect}
            isLoading={isProfilesLoading}
          />

          {/* Content Preview */}
          <div className="bg-white rounded-lg border border-gray-200 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-dark-tertiary uppercase tracking-wide">
                Content Being Analyzed
              </span>
              <span className="text-xs text-dark-tertiary">
                {currentContent.length} chars
              </span>
            </div>
            <div className="text-sm text-dark-text bg-gray-50 rounded p-2 max-h-24 overflow-y-auto">
              {currentContent ? (
                <p className="whitespace-pre-wrap break-words">
                  {currentContent.slice(0, 500)}
                  {currentContent.length > 500 && '...'}
                </p>
              ) : (
                <p className="text-dark-tertiary italic">
                  Start typing in a text field on any page...
                </p>
              )}
            </div>
          </div>

          {/* Analyzing State */}
          {isAnalyzing && <AnalyzingState />}

          {/* Error State */}
          {analysisError && !isAnalyzing && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{analysisError}</span>
            </div>
          )}

          {/* Results */}
          {analysisResult && !isAnalyzing && (
            <>
              {/* Scores */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-dark-tertiary uppercase tracking-wide">
                    3-Pillar Scores
                  </span>
                  <button
                    onClick={handleRefresh}
                    disabled={isAnalyzing}
                    className="flex items-center gap-1 text-xs text-brand-500 hover:text-brand-600 
                               disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className={`w-3 h-3 ${isAnalyzing ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                </div>
                <ScoreGrid scores={scores} isLoading={isAnalyzing} />
              </div>

              {/* Recommendations */}
              <div>
                <span className="block text-xs font-medium text-dark-tertiary uppercase tracking-wide mb-2">
                  Analysis & Recommendations
                </span>
                <div className="bg-white rounded-lg border border-gray-200 p-3">
                  <RecommendationList
                    violations={violations}
                    recommendations={recommendations}
                    isLoading={isAnalyzing}
                  />
                </div>
              </div>
            </>
          )}

          {/* Empty State - No content yet */}
          {!currentContent && !analysisResult && (
            <EmptyState
              title="Ready to analyze"
              description="Start typing in any text field on this page to get real-time content analysis"
              icon={FileText}
            />
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-100 bg-white">
        <p className="text-xs text-center text-dark-tertiary">
          Powered by Contentry.ai •{' '}
          <a
            href="https://contentry.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="text-brand-500 hover:underline"
          >
            Learn more
          </a>
        </p>
      </div>
    </div>
  );
}

export default SidePanel;
