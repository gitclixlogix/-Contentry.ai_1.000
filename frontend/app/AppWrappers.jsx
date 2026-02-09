'use client';
import React from 'react';
import '@/styles/App.css';
import '@/styles/Contact.css';
import '@/styles/Plugins.css';
import '@/styles/MiniCalendar.css';
import { ChakraProvider } from '@chakra-ui/react';
import '@/i18n/config';
import { AuthProvider } from '@/context/AuthContext';
import { GlobalErrorBoundary } from '@/components/shared';

import theme from '@/theme/theme';

const _NoSSR = ({ children }) => <React.Fragment>{children}</React.Fragment>;

export default function AppWrappers({ children }) {
  // Error handler for logging
  const handleError = (error, errorInfo) => {
    // Log to console
    console.error('Application error:', error);
    
    // Could send to error tracking service here
    // Example: Sentry, LogRocket, etc.
  };

  return (
    <ChakraProvider theme={theme}>
      <GlobalErrorBoundary onError={handleError}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </GlobalErrorBoundary>
    </ChakraProvider>
  );
}

