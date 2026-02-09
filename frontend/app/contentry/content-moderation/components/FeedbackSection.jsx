'use client';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import {
  Box,
  Button,
  Flex,
  HStack,
  Text,
  Textarea,
  VStack,
  useColorModeValue,
} from '@chakra-ui/react';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

/**
 * Feedback section component for collecting user feedback on analysis accuracy
 * @param {Object} analysis - The analysis object (not currently used but kept for potential future use)
 * @param {string} content - The original content that was analyzed
 * @param {string} userId - The user ID submitting the feedback
 */
export default function FeedbackSection({ analysis, content, userId }) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  const bgColor = useColorModeValue('#fff7ed', 'orange.900');
  const borderColor = useColorModeValue('#fed7aa', 'orange.700');
  const textColor = useColorModeValue('orange.800', 'orange.100');
  const secondaryTextColor = useColorModeValue('orange.700', 'orange.200');

  const handleSubmitFeedback = async () => {
    if (!feedback.trim()) {
      alert('Please enter your feedback');
      return;
    }

    setSubmitting(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/feedback`, {
        user_id: userId,
        content: content,
        correction: feedback,
        feedback_type: 'correction'
      });
      console.log('Feedback submitted successfully:', response.data);
      alert('Thank you! Your feedback helps improve our AI accuracy.');
      setFeedback('');
      setShowFeedback(false);
    } catch (error) {
      console.error('Failed to submit feedback:', error.response?.data || error.message);
      alert('Failed to submit feedback: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box mt={6} p={4} bg={bgColor} borderRadius="lg" border="1px solid" borderColor={borderColor}>
      <Flex align="center" justify="space-between" mb={showFeedback ? 4 : 0}>
        <HStack>
          <Text fontSize="xl">💡</Text>
          <Text fontWeight="600" color={textColor}>Found inaccuracies in this analysis?</Text>
        </HStack>
        <Button size="sm" variant="outline" onClick={() => setShowFeedback(!showFeedback)}>
          {showFeedback ? 'Cancel' : 'Teach AI'}
        </Button>
      </Flex>
      
      {showFeedback && (
        <VStack align="stretch" spacing={4}>
          <Textarea
            placeholder="Explain what's incorrect or what could be improved in this analysis..."
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            minH="100px"
          />
          <Button onClick={handleSubmitFeedback} isLoading={submitting} colorScheme="brand" size="sm">
            Submit Feedback
          </Button>
          <Text fontSize="xs" color={secondaryTextColor}>
            Your feedback will be used to improve future content analysis accuracy.
          </Text>
        </VStack>
      )}
    </Box>
  );
}
