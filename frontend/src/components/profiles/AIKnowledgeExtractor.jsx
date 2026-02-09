/**
 * AIKnowledgeExtractor Component
 * 
 * Allows users to upload documents or images to a Strategic Profile
 * and automatically extract key rules/guidelines using AI.
 * 
 * Features:
 * - Native file input with drag & drop support
 * - Document analysis (PDF, DOCX, TXT)
 * - Image analysis with color palette extraction
 * - Review and edit AI-generated summary
 * - Approve/reject extracted knowledge
 */

'use client';
import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Text,
  useColorModeValue,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Textarea,
  Badge,
  Icon,
  Spinner,
  useToast,
  Progress,
  Flex,
  Divider,
  Tooltip,
  IconButton,
  Alert,
  AlertIcon,
  SimpleGrid,
  Card,
  CardBody,
} from '@chakra-ui/react';
import {
  FaUpload,
  FaRobot,
  FaFileAlt,
  FaImage,
  FaCheck,
  FaTimes,
  FaEdit,
  FaPalette,
  FaLightbulb,
  FaMagic,
} from 'react-icons/fa';
import { useTranslation } from 'react-i18next';
import api from '@/lib/api';

// Accepted file types
const ACCEPTED_EXTENSIONS = '.pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp';
const ACCEPTED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'text/markdown',
  'image/png',
  'image/jpeg',
  'image/webp',
];

const AIKnowledgeExtractor = ({ profileId, userId, onKnowledgeAdded }) => {
  const { t } = useTranslation();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [editedSummary, setEditedSummary] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDragActive, setIsDragActive] = useState(false);
  
  const fileInputRef = useRef(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const gradientBg = useColorModeValue(
    'linear(to-br, brand.50, blue.50)',
    'linear(to-br, gray.700, blue.900)'
  );

  // Validate file type
  const isValidFile = (file) => {
    if (!file) return false;
    
    // Check MIME type
    if (ACCEPTED_MIME_TYPES.includes(file.type)) return true;
    
    // Fallback: check extension
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    return ACCEPTED_EXTENSIONS.includes(ext);
  };

  // Handle file upload
  const handleFile = useCallback(async (file) => {
    if (!file) return;
    
    if (!isValidFile(file)) {
      toast({
        title: t('strategicProfiles.aiKnowledgeExtractor.toasts.invalidFileType'),
        description: t('strategicProfiles.aiKnowledgeExtractor.toasts.invalidFileTypeDesc'),
        status: 'error',
        duration: 5000,
      });
      return;
    }

    setIsAnalyzing(true);
    setUploadProgress(10);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);
      
      setUploadProgress(30);
      
      const response = await api.post(
        `/knowledge-agent/analyze-upload/${profileId}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 50) / progressEvent.total
            ) + 30;
            setUploadProgress(percentCompleted);
          }
        }
      );
      
      setUploadProgress(90);
      
      if (response.data.success) {
        setAnalysisResult(response.data);
        setEditedSummary(response.data.summary || '');
        setUploadProgress(100);
        onOpen();
        
        toast({
          title: t('strategicProfiles.aiKnowledgeExtractor.toasts.analysisComplete'),
          description: t('strategicProfiles.aiKnowledgeExtractor.toasts.rulesExtracted', { 
            count: response.data.rule_count, 
            filename: file.name 
          }),
          status: 'success',
          duration: 3000,
        });
      } else {
        throw new Error(response.data.error || t('strategicProfiles.aiKnowledgeExtractor.toasts.analysisFailed'));
      }
      
    } catch (error) {
      console.error('Analysis error:', error);
      toast({
        title: t('strategicProfiles.aiKnowledgeExtractor.toasts.analysisFailed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsAnalyzing(false);
      setUploadProgress(0);
    }
  }, [profileId, userId, onOpen, toast, t]);

  // Native drag handlers
  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    // Only deactivate if leaving the drop zone entirely
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDragActive(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  const handleFileInput = useCallback((e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
    // Reset input to allow re-uploading same file
    e.target.value = '';
  }, [handleFile]);

  const handleZoneClick = () => {
    if (!isAnalyzing && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleApprove = async () => {
    try {
      await api.post(
        `/knowledge-agent/approve/${analysisResult.pending_id}`,
        {
          profile_id: profileId,
          user_id: userId,
          summary: analysisResult.summary,
          extracted_rules: analysisResult.key_rules || analysisResult.visual_rules || [],
          source_file: analysisResult.file_name,
          edited_summary: editedSummary !== analysisResult.summary ? editedSummary : null
        }
      );
      
      toast({
        title: t('strategicProfiles.aiKnowledgeExtractor.toasts.knowledgeSaved'),
        description: t('strategicProfiles.aiKnowledgeExtractor.toasts.rulesAdded'),
        status: 'success',
        duration: 3000,
      });
      
      onClose();
      setAnalysisResult(null);
      
      if (onKnowledgeAdded) {
        onKnowledgeAdded();
      }
      
    } catch (error) {
      toast({
        title: t('strategicProfiles.aiKnowledgeExtractor.toasts.saveFailed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleReject = async () => {
    try {
      await api.post(
        `/knowledge-agent/reject/${analysisResult.pending_id}`,
        null,
        { params: { reason: 'User rejected extraction' } }
      );
      
      toast({
        title: t('strategicProfiles.aiKnowledgeExtractor.toasts.extractionDiscarded'),
        status: 'info',
        duration: 2000,
      });
      
      onClose();
      setAnalysisResult(null);
      
    } catch (error) {
      console.error('Reject error:', error);
    }
  };

  // Get category color for badges
  const getCategoryColor = (category) => {
    const colors = {
      voice: 'blue',
      terminology: 'blue',
      prohibited: 'red',
      required: 'green',
      compliance: 'orange',
      formatting: 'teal',
      visual: 'pink',
    };
    return colors[category?.toLowerCase()] || 'gray';
  };

  return (
    <>
      {/* Upload Zone */}
      <Box
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleZoneClick}
        p={6}
        borderWidth="2px"
        borderStyle="dashed"
        borderColor={isDragActive ? 'brand.500' : borderColor}
        borderRadius="lg"
        bg={isDragActive ? hoverBg : 'transparent'}
        bgGradient={!isDragActive ? gradientBg : undefined}
        cursor={isAnalyzing ? 'wait' : 'pointer'}
        transition="all 0.2s"
        _hover={{ borderColor: 'brand.400', bg: hoverBg }}
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />
        
        <VStack spacing={3}>
          {isAnalyzing ? (
            <>
              <Spinner size="lg" color="brand.500" thickness="3px" />
              <Text fontWeight="600">{t('strategicProfiles.aiKnowledgeExtractor.analyzing')}</Text>
              <Progress
                value={uploadProgress}
                size="sm"
                colorScheme="brand"
                width="200px"
                borderRadius="full"
              />
              <Text fontSize="sm" color="gray.500">
                {t('strategicProfiles.aiKnowledgeExtractor.extractingRules')}
              </Text>
            </>
          ) : (
            <>
              <HStack spacing={2}>
                <Icon as={FaRobot} boxSize={6} color="brand.500" />
                <Icon as={FaMagic} boxSize={5} color="blue.500" />
              </HStack>
              <Text fontWeight="600" textAlign="center">
                {isDragActive
                  ? t('strategicProfiles.aiKnowledgeExtractor.dropHere')
                  : t('strategicProfiles.aiKnowledgeExtractor.title')}
              </Text>
              <Text fontSize="sm" color="gray.500" textAlign="center">
                {t('strategicProfiles.aiKnowledgeExtractor.dropHint')}
              </Text>
              <HStack spacing={2} flexWrap="wrap" justify="center">
                <Badge colorScheme="blue"><Icon as={FaFileAlt} mr={1} />{t('strategicProfiles.aiKnowledgeExtractor.fileTypes.pdf')}</Badge>
                <Badge colorScheme="blue"><Icon as={FaFileAlt} mr={1} />{t('strategicProfiles.aiKnowledgeExtractor.fileTypes.docx')}</Badge>
                <Badge colorScheme="green"><Icon as={FaImage} mr={1} />{t('strategicProfiles.aiKnowledgeExtractor.fileTypes.png')}</Badge>
                <Badge colorScheme="green"><Icon as={FaImage} mr={1} />{t('strategicProfiles.aiKnowledgeExtractor.fileTypes.jpg')}</Badge>
              </HStack>
            </>
          )}
        </VStack>
      </Box>

      {/* Review Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl" scrollBehavior="inside">
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent bg={cardBg}>
          <ModalHeader>
            <HStack>
              <Icon as={FaRobot} color="brand.500" />
              <Text>{t('strategicProfiles.aiKnowledgeExtractor.reviewModal.title')}</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            {analysisResult && (
              <VStack spacing={4} align="stretch">
                {/* File Info */}
                <HStack>
                  <Icon 
                    as={analysisResult.source_type === 'image' ? FaImage : FaFileAlt} 
                    color={analysisResult.source_type === 'image' ? 'green.500' : 'blue.500'}
                  />
                  <Text fontWeight="500">{analysisResult.file_name}</Text>
                  <Badge colorScheme={analysisResult.source_type === 'image' ? 'green' : 'blue'}>
                    {t(`strategicProfiles.aiKnowledgeExtractor.reviewModal.${analysisResult.source_type}`)}
                  </Badge>
                </HStack>
                
                <Divider />
                
                {/* Rule Count */}
                <Alert status="info" borderRadius="md">
                  <AlertIcon as={FaLightbulb} />
                  <Text>
                    {t('strategicProfiles.aiKnowledgeExtractor.reviewModal.rulesExtracted', {
                      count: analysisResult.rule_count,
                      type: t(`strategicProfiles.aiKnowledgeExtractor.reviewModal.${analysisResult.source_type}`)
                    })}
                  </Text>
                </Alert>
                
                {/* Extracted Rules */}
                {(analysisResult.key_rules || analysisResult.visual_rules) && (
                  <Box>
                    <Text fontWeight="600" mb={2}>{t('strategicProfiles.aiKnowledgeExtractor.reviewModal.extractedRules')}</Text>
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={2}>
                      {(analysisResult.key_rules || analysisResult.visual_rules || []).map((rule, idx) => (
                        <Card key={idx} size="sm" variant="outline">
                          <CardBody py={2} px={3}>
                            <HStack justify="space-between" mb={1}>
                              <Badge 
                                size="sm" 
                                colorScheme={getCategoryColor(rule.category)}
                              >
                                {t(`strategicProfiles.aiKnowledgeExtractor.categories.${rule.category?.toLowerCase()}`) || rule.category}
                              </Badge>
                              {rule.priority && (
                                <Badge 
                                  size="sm" 
                                  colorScheme={rule.priority === 'high' ? 'red' : 'gray'}
                                >
                                  {t(`strategicProfiles.aiKnowledgeExtractor.priority.${rule.priority?.toLowerCase()}`) || rule.priority}
                                </Badge>
                              )}
                            </HStack>
                            <Text fontSize="sm">{rule.rule}</Text>
                          </CardBody>
                        </Card>
                      ))}
                    </SimpleGrid>
                  </Box>
                )}
                
                {/* Color Palette for Images */}
                {analysisResult.colors && analysisResult.colors.length > 0 && (
                  <Box>
                    <HStack mb={2}>
                      <Icon as={FaPalette} color="pink.500" />
                      <Text fontWeight="600">{t('strategicProfiles.aiKnowledgeExtractor.reviewModal.detectedColors')}</Text>
                    </HStack>
                    <HStack spacing={2} flexWrap="wrap">
                      {analysisResult.colors.map((color, idx) => (
                        <Tooltip key={idx} label={color} placement="top">
                          <Box
                            w="40px"
                            h="40px"
                            bg={color}
                            borderRadius="md"
                            border="2px solid"
                            borderColor={borderColor}
                            cursor="pointer"
                          />
                        </Tooltip>
                      ))}
                    </HStack>
                  </Box>
                )}
                
                <Divider />
                
                {/* Editable Summary */}
                <Box>
                  <HStack mb={2}>
                    <Icon as={FaEdit} />
                    <Text fontWeight="600">{t('strategicProfiles.aiKnowledgeExtractor.reviewModal.summaryLabel')}</Text>
                  </HStack>
                  <Textarea
                    value={editedSummary}
                    onChange={(e) => setEditedSummary(e.target.value)}
                    minH="150px"
                    placeholder={t('strategicProfiles.aiKnowledgeExtractor.reviewModal.summaryPlaceholder')}
                  />
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    {t('strategicProfiles.aiKnowledgeExtractor.reviewModal.summaryHint')}
                  </Text>
                </Box>
              </VStack>
            )}
          </ModalBody>
          
          <ModalFooter>
            <HStack spacing={3}>
              <Button
                leftIcon={<FaTimes />}
                variant="outline"
                colorScheme="red"
                onClick={handleReject}
              >
                {t('strategicProfiles.aiKnowledgeExtractor.reviewModal.discard')}
              </Button>
              <Button
                leftIcon={<FaCheck />}
                colorScheme="brand"
                onClick={handleApprove}
              >
                {t('strategicProfiles.aiKnowledgeExtractor.reviewModal.approveAndSave')}
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default AIKnowledgeExtractor;
