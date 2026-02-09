'use client';
import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import { useWorkspace } from '@/context/WorkspaceContext';
import dynamic from 'next/dynamic';
import {
  Box, Button, Card, CardBody, Heading, Text, Textarea, VStack, HStack, Input, Select,
  Grid, Checkbox, CheckboxGroup, Stack, Icon, IconButton, Tooltip, Modal, ModalOverlay,
  ModalContent, ModalHeader, ModalBody, ModalCloseButton, ModalFooter, useDisclosure,
  useColorModeValue, Tabs, TabList, TabPanels, Tab, TabPanel, Badge, Table, Thead,
  Tbody, Tr, Th, Td, FormControl, FormLabel, useToast, Flex, Progress,
  Slider, SliderTrack, SliderFilledTrack, SliderThumb, SliderMark, FormHelperText,
  Spinner, Center, Wrap, WrapItem, Tag, TagLabel, Alert, AlertIcon, AlertDescription,
  Image, Divider, Avatar
} from '@chakra-ui/react';
import {
  FaMagic, FaCopy, FaClock, FaTrash, FaToggleOn, FaToggleOff, FaEdit,
  FaCalendarAlt, FaUpload, FaSyncAlt, FaCheckCircle, FaFacebookF, FaTwitter, FaLinkedinIn, FaInstagram,
  FaBrain, FaPaperPlane, FaExpand, FaFolderOpen, FaComments, FaPlus, FaUser, FaRobot, FaImage, FaShare
} from 'react-icons/fa';
import api, { getApiUrl } from '@/lib/api';
import { getErrorMessage } from '@/lib/errorUtils';
import VoiceDictation from '@/components/voice/VoiceDictation';
import useContentAnalyzer from '@/hooks/useContentAnalyzer';
import AnalysisResults from './components/AnalysisResults';
import PlatformSelector, { PLATFORM_CONFIG, getStrictestLimit, getPlatformGuidance } from '@/components/social/PlatformSelector';
import CharacterCounter from '@/components/common/CharacterCounter';
// ARCH-004: Background Job System imports for async operations
import useJobStatus, { JOB_STATUS, submitAsyncJob } from '@/hooks/useJobStatus';
import JobProgressIndicator from '@/components/common/JobProgressIndicator';
// ARCH-013: Rate Limiting UI
import { RateLimitBadge, RateLimitError } from '@/components/common/RateLimitIndicator';
import { useRateLimitStatus } from '@/hooks/useRateLimitStatus';

// Lazy load heavy components that aren't immediately visible
const VoiceAssistant = dynamic(() => import('@/components/voice/VoiceAssistant'), {
  ssr: false,
  loading: () => null,
});

const MediaAnalyzer = dynamic(() => import('@/components/media/MediaAnalyzer'), {
  ssr: false,
  loading: () => <Center py={4}><Spinner size="md" /></Center>,
});

const PostToSocialModal = dynamic(() => import('@/components/social/PostToSocialModal'), {
  ssr: false,
  loading: () => null,
});

export default function ContentGenerationTab({ user: propUser, language, setActiveTab }) {
  const { t } = useTranslation();
  const { user: authUser, isHydrated } = useAuth();  // Use auth context directly for reliability
  const { currentWorkspace, isEnterpriseWorkspace, enterpriseInfo } = useWorkspace();
  
  // Prefer auth context user over prop (prop is legacy, auth context is more reliable)
  const user = authUser || propUser;
  
  const [prompt, setPrompt] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentTone, setCurrentTone] = useState('professional');
  const [currentJobTitle, setCurrentJobTitle] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [activeCharLimit, setActiveCharLimit] = useState(null);  // Platform-aware character limit
  const [hashtagCount, setHashtagCount] = useState(3); // Default 3 hashtags
  const [scheduleHashtagCount, setScheduleHashtagCount] = useState(3); // For schedule prompt tab
  const { isOpen: isMediaOpen, onOpen: onMediaOpen, onClose: onMediaClose } = useDisclosure();
  const { isOpen: isPostOpen, onOpen: onPostOpen, onClose: onPostClose } = useDisclosure();
  const { isOpen: isSocialModalOpen, onOpen: onSocialModalOpen, onClose: onSocialModalClose } = useDisclosure();
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure();
  const [openModalInScheduleMode, setOpenModalInScheduleMode] = useState(false);
  
  // Conversation history for chat-style interaction (session-only)
  const [conversationHistory, setConversationHistory] = useState([]);
  const [followUpPrompt, setFollowUpPrompt] = useState('');
  const chatEndRef = useRef(null);
  
  // Store the pending prompt for async job completion
  const pendingPromptRef = useRef('');
  
  // Map to store prompts by job ID (more reliable than single ref)
  const jobPromptsRef = useRef(new Map());
  
  // Track if we've added to conversation for the current job (prevent duplicates)
  const lastAddedJobIdRef = useRef(null);
  
  // Edit prompt state
  const [editingPrompt, setEditingPrompt] = useState(null);
  
  // Promotional content checkbox state
  const [isPromotionalContent, setIsPromotionalContent] = useState(false);
  const [isSchedulePromotionalContent, setIsSchedulePromotionalContent] = useState(false);
  
  // Strategic Profile state
  const [strategicProfiles, setStrategicProfiles] = useState([]);
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  
  // Project state - for linking content to projects
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [loadingProjects, setLoadingProjects] = useState(false);
  
  // Image generation state
  const [includeImage, setIncludeImage] = useState(false);
  const [imageStyle, setImageStyle] = useState('simple');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [modelInfo, setModelInfo] = useState(null); // To show which AI model was used
  
  // Regeneration state
  const [regenerating, setRegenerating] = useState(false);
  const [regeneratingImage, setRegeneratingImage] = useState(false);
  const { isOpen: isFeedbackOpen, onOpen: onFeedbackOpen, onClose: onFeedbackClose } = useDisclosure();
  const { isOpen: isImageFeedbackOpen, onOpen: onImageFeedbackOpen, onClose: onImageFeedbackClose } = useDisclosure();
  const { isOpen: isContentExpandOpen, onOpen: onContentExpandOpen, onClose: onContentExpandClose } = useDisclosure();
  const { isOpen: isImageExpandOpen, onOpen: onImageExpandOpen, onClose: onImageExpandClose } = useDisclosure();
  const [contentFeedback, setContentFeedback] = useState('');
  const [imageFeedback, setImageFeedback] = useState('');
  const [contentBoxHeight, setContentBoxHeight] = useState(200); // Resizable height
  
  // Use reusable content analyzer hook (also provides rewriteContent)
  const { analyzing: analyzingGenerated, analysis, analyzeContent, rewriteContent, resetAnalysis, handleJobComplete: handleAnalysisJobComplete, handleJobError: handleAnalysisJobError, setAnalysisResult } = useContentAnalyzer();
  
  // Analysis job tracking state
  const [analysisJobId, setAnalysisJobId] = useState(null);
  
  // Scheduled content state
  const [scheduledPrompts, setScheduledPrompts] = useState([]);
  const [generatedHistory, setGeneratedHistory] = useState([]);
  const [connectedPlatforms, setConnectedPlatforms] = useState([]);
  const [scheduleData, setScheduleData] = useState({
    prompt: '',
    schedule_type: 'daily',
    schedule_time: '09:00',
    schedule_days: [],
    start_date: new Date().toISOString().split('T')[0], // Today's date
    timezone: 'UTC',
    auto_post: false,
    platforms: [],
    reanalyze_before_post: true,
    hashtag_count: 3
  });
  const [showScheduleOptions, setShowScheduleOptions] = useState(false);  // For showing/hiding schedule form
  const [isScheduling, setIsScheduling] = useState(false);  // For button loading state only
  const toast = useToast();
  
  // User permissions state for approval workflow
  const [userPermissions, setUserPermissions] = useState(null);
  const [submittingForApproval, setSubmittingForApproval] = useState(false);
  
  // ARCH-013: Rate limiting state
  const [rateLimitError, setRateLimitError] = useState(null);
  const { tier, hourlyRemaining, hourlyLimit, isNearLimit, refresh: refreshRateLimit } = useRateLimitStatus();
  
  // ARCH-004: Async job state for background processing
  const [generationJobId, setGenerationJobId] = useState(null);
  const [imageJobId, setImageJobId] = useState(null);
  const [useAsyncGeneration, setUseAsyncGeneration] = useState(true); // Enable async by default
  
  // Track content generation job status
  const {
    status: genJobStatus,
    progress: genJobProgress,
    result: genJobResult,
    error: genJobError,
    isLoading: genJobIsLoading,
    isCompleted: genJobIsCompleted,
    isFailed: genJobIsFailed,
    cancel: cancelGenJob,
  } = useJobStatus(generationJobId, {
    userId: user?.id,
    onComplete: (result) => {
      // Handle async content generation completion
      if (result?.generated_content || result?.content) {
        const content = result.generated_content || result.content;
        
        // Get the current jobId at time of completion
        const currentJobId = generationJobId;
        
        // Strong guard: check if we already processed this exact job
        if (!currentJobId || lastAddedJobIdRef.current === currentJobId) {
          console.log('[Conversation] Skipping duplicate completion callback for job:', currentJobId);
          return;
        }
        
        // Mark this job as processed BEFORE doing anything
        lastAddedJobIdRef.current = currentJobId;
        
        setGeneratedContent(content);
        
        // Store model info from the result
        if (result.model_used) {
          setModelInfo({
            text: {
              model: result.model_used,
              tier: result.model_tier,
              reasoning: result.model_reasoning,
              tokens: result.usage?.tokens_used,
              cost: result.usage?.estimated_cost
            }
          });
        }
        
        // Get prompt from multiple sources in order of reliability:
        // 1. result.prompt (from backend)
        // 2. jobPromptsRef map (stored by job ID)
        // 3. pendingPromptRef (legacy fallback)
        const originalPrompt = result.prompt || 
                               jobPromptsRef.current.get(currentJobId) || 
                               pendingPromptRef.current;
        
        // Only add to conversation if we have a valid prompt
        if (originalPrompt && originalPrompt.trim()) {
          console.log('[Conversation] Adding user prompt:', originalPrompt.substring(0, 50) + '...');
          addToConversation('user', originalPrompt);
        } else {
          console.warn('[Conversation] No prompt found for job:', currentJobId);
        }
        
        addToConversation('assistant', content);
        
        // Clean up the job prompt from the map
        jobPromptsRef.current.delete(currentJobId);
        
        // Clear the pending prompt
        pendingPromptRef.current = '';
        
        // Silent success - no toast needed, the UI updates show success
        
        // Auto-analyze the generated content (no toast here - handled by analysis job)
        analyzeGeneratedContent(content);
        
        // If image was requested, generate it now
        if (includeImage) {
          generateImageAsync(content);
        }
      }
      setLoading(false);
      setGenerationJobId(null);
    },
    onError: (error) => {
      setLoading(false);
      setGenerationJobId(null);
      toast({
        title: 'Generation failed',
        description: error || 'Please try again.',
        status: 'error',
        duration: 5000,
      });
    },
  });
  
  // Track image generation job status
  const {
    status: imgJobStatus,
    progress: imgJobProgress,
    result: imgJobResult,
    error: imgJobError,
    isLoading: imgJobIsLoading,
    isCompleted: imgJobIsCompleted,
    isFailed: imgJobIsFailed,
    cancel: cancelImgJob,
  } = useJobStatus(imageJobId, {
    userId: user?.id,
    onComplete: (result) => {
      // Handle async image generation completion
      // Backend returns: result.images[0].data (base64) or result.image_base64 (legacy)
      const imageData = result?.images?.[0]?.data || result?.image_base64;
      const imageUrl = result?.images?.[0]?.url || result?.url;
      const mimeType = result?.images?.[0]?.mime_type || result?.mime_type || 'image/png';
      
      if (imageData || imageUrl) {
        const imageObj = {
          base64: imageData,
          url: imageUrl,
          mimeType: mimeType,
          model: result.model,
          style: result.detected_style || result.style,
          justification: result.justification,
          cost: result.estimated_cost
        };
        setGeneratedImage(imageObj);
        
        // Update model info
        setModelInfo(prev => ({
          ...prev,
          image: {
            model: result.model,
            provider: result.provider,
            justification: result.justification
          }
        }));
        
        // Silent success - no toast needed, the image appearing is the feedback
      } else {
        // Only show warning if something went wrong
        toast({
          title: 'Image generation incomplete',
          description: 'No image data was returned. Please try regenerating.',
          status: 'warning',
          duration: 5000,
        });
      }
      setImageLoading(false);
      setImageJobId(null);
    },
    onError: (error) => {
      setImageLoading(false);
      setImageJobId(null);
      toast({
        title: 'Image generation failed',
        description: error || 'You can try regenerating the image.',
        status: 'warning',
        duration: 5000,
      });
    },
  });

  // Track content analysis job status
  const {
    status: analysisJobStatus,
    result: analysisJobResult,
    error: analysisJobError,
    isCompleted: analysisJobIsCompleted,
    isFailed: analysisJobIsFailed,
  } = useJobStatus(analysisJobId, {
    userId: user?.id,
    onComplete: (result) => {
      // Handle async analysis completion - silently update state, no toast
      if (result) {
        handleAnalysisJobComplete(result);
      }
      setAnalysisJobId(null);
    },
    onError: (error) => {
      handleAnalysisJobError(error);
      setAnalysisJobId(null);
      // Only show error toast, not success
      toast({
        title: 'Analysis failed',
        description: error || 'Could not analyze content.',
        status: 'error',
        duration: 5000,
      });
    },
  });

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const historyCardBg = useColorModeValue('white', 'gray.700');
  const analysisSectionBg = useColorModeValue('gray.50', 'gray.700');
  const accuracyBoxBg = useColorModeValue('blue.50', 'blue.900');
  const culturalBorderColor = useColorModeValue('blue.200', 'blue.600');
  const culturalBg = useColorModeValue('blue.50', 'blue.900');
  const culturalHoverBg = useColorModeValue('blue.100', 'blue.800');
  const culturalDimBg = useColorModeValue('white', 'gray.700');
  const culturalDimBorder = useColorModeValue('gray.200', 'gray.600');
  const feedbackBg = useColorModeValue('#fff7ed', 'orange.900');
  const feedbackBorder = useColorModeValue('#fed7aa', 'orange.700');
  const feedbackTextColor = useColorModeValue('orange.900', 'orange.100');
  const scheduleBoxBg = useColorModeValue('blue.50', 'blue.900');
  const schedulingBlueBg = useColorModeValue('blue.50', 'blue.900');
  const schedulingBorderColor = useColorModeValue('blue.200', 'blue.700');
  const borderColorDefault = useColorModeValue('gray.200', 'gray.600');

  // Load user permissions for approval workflow (ONLY for enterprise workspace)
  const loadUserPermissions = async () => {
    if (!user?.id) return;
    
    // Personal workspace doesn't have approval workflow
    // Only enterprise/company workspace uses approval
    if (!isEnterpriseWorkspace) {
      setUserPermissions({ can_publish_directly: true, needs_approval: false });
      return;
    }
    
    try {
      const API = getApiUrl();
      const response = await api.get(`/approval/user-permissions`, {
        headers: { 'X-User-ID': user.id }
      });
      setUserPermissions(response.data.permissions);
    } catch (error) {
      console.error('Failed to load user permissions:', error);
      // Default to allowing publish (backwards compatibility for existing users)
      setUserPermissions({ can_publish_directly: true, needs_approval: false });
    }
  };

  // Load connected platforms for auto-post
  const loadConnectedPlatforms = async () => {
    if (!user?.id) return;
    try {
      const API = getApiUrl();
      const response = await api.get(`/social/profiles`, {
        headers: { 'X-User-ID': user.id },
        params: { sync: false }  // Use cached data for faster loading
      });
      const profiles = response.data.profiles || [];
      if (profiles.length > 0) {
        setConnectedPlatforms(profiles[0].linked_networks || []);
      }
    } catch (error) {
      console.error('Failed to load connected platforms:', error);
    }
  };

  // Load strategic profiles
  const loadStrategicProfiles = async () => {
    if (!user?.id) return;
    setLoadingProfiles(true);
    try {
      const API = getApiUrl();
      let profiles = [];
      
      if (isEnterpriseWorkspace && enterpriseInfo?.id) {
        // Load enterprise strategic profiles
        const response = await api.get(`/enterprises/${enterpriseInfo.id}/strategic-profiles`, {
          headers: { 'X-User-ID': user.id }
        });
        profiles = response.data.profiles || [];
        console.log('ContentGeneration: Loaded enterprise strategic profiles:', profiles.length);
      } else {
        // Load personal strategic profiles
        const response = await api.get(`/profiles/strategic`, {
          headers: { 'X-User-ID': user.id }
        });
        profiles = response.data.profiles || [];
        console.log('ContentGeneration: Loaded personal strategic profiles:', profiles.length);
      }
      
      setStrategicProfiles(profiles);
      // Reset selected profile and select default when profiles change
      setSelectedProfileId(null);
      const defaultProfile = profiles.find(p => p.is_default);
      if (defaultProfile) {
        setSelectedProfileId(defaultProfile.id);
      }
    } catch (error) {
      console.error('Failed to load strategic profiles:', error);
    } finally {
      setLoadingProfiles(false);
    }
  };

  // Get selected profile data
  const getSelectedProfile = () => {
    return strategicProfiles.find(p => p.id === selectedProfileId);
  };
  
  // Auto-populate platforms from selected strategic profile
  useEffect(() => {
    if (selectedProfileId && strategicProfiles.length > 0) {
      const profile = strategicProfiles.find(p => p.id === selectedProfileId);
      if (profile?.default_platforms && profile.default_platforms.length > 0) {
        setSelectedPlatforms(profile.default_platforms);
      }
    }
  }, [selectedProfileId, strategicProfiles]);

  // Load projects for user
  const loadProjects = async () => {
    if (!user?.id) return;
    setLoadingProjects(true);
    try {
      const API = getApiUrl();
      const response = await api.get(`/projects`, {
        headers: { 'X-User-ID': user.id }
      });
      setProjects(response.data.projects || []);
      
      // Check URL for pre-selected project
      const urlParams = new URLSearchParams(window.location.search);
      const projectFromUrl = urlParams.get('project');
      if (projectFromUrl) {
        setSelectedProjectId(projectFromUrl);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoadingProjects(false);
    }
  };

  // Update active character limit when platforms change
  useEffect(() => {
    const limit = getStrictestLimit(selectedPlatforms);
    setActiveCharLimit(limit);
  }, [selectedPlatforms]);

  // Load default platforms from selected strategic profile
  useEffect(() => {
    if (selectedProfileId && strategicProfiles.length > 0) {
      const profile = strategicProfiles.find(p => p.id === selectedProfileId);
      if (profile?.default_platforms && profile.default_platforms.length > 0) {
        setSelectedPlatforms(profile.default_platforms);
      }
    }
  }, [selectedProfileId, strategicProfiles]);

  // Auto-rewrite when generated content has low analysis score (runs ONCE only)
  const autoRewriteTriggeredRef = useRef(false);
  
  useEffect(() => {
    // Skip if no analysis, no generated content, or already triggered
    if (!analysis || !generatedContent || loading || autoRewriteTriggeredRef.current) {
      return;
    }
    
    const overallScore = analysis.overall_score ?? 
      Math.round((
        (analysis.compliance_score ?? 70) + 
        (analysis.accuracy_score ?? 85) + 
        (analysis.cultural_score ?? 75)
      ) / 3);
    
    // Only auto-rewrite if score is below 80 - triggers ONCE
    if (overallScore < 80) {
      console.log(`ContentGeneration: Auto-rewrite triggered - score ${overallScore} < 80`);
      autoRewriteTriggeredRef.current = true;
      handleRewriteGenerated();
    }
  }, [analysis, generatedContent, loading]);
  
  // Reset auto-rewrite trigger when new content is generated
  useEffect(() => {
    if (!generatedContent) {
      autoRewriteTriggeredRef.current = false;
    }
  }, [generatedContent]);

  useEffect(() => {
    // Wait for auth to be hydrated before making API calls
    if (!isHydrated) {
      console.log('ContentGenerationTab: Waiting for auth hydration...');
      return;
    }
    
    if (user?.id) {
      console.log('ContentGenerationTab: Loading data for user:', user.id);
      setCurrentTone(user.default_tone || 'professional');
      setCurrentJobTitle(user.job_title || '');
      loadScheduledPrompts();
      loadGeneratedHistory();
      loadConnectedPlatforms();
      loadStrategicProfiles();
      loadUserPermissions();
      loadProjects();  // Load projects on mount
    } else {
      console.log('ContentGenerationTab: No user available yet');
    }
  }, [isHydrated, user?.id]); // Watch for hydration and user.id

  // Reload user permissions when workspace changes
  useEffect(() => {
    if (isHydrated && user?.id) {
      loadUserPermissions();
      loadStrategicProfiles();
    }
  }, [isEnterpriseWorkspace, enterpriseInfo?.id]);

  const loadScheduledPrompts = async () => {
    if (!user) return;
    try {
      const API = getApiUrl();
      const response = await api.get(`/scheduler/scheduled-prompts`, {
        headers: { 'X-User-ID': user.id }
      });
      setScheduledPrompts(response.data || []);
    } catch (error) {
      console.error('Failed to load scheduled prompts:', error);
    }
  };

  const loadGeneratedHistory = async () => {
    if (!user) return;
    try {
      const API = getApiUrl();
      const response = await api.get(`/generated-content`, {
        headers: { 'user-id': user.id }
      });
      setGeneratedHistory(response.data.generated_content || []);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast({
        title: t('contentGeneration.errors.enterPrompt'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    setGeneratedContent('');
    setGeneratedImage(null);
    setModelInfo(null);
    resetAnalysis();
    
    // Platform-aware context for generation
    const platformGuidance = getPlatformGuidance(selectedPlatforms);
    const platformContext = selectedPlatforms.length > 0 ? {
      target_platforms: selectedPlatforms,
      platform_guidance: platformGuidance,
      character_limit: activeCharLimit
    } : null;
    
    try {
      // ARCH-004: Use async mode for better UX (no timeout, real-time progress)
      if (useAsyncGeneration) {
        // Store the prompt BEFORE anything else, so we can use it when job completes
        const currentPrompt = prompt.trim();
        pendingPromptRef.current = currentPrompt;
        console.log('[ContentGen] Stored prompt in ref:', currentPrompt.substring(0, 50) + '...');
        
        // Submit async job
        const { jobId, error } = await submitAsyncJob('/content/generate/async', {
          prompt: currentPrompt,
          tone: currentTone,
          job_title: currentJobTitle,
          platforms: selectedPlatforms,
          language: language,
          hashtag_count: hashtagCount,
          profile_id: selectedProfileId,
          platform_context: platformContext,
          character_limit: activeCharLimit,
          content_type: 'post'
        }, user?.id);
        
        if (error) {
          throw new Error(error);
        }
        
        // Store prompt by job ID for reliable retrieval on completion
        if (jobId) {
          jobPromptsRef.current.set(jobId, currentPrompt);
          console.log('[ContentGen] Stored prompt for job:', jobId);
        }
        
        // Store job ID for tracking - the useJobStatus hook will handle completion
        setGenerationJobId(jobId);
        
        // Clear UI prompt for follow-up input (but pendingPromptRef and jobPromptsRef still have the value)
        setPrompt('');
        
        return; // Job completion is handled by the useJobStatus hook
      }
      
      // Legacy synchronous mode (fallback)
      const API = getApiUrl();
      
      // Generate text content with Strategic Profile and Platform context
      const response = await api.post(`/content/generate`, {
        prompt,
        tone: currentTone,
        job_title: currentJobTitle,
        user_id: user?.id,
        platforms: selectedPlatforms,
        language: language,
        hashtag_count: hashtagCount,
        profile_id: selectedProfileId,  // Include strategic profile for RAG context
        platform_context: platformContext,  // Platform-aware generation
        character_limit: activeCharLimit  // Enforce character limit
      });
      
      const content = response.data.generated_content;
      setGeneratedContent(content);
      
      // Store model info from the response
      if (response.data.model_used) {
        setModelInfo({
          text: {
            model: response.data.model_used,
            tier: response.data.model_tier,
            reasoning: response.data.model_reasoning,
            tokens: response.data.usage?.tokens_used,
            cost: response.data.usage?.estimated_cost
          }
        });
      }
      
      // Show character limit warning if over limit
      if (activeCharLimit && content.length > activeCharLimit) {
        toast({
          title: 'Content exceeds character limit',
          description: `Generated ${content.length} characters, but limit is ${activeCharLimit}. Consider editing or regenerating.`,
          status: 'warning',
          duration: 5000,
        });
      }

      // Generate image if requested using async method
      if (includeImage) {
        await generateImageAsync(content);
      }

      // Auto-analyze the generated content AFTER image generation
      await analyzeGeneratedContent(content);
      
      // Add to conversation history
      addToConversation('user', prompt);
      addToConversation('assistant', content);
      
      // Clear prompt for follow-up input
      setPrompt('');
      
      // Scroll to latest message
      setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      
    } catch (error) {
      // ARCH-013: Handle rate limit errors specifically
      if (error.response?.status === 429) {
        const rateLimitData = error.response?.data?.detail || error.response?.data;
        setRateLimitError(rateLimitData);
        toast({
          title: 'Rate limit exceeded',
          description: rateLimitData?.message || 'You have exceeded your hourly request limit.',
          status: 'warning',
          duration: 8000,
        });
      } else {
        toast({
          title: t('contentGeneration.errors.generationFailed'),
          description: getErrorMessage(error),
          status: 'error',
          duration: 5000,
        });
      }
    } finally {
      if (!useAsyncGeneration) {
        setLoading(false);
      }
    }
  };
  
  // ARCH-004: Async image generation helper
  const generateImageAsync = async (contentText) => {
    if (!contentText?.trim()) return;
    
    setImageLoading(true);
    setGeneratedImage(null);
    
    const imagePrompt = `Create a professional social media image that visually represents this content: ${contentText.substring(0, 300)}`;
    
    try {
      // Try async endpoint first
      const { jobId, error } = await submitAsyncJob('/ai/generate-image/async', {
        prompt: imagePrompt,
        style: imageStyle,
        model: 'gpt-image-1',
        size: '1024x1024',
        quality: 'auto'
      }, user?.id);
      
      if (error) {
        throw new Error(error);
      }
      
      // Store job ID for tracking - the useJobStatus hook will handle completion
      setImageJobId(jobId);
      
      // No toast needed - the visual indicator shows image is generating
      
    } catch (asyncError) {
      console.warn('Async image generation failed, falling back to sync:', asyncError);
      
      // Fallback to synchronous with retries
      const API = getApiUrl();
      const maxRetries = 3;
      let retryCount = 0;
      let imageGenerated = false;
      
      while (retryCount < maxRetries && !imageGenerated) {
        try {
          if (retryCount > 0) {
            await new Promise(resolve => setTimeout(resolve, 1500 * retryCount));
            // Silent retry - no toast needed
          }
          
          const imageResponse = await api.post(`/content/generate-image`, {
            prompt: imagePrompt,
            style: imageStyle,
            prefer_quality: retryCount > 0
          }, {
            headers: { 'X-User-ID': user?.id },
            timeout: 45000
          });
          
          if (imageResponse.data.success && imageResponse.data.image_base64) {
            setGeneratedImage({
              base64: imageResponse.data.image_base64,
              mimeType: imageResponse.data.mime_type || 'image/png',
              model: imageResponse.data.model,
              style: imageResponse.data.detected_style,
              justification: imageResponse.data.justification,
              cost: imageResponse.data.estimated_cost
            });
            
            setModelInfo(prev => ({
              ...prev,
              image: {
                model: imageResponse.data.model,
                provider: imageResponse.data.provider,
                justification: imageResponse.data.justification
              }
            }));
            
            // Silent success - image appearing is the feedback
            imageGenerated = true;
          } else {
            retryCount++;
          }
        } catch (imageError) {
          retryCount++;
          if (retryCount >= maxRetries) {
            // Only show error after all retries failed
            toast({
              title: t('contentGeneration.toasts.imageGenerationFailed'),
              description: `${getErrorMessage(imageError)}. You can click "Regenerate picture" to try again.`,
              status: 'warning',
              duration: 5000,
            });
          }
        }
      }
      setImageLoading(false);
    }
  };
  
  // Helper to add messages to conversation history - with deduplication
  const addToConversation = (role, content) => {
    setConversationHistory(prev => {
      // Prevent duplicate entries (same role + content within last 2 messages)
      const lastTwoMessages = prev.slice(-2);
      const isDuplicate = lastTwoMessages.some(
        msg => msg.role === role && msg.content === content
      );
      
      if (isDuplicate) {
        console.log('[Conversation] Skipping duplicate message');
        return prev; // Don't add duplicate
      }
      
      return [
        ...prev,
        { role, content, timestamp: new Date().toISOString() }
      ];
    });
    
    // Scroll to latest message
    setTimeout(() => {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };
  
  // Handle follow-up conversation - send context-aware refinement request
  const handleFollowUp = async () => {
    if (!followUpPrompt.trim()) {
      toast({
        title: 'Please enter a follow-up message',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setLoading(true);
    
    try {
      const API = getApiUrl();
      const selectedProfile = getSelectedProfile();
      
      // Build conversation context for the AI
      const conversationContext = conversationHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Add the follow-up request
      conversationContext.push({
        role: 'user',
        content: followUpPrompt
      });
      
      // Generate with conversation context
      const response = await api.post(`/content/generate`, {
        prompt: followUpPrompt,
        tone: selectedProfile?.writing_tone || currentTone,
        job_title: selectedProfile?.job_title || currentJobTitle,
        user_id: user?.id,
        platforms: selectedPlatforms,
        language: language,
        hashtag_count: hashtagCount,
        profile_id: selectedProfileId,
        conversation_history: conversationContext,  // Pass conversation context
        character_limit: activeCharLimit,
        is_follow_up: true  // Flag to indicate this is a refinement request
      });
      
      const content = response.data.generated_content;
      setGeneratedContent(content);
      
      // Update conversation history
      const newConversation = [
        ...conversationHistory,
        { role: 'user', content: followUpPrompt, timestamp: new Date().toISOString() },
        { role: 'assistant', content: content, timestamp: new Date().toISOString() }
      ];
      setConversationHistory(newConversation);
      
      // Clear follow-up input
      setFollowUpPrompt('');
      
      // Scroll to latest
      setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      
      toast({
        title: 'Content refined successfully!',
        status: 'success',
        duration: 3000,
      });
      
      // Auto-analyze the new content
      await analyzeGeneratedContent(content);
      
    } catch (error) {
      toast({
        title: 'Refinement failed',
        description: getErrorMessage(error),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Quick action handlers for AI response refinement
  const handleQuickAction = async (action, content) => {
    if (!content) return;
    
    let refinementPrompt = '';
    switch (action) {
      case 'shorter':
        refinementPrompt = 'Make this content shorter and more concise while keeping the key message.';
        break;
      case 'emojis':
        refinementPrompt = 'Add relevant emojis to make this content more engaging and visually appealing.';
        break;
      case 'professional':
        refinementPrompt = 'Rewrite this content in a more professional and formal tone.';
        break;
      default:
        return;
    }
    
    setPrompt(refinementPrompt);
    // The user can then click send to process the refinement
    toast({
      title: `Refinement: ${action}`,
      description: 'Click send to apply this refinement',
      status: 'info',
      duration: 2000,
    });
  };
  
  // Clear conversation and start fresh
  const handleNewConversation = () => {
    setConversationHistory([]);
    setPrompt('');
    setFollowUpPrompt('');
    setGeneratedContent('');
    setGeneratedImage(null);
    resetAnalysis();
    lastAddedJobIdRef.current = null; // Reset job tracking
    pendingPromptRef.current = '';
    toast({
      title: 'Conversation cleared',
      description: 'Start a new content generation',
      status: 'info',
      duration: 2000,
    });
  };

  // Analyze generated content wrapper with toast notifications
  const analyzeGeneratedContent = async (content) => {
    const result = await analyzeContent(content, {
      userId: user?.id,
      language: language,
      tone: currentTone,
      jobTitle: currentJobTitle,
      profileId: selectedProfileId,  // Include strategic profile for cultural analysis
    });
    
    // Check if result is async (has jobId) or sync (has analysis data)
    if (result?.jobId) {
      // Async mode - store job ID for tracking (analysis runs silently)
      setAnalysisJobId(result.jobId);
      // No toast here - analysis happens silently in background
    } else if (!result) {
      // Only show toast on error
      toast({
        title: t('contentGeneration.toasts.analysisFailed'),
        description: t('contentGeneration.toasts.couldNotAnalyze'),
        status: 'error',
        duration: 3000,
      });
    }
    // For sync mode with result - analysis is already complete, no toast needed
  };

  const handleRewriteGenerated = async () => {
    if (!generatedContent) return;
    
    setLoading(true);
    try {
      const response = await api.post(`/content/rewrite`, {
        content: generatedContent,
        tone: currentTone,
        job_title: currentJobTitle,
        user_id: user?.id,
        language: language,
        hashtag_count: hashtagCount,
        profile_id: selectedProfileId,
        analysis_result: analysis || {},
        use_iterative: true,  // Use iterative agent to guarantee score >= 80
        target_score: 80
      });
      
      setGeneratedContent(response.data.rewritten_content);
      
      // Re-analyze after rewrite (silently)
      await analyzeGeneratedContent(response.data.rewritten_content);
      
    } catch (error) {
      console.error('Rewrite error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyContent = () => {
    if (generatedContent) {
      navigator.clipboard.writeText(generatedContent);
      toast({
        title: 'Copied to clipboard!',
        status: 'success',
        duration: 2000,
      });
    }
  };

  const handleUseInAnalyzeTab = () => {
    if (generatedContent) {
      localStorage.setItem('generated_content', generatedContent);
      setActiveTab(0);
      toast({
        title: 'Content loaded!',
        description: 'Switched to Analyze Content tab',
        status: 'success',
        duration: 2000,
      });
    }
  };

  // Save generated content as draft
  const handleSaveDraft = async () => {
    if (!generatedContent.trim()) {
      toast({ title: 'No content to save', status: 'warning', duration: 3000 });
      return;
    }

    try {
      const API = getApiUrl();
      const postResponse = await api.post(`/posts`, {
        title: generatedContent.substring(0, 50) + '...',
        content: generatedContent,
        platforms: [],
        status: 'draft',
        user_id: user?.id,
        project_id: selectedProjectId || null,  // Include project_id if selected
        workspace_type: isEnterpriseWorkspace ? 'enterprise' : 'personal',
        enterprise_id: isEnterpriseWorkspace ? enterpriseInfo?.id : null
      }, {
        headers: { 'X-User-ID': user?.id }
      });

      // If project is selected and post was created, link it to the project
      if (selectedProjectId && postResponse.data?.id) {
        try {
          await api.post(`/projects/${selectedProjectId}/content`, {
            content_id: postResponse.data.id,
            content_type: 'post'
          }, {
            headers: { 'X-User-ID': user?.id }
          });
        } catch (linkError) {
          console.error('Failed to link post to project:', linkError);
        }
      }

      const selectedProject = projects.find(p => p.project_id === selectedProjectId);
      toast({
        title: 'Draft saved successfully!',
        description: selectedProject ? `Linked to project: ${selectedProject.name}` : '',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({ title: 'Failed to save draft', status: 'error', duration: 3000 });
    }
  };

  // Submit content for approval (for Creator role users)
  const handleSubmitForApproval = async () => {
    if (!generatedContent.trim()) {
      toast({ title: 'No content to submit', status: 'warning', duration: 3000 });
      return;
    }

    setSubmittingForApproval(true);
    try {
      const API = getApiUrl();
      
      // First save as draft with project_id
      const postResponse = await api.post(`/posts`, {
        title: generatedContent.substring(0, 50) + '...',
        content: generatedContent,
        platforms: selectedPlatforms,
        status: 'draft',
        user_id: user?.id,
        project_id: selectedProjectId || null,  // Include project_id if selected
        workspace_type: isEnterpriseWorkspace ? 'enterprise' : 'personal',
        enterprise_id: isEnterpriseWorkspace ? enterpriseInfo?.id : null
      }, {
        headers: { 'X-User-ID': user?.id }
      });
      
      const postId = postResponse.data.id;
      
      // If project is selected, link it to the project
      if (selectedProjectId && postId) {
        try {
          await api.post(`/projects/${selectedProjectId}/content`, {
            content_id: postId,
            content_type: 'post'
          }, {
            headers: { 'X-User-ID': user?.id }
          });
        } catch (linkError) {
          console.error('Failed to link post to project:', linkError);
        }
      }
      
      // Then submit for approval
      await api.post(`/approval/submit/${postId}`, {}, {
        headers: { 'X-User-ID': user?.id }
      });

      const selectedProject = projects.find(p => p.project_id === selectedProjectId);
      toast({
        title: 'Submitted for approval!',
        description: selectedProject 
          ? `Linked to project: ${selectedProject.name}. Your manager will review this content.`
          : 'Your manager will review this content.',
        status: 'success',
        duration: 5000,
      });
      
      // Clear form after successful submission
      setGeneratedContent('');
      setGeneratedImage(null);
      resetAnalysis();
      
    } catch (error) {
      toast({ 
        title: 'Failed to submit for approval', 
        description: getErrorMessage(error),
        status: 'error', 
        duration: 5000 
      });
    } finally {
      setSubmittingForApproval(false);
    }
  };

  // Clear generated content
  const handleClearGenerated = () => {
    if (generatedContent.trim() && !confirm('Are you sure you want to clear the generated content?')) {
      return;
    }
    setGeneratedContent('');
    setGeneratedImage(null);
    resetAnalysis();
  };

  // Regenerate content with optional feedback
  const handleRegenerateContent = async () => {
    setRegenerating(true);
    try {
      const API = getApiUrl();
      const response = await api.post(`/content/regenerate`, {
        original_content: generatedContent,
        original_prompt: prompt,
        feedback: contentFeedback || null,
        tone: currentTone,
        job_title: currentJobTitle,
        platforms: selectedPlatforms,
        language: language,
        hashtag_count: hashtagCount
      }, {
        headers: { 'X-User-ID': user?.id || 'anonymous' }
      });

      setGeneratedContent(response.data.regenerated_content);
      setModelInfo({
        text: {
          model: response.data.model_used,
          tier: response.data.model_tier,
          tokens: response.data.usage?.tokens_used,
          cost: response.data.usage?.estimated_cost,
          reasoning: response.data.feedback_incorporated 
            ? 'Regenerated with your feedback' 
            : 'Fresh alternative generated'
        }
      });

      // Re-analyze the new content
      await analyzeContent(response.data.regenerated_content, user?.id);

      toast({
        title: 'Content regenerated!',
        description: contentFeedback ? 'Your feedback was incorporated' : 'Fresh alternative created',
        status: 'success',
        duration: 3000,
      });

      setContentFeedback('');
      onFeedbackClose();
    } catch (error) {
      toast({
        title: 'Regeneration failed',
        description: getErrorMessage(error),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setRegenerating(false);
    }
  };

  // Regenerate image with optional feedback - based on the GENERATED CONTENT
  const handleRegenerateImage = async () => {
    setRegeneratingImage(true);
    try {
      const API = getApiUrl();
      // Use the generated content for the image, not the original prompt
      const imagePrompt = `Create a professional social media image that visually represents this content: ${generatedContent.substring(0, 300)}`;
      
      const response = await api.post(`/content/regenerate-image`, {
        original_prompt: imagePrompt,
        feedback: imageFeedback || null,
        style: imageStyle,
        prefer_quality: true
      }, {
        headers: { 'X-User-ID': user?.id || 'anonymous' }
      });

      if (response.data.success) {
        setGeneratedImage({
          base64: response.data.image_base64,
          mimeType: response.data.mime_type || 'image/png',
          model: response.data.model,
          style: response.data.detected_style,
          justification: response.data.justification,
          cost: response.data.estimated_cost
        });

        // Silent success - image appearing is the feedback
      } else {
        throw new Error(response.data.error || 'Image regeneration failed');
      }

      setImageFeedback('');
      onImageFeedbackClose();
    } catch (error) {
      toast({
        title: 'Image regeneration failed',
        description: getErrorMessage(error),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setRegeneratingImage(false);
    }
  };

  // Schedule a prompt for future content generation
  const schedulePromptForGeneration = async () => {
    if (!prompt.trim()) {
      toast({
        title: t('contentGeneration.errors.promptRequired'),
        description: t('contentGeneration.errors.enterPromptToSchedule'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (!scheduleData.start_date) {
      toast({
        title: t('contentGeneration.errors.selectStartDate'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (selectedPlatforms.length === 0) {
      toast({
        title: t('contentGeneration.errors.selectPlatform'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsScheduling(true);
    try {
      const API = getApiUrl();
      
      // Schedule the prompt for future content generation
      const response = await api.post(`/scheduler/schedule-prompt`, {
        prompt: prompt,
        schedule_type: scheduleData.schedule_type,
        schedule_time: scheduleData.schedule_time,
        start_date: scheduleData.start_date,
        schedule_days: scheduleData.schedule_days,
        platforms: selectedPlatforms,
        auto_post: scheduleData.auto_post,
        tone: currentTone,
        reanalyze_before_post: scheduleData.reanalyze_before_post,
        workspace_type: isEnterpriseWorkspace ? 'enterprise' : 'personal',
        enterprise_id: isEnterpriseWorkspace ? enterpriseInfo?.id : null
      }, {
        headers: { 'X-User-ID': user?.id }
      });
      
      const scheduledDateTime = new Date(scheduleData.start_date + 'T' + scheduleData.schedule_time);
      const needsApproval = response.data.needs_approval;
      
      toast({
        title: 'Prompt Scheduled!',
        description: needsApproval
          ? `Content will be generated on ${scheduledDateTime.toLocaleString()} and submitted for manager approval`
          : scheduleData.auto_post 
            ? `Content will be generated and auto-posted on ${scheduledDateTime.toLocaleString()} if score ≥ 85`
            : `Content will be generated on ${scheduledDateTime.toLocaleString()} and saved for your review`,
        status: 'success',
        duration: 6000,
      });

      // Reset form
      setPrompt('');
      setGeneratedContent('');
      resetAnalysis();
      loadScheduledPrompts();
      
    } catch (error) {
      toast({
        title: 'Failed to schedule prompt',
        description: getErrorMessage(error),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsScheduling(false);
    }
  };

  const createSchedule = async () => {
    if (!scheduleData.prompt) {
      toast({
        title: t('contentGeneration.errors.enterPrompt'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (scheduleData.auto_post && (!scheduleData.platforms || scheduleData.platforms.length === 0)) {
      toast({
        title: t('contentGeneration.errors.selectPlatformAutoPost'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsScheduling(true);
    try {
      const API = getApiUrl();
      await api.post(`/scheduled-prompts`, scheduleData, {
        headers: { 'user-id': user.id }
      });
      
      toast({
        title: t('contentGeneration.toasts.scheduleCreated'),
        description: scheduleData.auto_post 
          ? t('contentGeneration.toasts.contentGeneratedPosted') 
          : t('contentGeneration.toasts.contentGeneratedAuto'),
        status: 'success',
        duration: 5000,
      });

      setScheduleData({
        prompt: '',
        schedule_type: 'daily',
        schedule_time: '09:00',
        schedule_days: [],
        timezone: 'UTC',
        auto_post: false,
        platforms: [],
        reanalyze_before_post: true
      });
      
      loadScheduledPrompts();
    } catch (error) {
      toast({
        title: t('contentGeneration.errors.createScheduleFailed'),
        description: getErrorMessage(error),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsScheduling(false);
    }
  };

  const deleteSchedule = async (id) => {
    try {
      const API = getApiUrl();
      await api.delete(`/scheduler/scheduled-prompts/${id}`, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: t('contentGeneration.toasts.scheduleRemoved'),
        status: 'success',
        duration: 2000,
      });
      
      loadScheduledPrompts();
    } catch (error) {
      toast({
        title: t('contentGeneration.errors.deleteScheduleFailed'),
        status: 'error',
        duration: 3000,
      });
    }
  };

  const toggleSchedule = async (id) => {
    try {
      const API = getApiUrl();
      await api.put(`/scheduler/scheduled-prompts/${id}/toggle`, {}, {
        headers: { 'X-User-ID': user.id }
      });
      
      loadScheduledPrompts();
    } catch (error) {
      toast({
        title: t('contentGeneration.errors.toggleScheduleFailed'),
        status: 'error',
        duration: 3000,
      });
    }
  };

  const openEditPrompt = (promptData) => {
    setEditingPrompt({
      ...promptData,
      hashtag_count: promptData.hashtag_count || 3
    });
    onEditOpen();
  };

  const saveEditedPrompt = async () => {
    if (!editingPrompt) return;
    
    try {
      const API = getApiUrl();
      await api.put(`/scheduler/scheduled-prompts/${editingPrompt.id}`, {
        prompt: editingPrompt.prompt,
        schedule_type: editingPrompt.schedule_type,
        schedule_time: editingPrompt.schedule_time,
        auto_post: editingPrompt.auto_post,
        platforms: editingPrompt.platforms,
        hashtag_count: editingPrompt.hashtag_count
      }, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: 'Scheduled prompt updated',
        status: 'success',
        duration: 2000,
      });
      
      onEditClose();
      setEditingPrompt(null);
      loadScheduledPrompts();
    } catch (error) {
      toast({
        title: 'Failed to update prompt',
        description: getErrorMessage(error),
        status: 'error',
        duration: 5000,
      });
    }
  };

  const getFlagColor = (status) => {
    if (!status) return 'gray';
    const colorMap = {
      'no_flag': 'green',
      'minor_concern': 'yellow',
      'policy_violation': 'orange',
      'harassment': 'red',
      'hate_speech': 'red'
    };
    return colorMap[status] || 'gray';
  };

  const quickSuggestions = [
    'Announce a new product launch',
    'Share a customer success story',
    'Promote an upcoming event or webinar',
    'Create a motivational Monday post',
    'Share industry insights or trends',
    'Celebrate a company milestone',
    'Share a team achievement',
    'Post about company culture'
  ];

  return (
    <Box>
      {/* ARCH-013: Rate Limit Error Display */}
      {rateLimitError && (
        <Box mb={4}>
          <RateLimitError 
            error={rateLimitError} 
            onRetry={() => {
              setRateLimitError(null);
              refreshRateLimit();
            }} 
          />
        </Box>
      )}
      
      <Tabs variant="enclosed" colorScheme="brand">
        <TabList>
          <Tab fontSize={{ base: 'xs', md: 'sm' }}><Icon as={FaMagic} mr={2} /> {t('contentGeneration.tabs.generatePost')}</Tab>
          <Tab fontSize={{ base: 'xs', md: 'sm' }}><Icon as={FaCalendarAlt} mr={2} /> {t('contentGeneration.tabs.schedulePrompt')}</Tab>
          {/* ARCH-013: Rate Limit Badge */}
          <Box ml="auto" display="flex" alignItems="center">
            <RateLimitBadge showUpgrade={true} />
          </Box>
        </TabList>

        <TabPanels>
          {/* Tab 1: Generate Post */}
          <TabPanel px={0}>
            <Grid templateColumns="1fr" gap={4}>
              {/* Settings Panel (always single column now) */}
              <Card bg={cardBg}>
                <CardBody>
                  <VStack spacing={3} align="stretch">
                    <HStack justify="space-between">
                      <Heading size="sm" color={textColor}>{t('contentGeneration.generatePostTitle')}</Heading>
                      {conversationHistory.length > 0 && (
                        <Tooltip label="Start new generation">
                          <IconButton 
                            icon={<FaPlus />} 
                            size="sm" 
                            colorScheme="brand"
                            onClick={handleNewConversation}
                            aria-label="New conversation"
                          />
                        </Tooltip>
                      )}
                    </HStack>

                    {/* Unified Prompt & Conversation Area */}
                    <Box position="relative" suppressHydrationWarning>
                      {/* Conversation History Display (shown above input when there's history) */}
                      {conversationHistory.length > 0 && (
                        <Box
                          maxH="300px"
                          overflowY="auto"
                          mb={2}
                          p={3}
                          bg={historyCardBg}
                          borderRadius="md"
                          borderWidth="1px"
                          borderColor={borderColorDefault}
                        >
                          <VStack spacing={3} align="stretch">
                            {conversationHistory.map((msg, index) => (
                              <Box key={index}>
                                {msg.role === 'user' ? (
                                  // User messages aligned to RIGHT
                                  <HStack align="start" spacing={2} justify="flex-end">
                                    <Box 
                                      flex={1} 
                                      maxW="80%"
                                      bg="blue.500"
                                      color="white"
                                      p={3}
                                      borderRadius="lg"
                                      borderBottomRightRadius="sm"
                                    >
                                      <Text fontSize="sm">{msg.content}</Text>
                                    </Box>
                                    <Avatar size="xs" name="You" bg="blue.600" />
                                  </HStack>
                                ) : (
                                  // AI messages aligned to LEFT
                                  <HStack align="start" spacing={2}>
                                    <Avatar size="xs" icon={<Icon as={FaRobot} />} bg="purple.500" />
                                    <Box 
                                      flex={1}
                                      maxW="80%"
                                      bg={analysisSectionBg}
                                      p={3}
                                      borderRadius="lg"
                                      borderBottomLeftRadius="sm"
                                    >
                                      <HStack mb={1}>
                                        <Text fontSize="xs" fontWeight="600" color="purple.500">AI Assistant</Text>
                                        {msg.metadata?.score && (
                                          <Badge colorScheme={msg.metadata.score >= 80 ? 'green' : 'orange'} fontSize="xs">
                                            Score: {msg.metadata.score}
                                          </Badge>
                                        )}
                                      </HStack>
                                      <Text fontSize="sm" color={textColor} whiteSpace="pre-wrap">{msg.content}</Text>
                                      {msg.metadata?.hashtags && msg.metadata.hashtags.length > 0 && (
                                        <Wrap mt={2} spacing={1}>
                                          {msg.metadata.hashtags.map((tag, i) => (
                                            <Tag key={i} size="sm" colorScheme="blue" variant="subtle">
                                              #{tag.replace('#', '')}
                                            </Tag>
                                          ))}
                                        </Wrap>
                                      )}
                                      {msg.metadata?.imageUrl && (
                                        <Box mt={2}>
                                          <Image src={msg.metadata.imageUrl} alt="Generated" maxH="150px" borderRadius="md" />
                                        </Box>
                                      )}
                                      {/* Action buttons for AI response */}
                                      <HStack mt={2} spacing={1}>
                                        <Tooltip label="Copy">
                                          <IconButton
                                            icon={<FaCopy />}
                                            size="xs"
                                            variant="ghost"
                                            onClick={() => {
                                              navigator.clipboard.writeText(msg.content);
                                              toast({ title: 'Copied!', status: 'success', duration: 1500 });
                                            }}
                                          />
                                        </Tooltip>
                                        <Button size="xs" variant="ghost" onClick={() => handleQuickAction('shorter', msg.content)}>Shorter</Button>
                                        <Button size="xs" variant="ghost" onClick={() => handleQuickAction('emojis', msg.content)}>+ Emojis</Button>
                                        <Button size="xs" variant="ghost" onClick={() => handleQuickAction('professional', msg.content)}>Professional</Button>
                                      </HStack>
                                    </Box>
                                  </HStack>
                                )}
                              </Box>
                            ))}
                          </VStack>
                        </Box>
                      )}
                      
                      {/* AI Typing Indicator - Shows when processing */}
                      {(loading || generationJobId) && (
                        <Box
                          p={3}
                          mb={2}
                          bg={analysisSectionBg}
                          borderRadius="md"
                          borderWidth="1px"
                          borderColor={borderColorDefault}
                        >
                          <HStack spacing={3}>
                            <Avatar size="xs" icon={<Icon as={FaRobot} />} bg="purple.500" />
                            <HStack spacing={1}>
                              <Box 
                                w="8px" 
                                h="8px" 
                                bg="purple.400" 
                                borderRadius="full"
                                animation="bounce 1.4s ease-in-out infinite"
                                sx={{
                                  '@keyframes bounce': {
                                    '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 },
                                    '40%': { transform: 'scale(1)', opacity: 1 }
                                  }
                                }}
                              />
                              <Box 
                                w="8px" 
                                h="8px" 
                                bg="purple.400" 
                                borderRadius="full"
                                animation="bounce 1.4s ease-in-out infinite"
                                sx={{
                                  animationDelay: '0.2s',
                                  '@keyframes bounce': {
                                    '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 },
                                    '40%': { transform: 'scale(1)', opacity: 1 }
                                  }
                                }}
                              />
                              <Box 
                                w="8px" 
                                h="8px" 
                                bg="purple.400" 
                                borderRadius="full"
                                animation="bounce 1.4s ease-in-out infinite"
                                sx={{
                                  animationDelay: '0.4s',
                                  '@keyframes bounce': {
                                    '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 },
                                    '40%': { transform: 'scale(1)', opacity: 1 }
                                  }
                                }}
                              />
                            </HStack>
                            <Text fontSize="sm" color="purple.500" fontWeight="500">
                              AI is generating content...
                            </Text>
                          </HStack>
                        </Box>
                      )}

                      {/* Input Textarea with Send Button */}
                      <Box position="relative">
                        <Textarea
                          placeholder={conversationHistory.length > 0 ? "Refine or continue the conversation..." : t('contentGeneration.promptPlaceholder')}
                          value={prompt}
                          onChange={(e) => setPrompt(e.target.value)}
                          onKeyDown={(e) => {
                            // Submit on Enter (without Shift)
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleGenerate();
                            }
                          }}
                          minH={conversationHistory.length > 0 ? "80px" : "120px"}
                          bg={historyCardBg}
                          pr="60px"
                          pb="10px"
                          spellCheck="false"
                          size="sm"
                        />
                        
                        {/* Send Arrow Button - positioned inside textarea */}
                        <Box position="absolute" bottom="12px" right="12px" zIndex={1}>
                          <Tooltip label={loading ? "Processing..." : "Send"}>
                            <IconButton
                              icon={loading || generationJobId ? <Spinner size="sm" /> : <FaPaperPlane />}
                              onClick={handleGenerate}
                              isDisabled={!prompt.trim() || loading || generationJobId !== null}
                              colorScheme="brand"
                              size="sm"
                              borderRadius="full"
                              aria-label="Send message"
                              bg="brand.500"
                              color="white"
                              _hover={{ bg: 'brand.600', transform: 'scale(1.05)' }}
                              _disabled={{ bg: 'gray.300', cursor: 'not-allowed' }}
                              transition="all 0.2s"
                            />
                          </Tooltip>
                        </Box>
                      </Box>
                      
                      {/* Voice, Media & Action buttons - below textarea */}
                      <HStack spacing={2} justify="space-between">
                        <HStack spacing={1}>
                          <Tooltip label={t('contentGeneration.uploadMedia')} placement="top">
                            <IconButton
                              icon={<FaUpload />}
                              onClick={onMediaOpen}
                              colorScheme="green"
                              variant="ghost"
                              size="xs"
                              aria-label="Upload media"
                            />
                          </Tooltip>
                          <VoiceDictation onTranscript={(text) => setPrompt(prompt + (prompt ? ' ' : '') + text)} />
                          <VoiceAssistant />
                        </HStack>
                        
                        {/* Action buttons when conversation exists */}
                        {conversationHistory.length > 0 && (
                          <HStack spacing={2}>
                            <Tooltip label="Start new conversation">
                              <IconButton
                                icon={<FaPlus />}
                                onClick={handleNewConversation}
                                size="sm"
                                colorScheme="red"
                                variant="outline"
                              />
                            </Tooltip>
                            {/* Show Submit for Approval if user needs approval (enterprise workspace) */}
                            {isEnterpriseWorkspace && userPermissions !== null && userPermissions.needs_approval && !userPermissions.can_publish_directly ? (
                              <Tooltip label="Submit content for manager review">
                                <Button
                                  leftIcon={<FaPaperPlane />}
                                  onClick={handleSubmitForApproval}
                                  isLoading={submittingForApproval}
                                  size="sm"
                                  colorScheme="orange"
                                >
                                  Submit for Approval
                                </Button>
                              </Tooltip>
                            ) : (
                              <Button
                                leftIcon={<FaShare />}
                                onClick={() => {
                                  setOpenModalInScheduleMode(false);
                                  onSocialModalOpen();
                                }}
                                size="sm"
                                colorScheme="blue"
                                isDisabled={isEnterpriseWorkspace && userPermissions === null}
                              >
                                {isEnterpriseWorkspace && userPermissions === null ? 'Loading...' : 'Post to Social'}
                              </Button>
                            )}
                          </HStack>
                        )}
                      </HStack>
                    </Box>
                    
                    {/* Image Generation & Promotional Content Options - inline below prompt */}
                    <HStack spacing={6} mt={2} flexWrap="wrap">
                      <Checkbox
                        isChecked={includeImage}
                        onChange={(e) => setIncludeImage(e.target.checked)}
                        colorScheme="blue"
                        size="sm"
                      >
                        <HStack spacing={1}>
                          <Icon as={FaImage} color="blue.500" boxSize={3} />
                          <Text fontSize="xs" fontWeight="600" color={textColorSecondary}>
                            {t('contentGeneration.generateImage')}
                          </Text>
                        </HStack>
                      </Checkbox>
                      {includeImage && (
                        <Select
                          size="xs"
                          value={imageStyle}
                          onChange={(e) => setImageStyle(e.target.value)}
                          w="120px"
                          ml={-2}
                        >
                          <option value="simple">{t('contentGeneration.styleSimple')}</option>
                          <option value="creative">{t('contentGeneration.styleCreative')}</option>
                          <option value="photorealistic">{t('contentGeneration.stylePhotorealistic')}</option>
                          <option value="illustration">{t('contentGeneration.styleIllustration')}</option>
                        </Select>
                      )}
                      <Checkbox
                        isChecked={isPromotionalContent}
                        onChange={(e) => setIsPromotionalContent(e.target.checked)}
                        colorScheme="brand"
                        size="sm"
                      >
                        <Text fontSize="xs" fontWeight="600" color={textColorSecondary}>
                          {t('contentGeneration.promotionalContent')}
                        </Text>
                      </Checkbox>
                    </HStack>

                    {/* Strategic Profile Selector - Below the prompt */}
                    <Box p={3} bg={analysisSectionBg} borderRadius="md" borderWidth="1px" borderColor={borderColorDefault}>
                      <HStack justify="space-between" mb={2}>
                        <HStack>
                          <Icon as={FaBrain} color="blue.500" boxSize={4} />
                          <Text fontWeight="600" fontSize="sm" color={textColor}>{t('contentGeneration.strategicProfile')}</Text>
                        </HStack>
                        {getSelectedProfile()?.knowledge_stats?.has_knowledge && (
                          <Badge colorScheme="green" fontSize="xs">
                            {getSelectedProfile()?.knowledge_stats?.document_count} {t('common.docs')}
                          </Badge>
                        )}
                      </HStack>
                      <Select
                        value={selectedProfileId || ''}
                        onChange={(e) => {
                          setSelectedProfileId(e.target.value);
                          // Update tone based on selected profile
                          const profile = strategicProfiles.find(p => p.id === e.target.value);
                          if (profile) {
                            setCurrentTone(profile.writing_tone);
                            // Auto-populate platforms from profile defaults
                            if (profile.default_platforms && profile.default_platforms.length > 0) {
                              setSelectedPlatforms(profile.default_platforms);
                            }
                          }
                        }}
                        size="sm"
                        bg={historyCardBg}
                        isDisabled={loadingProfiles}
                      >
                        {strategicProfiles.map(profile => (
                          <option key={profile.id} value={profile.id}>
                            {profile.name} {profile.is_default ? `(${t('common.default')})` : ''} - {t(`tones.${profile.writing_tone}`, profile.writing_tone)}
                          </option>
                        ))}
                      </Select>
                      {getSelectedProfile()?.seo_keywords?.length > 0 && (
                        <Wrap mt={2} spacing={1}>
                          {getSelectedProfile().seo_keywords.slice(0, 5).map((kw, i) => (
                            <WrapItem key={i}>
                              <Tag size="sm" colorScheme="green" variant="subtle">
                                <TagLabel fontSize="xs">{kw}</TagLabel>
                              </Tag>
                            </WrapItem>
                          ))}
                        </Wrap>
                      )}
                    </Box>

                    {/* Media Analyzer Modal */}
                    <Modal isOpen={isMediaOpen} onClose={onMediaClose} size="xl" isCentered>
                      <ModalOverlay bg="blackAlpha.600" zIndex={10000} />
                      <ModalContent bg={cardBg} zIndex={10001}>
                        <ModalHeader>{t('contentGeneration.uploadMedia')}</ModalHeader>
                        <ModalCloseButton />
                        <ModalBody pb={6}>
                          <MediaAnalyzer onAnalysisComplete={(result) => {
                            if (result.description) {
                              setPrompt(prompt + '\n\nBased on this image: ' + result.description);
                            }
                            onMediaClose();
                          }} />
                        </ModalBody>
                      </ModalContent>
                    </Modal>

                    {/* Hashtag Slider */}
                    <Box>
                      <HStack justify="space-between" mb={2}>
                        <Text fontSize="xs" fontWeight="600" color={textColorSecondary}>{t('contentGeneration.hashtags')}</Text>
                        <Badge colorScheme="brand" fontSize="xs">{hashtagCount}</Badge>
                      </HStack>
                      <Slider
                        aria-label="hashtag-count"
                        value={hashtagCount}
                        min={0}
                        max={10}
                        step={1}
                        onChange={(val) => setHashtagCount(val)}
                        colorScheme="brand"
                      >
                        <SliderTrack h="6px" borderRadius="full">
                          <SliderFilledTrack />
                        </SliderTrack>
                        <SliderThumb boxSize={4} />
                      </Slider>
                    </Box>

                    {/* Platform Selection - Platform-Aware Content */}
                    <Box>
                      <Text fontSize="xs" fontWeight="600" mb={2} color={textColorSecondary}>
                        {t('contentGeneration.platforms')} - {t('contentGeneration.platformAwareContent')}
                      </Text>
                      <PlatformSelector
                        connectedPlatforms={connectedPlatforms}
                        selectedPlatforms={selectedPlatforms}
                        onChange={setSelectedPlatforms}
                        showAllPlatforms={true}
                        showCharLimits={true}
                        compact={false}
                      />
                      {selectedPlatforms.length > 0 && (
                        <Text fontSize="xs" color="blue.500" mt={2}>
                          ✨ AI will optimize content for {selectedPlatforms.length} platform{selectedPlatforms.length > 1 ? 's' : ''}
                        </Text>
                      )}
                    </Box>

                    {/* Project Selection Dropdown */}
                    <FormControl>
                      <FormLabel fontSize="xs" fontWeight="600" color={textColor} mb={1}>
                        <HStack spacing={1}>
                          <Icon as={FaFolderOpen} color="blue.500" boxSize={3} />
                          <Text>{t('contentGeneration.assignToProject')}</Text>
                        </HStack>
                      </FormLabel>
                      <Select
                        size="sm"
                        placeholder={t('contentGeneration.noProjectSelected')}
                        value={selectedProjectId}
                        onChange={(e) => setSelectedProjectId(e.target.value)}
                        bg={historyCardBg}
                        isDisabled={loadingProjects}
                      >
                        {projects.map(project => (
                          <option key={project.project_id} value={project.project_id}>
                            {project.name} {project.project_type === 'enterprise' ? `(${t('nav.enterprise')})` : `(${t('common.profile')})`}
                          </option>
                        ))}
                      </Select>
                      <FormHelperText fontSize="2xs" color={textColorSecondary}>
                        {selectedProjectId 
                          ? `${t('contentGeneration.contentLinkedTo', 'Content will be linked to')}: ${projects.find(p => p.project_id === selectedProjectId)?.name}`
                          : t('contentGeneration.selectProjectOrganize')
                        }
                      </FormHelperText>
                    </FormControl>
                    
                    {/* ARCH-004: Async Job Progress - removed duplicate indicator */}
                    {/* Progress shown in typing indicator above */}
                    
                    {imageJobId && (
                      <Box 
                        position="relative"
                        borderRadius="xl" 
                        overflow="hidden"
                        bg="linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)"
                        p={6}
                        minH="200px"
                      >
                        {/* Animated background effect */}
                        <Box
                          position="absolute"
                          top="0"
                          left="0"
                          right="0"
                          bottom="0"
                          opacity={0.3}
                          background="radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%), radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 40%)"
                          animation="pulse 4s ease-in-out infinite"
                          sx={{
                            '@keyframes pulse': {
                              '0%, 100%': { opacity: 0.3 },
                              '50%': { opacity: 0.5 },
                            }
                          }}
                        />
                        
                        <VStack spacing={4} position="relative" zIndex={1}>
                          {/* AI Icon with glow effect */}
                          <Box position="relative">
                            <Box
                              position="absolute"
                              top="50%"
                              left="50%"
                              transform="translate(-50%, -50%)"
                              w="80px"
                              h="80px"
                              borderRadius="full"
                              bg="rgba(139, 92, 246, 0.3)"
                              filter="blur(20px)"
                              animation="breathe 2s ease-in-out infinite"
                              sx={{
                                '@keyframes breathe': {
                                  '0%, 100%': { transform: 'translate(-50%, -50%) scale(1)', opacity: 0.3 },
                                  '50%': { transform: 'translate(-50%, -50%) scale(1.2)', opacity: 0.5 },
                                }
                              }}
                            />
                            <Icon 
                              as={FaImage} 
                              boxSize={10} 
                              color="white"
                              animation="float 3s ease-in-out infinite"
                              sx={{
                                '@keyframes float': {
                                  '0%, 100%': { transform: 'translateY(0)' },
                                  '50%': { transform: 'translateY(-5px)' },
                                }
                              }}
                            />
                          </Box>
                          
                          {/* Status text */}
                          <VStack spacing={1}>
                            <Text 
                              color="white" 
                              fontWeight="bold" 
                              fontSize="lg"
                              textAlign="center"
                            >
                              Creating your image with AI
                            </Text>
                            <Text 
                              color="whiteAlpha.700" 
                              fontSize="sm"
                              textAlign="center"
                            >
                              Analyzing content and generating visuals...
                            </Text>
                          </VStack>
                          
                          {/* Animated progress bar */}
                          <Box w="full" maxW="280px">
                            <Box
                              h="3px"
                              bg="whiteAlpha.200"
                              borderRadius="full"
                              overflow="hidden"
                            >
                              <Box
                                h="full"
                                bg="linear-gradient(90deg, #8b5cf6, #ec4899, #8b5cf6)"
                                backgroundSize="200% 100%"
                                animation="shimmer 2s linear infinite"
                                sx={{
                                  '@keyframes shimmer': {
                                    '0%': { backgroundPosition: '200% 0' },
                                    '100%': { backgroundPosition: '-200% 0' },
                                  }
                                }}
                              />
                            </Box>
                          </Box>
                          
                          {/* Animated dots */}
                          <HStack spacing={2}>
                            {[0, 1, 2].map((i) => (
                              <Box
                                key={i}
                                w="8px"
                                h="8px"
                                borderRadius="full"
                                bg="white"
                                animation={`dotPulse 1.4s ease-in-out ${i * 0.2}s infinite`}
                                sx={{
                                  '@keyframes dotPulse': {
                                    '0%, 80%, 100%': { opacity: 0.3, transform: 'scale(0.8)' },
                                    '40%': { opacity: 1, transform: 'scale(1)' },
                                  }
                                }}
                              />
                            ))}
                          </HStack>
                        </VStack>
                      </Box>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            </Grid>

            {/* Full Width Analysis Section - Shows after content is analyzed */}
            {generatedContent && analysis && (
              <Card mt={4} borderWidth="2px" borderColor="brand.500">
                <CardBody>
                  <AnalysisResults analysis={analysis} title="Content Analysis" compact={false} />
                </CardBody>
              </Card>
            )}

            {/* Generated Image Display - Shows if image was generated */}
            {generatedImage && (
              <Card mt={4}>
                <CardBody>
                  <HStack justify="space-between" mb={2}>
                    <Text fontWeight="600" fontSize="sm" color={textColor}>Generated Image</Text>
                    <HStack spacing={2}>
                      <Badge colorScheme="blue" fontSize="xs">{generatedImage.style} style</Badge>
                      <Tooltip label={t('common.expand')}>
                        <IconButton
                          icon={<FaExpand />}
                          size="xs"
                          colorScheme="blue"
                          variant="ghost"
                          onClick={onImageExpandOpen}
                          aria-label="Expand image"
                        />
                      </Tooltip>
                      <Tooltip label="Regenerate image with feedback">
                        <IconButton
                          icon={<FaSyncAlt />}
                          size="xs"
                          colorScheme="blue"
                          variant="ghost"
                          onClick={onImageFeedbackOpen}
                          isLoading={regeneratingImage}
                          aria-label="Regenerate image"
                        />
                      </Tooltip>
                    </HStack>
                  </HStack>
                  <Box 
                    borderRadius="md" 
                    overflow="hidden" 
                    mb={2}
                    cursor="pointer"
                    onClick={onImageExpandOpen}
                    _hover={{ opacity: 0.9 }}
                    transition="opacity 0.2s"
                  >
                    <img 
                      src={`data:${generatedImage.mimeType};base64,${generatedImage.base64}`}
                      alt="Generated content image"
                      style={{ maxWidth: '100%', maxHeight: '300px', objectFit: 'contain' }}
                    />
                  </Box>
                  <Text fontSize="xs" color={textColorSecondary}>
                    Model: {generatedImage.model}
                  </Text>
                </CardBody>
              </Card>
            )}

            {/* Post to Social Modal - Uses real Ayrshare integration */}
            <PostToSocialModal
              isOpen={isPostOpen}
              onClose={onPostClose}
              content={generatedContent}
              userId={user?.id}
              imageBase64={generatedImage?.base64}
              imageMimeType={generatedImage?.mimeType || 'image/png'}
              onPostSuccess={() => {
                setGeneratedContent('');
                setGeneratedImage(null);
                resetAnalysis();
              }}
            />
            
            {/* Social Modal for conversation Post to Social button */}
            <PostToSocialModal
              isOpen={isSocialModalOpen}
              onClose={() => {
                onSocialModalClose();
                setOpenModalInScheduleMode(false);
              }}
              content={generatedContent}
              userId={user?.id}
              imageBase64={generatedImage?.base64}
              imageMimeType={generatedImage?.mimeType || 'image/png'}
              defaultSchedule={openModalInScheduleMode}
              onPostSuccess={() => {
                setGeneratedContent('');
                setGeneratedImage(null);
                resetAnalysis();
                setOpenModalInScheduleMode(false);
              }}
            />
          </TabPanel>
          {/* Tab 2: Schedule */}
          <TabPanel px={0}>
            <Card bg={cardBg}>
              <CardBody>
                <VStack align="stretch" spacing={4}>
                  <Heading size="sm">Schedule Automatic Content Generation & Posting</Heading>
                  
                  <FormControl suppressHydrationWarning>
                    <Text fontSize="xs" fontWeight="600" color={textColorSecondary} mb={1}>Prompt</Text>
                    <Box position="relative">
                      <Textarea
                        placeholder="Describe what content you want generated automatically..."
                        value={scheduleData.prompt}
                        onChange={(e) => setScheduleData({...scheduleData, prompt: e.target.value})}
                        minH="100px"
                        size="sm"
                        spellCheck="false"
                        pr="100px"
                        pb="40px"
                      />
                      {/* Voice & Media Tools for Schedule Prompt */}
                      <Box position="absolute" bottom="8px" right="8px" zIndex={1}>
                        <HStack spacing={1}>
                          <Tooltip label={t('contentGeneration.uploadMedia')} placement="top">
                            <IconButton
                              icon={<FaUpload />}
                              onClick={onMediaOpen}
                              colorScheme="green"
                              variant="ghost"
                              size="xs"
                              aria-label="Upload media"
                            />
                          </Tooltip>
                          <VoiceDictation onTranscript={(text) => setScheduleData({...scheduleData, prompt: scheduleData.prompt + (scheduleData.prompt ? ' ' : '') + text})} />
                          <VoiceAssistant />
                        </HStack>
                      </Box>
                    </Box>
                  </FormControl>

                  {/* Image Generation & Promotional Content Options - inline below prompt (same as Generate Post) */}
                  <HStack spacing={6} flexWrap="wrap">
                    <Checkbox
                      isChecked={scheduleData.includeImage || false}
                      onChange={(e) => setScheduleData({...scheduleData, includeImage: e.target.checked})}
                      colorScheme="blue"
                      size="sm"
                    >
                      <HStack spacing={1}>
                        <Icon as={FaImage} color="blue.500" boxSize={3} />
                        <Text fontSize="xs" fontWeight="600" color={textColorSecondary}>
                          {t('contentGeneration.generateImage')}
                        </Text>
                      </HStack>
                    </Checkbox>
                    {scheduleData.includeImage && (
                      <Select
                        size="xs"
                        value={scheduleData.imageStyle || 'creative'}
                        onChange={(e) => setScheduleData({...scheduleData, imageStyle: e.target.value})}
                        w="120px"
                        ml={-2}
                      >
                        <option value="simple">{t('contentGeneration.styleSimple')}</option>
                        <option value="creative">{t('contentGeneration.styleCreative')}</option>
                        <option value="photorealistic">{t('contentGeneration.stylePhotorealistic')}</option>
                        <option value="illustration">{t('contentGeneration.styleIllustration')}</option>
                      </Select>
                    )}
                    <Checkbox
                      isChecked={isSchedulePromotionalContent}
                      onChange={(e) => setIsSchedulePromotionalContent(e.target.checked)}
                      colorScheme="brand"
                      size="sm"
                    >
                      <Text fontSize="xs" fontWeight="600" color={textColorSecondary}>
                        {t('contentGeneration.promotionalContent')}
                      </Text>
                    </Checkbox>
                  </HStack>

                  {/* Platform Selection - Platform-Aware Content (same as Generate Post) */}
                  <Box>
                    <Text fontSize="xs" fontWeight="600" mb={2} color={textColorSecondary}>
                      {t('contentGeneration.platforms')} - {t('contentGeneration.platformAwareContent')}
                    </Text>
                    <PlatformSelector
                      connectedPlatforms={connectedPlatforms}
                      selectedPlatforms={selectedPlatforms}
                      onChange={setSelectedPlatforms}
                      showAllPlatforms={true}
                      showCharLimits={true}
                      compact={false}
                    />
                    {selectedPlatforms.length > 0 && (
                      <Text fontSize="xs" color="blue.500" mt={2}>
                        ✨ AI will optimize content for {selectedPlatforms.length} platform{selectedPlatforms.length > 1 ? 's' : ''}
                      </Text>
                    )}
                  </Box>

                  {/* Schedule Type, Time, Start Date - All on one line */}
                  <Grid templateColumns={{ base: '1fr', md: 'repeat(3, 1fr)' }} gap={3}>
                    <Box>
                      <Text fontSize="xs" fontWeight="600" color={textColorSecondary} mb={1}>Schedule Type</Text>
                      <Select 
                        size="sm"
                        value={scheduleData.schedule_type}
                        onChange={(e) => setScheduleData({...scheduleData, schedule_type: e.target.value})}
                      >
                        <option value="once">Once</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                      </Select>
                    </Box>

                    <Box>
                      <Text fontSize="xs" fontWeight="600" color={textColorSecondary} mb={1}>Time</Text>
                      <Input 
                        size="sm"
                        type="time"
                        value={scheduleData.schedule_time}
                        onChange={(e) => setScheduleData({...scheduleData, schedule_time: e.target.value})}
                      />
                    </Box>

                    <Box>
                      <Text fontSize="xs" fontWeight="600" color={textColorSecondary} mb={1}>
                        {scheduleData.schedule_type === 'once' ? 'Date' : 'Start Date'}
                      </Text>
                      <Input
                        size="sm"
                        type="date"
                        value={scheduleData.start_date || ''}
                        onChange={(e) => setScheduleData({ ...scheduleData, start_date: e.target.value })}
                        min={new Date().toISOString().split('T')[0]}
                      />
                    </Box>
                  </Grid>

                  {scheduleData.schedule_type === 'weekly' && (
                    <Box>
                      <Text fontSize="xs" fontWeight="600" color={textColorSecondary} mb={1}>Select Days</Text>
                      <CheckboxGroup 
                        value={scheduleData.schedule_days}
                        onChange={(values) => setScheduleData({...scheduleData, schedule_days: values})}
                      >
                        <HStack spacing={3} flexWrap="wrap">
                          <Checkbox value="monday" size="sm">Mon</Checkbox>
                          <Checkbox value="tuesday" size="sm">Tue</Checkbox>
                          <Checkbox value="wednesday" size="sm">Wed</Checkbox>
                          <Checkbox value="thursday" size="sm">Thu</Checkbox>
                          <Checkbox value="friday" size="sm">Fri</Checkbox>
                          <Checkbox value="saturday" size="sm">Sat</Checkbox>
                          <Checkbox value="sunday" size="sm">Sun</Checkbox>
                        </HStack>
                      </CheckboxGroup>
                    </Box>
                  )}

                  {scheduleData.schedule_type === 'monthly' && (
                    <Box>
                      <Text fontSize="xs" fontWeight="600" color={textColorSecondary} mb={1}>Day of Month</Text>
                      <Select
                        size="sm"
                        value={scheduleData.schedule_days[0] || '1'}
                        onChange={(e) => setScheduleData({ ...scheduleData, schedule_days: [e.target.value] })}
                      >
                        {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
                          <option key={day} value={String(day)}>
                            {day}{day === 1 ? 'st' : day === 2 ? 'nd' : day === 3 ? 'rd' : 'th'}
                          </option>
                        ))}
                        <option value="last">Last day of month</option>
                      </Select>
                    </Box>
                  )}

                  {/* Hashtag Slider for Schedule Prompt - Compact */}
                  <Box>
                    <HStack justify="space-between" mb={2}>
                      <Text fontSize="xs" fontWeight="600" color={textColorSecondary}>Hashtags</Text>
                      <Badge colorScheme="brand" fontSize="xs">{scheduleData.hashtag_count || 3}</Badge>
                    </HStack>
                    <Slider
                      aria-label="schedule-hashtag-count"
                      value={scheduleData.hashtag_count || 3}
                      min={0}
                      max={10}
                      step={1}
                      onChange={(val) => setScheduleData({...scheduleData, hashtag_count: val})}
                      colorScheme="brand"
                    >
                      <SliderTrack h="6px" borderRadius="full">
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb boxSize={4} />
                    </Slider>
                  </Box>

                  {/* Auto-Post Options */}
                  <Box borderWidth="1px" borderRadius="md" p={3} bg={scheduleBoxBg}>
                    <Checkbox 
                      isChecked={scheduleData.auto_post}
                      onChange={(e) => setScheduleData({...scheduleData, auto_post: e.target.checked})}
                      mb={scheduleData.auto_post ? 3 : 0}
                      size="sm"
                    >
                      <Text fontSize="xs" fontWeight="600" color={textColorSecondary}>Automatically post to social media after generation</Text>
                    </Checkbox>

                    {scheduleData.auto_post && (
                      <VStack align="stretch" spacing={3} pl={6}>
                        <Box>
                          <Text fontSize="xs" fontWeight="600" color={textColorSecondary} mb={1}>Select Platforms (Connected Accounts Only)</Text>
                          <PlatformSelector
                            connectedPlatforms={connectedPlatforms}
                            selectedPlatforms={scheduleData.platforms}
                            onChange={(platforms) => setScheduleData({...scheduleData, platforms})}
                          />
                        </Box>

                        <Checkbox
                          isChecked={scheduleData.reanalyze_before_post}
                          onChange={(e) => setScheduleData({...scheduleData, reanalyze_before_post: e.target.checked})}
                          size="sm"
                        >
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="600" fontSize="xs" color={textColorSecondary}>Reanalyze content 1 hour before posting</Text>
                            <Text fontSize="xs" color={textColorSecondary}>
                              If content becomes offensive, it will not be posted and you will be notified
                            </Text>
                          </VStack>
                        </Checkbox>
                      </VStack>
                    )}
                  </Box>

                  <Button
                    colorScheme="brand"
                    size="sm"
                    leftIcon={<FaCalendarAlt />}
                    onClick={createSchedule}
                    isLoading={isScheduling}
                  >
                    Create Schedule
                  </Button>

                  {/* Strategic Profile Selector - Below Create Schedule button */}
                  <Box p={3} bg={analysisSectionBg} borderRadius="md" borderWidth="1px" borderColor={borderColorDefault}>
                    <HStack justify="space-between" mb={2}>
                      <HStack>
                        <Icon as={FaBrain} color="blue.500" boxSize={4} />
                        <Text fontWeight="600" fontSize="sm" color={textColor}>{t('contentGeneration.strategicProfile')}</Text>
                      </HStack>
                      {getSelectedProfile()?.knowledge_stats?.has_knowledge && (
                        <Badge colorScheme="green" fontSize="xs">
                          {getSelectedProfile()?.knowledge_stats?.document_count} {t('common.docs')}
                        </Badge>
                      )}
                    </HStack>
                    <Select
                      value={selectedProfileId || ''}
                      onChange={(e) => {
                        setSelectedProfileId(e.target.value);
                        // Auto-populate platforms from profile defaults for scheduling too
                        const profile = strategicProfiles.find(p => p.id === e.target.value);
                        if (profile && profile.default_platforms && profile.default_platforms.length > 0) {
                          setSelectedPlatforms(profile.default_platforms);
                        }
                      }}
                      size="sm"
                      bg={historyCardBg}
                      isDisabled={loadingProfiles}
                    >
                      {strategicProfiles.map(profile => (
                        <option key={profile.id} value={profile.id}>
                          {profile.name} {profile.is_default ? `(${t('common.default')})` : ''} - {t(`tones.${profile.writing_tone}`, profile.writing_tone)}
                        </option>
                      ))}
                    </Select>
                  </Box>

                  {/* Scheduled Prompts Table */}
                  <Box mt={8}>
                    <Heading size="md" mb={4}>Your Scheduled Prompts ({scheduledPrompts.length})</Heading>
                    {scheduledPrompts.length === 0 ? (
                      <Text color={textColorSecondary}>No scheduled prompts yet. Create one above!</Text>
                    ) : (
                      <Box overflowX="auto">
                        <Table variant="simple" size="sm">
                          <Thead>
                            <Tr>
                              <Th>Prompt</Th>
                              <Th>Schedule</Th>
                              <Th>Next Run</Th>
                              <Th>Auto-Post</Th>
                              <Th>Status</Th>
                              <Th>Actions</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {scheduledPrompts.map((scheduled) => (
                              <Tr key={scheduled.id}>
                                <Td maxW="300px" isTruncated>{scheduled.prompt}</Td>
                                <Td>
                                  <Text fontSize="sm">
                                    {scheduled.schedule_type} at {scheduled.schedule_time}
                                  </Text>
                                </Td>
                                <Td fontSize="sm">
                                  {scheduled.next_run ? new Date(scheduled.next_run).toLocaleString() : 'N/A'}
                                </Td>
                                <Td>
                                  {scheduled.auto_post ? (
                                    <Badge colorScheme="blue">
                                      <Icon as={FaCheckCircle} mr={1} />
                                      Yes
                                    </Badge>
                                  ) : (
                                    <Badge colorScheme="gray">No</Badge>
                                  )}
                                </Td>
                                <Td>
                                  <Badge colorScheme={scheduled.status === 'active' ? 'green' : 'gray'}>
                                    {scheduled.status === 'active' ? 'Active' : 'Paused'}
                                  </Badge>
                                </Td>
                                <Td>
                                  <HStack spacing={0}>
                                    <Tooltip label="Edit">
                                      <IconButton
                                        size="xs"
                                        icon={<FaEdit />}
                                        onClick={() => openEditPrompt(scheduled)}
                                        colorScheme="blue"
                                        variant="ghost"
                                        aria-label="Edit schedule"
                                      />
                                    </Tooltip>
                                    <Tooltip label={scheduled.status === 'active' ? 'Pause' : 'Activate'}>
                                      <IconButton
                                        size="xs"
                                        icon={scheduled.status === 'active' ? <FaToggleOn /> : <FaToggleOff />}
                                        onClick={() => toggleSchedule(scheduled.id)}
                                        colorScheme={scheduled.status === 'active' ? 'green' : 'gray'}
                                        variant="ghost"
                                        aria-label="Toggle schedule"
                                      />
                                    </Tooltip>
                                    <Tooltip label="Delete">
                                      <IconButton
                                        size="xs"
                                        icon={<FaTrash />}
                                        onClick={() => deleteSchedule(scheduled.id)}
                                        colorScheme="red"
                                        variant="ghost"
                                        aria-label="Delete schedule"
                                      />
                                    </Tooltip>
                                  </HStack>
                                </Td>
                              </Tr>
                            ))}
                          </Tbody>
                        </Table>
                      </Box>
                    )}
                  </Box>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* Edit Scheduled Prompt Modal */}
      <Modal isOpen={isEditOpen} onClose={onEditClose} size="lg">
        <ModalOverlay zIndex={10000} />
        <ModalContent zIndex={10001}>
          <ModalHeader>Edit Scheduled Prompt</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={4}>
            {editingPrompt && (
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>Prompt</FormLabel>
                  <Textarea
                    value={editingPrompt.prompt}
                    onChange={(e) => setEditingPrompt({...editingPrompt, prompt: e.target.value})}
                    minH="100px"
                  />
                </FormControl>
                
                <Grid templateColumns="1fr 1fr" gap={4}>
                  <FormControl>
                    <FormLabel>Schedule Type</FormLabel>
                    <Select
                      value={editingPrompt.schedule_type}
                      onChange={(e) => setEditingPrompt({...editingPrompt, schedule_type: e.target.value})}
                    >
                      <option value="once">Once</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </Select>
                  </FormControl>
                  <FormControl>
                    <FormLabel>Time</FormLabel>
                    <Input
                      type="time"
                      value={editingPrompt.schedule_time}
                      onChange={(e) => setEditingPrompt({...editingPrompt, schedule_time: e.target.value})}
                    />
                  </FormControl>
                </Grid>

                <FormControl>
                  <HStack justify="space-between" mb={2}>
                    <FormLabel mb={0}>Hashtags</FormLabel>
                    <Badge colorScheme="brand">{editingPrompt.hashtag_count || 3}</Badge>
                  </HStack>
                  <Slider
                    value={editingPrompt.hashtag_count || 3}
                    min={0}
                    max={10}
                    onChange={(val) => setEditingPrompt({...editingPrompt, hashtag_count: val})}
                    colorScheme="brand"
                  >
                    <SliderTrack h="6px" borderRadius="full">
                      <SliderFilledTrack />
                    </SliderTrack>
                    <SliderThumb boxSize={4} />
                  </Slider>
                </FormControl>

                <Checkbox
                  isChecked={editingPrompt.auto_post}
                  onChange={(e) => setEditingPrompt({...editingPrompt, auto_post: e.target.checked})}
                >
                  Auto-post to social media
                </Checkbox>

                {editingPrompt.auto_post && (
                  <FormControl>
                    <FormLabel>Platforms</FormLabel>
                    <CheckboxGroup
                      value={editingPrompt.platforms || []}
                      onChange={(values) => setEditingPrompt({...editingPrompt, platforms: values})}
                    >
                      <HStack spacing={3} flexWrap="wrap">
                        <Checkbox value="Facebook">Facebook</Checkbox>
                        <Checkbox value="Twitter">Twitter</Checkbox>
                        <Checkbox value="LinkedIn">LinkedIn</Checkbox>
                        <Checkbox value="Instagram">Instagram</Checkbox>
                      </HStack>
                    </CheckboxGroup>
                  </FormControl>
                )}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onEditClose}>Cancel</Button>
            <Button colorScheme="brand" onClick={saveEditedPrompt}>Save Changes</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Content Regeneration Feedback Modal */}
      <Modal isOpen={isFeedbackOpen} onClose={onFeedbackClose} size="md">
        <ModalOverlay bg="blackAlpha.600" zIndex={10000} />
        <ModalContent bg={cardBg} zIndex={10001}>
          <ModalHeader color={textColor}>Regenerate Content</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Text fontSize="sm" color={textColorSecondary}>
                Provide feedback to guide the regeneration, or leave empty for a fresh alternative.
              </Text>
              <FormControl>
                <FormLabel fontSize="sm">Your Feedback (optional)</FormLabel>
                <Textarea
                  value={contentFeedback}
                  onChange={(e) => setContentFeedback(e.target.value)}
                  placeholder="e.g., Make it more concise, Add more emotion, Focus on benefits..."
                  rows={3}
                />
                <FormHelperText fontSize="xs">
                  Examples: &quot;Make it shorter&quot;, &quot;Add more hashtags&quot;, &quot;Make the tone more casual&quot;
                </FormHelperText>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onFeedbackClose}>Cancel</Button>
            <Button 
              colorScheme="teal" 
              onClick={handleRegenerateContent} 
              isLoading={regenerating}
              leftIcon={<FaSyncAlt />}
            >
              {contentFeedback ? 'Regenerate with Feedback' : 'Generate Alternative'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Image Regeneration Feedback Modal */}
      <Modal isOpen={isImageFeedbackOpen} onClose={onImageFeedbackClose} size="md">
        <ModalOverlay bg="blackAlpha.600" zIndex={10000} />
        <ModalContent bg={cardBg} zIndex={10001}>
          <ModalHeader color={textColor}>Regenerate Image</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Text fontSize="sm" color={textColorSecondary}>
                Provide feedback to guide the image regeneration, or leave empty for a fresh alternative.
              </Text>
              <FormControl>
                <FormLabel fontSize="sm">Your Feedback (optional)</FormLabel>
                <Textarea
                  value={imageFeedback}
                  onChange={(e) => setImageFeedback(e.target.value)}
                  placeholder="e.g., Make it more colorful, Add people, Use minimalist style..."
                  rows={3}
                />
                <FormHelperText fontSize="xs">
                  Examples: &quot;Make it brighter&quot;, &quot;Add professional elements&quot;, &quot;Use warmer colors&quot;
                </FormHelperText>
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Image Style</FormLabel>
                <Select 
                  value={imageStyle} 
                  onChange={(e) => setImageStyle(e.target.value)}
                  size="sm"
                >
                  <option value="simple">Simple/Clean</option>
                  <option value="creative">Creative</option>
                  <option value="photorealistic">Photorealistic</option>
                  <option value="illustration">Illustration</option>
                  <option value="artistic">Artistic</option>
                </Select>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onImageFeedbackClose}>Cancel</Button>
            <Button 
              colorScheme="blue" 
              onClick={handleRegenerateImage} 
              isLoading={regeneratingImage}
              leftIcon={<FaSyncAlt />}
            >
              {imageFeedback ? 'Regenerate with Feedback' : 'Generate New Image'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
      
      {/* Content Expand Modal */}
      <Modal isOpen={isContentExpandOpen} onClose={onContentExpandClose} size="4xl" scrollBehavior="inside">
        <ModalOverlay bg="blackAlpha.700" zIndex={10000} />
        <ModalContent bg={cardBg} maxH="90vh" zIndex={10001}>
          <ModalHeader color={textColor}>
            <HStack justify="space-between">
              <Text>{t('contentGeneration.generatedContent')}</Text>
              <HStack spacing={2}>
                <Tooltip label={t('common.copy')}>
                  <IconButton icon={<FaCopy />} onClick={handleCopyContent} size="sm" variant="ghost" aria-label="Copy" />
                </Tooltip>
              </HStack>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Box 
              borderWidth="1px" 
              borderRadius="md" 
              p={4} 
              bg={analysisSectionBg}
              minH="400px"
            >
              <Text whiteSpace="pre-wrap" fontSize="md" color={textColor} lineHeight="1.8">
                {generatedContent}
              </Text>
            </Box>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Image Expand Modal */}
      <Modal isOpen={isImageExpandOpen} onClose={onImageExpandClose} size="6xl" isCentered>
        <ModalOverlay bg="blackAlpha.800" zIndex={10000} />
        <ModalContent bg="transparent" boxShadow="none" maxW="95vw" maxH="95vh" zIndex={10001}>
          <ModalCloseButton color="white" bg="blackAlpha.600" borderRadius="full" _hover={{ bg: 'blackAlpha.800' }} />
          <ModalBody p={0} display="flex" justifyContent="center" alignItems="center">
            {generatedImage && (
              <Image
                src={`data:${generatedImage.mimeType};base64,${generatedImage.base64}`}
                alt="Generated content image - expanded view"
                maxW="95vw"
                maxH="90vh"
                objectFit="contain"
                borderRadius="lg"
              />
            )}
          </ModalBody>
          <ModalFooter justifyContent="center" pt={2}>
            {generatedImage && (
              <HStack spacing={4}>
                <Badge colorScheme="blue" fontSize="sm" px={3} py={1}>
                  {generatedImage.style} style
                </Badge>
                <Text fontSize="sm" color="white">
                  Model: {generatedImage.model}
                </Text>
              </HStack>
            )}
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
