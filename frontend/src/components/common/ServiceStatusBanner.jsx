/**
 * Service Unavailable Banner Component (ARCH-003)
 * 
 * Displays when external services are experiencing issues.
 * Provides user-friendly messaging and estimated recovery times.
 */

import React from 'react';
import {
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Box,
  HStack,
  VStack,
  Text,
  Badge,
  Button,
  Collapse,
  useDisclosure,
  Icon,
  Progress,
} from '@chakra-ui/react';
import { 
  FaExclamationTriangle, 
  FaInfoCircle, 
  FaSync,
  FaChevronDown,
  FaChevronUp,
  FaClock
} from 'react-icons/fa';
import { useServiceAvailability } from '@/hooks/useServiceAvailability';

/**
 * Global service status banner - shows when system is degraded
 */
export const ServiceStatusBanner = ({ onRefresh }) => {
  const { isOpen, onToggle } = useDisclosure();
  const { 
    isDegraded, 
    systemHealth, 
    loading, 
    refresh 
  } = useServiceAvailability();
  
  if (!isDegraded || loading) return null;
  
  const openServices = systemHealth?.circuits?.open_services || [];
  const status = systemHealth?.status || 'degraded';
  
  const statusConfig = {
    healthy: { color: 'green', icon: FaInfoCircle, title: 'All Systems Operational' },
    degraded: { color: 'orange', icon: FaExclamationTriangle, title: 'Some Services Degraded' },
    critical: { color: 'red', icon: FaExclamationTriangle, title: 'Service Disruption' },
  };
  
  const config = statusConfig[status] || statusConfig.degraded;
  
  return (
    <Alert 
      status={status === 'critical' ? 'error' : 'warning'} 
      variant="subtle"
      borderRadius="md"
      mb={4}
    >
      <AlertIcon as={config.icon} />
      <Box flex="1">
        <HStack justify="space-between" align="center">
          <AlertTitle>{config.title}</AlertTitle>
          <HStack spacing={2}>
            <Button 
              size="xs" 
              variant="ghost" 
              leftIcon={<FaSync />}
              onClick={() => { refresh(); onRefresh?.(); }}
              isLoading={loading}
            >
              Refresh
            </Button>
            <Button 
              size="xs" 
              variant="ghost" 
              rightIcon={isOpen ? <FaChevronUp /> : <FaChevronDown />}
              onClick={onToggle}
            >
              Details
            </Button>
          </HStack>
        </HStack>
        
        <AlertDescription>
          <Text fontSize="sm" mt={1}>
            {systemHealth?.message || 'Some features may be temporarily unavailable.'}
          </Text>
        </AlertDescription>
        
        <Collapse in={isOpen}>
          <VStack align="stretch" mt={3} spacing={2}>
            {openServices.map(service => (
              <HStack key={service} justify="space-between" fontSize="sm">
                <Text>{formatServiceName(service)}</Text>
                <Badge colorScheme="red">Unavailable</Badge>
              </HStack>
            ))}
            <Text fontSize="xs" color="gray.500" mt={2}>
              Services typically recover automatically. Refresh to check current status.
            </Text>
          </VStack>
        </Collapse>
      </Box>
    </Alert>
  );
};

/**
 * Feature-specific unavailable message
 */
export const FeatureUnavailable = ({ 
  feature, 
  title, 
  message,
  showRetryTimer = true,
  retryAfter = 60,
  onRetry 
}) => {
  const [countdown, setCountdown] = React.useState(retryAfter);
  
  React.useEffect(() => {
    if (!showRetryTimer || countdown <= 0) return;
    
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [showRetryTimer, countdown]);
  
  return (
    <Alert
      status="warning"
      variant="subtle"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      textAlign="center"
      borderRadius="lg"
      py={6}
      px={8}
    >
      <AlertIcon boxSize="40px" mr={0} />
      <AlertTitle mt={4} mb={1} fontSize="lg">
        {title || 'Service Temporarily Unavailable'}
      </AlertTitle>
      <AlertDescription maxWidth="md">
        <VStack spacing={3}>
          <Text>
            {message || `The ${formatServiceName(feature)} service is temporarily unavailable. Please try again shortly.`}
          </Text>
          
          {showRetryTimer && countdown > 0 && (
            <HStack spacing={2} color="gray.600">
              <Icon as={FaClock} />
              <Text fontSize="sm">
                Estimated recovery: {formatTime(countdown)}
              </Text>
            </HStack>
          )}
          
          {onRetry && (
            <Button 
              mt={2}
              size="sm"
              colorScheme="orange"
              onClick={onRetry}
              isDisabled={countdown > 0}
            >
              {countdown > 0 ? `Retry in ${countdown}s` : 'Try Again'}
            </Button>
          )}
        </VStack>
      </AlertDescription>
    </Alert>
  );
};

/**
 * Inline service status indicator
 */
export const ServiceStatusIndicator = ({ service, showLabel = true }) => {
  const { isFeatureAvailable, loading } = useServiceAvailability();
  
  if (loading) {
    return null;
  }
  
  const available = isFeatureAvailable(service);
  
  return (
    <HStack spacing={1}>
      <Box
        w={2}
        h={2}
        borderRadius="full"
        bg={available ? 'green.400' : 'red.400'}
      />
      {showLabel && (
        <Text fontSize="xs" color={available ? 'green.600' : 'red.600'}>
          {available ? 'Available' : 'Unavailable'}
        </Text>
      )}
    </HStack>
  );
};

/**
 * Service health dashboard card
 */
export const ServiceHealthCard = () => {
  const { systemHealth, loading, refresh } = useServiceAvailability();
  
  if (loading || !systemHealth) {
    return null;
  }
  
  const { status, circuits, features } = systemHealth;
  const healthPercentage = circuits?.summary?.total > 0
    ? ((circuits.summary.closed || 0) / circuits.summary.total) * 100
    : 100;
  
  return (
    <Box p={4} borderWidth="1px" borderRadius="lg" bg="white">
      <HStack justify="space-between" mb={3}>
        <Text fontWeight="semibold">System Health</Text>
        <Badge 
          colorScheme={status === 'healthy' ? 'green' : status === 'degraded' ? 'orange' : 'red'}
        >
          {status?.charAt(0).toUpperCase() + status?.slice(1)}
        </Badge>
      </HStack>
      
      <Progress 
        value={healthPercentage} 
        size="sm" 
        colorScheme={healthPercentage === 100 ? 'green' : healthPercentage > 50 ? 'orange' : 'red'}
        borderRadius="full"
        mb={3}
      />
      
      <HStack justify="space-between" fontSize="sm">
        <Text color="gray.600">
          {circuits?.summary?.closed || 0} / {circuits?.summary?.total || 0} services healthy
        </Text>
        <Button size="xs" variant="ghost" onClick={refresh}>
          <FaSync />
        </Button>
      </HStack>
    </Box>
  );
};

// Helper functions
function formatServiceName(service) {
  const names = {
    openai: 'OpenAI',
    gemini: 'Gemini AI',
    claude: 'Claude AI',
    stripe: 'Payments',
    ayrshare: 'Social Posting',
    vision_api: 'Media Analysis',
    image_generation: 'Image Generation',
    ai_content_generation: 'AI Content',
    ai_content_analysis: 'Content Analysis',
    ai_image_generation: 'Image Generation',
    social_posting: 'Social Posting',
    stripe_payments: 'Payment Processing',
  };
  return names[service] || service.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatTime(seconds) {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
}

export default ServiceStatusBanner;
