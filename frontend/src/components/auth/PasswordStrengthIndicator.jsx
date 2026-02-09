'use client';
import { useMemo } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Progress,
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import { FaCheck, FaTimes } from 'react-icons/fa';

/**
 * Password Strength Indicator Component
 * Shows real-time feedback on password requirements
 * 
 * Requirements:
 * - 8+ characters
 * - 1 uppercase letter
 * - 1 lowercase letter  
 * - 1 number
 * - 1 special character
 */
export default function PasswordStrengthIndicator({ password = '', showRequirements = true }) {
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const successColor = useColorModeValue('green.500', 'green.400');
  const errorColor = useColorModeValue('red.500', 'red.400');
  const textColor = useColorModeValue('gray.600', 'gray.400');

  // Calculate requirements using useMemo instead of useEffect + setState
  const requirements = useMemo(() => ({
    min_length: password.length >= 8,
    has_uppercase: /[A-Z]/.test(password),
    has_lowercase: /[a-z]/.test(password),
    has_number: /\d/.test(password),
    has_symbol: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'`~]/.test(password),
  }), [password]);

  // Calculate strength percentage
  const metRequirements = Object.values(requirements).filter(Boolean).length;
  const strengthPercent = (metRequirements / 5) * 100;

  // Determine strength label and color
  const getStrengthInfo = () => {
    if (metRequirements === 0) return { label: '', color: 'gray' };
    if (metRequirements <= 2) return { label: 'Weak', color: 'red' };
    if (metRequirements <= 3) return { label: 'Fair', color: 'orange' };
    if (metRequirements <= 4) return { label: 'Good', color: 'yellow' };
    return { label: 'Strong', color: 'green' };
  };

  const strengthInfo = getStrengthInfo();

  const requirementsList = [
    { key: 'min_length', label: 'At least 8 characters' },
    { key: 'has_uppercase', label: 'One uppercase letter (A-Z)' },
    { key: 'has_lowercase', label: 'One lowercase letter (a-z)' },
    { key: 'has_number', label: 'One number (0-9)' },
    { key: 'has_symbol', label: 'One special character (!@#$%...)' },
  ];

  // Don't show anything if password is empty
  if (!password) {
    return showRequirements ? (
      <Box 
        p={3} 
        bg={bgColor} 
        borderRadius="md" 
        borderWidth="1px" 
        borderColor={borderColor}
        mt={2}
      >
        <Text fontSize="xs" fontWeight="medium" color={textColor} mb={2}>
          Password Requirements:
        </Text>
        <VStack align="start" spacing={1}>
          {requirementsList.map((req) => (
            <HStack key={req.key} spacing={2}>
              <Icon as={FaTimes} boxSize={3} color="gray.400" />
              <Text fontSize="xs" color="gray.400">
                {req.label}
              </Text>
            </HStack>
          ))}
        </VStack>
      </Box>
    ) : null;
  }

  return (
    <Box mt={2}>
      {/* Strength Bar */}
      <HStack justify="space-between" mb={1}>
        <Text fontSize="xs" color={textColor}>
          Password Strength
        </Text>
        <Text fontSize="xs" fontWeight="medium" color={`${strengthInfo.color}.500`}>
          {strengthInfo.label}
        </Text>
      </HStack>
      <Progress 
        value={strengthPercent} 
        size="xs" 
        colorScheme={strengthInfo.color}
        borderRadius="full"
        mb={2}
      />

      {/* Requirements List */}
      {showRequirements && (
        <Box 
          p={3} 
          bg={bgColor} 
          borderRadius="md" 
          borderWidth="1px" 
          borderColor={borderColor}
        >
          <VStack align="start" spacing={1}>
            {requirementsList.map((req) => {
              const isMet = requirements[req.key];
              return (
                <HStack key={req.key} spacing={2}>
                  <Icon 
                    as={isMet ? FaCheck : FaTimes} 
                    boxSize={3} 
                    color={isMet ? successColor : errorColor} 
                  />
                  <Text 
                    fontSize="xs" 
                    color={isMet ? successColor : textColor}
                    textDecoration={isMet ? 'none' : 'none'}
                  >
                    {req.label}
                  </Text>
                </HStack>
              );
            })}
          </VStack>
        </Box>
      )}
    </Box>
  );
}

/**
 * Helper function to check if password is valid
 * Can be imported and used for form validation
 */
export function isPasswordValid(password) {
  return (
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[a-z]/.test(password) &&
    /\d/.test(password) &&
    /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'`~]/.test(password)
  );
}
