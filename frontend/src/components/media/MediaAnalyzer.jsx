'use client';
import { useState } from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Text,
  Badge,
  Icon,
  Image,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  List,
  ListItem,
  ListIcon,
  useColorModeValue,
  Spinner,
  Flex,
} from '@chakra-ui/react';
import { FaUpload, FaCheckCircle, FaExclamationTriangle, FaTimesCircle, FaImage } from 'react-icons/fa';
import api from '@/lib/api';

export default function MediaAnalyzer({ onMediaAnalyzed }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setAnalysis(null);
    }
  };

  const analyzeMedia = async () => {
    if (!selectedFile) return;

    setAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await api.post('/media/analyze-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      console.log('Media analysis response:', response.data);
      const analysisData = response.data.analysis;
      console.log('Setting analysis:', analysisData);
      setAnalysis(analysisData);
      
      if (onMediaAnalyzed) {
        onMediaAnalyzed(analysisData, selectedFile);
      }
    } catch (error) {
      console.error('Analysis error:', error);
      setAnalysis({
        safety_status: 'error',
        risk_level: 'unknown',
        summary: `Analysis failed: ${error.response?.data?.detail || error.message}`,
        description: 'Failed to analyze media',
        issues: [error.message],
        recommendations: ['Please try again or contact support'],
        labels: [],
        safe_search: null
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      safe: 'green',
      questionable: 'orange',
      unsafe: 'red',
      unknown: 'blue',
      error: 'red'
    };
    return colors[status] || 'gray';
  };

  return (
    <Box>
      <VStack align="stretch" spacing={4}>
        {/* Upload Section */}
        {!previewUrl && (
          <Box
            borderWidth="2px"
            borderStyle="dashed"
            borderColor={borderColor}
            borderRadius="md"
            p={8}
            textAlign="center"
            cursor="pointer"
            _hover={{ borderColor: 'brand.500', bg: hoverBg }}
            onClick={() => document.getElementById('media-upload-input').click()}
          >
            <input
              id="media-upload-input"
              type="file"
              accept="image/*,video/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            <Icon as={FaImage} boxSize={12} color="gray.400" mb={4} />
            <Text fontWeight="600" mb={2}>Upload Image or Video</Text>
            <Text fontSize="sm" color="gray.500">
              Click to browse or drag & drop
            </Text>
            <Text fontSize="xs" color="gray.400" mt={2}>
              Supported: JPG, PNG, GIF, MP4, MOV
            </Text>
          </Box>
        )}

        {/* Preview & Analysis */}
        {previewUrl && (
          <Box>
            <HStack justify="space-between" mb={2}>
              <Text fontWeight="600">Selected Media</Text>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setPreviewUrl(null);
                  setSelectedFile(null);
                  setAnalysis(null);
                }}
              >
                Remove
              </Button>
            </HStack>
            
            {/* Preview - handle both images and videos */}
            {selectedFile?.type?.startsWith('video/') ? (
              <Box
                as="video"
                src={previewUrl}
                controls
                maxH="300px"
                width="100%"
                objectFit="contain"
                borderRadius="md"
                borderWidth="1px"
                borderColor={borderColor}
                mb={4}
              />
            ) : (
              <Image
                src={previewUrl}
                alt="Preview"
                maxH="300px"
                objectFit="contain"
                borderRadius="md"
                borderWidth="1px"
                borderColor={borderColor}
                mb={4}
              />
            )}

            {!analysis && (
              <Button
                colorScheme="brand"
                leftIcon={<FaUpload />}
                onClick={analyzeMedia}
                isLoading={analyzing}
                loadingText="Analyzing..."
                width="full"
              >
                Analyze for Offensive Content
              </Button>
            )}
          </Box>
        )}

        {/* Analysis Results - Simplified */}
        {analysis && (
          <Alert
            status={analysis.safety_status === 'safe' ? 'success' : analysis.safety_status === 'questionable' ? 'warning' : analysis.safety_status === 'unknown' ? 'info' : 'error'}
            variant="left-accent"
            flexDirection="column"
            alignItems="flex-start"
            borderRadius="md"
          >
            <HStack mb={2} width="full">
              <AlertIcon boxSize={6} />
              <AlertTitle fontSize="lg">
                {analysis.is_video ? 'Video Analysis Complete' : 'Content Analysis Complete'}
              </AlertTitle>
              <Badge colorScheme={getStatusColor(analysis.safety_status)} ml="auto">
                {(analysis.risk_level || 'unknown').toUpperCase()} RISK
              </Badge>
            </HStack>
            
            <AlertDescription width="full">
              <Text mb={3}>{analysis.summary || analysis.description}</Text>

              {/* Safe Search Results */}
              {analysis.safe_search && (
                <Box mb={3}>
                  <Text fontWeight="600" fontSize="sm" mb={2}>Safety Check:</Text>
                  <HStack spacing={4} flexWrap="wrap">
                    <Badge colorScheme={analysis.safe_search.adult === 'VERY_UNLIKELY' || analysis.safe_search.adult === 'UNLIKELY' ? 'green' : 'orange'}>
                      Adult: {analysis.safe_search.adult}
                    </Badge>
                    <Badge colorScheme={analysis.safe_search.violence === 'VERY_UNLIKELY' || analysis.safe_search.violence === 'UNLIKELY' ? 'green' : 'orange'}>
                      Violence: {analysis.safe_search.violence}
                    </Badge>
                    <Badge colorScheme={analysis.safe_search.racy === 'VERY_UNLIKELY' || analysis.safe_search.racy === 'UNLIKELY' ? 'green' : 'orange'}>
                      Racy: {analysis.safe_search.racy}
                    </Badge>
                  </HStack>
                </Box>
              )}

              {/* Recommendations */}
              {analysis.recommendations && analysis.recommendations.length > 0 && (
                <Box mb={3}>
                  <Text fontWeight="600" fontSize="sm" mb={2}>Recommendations:</Text>
                  <List spacing={1}>
                    {analysis.recommendations.map((rec, idx) => (
                      <ListItem key={idx} fontSize="sm">
                        <ListIcon as={FaCheckCircle} color="blue.500" />
                        {rec}
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* Labels/Tags */}
              {analysis.labels && analysis.labels.length > 0 && (
                <Box>
                  <Text fontWeight="600" fontSize="sm" mb={2}>Detected Content:</Text>
                  <HStack spacing={2} flexWrap="wrap">
                    {analysis.labels.map((label, idx) => (
                      <Badge key={idx} colorScheme="blue" fontSize="xs">
                        {label.description} ({label.score}%)
                      </Badge>
                    ))}
                  </HStack>
                </Box>
              )}
            </AlertDescription>
          </Alert>
        )}
      </VStack>
    </Box>
  );
}
