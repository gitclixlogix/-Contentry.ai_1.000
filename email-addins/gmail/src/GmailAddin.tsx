import React, { useCallback, useEffect, useRef } from 'react';
import { AnalysisPanel } from '@contentry/shared/components/AnalysisPanel';
import type { EmailContent } from '@contentry/shared/lib/types';

declare global {
  interface Window {
    gmail?: {
      getSubject: () => string;
      getBody: () => string;
      onContentChange: (callback: () => void) => void;
    };
  }
}

export function GmailAddin() {
  const contentChangeCallbackRef = useRef<(() => void) | null>(null);

  // Get email content from Gmail API
  const getEmailContent = useCallback(async (): Promise<EmailContent> => {
    // In production, this will use Gmail's API
    // For now, we'll check if Gmail context is available
    if (window.gmail) {
      return {
        subject: window.gmail.getSubject() || '',
        body: window.gmail.getBody() || '',
      };
    }

    // Fallback for testing: try to find compose elements in parent window
    try {
      const subject = parent.document.querySelector<HTMLInputElement>('input[name="subjectbox"]')?.value || '';
      const body = parent.document.querySelector<HTMLDivElement>('[aria-label="Message Body"]')?.innerText || '';
      return { subject, body };
    } catch (e) {
      // Cross-origin access denied, return empty
      return { subject: '', body: '' };
    }
  }, []);

  // Set up content change listener
  const onContentChange = useCallback((callback: () => void): (() => void) => {
    contentChangeCallbackRef.current = callback;

    // If Gmail context is available, use its event system
    if (window.gmail?.onContentChange) {
      window.gmail.onContentChange(callback);
    }

    // Fallback: Poll for changes
    const intervalId = setInterval(() => {
      if (contentChangeCallbackRef.current) {
        contentChangeCallbackRef.current();
      }
    }, 2000);

    // Cleanup function
    return () => {
      clearInterval(intervalId);
      contentChangeCallbackRef.current = null;
    };
  }, []);

  return (
    <div style={{ width: '100%', height: '100vh', overflow: 'hidden' }}>
      <AnalysisPanel
        platform="gmail"
        getEmailContent={getEmailContent}
        onContentChange={onContentChange}
      />
    </div>
  );
}
