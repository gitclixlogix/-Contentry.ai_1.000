import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AnalysisPanel } from '@contentry/shared/components/AnalysisPanel';
import { LoadingState } from '@contentry/shared/components/LoadingState';
import type { EmailContent } from '@contentry/shared/lib/types';

declare const Office: any;

export function OutlookAddin() {
  const [isOfficeReady, setIsOfficeReady] = useState(false);
  const [mailboxItem, setMailboxItem] = useState<any>(null);
  const contentChangeCallbackRef = useRef<(() => void) | null>(null);

  // Initialize Office context
  useEffect(() => {
    const initOffice = async () => {
      try {
        // Get the current mailbox item (compose mode)
        if (Office?.context?.mailbox?.item) {
          setMailboxItem(Office.context.mailbox.item);
        }
        setIsOfficeReady(true);
      } catch (error) {
        console.error('Failed to initialize Office:', error);
        setIsOfficeReady(true); // Continue anyway for dev/testing
      }
    };

    // Check if Office is already ready
    if (typeof Office !== 'undefined' && Office.context) {
      initOffice();
    } else {
      // Wait for Office.onReady
      const checkOffice = setInterval(() => {
        if (typeof Office !== 'undefined' && Office.context) {
          clearInterval(checkOffice);
          initOffice();
        }
      }, 100);

      // Timeout after 5 seconds
      setTimeout(() => {
        clearInterval(checkOffice);
        setIsOfficeReady(true);
      }, 5000);
    }
  }, []);

  // Get email content from Outlook
  const getEmailContent = useCallback(async (): Promise<EmailContent> => {
    if (!mailboxItem) {
      return { subject: '', body: '' };
    }

    try {
      // Get subject
      const subject = await new Promise<string>((resolve) => {
        mailboxItem.subject.getAsync((result: any) => {
          resolve(result.status === 'succeeded' ? result.value : '');
        });
      });

      // Get body (as text)
      const body = await new Promise<string>((resolve) => {
        mailboxItem.body.getAsync(
          'text', // coercionType: text (not html)
          (result: any) => {
            resolve(result.status === 'succeeded' ? result.value : '');
          }
        );
      });

      return { subject, body };
    } catch (error) {
      console.error('Failed to get email content:', error);
      return { subject: '', body: '' };
    }
  }, [mailboxItem]);

  // Set up content change listener
  const onContentChange = useCallback((callback: () => void): (() => void) => {
    contentChangeCallbackRef.current = callback;

    // Outlook doesn't have a direct content change event in compose mode
    // We'll poll for changes periodically
    const intervalId = setInterval(() => {
      if (contentChangeCallbackRef.current) {
        contentChangeCallbackRef.current();
      }
    }, 2000);

    // Also listen for item changed event if available
    if (mailboxItem?.addHandlerAsync) {
      try {
        mailboxItem.addHandlerAsync(
          Office.EventType.ItemChanged,
          () => {
            if (contentChangeCallbackRef.current) {
              contentChangeCallbackRef.current();
            }
          }
        );
      } catch (e) {
        console.log('ItemChanged handler not available');
      }
    }

    // Cleanup function
    return () => {
      clearInterval(intervalId);
      contentChangeCallbackRef.current = null;
    };
  }, [mailboxItem]);

  if (!isOfficeReady) {
    return <LoadingState message="Connecting to Outlook..." />;
  }

  return (
    <div style={{ width: '100%', height: '100vh', overflow: 'hidden' }}>
      <AnalysisPanel
        platform="outlook"
        getEmailContent={getEmailContent}
        onContentChange={onContentChange}
      />
    </div>
  );
}
