'use client';
import { useState, useEffect } from 'react';
import {
  Box,
  Progress,
  Text,
  VStack,
  HStack,
  Icon,
  Spinner,
  Badge,
  Button,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertDescription,
  Collapse,
} from '@chakra-ui/react';
import { FaCheckCircle, FaTimesCircle, FaBan, FaSyncAlt } from 'react-icons/fa';
import useJobStatus, { JOB_STATUS } from '@/hooks/useJobStatus';

/**
 * Job Progress Indicator Component (ARCH-004)
 * 
 * Displays real-time job progress with status updates.
 * Used for showing async operation progress in the UI.
 * 
 * @param {string} jobId - The job ID to track
 * @param {string} userId - User ID for authentication
 * @param {function} onComplete - Callback when job completes successfully
 * @param {function} onError - Callback when job fails
 * @param {boolean} showCancelButton - Whether to show cancel button (default: true)
 * @param {string} title - Title to show above progress (optional)
 */
export default function JobProgressIndicator({
  jobId,
  userId,
  onComplete,
  onError,
  showCancelButton = true,
  title = 'Processing...',
  compact = false,
}) {
  const {
    status,
    progress,
    result,
    error,
    isLoading,
    isCompleted,
    isFailed,
    isCancelled,
    progressPercentage,
    progressMessage,
    currentStep,
    cancel,
  } = useJobStatus(jobId, { userId, onComplete, onError });

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  // Get status color
  const getStatusColor = () => {
    switch (status) {
      case JOB_STATUS.COMPLETED:
        return 'green';
      case JOB_STATUS.FAILED:
        return 'red';
      case JOB_STATUS.CANCELLED:
        return 'orange';
      case JOB_STATUS.PROCESSING:
        return 'blue';
      case JOB_STATUS.RETRYING:
        return 'yellow';
      default:
        return 'gray';
    }
  };

  // Get status icon
  const getStatusIcon = () => {
    switch (status) {
      case JOB_STATUS.COMPLETED:
        return FaCheckCircle;
      case JOB_STATUS.FAILED:
        return FaTimesCircle;
      case JOB_STATUS.CANCELLED:
        return FaBan;
      case JOB_STATUS.RETRYING:
        return FaSyncAlt;
      default:
        return null;
    }
  };

  // Don't render if no job ID
  if (!jobId) return null;

  // Compact view for inline display
  if (compact) {
    return (
      <HStack spacing={2} py={1}>
        {isLoading && <Spinner size="sm" color="blue.500" />}
        {getStatusIcon() && <Icon as={getStatusIcon()} color={`${getStatusColor()}.500`} />}
        <Text fontSize="sm" color={textColor}>
          {progressMessage || currentStep || status}
        </Text>
        {isLoading && (
          <Text fontSize="xs" color="gray.500">
            {progressPercentage}%
          </Text>
        )}
      </HStack>
    );
  }

  return (
    <Box
      p={4}
      bg={bgColor}
      borderRadius="lg"
      borderWidth="1px"
      borderColor={borderColor}
      shadow="sm"
    >
      <VStack spacing={3} align="stretch">
        {/* Header with status */}
        <HStack justify="space-between">
          <HStack>
            {isLoading ? (
              <Spinner size="sm" color="blue.500" />
            ) : getStatusIcon() ? (
              <Icon as={getStatusIcon()} color={`${getStatusColor()}.500`} boxSize={5} />
            ) : null}
            <Text fontWeight="medium">{title}</Text>
          </HStack>
          <Badge colorScheme={getStatusColor()} variant="subtle">
            {status || 'Starting...'}
          </Badge>
        </HStack>

        {/* Progress bar */}
        {isLoading && (
          <Box>
            <Progress
              value={progressPercentage}
              size="sm"
              colorScheme="blue"
              borderRadius="full"
              hasStripe
              isAnimated={status === JOB_STATUS.PROCESSING}
            />
            <HStack justify="space-between" mt={1}>
              <Text fontSize="xs" color={textColor}>
                {currentStep || progressMessage || 'Processing...'}
              </Text>
              <Text fontSize="xs" color={textColor}>
                {progressPercentage}%
              </Text>
            </HStack>
          </Box>
        )}

        {/* Success message */}
        <Collapse in={isCompleted}>
          <Alert status="success" borderRadius="md" size="sm">
            <AlertIcon />
            <AlertDescription fontSize="sm">
              Job completed successfully!
            </AlertDescription>
          </Alert>
        </Collapse>

        {/* Error message */}
        <Collapse in={isFailed || Boolean(error)}>
          <Alert status="error" borderRadius="md" size="sm">
            <AlertIcon />
            <AlertDescription fontSize="sm">
              {error || 'Job failed. Please try again.'}
            </AlertDescription>
          </Alert>
        </Collapse>

        {/* Cancelled message */}
        <Collapse in={isCancelled}>
          <Alert status="warning" borderRadius="md" size="sm">
            <AlertIcon />
            <AlertDescription fontSize="sm">
              Job was cancelled.
            </AlertDescription>
          </Alert>
        </Collapse>

        {/* Cancel button */}
        {showCancelButton && isLoading && (
          <HStack justify="flex-end">
            <Button
              size="sm"
              variant="outline"
              colorScheme="red"
              onClick={cancel}
            >
              Cancel
            </Button>
          </HStack>
        )}
      </VStack>
    </Box>
  );
}

/**
 * Inline job status badge
 */
export function JobStatusBadge({ jobId, userId }) {
  const { status, progressPercentage, isLoading } = useJobStatus(jobId, { userId });

  if (!jobId || !status) return null;

  const getColor = () => {
    switch (status) {
      case JOB_STATUS.COMPLETED: return 'green';
      case JOB_STATUS.FAILED: return 'red';
      case JOB_STATUS.CANCELLED: return 'orange';
      case JOB_STATUS.PROCESSING: return 'blue';
      default: return 'gray';
    }
  };

  return (
    <Badge colorScheme={getColor()} variant="subtle">
      {isLoading ? `${status} (${progressPercentage}%)` : status}
    </Badge>
  );
}
