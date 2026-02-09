/**
 * GlobalErrorBoundary - Global error boundary for catching runtime errors
 * 
 * Wraps the app to catch React errors and display user-friendly error messages.
 * Provides retry functionality and support link.
 * 
 * Usage:
 * <GlobalErrorBoundary>
 *   <App />
 * </GlobalErrorBoundary>
 */

import React, { Component } from 'react';
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  HStack,
  Icon,
  Link,
  Code,
  Collapse,
  useColorModeValue
} from '@chakra-ui/react';
import { AlertTriangle, RefreshCw, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

// Functional component for the error UI (to use hooks)
function ErrorFallbackUI({ error, errorInfo, onReset }) {
  const [showDetails, setShowDetails] = React.useState(false);
  
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('red.200', 'red.800');
  const textColor = useColorModeValue('gray.600', 'gray.300');
  
  // Log error for debugging
  React.useEffect(() => {
    console.error('GlobalErrorBoundary caught error:', error);
    console.error('Error info:', errorInfo);
    
    // Send to error tracking service (if configured)
    if (typeof window !== 'undefined' && window.errorTracker) {
      window.errorTracker.captureException(error, {
        extra: { componentStack: errorInfo?.componentStack }
      });
    }
  }, [error, errorInfo]);

  const handleRetry = () => {
    // Clear any cached state that might cause issues
    if (typeof window !== 'undefined') {
      // Clear session storage errors
      try {
        sessionStorage.removeItem('lastError');
      } catch (e) {
        // Ignore storage errors
      }
    }
    
    if (onReset) {
      onReset();
    } else {
      // Reload the page as fallback
      window.location.reload();
    }
  };

  return (
    <Box 
      minH="100vh" 
      bg={bgColor} 
      display="flex" 
      alignItems="center" 
      justifyContent="center"
      p={4}
    >
      <Box 
        bg={cardBg} 
        p={8} 
        borderRadius="xl" 
        boxShadow="lg"
        border="1px"
        borderColor={borderColor}
        maxW="500px"
        w="full"
      >
        <VStack spacing={6} align="center" textAlign="center">
          {/* Error Icon */}
          <Box 
            p={4} 
            bg="red.100" 
            borderRadius="full"
          >
            <Icon as={AlertTriangle} boxSize={12} color="red.500" />
          </Box>
          
          {/* Error Title */}
          <Heading size="lg" color="red.500">
            Something went wrong
          </Heading>
          
          {/* Error Description */}
          <Text color={textColor} fontSize="md">
            We&apos;re sorry, but something unexpected happened. 
            Please try again or contact support if the problem persists.
          </Text>
          
          {/* Action Buttons */}
          <HStack spacing={4} pt={2}>
            <Button
              colorScheme="brand"
              leftIcon={<Icon as={RefreshCw} />}
              onClick={handleRetry}
              size="lg"
            >
              Try Again
            </Button>
            <Button
              variant="outline"
              leftIcon={<Icon as={HelpCircle} />}
              as={Link}
              href="/support"
              size="lg"
              _hover={{ textDecoration: 'none' }}
            >
              Get Help
            </Button>
          </HStack>
          
          {/* Error Details (collapsible, for debugging) */}
          {process.env.NODE_ENV === 'development' && (
            <Box w="full" pt={4}>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDetails(!showDetails)}
                rightIcon={<Icon as={showDetails ? ChevronUp : ChevronDown} />}
                color="gray.500"
              >
                {showDetails ? 'Hide' : 'Show'} Error Details
              </Button>
              <Collapse in={showDetails}>
                <Box 
                  mt={2} 
                  p={4} 
                  bg="gray.100" 
                  borderRadius="md" 
                  textAlign="left"
                  maxH="200px"
                  overflowY="auto"
                >
                  <Text fontSize="sm" fontWeight="bold" mb={2}>Error:</Text>
                  <Code fontSize="xs" display="block" whiteSpace="pre-wrap" mb={4}>
                    {error?.toString()}
                  </Code>
                  {errorInfo?.componentStack && (
                    <>
                      <Text fontSize="sm" fontWeight="bold" mb={2}>Component Stack:</Text>
                      <Code fontSize="xs" display="block" whiteSpace="pre-wrap">
                        {errorInfo.componentStack}
                      </Code>
                    </>
                  )}
                </Box>
              </Collapse>
            </Box>
          )}
        </VStack>
      </Box>
    </Box>
  );
}

// Class component for error boundary (required for componentDidCatch)
export class GlobalErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    
    // Log to console in all environments
    console.error('GlobalErrorBoundary caught error:', error, errorInfo);
    
    // Call optional onError callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback({
          error: this.state.error,
          errorInfo: this.state.errorInfo,
          onReset: this.handleReset
        });
      }
      
      return (
        <ErrorFallbackUI
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onReset={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

// Hook for programmatic error throwing (useful for async errors)
export function useErrorHandler() {
  const [, setError] = React.useState();
  
  return React.useCallback((error) => {
    setError(() => {
      throw error;
    });
  }, []);
}

export default GlobalErrorBoundary;
