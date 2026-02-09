/**
 * Rate Limit Indicator Component (ARCH-013)
 * 
 * Displays current rate limit status with:
 * - Remaining requests counter
 * - Progress bar showing usage
 * - Warnings when approaching limits
 * - Upgrade prompt for free tier users
 */

import React from 'react';
import {
  Box,
  HStack,
  VStack,
  Text,
  Progress,
  Badge,
  Tooltip,
  Icon,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Button,
  Collapse,
  useDisclosure,
  Skeleton,
} from '@chakra-ui/react';
import { FaRocket, FaClock, FaExclamationTriangle, FaChevronDown, FaChevronUp } from 'react-icons/fa';
import { useRateLimitStatus } from '@/hooks/useRateLimitStatus';
import { useRouter } from 'next/navigation';

// Tier badge colors
const TIER_COLORS = {
  free: 'gray',
  creator: 'teal',
  starter: 'blue',
  pro: 'purple',
  business: 'green',
  enterprise: 'gold'
};

/**
 * Compact rate limit indicator for headers/toolbars
 */
export const RateLimitBadge = ({ showUpgrade = true }) => {
  const router = useRouter();
  const { 
    loading, 
    tier, 
    tierName, 
    hourlyRemaining, 
    hourlyLimit, 
    isNearLimit,
    isAtLimit 
  } = useRateLimitStatus();
  
  if (loading) {
    return <Skeleton height="24px" width="100px" borderRadius="md" />;
  }
  
  const isUnlimited = hourlyLimit === -1;
  
  return (
    <Tooltip 
      label={
        isUnlimited 
          ? 'Unlimited requests (Enterprise)'
          : `${hourlyRemaining} of ${hourlyLimit} requests remaining this hour`
      }
      hasArrow
    >
      <HStack spacing={2}>
        <Badge 
          colorScheme={TIER_COLORS[tier] || 'gray'} 
          variant="subtle"
          px={2}
          py={1}
          borderRadius="md"
        >
          {tierName}
        </Badge>
        
        {!isUnlimited && (
          <HStack 
            spacing={1} 
            bg={isAtLimit ? 'red.100' : isNearLimit ? 'orange.100' : 'gray.100'} 
            px={2} 
            py={1} 
            borderRadius="md"
          >
            <Icon 
              as={isAtLimit ? FaExclamationTriangle : FaClock} 
              color={isAtLimit ? 'red.500' : isNearLimit ? 'orange.500' : 'gray.500'} 
              boxSize={3}
            />
            <Text 
              fontSize="xs" 
              fontWeight="medium"
              color={isAtLimit ? 'red.700' : isNearLimit ? 'orange.700' : 'gray.700'}
            >
              {hourlyRemaining} left
            </Text>
          </HStack>
        )}
        
        {showUpgrade && tier === 'free' && (
          <Button
            size="xs"
            colorScheme="purple"
            variant="ghost"
            leftIcon={<FaRocket />}
            onClick={() => router.push('/contentry/subscription/plans')}
          >
            Upgrade
          </Button>
        )}
      </HStack>
    </Tooltip>
  );
};

/**
 * Detailed rate limit card for settings/profile pages
 */
export const RateLimitCard = () => {
  const router = useRouter();
  const { isOpen, onToggle } = useDisclosure();
  const { 
    status,
    loading, 
    error,
    tier, 
    tierName, 
    hourlyRemaining, 
    hourlyLimit,
    hourlyUsed,
    hourlyResetSeconds,
    dailyCost,
    monthlyCost,
    isNearLimit,
    isAtLimit 
  } = useRateLimitStatus();
  
  if (loading) {
    return (
      <Box p={4} borderWidth="1px" borderRadius="lg" bg="white">
        <Skeleton height="20px" mb={2} />
        <Skeleton height="10px" width="60%" />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert status="warning" borderRadius="md">
        <AlertIcon />
        <AlertDescription>Unable to load rate limit status</AlertDescription>
      </Alert>
    );
  }
  
  const isUnlimited = hourlyLimit === -1;
  const usagePercentage = isUnlimited ? 0 : Math.round((hourlyUsed / hourlyLimit) * 100);
  const resetMinutes = Math.ceil(hourlyResetSeconds / 60);
  
  return (
    <Box 
      p={4} 
      borderWidth="1px" 
      borderRadius="lg" 
      bg="white"
      shadow="sm"
    >
      <VStack align="stretch" spacing={3}>
        {/* Header */}
        <HStack justify="space-between">
          <HStack spacing={2}>
            <Text fontWeight="semibold" fontSize="sm">API Usage</Text>
            <Badge colorScheme={TIER_COLORS[tier]} variant="subtle">
              {tierName}
            </Badge>
          </HStack>
          
          {!isUnlimited && (
            <Text fontSize="xs" color="gray.500">
              Resets in {resetMinutes} min
            </Text>
          )}
        </HStack>
        
        {/* Progress bar */}
        {!isUnlimited ? (
          <>
            <Progress 
              value={usagePercentage} 
              size="sm" 
              borderRadius="full"
              colorScheme={isAtLimit ? 'red' : isNearLimit ? 'orange' : 'blue'}
            />
            <HStack justify="space-between">
              <Text fontSize="xs" color="gray.600">
                {hourlyUsed} / {hourlyLimit} requests used
              </Text>
              <Text fontSize="xs" fontWeight="medium" color={isNearLimit ? 'orange.600' : 'gray.600'}>
                {hourlyRemaining} remaining
              </Text>
            </HStack>
          </>
        ) : (
          <HStack justify="center" py={2}>
            <Icon as={FaRocket} color="gold" />
            <Text fontSize="sm" fontWeight="medium" color="gray.700">
              Unlimited requests
            </Text>
          </HStack>
        )}
        
        {/* Warnings */}
        {isAtLimit && (
          <Alert status="error" size="sm" borderRadius="md">
            <AlertIcon boxSize={4} />
            <VStack align="start" spacing={0}>
              <AlertTitle fontSize="xs">Rate limit reached</AlertTitle>
              <AlertDescription fontSize="xs">
                Wait {resetMinutes} minutes or upgrade your plan
              </AlertDescription>
            </VStack>
          </Alert>
        )}
        
        {isNearLimit && !isAtLimit && (
          <Alert status="warning" size="sm" borderRadius="md">
            <AlertIcon boxSize={4} />
            <AlertDescription fontSize="xs">
              Approaching hourly limit ({usagePercentage}% used)
            </AlertDescription>
          </Alert>
        )}
        
        {/* Expandable details */}
        <Button 
          variant="ghost" 
          size="xs" 
          onClick={onToggle}
          rightIcon={isOpen ? <FaChevronUp /> : <FaChevronDown />}
        >
          {isOpen ? 'Hide' : 'Show'} details
        </Button>
        
        <Collapse in={isOpen}>
          <VStack align="stretch" spacing={2} pt={2} borderTopWidth="1px">
            <HStack justify="space-between">
              <Text fontSize="xs" color="gray.500">Today&apos;s cost</Text>
              <Text fontSize="xs" fontWeight="medium">${dailyCost.toFixed(4)}</Text>
            </HStack>
            <HStack justify="space-between">
              <Text fontSize="xs" color="gray.500">Monthly cost</Text>
              <Text fontSize="xs" fontWeight="medium">${monthlyCost.toFixed(4)}</Text>
            </HStack>
            {status?.daily?.soft_cap && (
              <HStack justify="space-between">
                <Text fontSize="xs" color="gray.500">Daily soft cap</Text>
                <Text fontSize="xs" fontWeight="medium">${status.daily.soft_cap.toFixed(2)}</Text>
              </HStack>
            )}
          </VStack>
        </Collapse>
        
        {/* Upgrade CTA for free tier */}
        {tier === 'free' && (
          <Button
            size="sm"
            colorScheme="purple"
            leftIcon={<FaRocket />}
            onClick={() => router.push('/contentry/subscription/plans')}
          >
            Upgrade for more requests
          </Button>
        )}
      </VStack>
    </Box>
  );
};

/**
 * Rate limit error display for 429 responses
 */
export const RateLimitError = ({ error, onRetry }) => {
  const router = useRouter();
  const resetSeconds = error?.reset_seconds || 3600;
  const resetMinutes = Math.ceil(resetSeconds / 60);
  
  return (
    <Alert
      status="error"
      variant="subtle"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      textAlign="center"
      borderRadius="lg"
      py={6}
    >
      <AlertIcon boxSize="40px" mr={0} />
      <AlertTitle mt={4} mb={1} fontSize="lg">
        Rate Limit Exceeded
      </AlertTitle>
      <AlertDescription maxWidth="sm">
        <VStack spacing={3}>
          <Text>
            {error?.message || 'You have exceeded your hourly request limit.'}
          </Text>
          <Text fontSize="sm" color="gray.600">
            Your limit will reset in approximately {resetMinutes} minutes.
          </Text>
          {error?.upgrade_message && (
            <Text fontSize="sm" fontStyle="italic" color="purple.600">
              {error.upgrade_message}
            </Text>
          )}
          <HStack spacing={3} mt={2}>
            {onRetry && (
              <Button size="sm" onClick={onRetry}>
                Try Again
              </Button>
            )}
            <Button 
              size="sm" 
              colorScheme="purple"
              onClick={() => router.push('/contentry/subscription/plans')}
            >
              View Plans
            </Button>
          </HStack>
        </VStack>
      </AlertDescription>
    </Alert>
  );
};

export default RateLimitCard;
