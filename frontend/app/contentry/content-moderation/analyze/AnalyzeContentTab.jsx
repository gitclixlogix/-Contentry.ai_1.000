'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import { useWorkspace } from '@/context/WorkspaceContext';
import dynamic from 'next/dynamic';
import {
  Box,
  Button,
  Card,
  CardBody,
  Textarea,
  Text,
  Flex,
  Badge,
  VStack,
  HStack,
  Icon,
  Input,
  Select,
  Grid,
  useColorModeValue,
  useDisclosure,
  Checkbox,
  IconButton,
  Tooltip,
  Progress,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useToast,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SliderMark,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  FormControl,
  FormLabel,
  FormHelperText,
  Spinner,
  Center,
  Wrap,
  WrapItem,
  Tag,
  TagLabel,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Image,
  Divider,
  Alert,
  AlertIcon,
  AlertDescription,
} from '@chakra-ui/react';
import { FaFacebookF, FaInstagram, FaLinkedinIn, FaYoutube, FaTwitter, FaUpload, FaSyncAlt, FaHistory, FaCopy, FaEdit, FaChartBar, FaFileAlt, FaDownload, FaFilePdf, FaCalendarAlt, FaClock, FaCheckCircle, FaBrain, FaImage, FaExpand, FaFolderOpen, FaGlobe, FaPaperPlane, FaExclamationTriangle, FaTimesCircle, FaCommentDots } from 'react-icons/fa';
import api, { getApiUrl } from '@/lib/api';
import { getErrorMessage } from '@/lib/errorUtils';
import { exportToJSON, exportToPDF } from '@/lib/exportUtils';
import VoiceDictation from '@/components/voice/VoiceDictation';
import AnalysisResults from '../components/AnalysisResults';
import FeedbackSection from '../components/FeedbackSection';
import useContentAnalyzer from '@/hooks/useContentAnalyzer';
import useJobStatus, { JOB_STATUS, submitAsyncJob } from '@/hooks/useJobStatus';
import JobProgressIndicator from '@/components/common/JobProgressIndicator';
import PlatformSelector, { PLATFORM_CONFIG, getStrictestLimit, getPlatformGuidance } from '@/components/social/PlatformSelector';
import CharacterCounter from '@/components/common/CharacterCounter';
// ARCH-013: Rate Limiting UI
import { RateLimitBadge, RateLimitError } from '@/components/common/RateLimitIndicator';
import { useRateLimitStatus } from '@/hooks/useRateLimitStatus';

// Lazy load heavy components that aren't immediately needed
const VoiceAssistant = dynamic(() => import('@/components/voice/VoiceAssistant'), {
  ssr: false,
  loading: () => null,
});

const PostToSocialModal = dynamic(() => import('@/components/social/PostToSocialModal'), {
  ssr: false,
  loading: () => null,
});

import MediaAnalyzer from '@/components/media/MediaAnalyzer';
import MediaUploader from '@/components/media/MediaUploader';

export default function AnalyzeContentTab({ user: propUser, language, setActiveTab, initialContent }) {
  const { t } = useTranslation();
  const router = useRouter();
  const { user: authUser, isHydrated } = useAuth();  // Use auth context directly for reliability
  const { currentWorkspace, isEnterpriseWorkspace, enterpriseInfo } = useWorkspace();
  
  // Prefer auth context user over prop (prop is legacy, auth context is more reliable)
  const user = authUser || propUser;
  
  const [content, setContent] = useState(initialContent || '');
  const [loading, setLoading] = useState(false);
  const [customAnalysisStep, setCustomAnalysisStep] = useState(''); // For promotional check step
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaPreviewUrl, setMediaPreviewUrl] = useState(null);
  const [mediaAnalysis, setMediaAnalysis] = useState(null);
  const [analyzingMedia, setAnalyzingMedia] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const { isOpen: isSocialModalOpen, onOpen: onSocialModalOpen, onClose: onSocialModalClose } = useDisclosure();
  const { isOpen: isMediaOpen, onOpen: onMediaOpen, onClose: onMediaClose } = useDisclosure();
  const [openModalInScheduleMode, setOpenModalInScheduleMode] = useState(false);
  
  // Strategic Profile state (same as ContentGenerationTab)
  const [strategicProfiles, setStrategicProfiles] = useState([]);
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  
  // Auto-rewrite trigger state - used to trigger rewrite from job completion callback
  const [triggerAutoRewrite, setTriggerAutoRewrite] = useState(false);
  const autoRewriteAnalysisRef = useRef(null); // Stores analysis for auto-rewrite
  
  // Project state - for linking content to projects
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [loadingProjects, setLoadingProjects] = useState(false);
  
  // Image generation state
  const [wantImage, setWantImage] = useState(false);  // Checkbox to enable image generation
  const [imageStyle, setImageStyle] = useState('simple');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [regeneratingImage, setRegeneratingImage] = useState(false);
  const { isOpen: isImageFeedbackOpen, onOpen: onImageFeedbackOpen, onClose: onImageFeedbackClose } = useDisclosure();
  const { isOpen: isImageExpandOpen, onOpen: onImageExpandOpen, onClose: onImageExpandClose } = useDisclosure();
  const [imageFeedback, setImageFeedback] = useState('');
  
  // Use reusable content analyzer hook
  const { 
    analyzing,
    analysis, 
    analysisStep, 
    analyzeContent: performAnalysis, 
    rewriteContent,
    resetAnalysis,
    setAnalysisResult,
    jobId: analyzerJobId,        // ARCH-004: Async job ID
    handleJobComplete,          // ARCH-004: Handle async job completion
    handleJobError,             // ARCH-004: Handle async job error
  } = useContentAnalyzer();
  
  // DEBUG: Log analysis state changes
  useEffect(() => {
    console.log('=== ANALYSIS STATE CHANGED ===', {
      hasAnalysis: !!analysis,
      score: analysis?.overall_score,
      issuesCount: analysis?.issues?.length,
      flaggedStatus: analysis?.flagged_status
    });
  }, [analysis]);
  
  // ARCH-004: Async job status tracking
  const [analysisJobId, setAnalysisJobId] = useState(null);
  const [useAsyncAnalysis, setUseAsyncAnalysis] = useState(true); // Enable async by default
  
  // Track job status for UI updates
  const {
    status: jobStatus,
    progress: jobProgress,
    result: jobResult,
    error: jobError,
    isLoading: jobIsLoading,
    isCompleted: jobIsCompleted,
    isFailed: jobIsFailed,
    cancel: cancelJob,
  } = useJobStatus(analysisJobId, {
    userId: user?.id,
    onComplete: (result) => {
      console.log('>>> ANALYSIS onComplete CALLBACK CALLED! Result score:', result?.overall_score);
      // Handle async job completion
      setAnalysisResult(result);
      setLoading(false);
      setCustomAnalysisStep('');
      setAnalysisJobId(null);
      console.log('Content analysis job completed:', result);
      
      // DIRECT AUTO-REWRITE CHECK: Trigger rewrite if score < 80
      // Use state to trigger since handleRewrite isn't available in this closure
      if (result && typeof result.overall_score === 'number' && result.overall_score < 80) {
        console.log(`>>> Auto-rewrite trigger: score ${result.overall_score} < 80`);
        if (!autoRewriteTriggeredRef.current) {
          autoRewriteTriggeredRef.current = true;
          autoRewriteAnalysisRef.current = result; // Store analysis for rewrite
          // Use state update to trigger rewrite (will be handled by useEffect)
          setTimeout(() => {
            setTriggerAutoRewrite(true);
          }, 2500);
        }
      }
    },
    onError: (error) => {
      setCustomAnalysisStep('');
      setLoading(false);
      setAnalysisJobId(null);
      console.error('Content analysis job failed:', error);
    },
  });
  
  // Promotional content detection state
  const [promotionalCheckDone, setPromotionalCheckDone] = useState(false);
  const [isPromotionalContent, setIsPromotionalContent] = useState(false);
  const [showPromotionalDialog, setShowPromotionalDialog] = useState(false);
  const [promotionalDetails, setPromotionalDetails] = useState(null);
  const promotionalCancelRef = useRef(null);

  // Rewritten content state
  const [rewrittenContent, setRewrittenContent] = useState('');
  const [rewrittenAnalysis, setRewrittenAnalysis] = useState(null);
  const [showRewriteComparison, setShowRewriteComparison] = useState(false);
  const [analyzingRewritten, setAnalyzingRewritten] = useState(false);
  const [rewriting, setRewriting] = useState(false);
  const [hashtagCount, setHashtagCount] = useState(3); // Default 3 hashtags
  
  // Rewrite Chat - Conversational refinement for rewritten content
  const [rewriteChatHistory, setRewriteChatHistory] = useState([]);
  const [rewriteChatInput, setRewriteChatInput] = useState('');
  const [isRefiningContent, setIsRefiningContent] = useState(false);


  // Sponsored content detection
  const [showSponsoredAlert, setShowSponsoredAlert] = useState(false);
  const [addWatermark, setAddWatermark] = useState(false);
  
  // Promotional content checkbox state (separate from detection logic)
  const [isPromotionalContentCheckbox, setIsPromotionalContentCheckbox] = useState(false);
  
  // Platform-Aware Content Engine state
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [activeCharLimit, setActiveCharLimit] = useState(null);
  
  // Approval Workflow state
  const [userPermissions, setUserPermissions] = useState(null);
  const [submittingForApproval, setSubmittingForApproval] = useState(false);
  
  // ARCH-013: Rate limiting state
  const [rateLimitError, setRateLimitError] = useState(null);
  const { tier, hourlyRemaining, hourlyLimit, isNearLimit, refresh: refreshRateLimit } = useRateLimitStatus();
  
  const toast = useToast();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const userMsgBg = useColorModeValue('blue.50', 'blue.900');
  const aiMsgBg = useColorModeValue('green.50', 'green.900');
  const rewriteBlueBg = useColorModeValue('blue.50', 'blue.900');
  const platformBg = useColorModeValue('gray.50', 'gray.700');
  const progressBoxBg = useColorModeValue('blue.50', 'blue.900');
  const progressTextColor = useColorModeValue('blue.700', 'blue.200');
  const analysisSectionBg = useColorModeValue('gray.50', 'gray.700');
  const borderColorDefault = useColorModeValue('gray.200', 'gray.600');
  const selectBg = useColorModeValue('white', 'gray.700');

  // Load strategic profiles (personal or enterprise based on workspace)
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
        console.log('Loaded enterprise strategic profiles:', profiles.length);
      } else {
        // Load personal strategic profiles
        const response = await api.get(`/profiles/strategic`, {
          headers: { 'X-User-ID': user.id }
        });
        profiles = response.data.profiles || [];
        console.log('Loaded personal strategic profiles:', profiles.length);
      }
      
      setStrategicProfiles(profiles);
      // Reset selected profile when profiles change
      setSelectedProfileId(null);
    } catch (error) {
      console.error('Failed to load strategic profiles:', error);
    } finally {
      setLoadingProfiles(false);
    }
  };
  
  // Auto-select default profile when profiles load
  useEffect(() => {
    if (strategicProfiles.length > 0 && !selectedProfileId) {
      const defaultProfile = strategicProfiles.find(p => p.is_default);
      if (defaultProfile) {
        setSelectedProfileId(defaultProfile.id);
      } else if (strategicProfiles.length === 1) {
        // If only one profile exists, select it
        setSelectedProfileId(strategicProfiles[0].id);
      }
    }
  }, [strategicProfiles, selectedProfileId]);

  // Get selected profile data
  const getSelectedProfile = () => {
    return strategicProfiles.find(p => p.id === selectedProfileId);
  };

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

  // Load user permissions for approval workflow (ONLY for enterprise workspace)
  const loadUserPermissions = async () => {
    if (!user?.id) return;
    
    // Only load approval permissions for enterprise workspace
    // Personal workspace doesn't have approval workflow
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

  // Load profiles, projects, and permissions when user becomes available
  useEffect(() => {
    // Wait for auth to be hydrated before making API calls
    if (!isHydrated) {
      console.log('AnalyzeContentTab: Waiting for auth hydration...');
      return;
    }
    
    if (user?.id) {
      console.log('AnalyzeContentTab: Loading data for user:', user.id);
      loadConversationHistory(user.id);
      loadStrategicProfiles();
      loadProjects();  // Load projects on mount
      loadUserPermissions();  // Load user permissions for approval workflow
    } else {
      console.log('AnalyzeContentTab: No user available yet');
    }

    // Load draft content from Content Generation if exists
    const draftContent = localStorage.getItem('draft_content');
    if (draftContent) {
      setContent(draftContent);
      localStorage.removeItem('draft_content');
    }

    // Load post for rewriting if exists
    const rewriteData = localStorage.getItem('rewrite_post_data');
    if (rewriteData) {
      const postData = JSON.parse(rewriteData);
      setContent(postData.original_content);
    }

    // Load generated content
    const generatedContent = localStorage.getItem('generated_content');
    if (generatedContent) {
      setContent(generatedContent);
      localStorage.removeItem('generated_content');
    }
  }, [isHydrated, user?.id, isEnterpriseWorkspace, enterpriseInfo?.id]); // Watch for hydration, user.id, workspace changes, and enterprise changes

  // Update content when initialContent prop changes
  useEffect(() => {
    if (initialContent) {
      setContent(initialContent);
      setAnalysisResult(null); // Reset analysis for new content
    }
  }, [initialContent]);

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

  // Auto-rewrite when analysis result has low score - runs ONCE only
  const autoRewriteTriggeredRef = useRef(false);
  const [pendingAutoRewrite, setPendingAutoRewrite] = useState(false);
  
  // Ref to hold the latest handleRewrite function
  const handleRewriteRef = useRef(null);
  
  // Effect to detect when auto-rewrite should be triggered
  // IMPORTANT: Wait for analysis to be fully complete (has score AND issues) before rewriting
  useEffect(() => {
    console.log('Auto-rewrite check effect running:', {
      hasAnalysis: !!analysis,
      analysisScore: analysis?.overall_score,
      selectedProfileId,
      rewriting,
      showRewriteComparison,
      alreadyTriggered: autoRewriteTriggeredRef.current
    });
    
    // Skip if no analysis, no profile, already rewriting, already showing comparison, or already triggered
    if (!analysis || !selectedProfileId || rewriting || showRewriteComparison || autoRewriteTriggeredRef.current) {
      return;
    }
    
    // Skip if analysis doesn't have overall_score yet (might still be loading)
    if (typeof analysis.overall_score !== 'number') {
      console.log('Auto-rewrite: waiting for overall_score to be set');
      return;
    }
    
    // Skip if analysis doesn't have issues array - indicates incomplete analysis
    if (!Array.isArray(analysis.issues)) {
      console.log('Auto-rewrite: waiting for issues array to be populated');
      return;
    }
    
    const overallScore = analysis.overall_score;
    
    // Only auto-rewrite if score is below 80 - triggers ONCE
    if (overallScore < 80) {
      console.log(`>>> AUTO-REWRITE TRIGGERED: score ${overallScore} < 80, issues: ${analysis.issues.length}`);
      autoRewriteTriggeredRef.current = true; // Prevent re-triggering
      setPendingAutoRewrite(true);
    }
  }, [analysis, selectedProfileId, rewriting, showRewriteComparison]);
  
  // Effect to execute the auto-rewrite after state is set - with delay to ensure analysis is displayed first
  useEffect(() => {
    // Ensure analysis is COMPLETE before rewriting (has score, issues, and other fields)
    const analysisIsComplete = analysis && 
      typeof analysis.overall_score === 'number' && 
      Array.isArray(analysis.issues);
    
    console.log('Auto-rewrite execute effect:', {
      pendingAutoRewrite,
      analysisIsComplete,
      hasHandleRewrite: !!handleRewriteRef.current,
      rewriting
    });
    
    if (pendingAutoRewrite && selectedProfileId && content.trim() && !rewriting && analysisIsComplete) {
      // Wait 2.5 seconds for UI to display original analysis before starting rewrite
      const timeoutId = setTimeout(() => {
        console.log('>>> EXECUTING AUTO-REWRITE NOW');
        setPendingAutoRewrite(false);
        // Use the ref to get the latest handleRewrite function
        if (handleRewriteRef.current) {
          handleRewriteRef.current();
        } else {
          console.error('handleRewrite ref is not set!');
        }
      }, 2500);
      
      return () => clearTimeout(timeoutId);
    }
  }, [pendingAutoRewrite, selectedProfileId, content, rewriting, analysis]);
  
  // Reset auto-rewrite trigger when content changes
  useEffect(() => {
    autoRewriteTriggeredRef.current = false;
    setPendingAutoRewrite(false);
  }, [content]);

  const loadConversationHistory = async (userId) => {
    try {
      const API = getApiUrl();
      const response = await api.get(`/conversation/history`, {
        params: { user_id: userId, limit: 10 }
      });
      setConversationHistory(response.data);
    } catch (error) {
      setConversationHistory([]);
    }
  };

  const cleanSummaryText = (summary) => {
    if (!summary) return '';
    let cleaned = summary;
    cleaned = cleaned.replace(/```json\s*/g, '').replace(/\s*```/g, '');
    try {
      if (cleaned.trim().startsWith('{')) {
        const jsonMatch = cleaned.match(/"summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"/);
        if (jsonMatch && jsonMatch[1]) {
          cleaned = jsonMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
        }
      }
    } catch (e) {
      // JSON parsing failed, use original text
    }
    cleaned = cleaned.replace(/^.*?"flagged_status"\s*:\s*"[^"]*"\s*,\s*/s, '');
    cleaned = cleaned.replace(/^.*?"summary"\s*:\s*"/s, '');
    cleaned = cleaned.replace(/"\s*,?\s*"issues".*$/s, '');
    cleaned = cleaned.replace(/"\s*[,}]\s*$/s, '');
    cleaned = cleaned.replace(/\.{3,}$/g, '');
    return cleaned.trim();
  };

  const handleSaveDraft = async () => {
    if (!content.trim()) {
      toast({ title: 'Please enter content to save', status: 'warning', duration: 3000 });
      return;
    }

    try {
      let finalContent = content;
      if (addWatermark && analysis?.is_sponsored) {
        const hasHashtags = content.toLowerCase().includes('#ad') || content.toLowerCase().includes('#sponsored');
        if (!hasHashtags) {
          finalContent = `${content}\n\n#ad #sponsored`;
        }
      }

      const API = getApiUrl();
      
      // Upload image if we have a generated image
      let attachedImageUrl = null;
      if (generatedImage?.base64) {
        try {
          const uploadResponse = await api.post(`/social/upload-image`, {
            image_base64: generatedImage.base64,
            mime_type: generatedImage.mimeType || 'image/png',
          }, {
            headers: { 'X-User-ID': user.id }
          });
          
          if (uploadResponse.data.success) {
            attachedImageUrl = uploadResponse.data.url;
          }
        } catch (uploadError) {
          console.error('Failed to upload image:', uploadError);
          // Continue saving draft without image
        }
      }
      
      const postResponse = await api.post(`/posts`, {
        title: finalContent.substring(0, 50) + '...',
        content: finalContent,
        platforms: [],
        status: 'draft',
        user_id: user.id,
        project_id: selectedProjectId || null,
        attached_image_url: attachedImageUrl,  // Store attached image URL
        attached_image_style: generatedImage?.style || null,
        attached_image_model: generatedImage?.model || null,
        workspace_type: isEnterpriseWorkspace ? 'enterprise' : 'personal',
        enterprise_id: isEnterpriseWorkspace ? enterpriseInfo?.id : null
      }, {
        headers: { 'X-User-ID': user.id }
      });

      // If project is selected and post was created, link it to the project
      if (selectedProjectId && postResponse.data?.post?.id) {
        try {
          await api.post(`/projects/${selectedProjectId}/content`, {
            content_id: postResponse.data.post.id,
            content_type: 'post'
          }, {
            headers: { 'X-User-ID': user.id }
          });
        } catch (linkError) {
          console.error('Failed to link post to project:', linkError);
        }
      }

      const selectedProject = projects.find(p => p.project_id === selectedProjectId);
      let description = '';
      if (selectedProject) {
        description = `Linked to project: ${selectedProject.name}`;
      }
      if (attachedImageUrl) {
        description += description ? '. Image attached!' : 'Image attached!';
      }
      if (addWatermark) {
        description += description ? '. Watermark added' : 'Watermark added to sponsored content';
      }
      
      toast({
        title: 'Draft saved successfully!',
        description: description || undefined,
        status: 'success',
        duration: 3000,
      });
      setAddWatermark(false);
    } catch (error) {
      toast({ title: 'Failed to save draft', status: 'error', duration: 3000 });
    }
  };

  const handleClear = () => {
    if (content.trim() && !confirm('Are you sure you want to clear this content without saving?')) {
      return;
    }
    setContent('');
    setAnalysisResult(null);
    setMediaFile(null);
    setRewrittenContent('');
    setRewrittenAnalysis(null);
    setShowRewriteComparison(false);
    setAnalyzingRewritten(false);
  };

  // Submit content for manager approval (for users without publish permission)
  const handleSubmitForApproval = async () => {
    if (!content.trim()) {
      toast({ title: 'Please enter content to submit', status: 'warning', duration: 3000 });
      return;
    }

    // Check if content has been analyzed
    if (!analysis) {
      toast({ 
        title: 'Content not analyzed', 
        description: 'Please analyze your content before submitting for approval.',
        status: 'warning', 
        duration: 4000 
      });
      return;
    }

    // Check if overall score is at least 80
    const overallScore = analysis.overall_score ?? analysis.score ?? 0;
    if (overallScore < 80) {
      toast({ 
        title: 'Score too low for submission', 
        description: `Your content scored ${Math.round(overallScore)}/100. A minimum score of 80 is required. Please rewrite your content manually or use the "Rewrite & Improve" feature.`,
        status: 'error', 
        duration: 6000 
      });
      return;
    }

    setSubmittingForApproval(true);
    try {
      const API = getApiUrl();
      
      // First save as draft with project_id
      const postResponse = await api.post(`/posts`, {
        title: content.substring(0, 50) + '...',
        content: content,
        platforms: selectedPlatforms,
        status: 'draft',
        user_id: user?.id,
        project_id: selectedProjectId || null,
        workspace_type: isEnterpriseWorkspace ? 'enterprise' : 'personal',
        enterprise_id: isEnterpriseWorkspace ? enterpriseInfo?.id : null
      }, {
        headers: { 'X-User-ID': user?.id }
      });
      
      const postId = postResponse.data?.post?.id || postResponse.data?.id;
      
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
      setContent('');
      setAnalysisResult(null);
      setMediaFile(null);
      setGeneratedImage(null);
      setSelectedPlatforms([]);
      
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

  // Check for promotional content before full analysis
  const checkPromotionalContent = async () => {
    console.log('>>> checkPromotionalContent CALLED');
    if (!content.trim()) {
      toast({ title: 'Please enter content to analyze', status: 'warning', duration: 3000 });
      setLoading(false);
      return;
    }

    setCustomAnalysisStep('Checking for promotional content...');

    try {
      const API = getApiUrl();
      const response = await api.post(`/content/check-promotional`, {
        content,
        user_id: user?.id
      });

      console.log('>>> Promotional check response:', response.data.is_promotional);

      if (response.data.is_promotional) {
        // Promotional content detected - show dialog to user
        // Keep loading state but pause for user decision
        console.log('>>> Promotional content detected, showing dialog');
        setIsPromotionalContent(true);
        setPromotionalDetails(response.data);
        setShowPromotionalDialog(true);
        setLoading(false);  // Stop loading while waiting for user input
        setCustomAnalysisStep('');
      } else {
        // Not promotional - proceed with full analysis
        console.log('>>> Not promotional, calling performFullAnalysis');
        setPromotionalCheckDone(true);
        await performFullAnalysis();
      }
    } catch (error) {
      console.error('Promotional check error:', error);
      // If check fails, proceed with full analysis anyway
      console.log('>>> Promotional check failed, proceeding with analysis anyway');
      setPromotionalCheckDone(true);
      await performFullAnalysis();
    }
  };

  // Handle user response to promotional content dialog
  const handlePromotionalResponse = async (addDisclosure) => {
    setShowPromotionalDialog(false);
    
    if (addDisclosure && promotionalDetails?.suggested_disclosure) {
      // Add disclosure to content
      const disclosureText = promotionalDetails.suggested_disclosure;
      const updatedContent = `${disclosureText}\n\n${content}`;
      setContent(updatedContent);
      toast({ 
        title: 'Disclosure added', 
        description: 'Promotional disclosure has been added to your content.',
        status: 'success', 
        duration: 3000 
      });
    }
    
    // Proceed with full analysis
    setPromotionalCheckDone(true);
    setLoading(true);
    await performFullAnalysis();
  };

  const performFullAnalysis = async () => {
    setLoading(true);
    const selectedProfile = getSelectedProfile();
    
    // Platform-aware context for AI analysis
    const platformGuidance = getPlatformGuidance(selectedPlatforms);
    const platformContext = selectedPlatforms.length > 0 ? {
      target_platforms: selectedPlatforms,
      platform_guidance: platformGuidance,
      character_limit: activeCharLimit
    } : null;
    
    try {
      let result;
      
      // STEP 1: Analyze attached media if present
      if (mediaFile) {
        setAnalyzingMedia(true);
        setCustomAnalysisStep('Analyzing attached media...');
        
        try {
          const API = getApiUrl();
          const formData = new FormData();
          formData.append('file', mediaFile);
          
          const mediaResponse = await api.post(`/media/analyze-upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          
          setMediaAnalysis(mediaResponse.data.analysis);
          
          // Show media analysis result
          const mediaStatus = mediaResponse.data.analysis?.safety_status;
          if (mediaStatus === 'unsafe') {
            toast({
              title: '⚠️ Media Safety Warning',
              description: 'Attached media may contain inappropriate content',
              status: 'error',
              duration: 5000
            });
          } else if (mediaStatus === 'questionable') {
            toast({
              title: '⚡ Media Review Recommended',
              description: 'Attached media may require manual review',
              status: 'warning',
              duration: 4000
            });
          }
        } catch (mediaError) {
          console.error('Media analysis error:', mediaError);
          toast({
            title: 'Media analysis failed',
            description: 'Could not analyze attached media',
            status: 'warning',
            duration: 3000
          });
        } finally {
          setAnalyzingMedia(false);
        }
      }
      
      // STEP 2: Analyze text content (and generate image if requested)
      // If image generation is requested, use the combined endpoint
      // This ensures: 1) Image generated FIRST, 2) Analysis includes BOTH text AND image
      if (wantImage) {
        setImageLoading(true);
        setGeneratedImage(null);
        
        // MULTI-STEP LOADING STATE: Show progress for unified transaction
        setCustomAnalysisStep('Generating image...');
        
        const API = getApiUrl();
        
        // Retry logic for first-try reliability
        let response;
        let retryCount = 0;
        const maxRetries = 2;
        
        while (retryCount <= maxRetries) {
          try {
            response = await api.post(`/content/analyze-with-image`, {
              content: content,
              user_id: user?.id,
              profile_id: selectedProfileId,
              generate_image: true,
              image_style: imageStyle,
              is_promotional: isPromotionalContentCheckbox,
              platform_context: platformContext  // Platform-aware analysis
            }, {
              timeout: 120000,  // 2 minute timeout for image generation + analysis
              headers: { 'X-User-ID': user?.id }  // Required for permission check
            });
            break;  // Success, exit retry loop
          } catch (retryError) {
            retryCount++;
            if (retryCount <= maxRetries) {
              console.log(`Attempt ${retryCount} failed, retrying...`);
              setCustomAnalysisStep(`Retrying image generation (${retryCount}/${maxRetries})...`);
              await new Promise(resolve => setTimeout(resolve, 1500 * retryCount));
            } else {
              throw retryError;
            }
          }
        }
        
        setCustomAnalysisStep('Analyzing content...');
        
        result = response.data;
        
        // Set the generated image if available - handle both URL and base64 formats
        if (result.generated_image) {
          const imageData = result.generated_image;
          console.log('Generated image data received:', Object.keys(imageData));
          
          // Check if we have base64 directly (preferred format after backend update)
          if (imageData.base64) {
            console.log('Using base64 format directly');
            setGeneratedImage({
              base64: imageData.base64,
              mimeType: imageData.mime_type || imageData.mimeType || 'image/png',
              model: imageData.model || 'Unknown',
              style: imageData.style || imageStyle,
              provider: imageData.provider,
              cost: imageData.estimated_cost || 0
            });
          }
          // Check if it's a data URL (contains base64 data)
          else if (imageData.url && imageData.url.startsWith('data:')) {
            console.log('Extracting base64 from data URL');
            // Extract base64 and mime type from data URL
            const [header, base64Data] = imageData.url.split(',');
            const mimeType = header.match(/data:(.*?);/)?.[1] || 'image/png';
            
            setGeneratedImage({
              base64: base64Data,
              mimeType: mimeType,
              model: imageData.model || 'Unknown',
              style: imageData.style || imageStyle,
              provider: imageData.provider,
              cost: imageData.estimated_cost || 0
            });
          } else if (imageData.image_base64) {
            console.log('Using image_base64 field');
            // Direct base64 format with image_base64 key
            setGeneratedImage({
              base64: imageData.image_base64,
              mimeType: imageData.mime_type || imageData.mimeType || 'image/png',
              model: imageData.model || 'Unknown',
              style: imageData.style || imageStyle,
              provider: imageData.provider,
              cost: imageData.estimated_cost || imageData.cost || 0
            });
          } else if (imageData.url) {
            console.log('Using URL format');
            // Regular URL - store as-is for display
            setGeneratedImage({
              url: imageData.url,
              model: imageData.model || 'Unknown',
              style: imageData.style || imageStyle,
              provider: imageData.provider,
              cost: imageData.estimated_cost || 0
            });
          } else {
            console.error('Could not parse image data:', imageData);
          }
          
          // Show toast about image analysis
          if (result.image_included_in_analysis) {
            toast({
              title: 'Image analyzed',
              description: result.image_compliance_penalty 
                ? `Image flagged: -${result.image_compliance_penalty} compliance penalty applied`
                : 'Image passed compliance checks',
              status: result.image_compliance_penalty ? 'warning' : 'success',
              duration: 4000
            });
          }
        }
        
        setCustomAnalysisStep('');
        setImageLoading(false);
        
        // Set the analysis result
        setAnalysisResult(result);
        
      } else {
        // Use the standard analysis hook (text only) with platform context
        // ARCH-004: Use async mode if enabled for better UX (no timeout, real-time progress)
        if (useAsyncAnalysis) {
          // Submit async job
          const { jobId, error } = await submitAsyncJob('/content/analyze/async', {
            content: content,
            language: language,
            profile_id: selectedProfileId,
            platform_context: platformContext,
          }, user?.id);
          
          if (error) {
            throw new Error(error);
          }
          
          // Store job ID for tracking
          console.log('>>> ASYNC JOB SUBMITTED! Job ID:', jobId);
          setAnalysisJobId(jobId);
          setCustomAnalysisStep('Analyzing content in background...');
          
          // The job status hook will handle completion
          return;
        } else {
          // Legacy synchronous mode
          result = await performAnalysis(content, {
            userId: user?.id,
            language: language,
            tone: selectedProfile?.writing_tone || 'professional',
            jobTitle: selectedProfile?.job_title || '',
            profileId: selectedProfileId,
            showProgress: true,
            platformContext: platformContext,
            async: false, // Explicitly use sync mode
          });
        }
      }

      if (result) {
        // Check if promotional content needs disclosure confirmation
        if (result.requires_disclosure_confirmation) {
          setShowSponsoredAlert(true);
        }
        // No toast for successful analysis - results speak for themselves
        
        loadConversationHistory(user?.id);
        
        // Auto-save analyzed content as a draft post (for history)
        try {
          const API = getApiUrl();
          await api.post(`/posts`, {
            title: content.substring(0, 50) + (content.length > 50 ? '...' : ''),
            content: content,
            platforms: selectedPlatforms,
            status: 'draft',
            user_id: user?.id,
            project_id: selectedProjectId || null,
            workspace_type: isEnterpriseWorkspace ? 'enterprise' : 'personal',
            enterprise_id: isEnterpriseWorkspace ? enterpriseInfo?.id : null,
            analysis_result: {
              flagged_status: result.flagged_status,
              compliance_score: result.compliance_score,
              issues_count: result.issues?.length || 0,
              analyzed_at: new Date().toISOString()
            }
          });
          console.log('Analysis auto-saved to history');
        } catch (saveError) {
          console.log('Auto-save to history skipped:', saveError.message);
        }
        
        // AUTO-REWRITE CHECK for synchronous analysis
        if (result && typeof result.overall_score === 'number' && result.overall_score < 80) {
          console.log(`Sync analysis auto-rewrite trigger: score ${result.overall_score} < 80`);
          if (!autoRewriteTriggeredRef.current) {
            autoRewriteTriggeredRef.current = true;
            autoRewriteAnalysisRef.current = result;
            // Use state to trigger rewrite after delay
            setTimeout(() => {
              setTriggerAutoRewrite(true);
            }, 2500);
          }
        }
        
        // Set loading to false for sync mode success
        setLoading(false);
      }
    } catch (error) {
      console.error('Analysis error:', error);
      setImageLoading(false);
      
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
          title: 'Analysis failed',
          description: getErrorMessage(error, 'Please try again'),
          status: 'error',
          duration: 5000,
        });
      }
      // Only set loading to false on error (not on success with async)
      setLoading(false);
    }
    // Note: Don't use finally block - async mode handles loading state via onComplete callback
  };

  // Separate function for image generation that can be called after analysis
  const generateImageForContent = async () => {
    if (!content.trim()) return;
    
    setImageLoading(true);
    setGeneratedImage(null);
    
    try {
      const API = getApiUrl();
      const imagePrompt = `Create a professional social media image that visually represents this content: ${content.substring(0, 300)}`;
      
      const imageResponse = await api.post(`/content/generate-image`, {
        prompt: imagePrompt,
        style: imageStyle,
        prefer_quality: false
      }, {
        headers: { 'X-User-ID': user?.id }
      });
      
      if (imageResponse.data.success) {
        setGeneratedImage({
          base64: imageResponse.data.image_base64,
          mimeType: imageResponse.data.mime_type || 'image/png',
          model: imageResponse.data.model,
          style: imageResponse.data.detected_style,
          justification: imageResponse.data.justification,
          cost: imageResponse.data.estimated_cost
        });
        
        toast({
          title: 'Image generated!',
          description: `Using ${imageResponse.data.model} (${imageResponse.data.detected_style} style)`,
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: 'Image generation failed',
        description: getErrorMessage(error),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setImageLoading(false);
    }
  };

  const handleAnalyze = async () => {
    console.log('>>> handleAnalyze CALLED');
    // Allow analysis if there's either text content OR attached media
    if (!content.trim() && !mediaFile) {
      toast({ title: 'Please enter content or attach media to analyze', status: 'warning', duration: 3000 });
      return;
    }

    if (!selectedProfileId) {
      toast({ title: t('contentGeneration.errors.selectStrategicProfile', 'Please select a Strategic Profile first'), status: 'warning', duration: 3000 });
      return;
    }

    // Set loading state IMMEDIATELY to show the button is working
    setLoading(true);
    setCustomAnalysisStep('Starting analysis...');

    // Reset state for new analysis
    setPromotionalCheckDone(false);
    setIsPromotionalContent(false);
    setAnalysisResult(null);
    setMediaAnalysis(null);
    
    // Start with promotional content check (or skip if only media)
    if (content.trim()) {
      console.log('>>> Calling checkPromotionalContent');
      await checkPromotionalContent();
    } else {
      // Only media - go directly to full analysis
      console.log('>>> Calling performFullAnalysis directly (no text)');
      await performFullAnalysis();
    }
  };

  const handleRewrite = async () => {
    console.log('>>> handleRewrite called');
    if (!content.trim()) {
      console.log('handleRewrite: no content');
      return;
    }

    if (!selectedProfileId) {
      console.log('handleRewrite: no profile selected');
      return;
    }

    // IMPORTANT: Ensure analysis is complete before rewriting
    // The analysis result is crucial for the rewrite agent to fix all issues
    if (!analysis || typeof analysis.overall_score !== 'number') {
      console.warn('Rewrite requested but analysis not complete. Analysis:', analysis);
      // Don't block - let the backend handle it, but log the warning
    }

    setRewriting(true);
    setRewrittenContent('');
    setRewrittenAnalysis(null);
    setGeneratedImage(null);
    
    try {
      const selectedProfile = getSelectedProfile();
      
      // Log analysis being sent for debugging
      console.log('Sending analysis to rewrite API:', {
        overall_score: analysis?.overall_score,
        issues_count: analysis?.issues?.length,
        compliance_score: analysis?.compliance_score,
        employment_law_violations: analysis?.employment_law_compliance?.violations?.length || 0
      });
      
      // Compliance-focused rewrite that uses analysis results
      // IMPORTANT: use_iterative=true ensures the agent rewrites until score >= 80
      const response = await api.post(`/content/rewrite`, {
        content,
        tone: selectedProfile?.writing_tone || 'professional',
        job_title: selectedProfile?.job_title || '',
        user_id: user?.id,
        language: language,
        hashtag_count: hashtagCount,
        profile_id: selectedProfileId,
        is_promotional: isPromotionalContentCheckbox,
        compliance_issues: isPromotionalContentCheckbox ? ['missing_disclosure'] : [],
        analysis_result: analysis || {},  // Pass FULL analysis for compliance-focused rewrite
        use_iterative: true,  // Enable iterative rewriting until score >= 80
        target_score: 80,
        max_iterations: 3  // Allow up to 3 rewrite attempts
      });

      const rewritten = response.data.rewritten_content;
      
      // Show side-by-side comparison (original on left, rewritten on right)
      setRewrittenContent(rewritten);
      setShowRewriteComparison(true);
      
      // Now analyze the rewritten content for comparison
      setAnalyzingRewritten(true);
      try {
        const analysisResponse = await api.post(`/content/analyze`, {
          content: rewritten,
          user_id: user?.id,
          profile_id: selectedProfileId,
          language: language
        });
        setRewrittenAnalysis(analysisResponse.data);
      } catch (analysisError) {
        console.error('Failed to analyze rewritten content:', analysisError);
      } finally {
        setAnalyzingRewritten(false);
      }
      
    } catch (error) {
      console.error('Rewrite error:', error);
    } finally {
      setRewriting(false);
    }
  };
  
  // Handle chat refinement of rewritten content
  const handleRefineRewrittenContent = async () => {
    if (!rewriteChatInput.trim() || !rewrittenContent) return;
    
    const userMessage = rewriteChatInput.trim();
    setRewriteChatInput('');
    
    // Add user message to chat history
    setRewriteChatHistory(prev => [...prev, { role: 'user', content: userMessage }]);
    
    setIsRefiningContent(true);
    try {
      const selectedProfile = getSelectedProfile();
      
      // Build conversation context
      const conversationContext = rewriteChatHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Add the current user request
      conversationContext.push({
        role: 'user',
        content: userMessage
      });
      
      // Send refinement request to the API
      const response = await api.post(`/content/refine`, {
        content: rewrittenContent,
        refinement_request: userMessage,
        tone: selectedProfile?.writing_tone || 'professional',
        job_title: selectedProfile?.job_title || '',
        user_id: user?.id,
        language: language,
        hashtag_count: hashtagCount,
        profile_id: selectedProfileId,
        is_promotional: isPromotionalContentCheckbox,
        conversation_history: conversationContext
      });
      
      const refinedContent = response.data.refined_content || response.data.rewritten_content;
      
      if (refinedContent) {
        // Update the rewritten content
        setRewrittenContent(refinedContent);
        
        // Add AI response to chat history
        setRewriteChatHistory(prev => [...prev, { 
          role: 'assistant', 
          content: `I've updated the content based on your request: "${userMessage}"`,
          refinedContent: refinedContent
        }]);
        
        toast({
          title: 'Content refined!',
          status: 'success',
          duration: 2000,
        });
      }
    } catch (error) {
      console.error('Error refining content:', error);
      toast({
        title: 'Failed to refine',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 3000,
      });
      
      // Add error message to chat
      setRewriteChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I had trouble processing that request. Please try again.',
        isError: true
      }]);
    } finally {
      setIsRefiningContent(false);
    }
  };
  
  // Clear rewrite chat when rewritten content changes significantly
  const clearRewriteChat = () => {
    setRewriteChatHistory([]);
    setRewriteChatInput('');
  };
  useEffect(() => {
    handleRewriteRef.current = handleRewrite;
  });

  // Effect to handle auto-rewrite trigger from job completion callback
  useEffect(() => {
    if (triggerAutoRewrite && !rewriting) {
      console.log('Auto-rewrite effect triggered, calling handleRewrite');
      setTriggerAutoRewrite(false);
      handleRewrite();
    }
  }, [triggerAutoRewrite, rewriting]);

  // Regenerate image with optional feedback - based on the REWRITTEN CONTENT
  const handleRegenerateImage = async () => {
    setRegeneratingImage(true);
    try {
      const API = getApiUrl();
      // Use the rewritten content for the image
      const imagePrompt = `Create a professional social media image that visually represents this content: ${rewrittenContent.substring(0, 300)}`;
      
      const response = await api.post(`/content/regenerate-image`, {
        original_prompt: imagePrompt,
        feedback: imageFeedback || null,
        style: imageStyle,
        prefer_quality: false
      }, {
        headers: { 'X-User-ID': user?.id }
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
        
        toast({
          title: 'Image regenerated!',
          description: imageFeedback ? 'Updated based on your feedback' : 'New variation generated',
          status: 'success',
          duration: 3000,
        });
        setImageFeedback('');
        onImageFeedbackClose();
      }
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

  const analyzeRewrittenContent = async (contentToAnalyze) => {
    setAnalyzingRewritten(true);
    try {
      const API = getApiUrl();
      const response = await api.post(`/content/analyze`, {
        content: contentToAnalyze,
        user_id: user?.id,
        language: language,
        profile_id: selectedProfileId  // Include strategic profile for profile-aware analysis
      });

      const cleanedAnalysis = {
        ...response.data,
        summary: cleanSummaryText(response.data.summary)
      };

      setRewrittenAnalysis(cleanedAnalysis);
    } catch (error) {
      console.error('Rewritten content analysis failed:', error);
      toast({ title: 'Analysis of rewritten content failed', status: 'error', duration: 3000 });
    } finally {
      setAnalyzingRewritten(false);
    }
  };

  const getFlagColor = (status) => {
    const colors = {
      good_coverage: 'green',
      rude_and_abusive: 'red',
      contain_harassment: 'red',
      policy_violation: 'orange',
      pending: 'gray'
    };
    return colors[status] || 'gray';
  };

  // Check if editing existing post
  const rewriteData = typeof window !== 'undefined' ? localStorage.getItem('rewrite_post_data') : null;
  const isEditingPost = rewriteData !== null;

  return (
    <Box>
      {/* ARCH-013: Rate Limit Error Display */}
      {rateLimitError && (
        <Card mb={4} bg="orange.50" borderColor="orange.500" borderWidth="2px">
          <CardBody p={4}>
            <RateLimitError 
              error={rateLimitError} 
              onRetry={() => {
                setRateLimitError(null);
                refreshRateLimit();
              }} 
            />
          </CardBody>
        </Card>
      )}
      
      {/* ARCH-013: Rate Limit Status Badge */}
      <Flex justify="flex-end" mb={2}>
        <RateLimitBadge showUpgrade={true} />
      </Flex>
      
      {isEditingPost && (
        <Card mb={4} bg="blue.50" borderColor="blue.500" borderWidth="2px">
          <CardBody p={4}>
            <HStack spacing={2}>
              <Icon as={FaEdit} color="blue.600" />
              <VStack align="start" spacing={0}>
                <Text fontWeight="700" color="blue.700" fontSize="md">
                  {t('contentModeration.editingExistingPost')}
                </Text>
                <Text fontSize="sm" color="blue.600">
                  {t('contentModeration.editingPostDesc')}
                </Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
      )}

      {/* Content Section - Content and Rewritten Content in ONE card with two columns */}
      <Card bg={cardBg} mb={6}>
        <CardBody p={4}>
          <Grid 
            templateColumns={{ 
              base: '1fr', 
              lg: showRewriteComparison && rewrittenContent 
                ? '1fr 1fr' 
                : (wantImage && (generatedImage || imageLoading)) 
                  ? '2fr 1fr'  // Content + Image side by side
                  : '1fr' 
            }} 
            gap={4}
          >
            {/* Left Column - Original Content */}
            <Box>
              <Text mb={2} fontWeight="600">{t('contentModeration.content')}</Text>
              <Box position="relative">
                <Textarea
                  placeholder={t('contentModeration.contentPlaceholder')}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  minH="200px"
                  pr="150px"
                  spellCheck="false"
                />
                <Box position="absolute" bottom="12px" right="12px" zIndex={1}>
                  <HStack spacing={2}>
                    <Tooltip label={t('contentModeration.uploadMedia')}>
                      <IconButton
                        icon={<FaUpload />}
                        onClick={onMediaOpen}
                        colorScheme="blue"
                        variant="ghost"
                        size="md"
                        aria-label="Upload media"
                      />
                    </Tooltip>
                    <VoiceDictation onTranscript={(text) => setContent(content + (content ? ' ' : '') + text)} />
                    <VoiceAssistant />
                  </HStack>
                </Box>
              </Box>
              
              {/* Action Buttons - Right under the prompt */}
              <Flex gap={2} wrap="wrap" mt={3} justify="space-between" align="center">
                <HStack spacing={2} flexWrap="wrap">
                  <Button
                    leftIcon={loading || analyzingMedia ? null : <FaSyncAlt />}
                    onClick={handleAnalyze}
                    isLoading={loading || analyzingMedia}
                    loadingText={analyzingMedia ? 'Analyzing media...' : t('contentModeration.analyzing')}
                    colorScheme="brand"
                    size="sm"
                    isDisabled={!selectedProfileId}
                    data-testid="analyze-content-btn"
                    spinner={
                      <HStack spacing={1}>
                        <Box w="6px" h="6px" borderRadius="full" bg="white" sx={{ animation: 'pulse 1.4s ease-in-out infinite', '@keyframes pulse': { '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 }, '40%': { transform: 'scale(1)', opacity: 1 } } }} />
                        <Box w="6px" h="6px" borderRadius="full" bg="white" sx={{ animation: 'pulse 1.4s ease-in-out 0.2s infinite', '@keyframes pulse': { '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 }, '40%': { transform: 'scale(1)', opacity: 1 } } }} />
                        <Box w="6px" h="6px" borderRadius="full" bg="white" sx={{ animation: 'pulse 1.4s ease-in-out 0.4s infinite', '@keyframes pulse': { '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 }, '40%': { transform: 'scale(1)', opacity: 1 } } }} />
                      </HStack>
                    }
                  >
                    {t('contentModeration.analyze')}
                    {mediaFile && !mediaAnalysis && ' (+ Media)'}
                  </Button>
                  <Tooltip 
                    label={!selectedProfileId ? "Select a Strategic Profile first" : !content.trim() ? "Enter content to rewrite" : ""}
                    isDisabled={!(!selectedProfileId || !content.trim())}
                  >
                    <Button
                      variant="outline"
                      onClick={handleRewrite}
                      isLoading={rewriting}
                      loadingText="Rewriting..."
                      isDisabled={loading || rewriting || !content.trim() || !selectedProfileId || imageLoading}
                      size="sm"
                      data-testid="rewrite-content-btn"
                    >
                      {t('contentModeration.rewrite')}
                    </Button>
                  </Tooltip>
                  <Button variant="outline" colorScheme="blue" onClick={handleSaveDraft} size="sm">
                    {t('contentModeration.saveDraft')}
                  </Button>
                  <Button variant="outline" colorScheme="red" onClick={handleClear} size="sm">
                    {t('contentModeration.clear')}
                  </Button>
                  
                  {/* Image Generation Status - inline with buttons */}
                  {imageLoading && (
                    <HStack spacing={2} px={2} py={1} bg="blue.50" borderRadius="md">
                      <Spinner size="xs" color="blue.500" />
                      <Text fontSize="xs" color="blue.600" fontWeight="500">
                        Generating image...
                      </Text>
                    </HStack>
                  )}
                </HStack>
                
                {/* Post to Social / Submit for Approval buttons - same row on right */}
                {analysis && (
                  <HStack spacing={2}>
                    {/* Loading state for enterprise users while permissions load */}
                    {isEnterpriseWorkspace && userPermissions === null && (
                      <Button colorScheme="gray" size="sm" isDisabled>
                        Loading...
                      </Button>
                    )}
                    {/* Show Submit for Approval for enterprise users who need approval */}
                    {isEnterpriseWorkspace && userPermissions !== null && userPermissions.needs_approval && !userPermissions.can_publish_directly && (
                      <Tooltip
                        label={(analysis?.overall_score ?? 0) < 80 
                          ? `Score ${Math.round(analysis?.overall_score ?? 0)}/100 is below 80. Improve your content first.`
                          : 'Submit for manager review'}
                        isDisabled={(analysis?.overall_score ?? 0) >= 80}
                      >
                        <Button
                          leftIcon={<FaPaperPlane />}
                          colorScheme="orange"
                          onClick={handleSubmitForApproval}
                          isLoading={submittingForApproval}
                          loadingText="Submitting..."
                          size="sm"
                          isDisabled={(analysis?.overall_score ?? 0) < 80}
                        >
                          Submit for Approval
                        </Button>
                      </Tooltip>
                    )}
                    {/* Show Post to Social for non-enterprise OR enterprise users who can publish directly */}
                    {(!isEnterpriseWorkspace || (userPermissions !== null && !userPermissions.needs_approval) || (userPermissions !== null && userPermissions.can_publish_directly)) && (
                      <>
                        <Button colorScheme="blue" onClick={() => {
                          setOpenModalInScheduleMode(false);
                          onSocialModalOpen();
                        }} size="sm">
                          {t('contentModeration.postToSocial')}
                        </Button>
                        <Button 
                          leftIcon={<FaCalendarAlt />} 
                          colorScheme="purple" 
                          variant="outline"
                          onClick={() => {
                            setOpenModalInScheduleMode(true);
                            onSocialModalOpen();
                          }} 
                          size="sm"
                        >
                          {t('contentModeration.schedule', 'Schedule')}
                        </Button>
                      </>
                    )}
                  </HStack>
                )}
              </Flex>
              
              {/* Image Generation & Promotional Content Options - inline below prompt */}
              <HStack spacing={6} mt={3} flexWrap="wrap">
                <Checkbox
                  isChecked={wantImage}
                  onChange={(e) => setWantImage(e.target.checked)}
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
                {wantImage && (
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
                  isChecked={isPromotionalContentCheckbox}
                  onChange={(e) => setIsPromotionalContentCheckbox(e.target.checked)}
                  colorScheme="brand"
                  size="sm"
                >
                  <Text fontSize="xs" fontWeight="600" color={textColor}>
                    {t('contentModeration.promotionalContent')}
                  </Text>
                </Checkbox>
              </HStack>
            </Box>

            {/* Right Column - Rewritten Content (only shown when rewrite exists) */}
            {showRewriteComparison && rewrittenContent && (
              <Box borderLeftWidth={{ base: 0, lg: "2px" }} borderColor="blue.400" pl={{ base: 0, lg: 4 }}>
                <HStack justify="space-between" mb={2}>
                  <HStack>
                    <Icon as={FaSyncAlt} color="blue.500" boxSize={4} />
                    <Text fontWeight="600" color="blue.500">{t('contentModeration.rewrittenContent')}</Text>
                  </HStack>
                  <IconButton
                    icon={<Text>✕</Text>}
                    size="xs"
                    variant="ghost"
                    onClick={() => { setShowRewriteComparison(false); clearRewriteChat(); }}
                    aria-label="Close rewrite"
                  />
                </HStack>

                <Textarea
                  value={rewrittenContent}
                  onChange={(e) => setRewrittenContent(e.target.value)}
                  minH="200px"
                  bg={rewriteBlueBg}
                  borderColor="blue.300"
                />
                
                <HStack spacing={2} mt={3}>
                  <Button
                    size="sm"
                    leftIcon={<Icon as={FaCopy} />}
                    onClick={() => {
                      navigator.clipboard.writeText(rewrittenContent);
                      toast({ title: t('contentModeration.copiedToClipboard'), status: 'success', duration: 2000 });
                    }}
                  >
                    {t('common.copy')}
                  </Button>
                  <Button
                    size="sm"
                    colorScheme="blue"
                    onClick={() => {
                      setContent(rewrittenContent);
                      if (rewrittenAnalysis) {
                        setAnalysisResult(rewrittenAnalysis);
                      }
                      setShowRewriteComparison(false);
                      setRewrittenContent('');
                      setRewrittenAnalysis(null);
                      clearRewriteChat();
                      toast({ title: 'Applied rewritten content', status: 'success', duration: 2000 });
                    }}
                  >
                    Use This Version
                  </Button>
                </HStack>

                {/* Chat Interface for Refining Rewritten Content */}
                <Box mt={4} pt={4} borderTopWidth="1px" borderColor="blue.200">
                  <HStack mb={2}>
                    <Icon as={FaCommentDots} color="blue.500" boxSize={4} />
                    <Text fontWeight="600" fontSize="sm" color="blue.600">Refine with AI</Text>
                  </HStack>
                  
                  {/* Chat History */}
                  {rewriteChatHistory.length > 0 && (
                    <Box 
                      maxH="150px" 
                      overflowY="auto" 
                      mb={2} 
                      p={2} 
                      bg={analysisSectionBg} 
                      borderRadius="md"
                      borderWidth="1px"
                      borderColor="blue.100"
                    >
                      <VStack spacing={2} align="stretch">
                        {rewriteChatHistory.map((msg, idx) => (
                          <Box key={idx}>
                            {msg.role === 'user' ? (
                              <HStack align="start" justify="flex-end">
                                <Box 
                                  maxW="85%" 
                                  bg="blue.500" 
                                  color="white" 
                                  px={3} 
                                  py={2} 
                                  borderRadius="lg"
                                  borderBottomRightRadius="sm"
                                >
                                  <Text fontSize="xs">{msg.content}</Text>
                                </Box>
                              </HStack>
                            ) : (
                              <HStack align="start">
                                <Box 
                                  maxW="85%" 
                                  bg={msg.isError ? 'red.50' : 'white'} 
                                  px={3} 
                                  py={2} 
                                  borderRadius="lg"
                                  borderBottomLeftRadius="sm"
                                  borderWidth="1px"
                                  borderColor={msg.isError ? 'red.200' : 'blue.100'}
                                >
                                  <Text fontSize="xs" color={msg.isError ? 'red.600' : textColor}>{msg.content}</Text>
                                </Box>
                              </HStack>
                            )}
                          </Box>
                        ))}
                      </VStack>
                    </Box>
                  )}
                  
                  {/* Chat Input */}
                  <HStack>
                    <Input
                      placeholder="Ask AI to refine... (e.g., 'Make it shorter', 'Add more enthusiasm')"
                      size="sm"
                      value={rewriteChatInput}
                      onChange={(e) => setRewriteChatInput(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleRefineRewrittenContent();
                        }
                      }}
                      isDisabled={isRefiningContent}
                    />
                    <IconButton
                      icon={isRefiningContent ? <Spinner size="sm" /> : <Icon as={FaPaperPlane} />}
                      colorScheme="blue"
                      size="sm"
                      onClick={handleRefineRewrittenContent}
                      isDisabled={!rewriteChatInput.trim() || isRefiningContent}
                      aria-label="Send refinement request"
                    />
                    <VoiceAssistant />
                  </HStack>
                </Box>
              </Box>
            )}
            
            {/* Generated Image Column - Shows when image is generated or loading */}
            {wantImage && !showRewriteComparison && (generatedImage || imageLoading) && (
              <Box>
                <Text mb={2} fontWeight="600">{t('contentGeneration.generatedImage')}</Text>
                {imageLoading ? (
                  <Box 
                    minH="200px" 
                    bg={analysisSectionBg} 
                    borderRadius="md" 
                    borderWidth="1px" 
                    borderColor="blue.200"
                    display="flex"
                    flexDirection="column"
                    alignItems="center"
                    justifyContent="center"
                  >
                    <Spinner size="lg" color="blue.500" mb={3} />
                    <Text fontSize="sm" color={textColorSecondary}>
                      {customAnalysisStep || 'Generating image...'}
                    </Text>
                  </Box>
                ) : generatedImage ? (
                  <Box position="relative" borderRadius="md" overflow="hidden" borderWidth="1px" borderColor="blue.200">
                    <Image 
                      src={generatedImage.url || `data:${generatedImage.mimeType || 'image/png'};base64,${generatedImage.base64}`} 
                      alt="Generated content image" 
                      objectFit="cover"
                      w="100%"
                      maxH="300px"
                      cursor="pointer"
                      onClick={onImageExpandOpen}
                    />
                    <HStack position="absolute" top={2} right={2} spacing={1}>
                      <Tooltip label="View full size">
                        <IconButton
                          icon={<FaExpand />}
                          size="sm"
                          colorScheme="blackAlpha"
                          onClick={onImageExpandOpen}
                          aria-label="Expand image"
                        />
                      </Tooltip>
                      <Tooltip label="Regenerate">
                        <IconButton
                          icon={<FaSyncAlt />}
                          size="sm"
                          colorScheme="blackAlpha"
                          onClick={handleRegenerateImage}
                          isLoading={regeneratingImage}
                          aria-label="Regenerate image"
                        />
                      </Tooltip>
                    </HStack>
                  </Box>
                ) : null}
              </Box>
            )}
          </Grid>
        </CardBody>
      </Card>

      {/* Analysis Comparison - Right after content boxes */}
      {showRewriteComparison && analysis && rewrittenAnalysis && !analyzingRewritten && (
        <Card bg={cardBg} mb={6} borderWidth="2px" borderColor="blue.400">
          <CardBody>
            <HStack mb={4}>
              <Icon as={FaChartBar} color="blue.500" />
              <Text fontWeight="700" color={textColor}>Analysis Comparison</Text>
            </HStack>

            <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={6}>
              <Box>
                <Text fontWeight="600" mb={3} color={textColor} pb={2} borderBottomWidth="2px" borderColor="gray.300">
                  Original Post Analysis
                </Text>
                <AnalysisResults analysis={analysis} title="" />
              </Box>
              <Box>
                <Text fontWeight="600" mb={3} color="blue.500" pb={2} borderBottomWidth="2px" borderColor="blue.300">
                  Rewritten Post Analysis
                </Text>
                <AnalysisResults analysis={rewrittenAnalysis} title="" />
              </Box>
            </Grid>
          </CardBody>
        </Card>
      )}

      {/* Overall Analysis Summary - Shown ABOVE Settings when score >= 80 and no rewrite comparison */}
      {analysis && !showRewriteComparison && (analysis.overall_score >= 80) && (
        <Card borderWidth="3px" borderColor={`${getFlagColor(analysis.flagged_status)}.500`} mb={6}>
          <CardBody>
            {/* Analysis Header with Export Button - Aligned on same row */}
            <Flex justify="space-between" align="center" mb={4}>
              <HStack spacing={2}>
                <Icon as={FaCheckCircle} color="green.500" boxSize={5} />
                <Text fontWeight="700" fontSize="lg" color={textColor}>Overall Analysis Summary</Text>
                <Badge colorScheme="green" fontSize="sm">Score: {analysis.overall_score}/100</Badge>
              </HStack>
              <Menu>
                <MenuButton
                  as={Button}
                  size="sm"
                  leftIcon={<Icon as={FaDownload} />}
                  colorScheme="brand"
                  variant="outline"
                >
                  Export Analysis
                </MenuButton>
                <MenuList>
                  <MenuItem 
                    icon={<Icon as={FaFileAlt} />}
                    onClick={() => {
                      exportToJSON(analysis, content);
                      toast({ title: 'Analysis exported as JSON', status: 'success', duration: 2000 });
                    }}
                  >
                    Export as JSON
                  </MenuItem>
                  <MenuItem 
                    icon={<Icon as={FaFilePdf} />}
                    onClick={() => {
                      exportToPDF(analysis, content);
                      toast({ title: 'Opening print dialog for PDF', status: 'info', duration: 2000 });
                    }}
                  >
                    Export as PDF
                  </MenuItem>
                </MenuList>
              </Menu>
            </Flex>
            <AnalysisResults analysis={analysis} title="" compact={false} />
            {user && <FeedbackSection analysis={analysis} content={content} userId={user.id} />}
          </CardBody>
        </Card>
      )}

      {/* Settings Section - Strategic Profile, Platform Selector, etc. */}
      <Card bg={cardBg} mb={6}>
        <CardBody p={4}>
          <VStack align="stretch" spacing={4}>
            {/* Attached Media Preview */}
            {mediaFile && (
              <Box p={3} bg={analysisSectionBg} borderRadius="md" borderWidth="1px" borderColor="blue.200">
                <HStack justify="space-between" mb={2}>
                  <HStack>
                    <Icon as={mediaFile.type?.startsWith('video/') ? FaUpload : FaImage} color="blue.500" boxSize={4} />
                    <Text fontWeight="600" fontSize="sm" color={textColor}>Attached Media</Text>
                    <Badge colorScheme="blue" fontSize="xs">{mediaFile.type?.startsWith('video/') ? 'Video' : 'Image'}</Badge>
                  </HStack>
                  <Button
                    size="xs"
                    variant="ghost"
                    colorScheme="red"
                    onClick={() => {
                      setMediaFile(null);
                      setMediaPreviewUrl(null);
                      setMediaAnalysis(null);
                    }}
                  >
                    Remove
                  </Button>
                </HStack>
                <HStack spacing={4}>
                  {mediaPreviewUrl && (
                    mediaFile.type?.startsWith('video/') ? (
                      <video src={mediaPreviewUrl} style={{ maxWidth: '120px', maxHeight: '80px', borderRadius: '8px' }} controls muted />
                    ) : (
                      <Image src={mediaPreviewUrl} alt="Preview" maxW="120px" maxH="80px" borderRadius="md" objectFit="cover" />
                    )
                  )}
                  <VStack align="start" spacing={1} flex={1}>
                    <Text fontSize="xs" color={textColorSecondary}>{mediaFile.name}</Text>
                    <Text fontSize="xs" color={textColorSecondary}>{(mediaFile.size / 1024 / 1024).toFixed(2)} MB</Text>
                    {mediaAnalysis ? (
                      <Badge 
                        colorScheme={mediaAnalysis.safety_status === 'safe' ? 'green' : mediaAnalysis.safety_status === 'questionable' ? 'orange' : 'red'}
                        fontSize="xs"
                      >
                        {mediaAnalysis.safety_status === 'safe' ? '✓ Safe' : mediaAnalysis.safety_status === 'questionable' ? '⚡ Review' : '⚠️ Unsafe'}
                      </Badge>
                    ) : (
                      <Text fontSize="xs" color="blue.500">Will be analyzed with content</Text>
                    )}
                  </VStack>
                </HStack>
              </Box>
            )}

            {/* Strategic Profile Selector */}
            <Box p={3} bg={analysisSectionBg} borderRadius="md" borderWidth="1px" borderColor={borderColorDefault}>
              <HStack justify="space-between" mb={2}>
                <HStack>
                  <Icon as={FaBrain} color="blue.500" boxSize={4} />
                  <Text fontWeight="600" fontSize="sm" color={textColor}>{t('contentGeneration.strategicProfile')}</Text>
                </HStack>
                {getSelectedProfile()?.knowledge_stats?.has_knowledge && (
                  <Badge colorScheme="blue" fontSize="xs">
                    {getSelectedProfile()?.knowledge_stats?.document_count} docs
                  </Badge>
                )}
              </HStack>
              <Select
                value={selectedProfileId || ''}
                onChange={(e) => setSelectedProfileId(e.target.value)}
                size="sm"
                bg={cardBg}
                isDisabled={loadingProfiles}
                placeholder="Choose a Profile..."
              >
                {strategicProfiles.map(profile => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} {profile.is_default ? '(Default)' : ''} - {profile.writing_tone}
                  </option>
                ))}
              </Select>
              {getSelectedProfile()?.seo_keywords?.length > 0 && (
                <Wrap mt={2} spacing={1}>
                  {getSelectedProfile().seo_keywords.slice(0, 5).map((kw, i) => (
                    <WrapItem key={i}>
                      <Tag size="sm" colorScheme="blue" variant="subtle">
                        <TagLabel fontSize="xs">{kw}</TagLabel>
                      </Tag>
                    </WrapItem>
                  ))}
                </Wrap>
              )}
              {loadingProfiles && (
                <HStack mt={2}>
                  <Spinner size="xs" />
                  <Text fontSize="xs" color={textColorSecondary}>Loading profiles...</Text>
                </HStack>
              )}
            </Box>

            {/* Platform Selector */}
            <Box p={3} bg={analysisSectionBg} borderRadius="md" borderWidth="1px" borderColor={borderColorDefault}>
              <HStack justify="space-between" mb={2}>
                <HStack>
                  <Icon as={FaGlobe} color="purple.500" boxSize={4} />
                  <Text fontWeight="600" fontSize="sm" color={textColor}>{t('contentGeneration.targetPlatforms', 'Target Platform(s)')}</Text>
                </HStack>
                {selectedPlatforms.length > 0 && (
                  <Badge colorScheme="purple" fontSize="xs">
                    {selectedPlatforms.length} {t('common.selected', 'selected')}
                  </Badge>
                )}
              </HStack>
              <Text fontSize="xs" color={textColorSecondary} mb={2}>
                {t('contentGeneration.selectPlatformsOptimize')}
              </Text>
              <PlatformSelector
                selectedPlatforms={selectedPlatforms}
                onChange={setSelectedPlatforms}
                showAllPlatforms={true}
                showConnectLink={false}
                showCharLimits={true}
                compact={false}
              />
              {activeCharLimit && (
                <Box mt={3}>
                  <CharacterCounter 
                    current={content.length} 
                    limit={activeCharLimit}
                    showProgress={true}
                    size="sm"
                  />
                </Box>
              )}
            </Box>

            {/* Hashtag Slider */}
            <Box>
              <HStack justify="space-between" mb={2}>
                <Text fontSize="xs" fontWeight="600" color={textColor}>{t('contentModeration.hashtags')}</Text>
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

            {/* Project Selection */}
            <FormControl>
              <FormLabel fontSize="xs" fontWeight="600" color={textColor} mb={1}>
                <HStack spacing={1}>
                  <Icon as={FaFolderOpen} color="blue.500" boxSize={3} />
                  <Text>Assign to Project (Optional)</Text>
                </HStack>
              </FormLabel>
              <Select
                size="sm"
                placeholder="No project selected"
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                  bg={selectBg}
                  isDisabled={loadingProjects}
                >
                  {projects.map(project => (
                    <option key={project.project_id} value={project.project_id}>
                      {project.name} {project.project_type === 'enterprise' ? '(Enterprise)' : '(Personal)'}
                    </option>
                  ))}
                </Select>
                <FormHelperText fontSize="2xs" color={textColorSecondary}>
                  {selectedProjectId 
                    ? `Content will be linked to: ${projects.find(p => p.project_id === selectedProjectId)?.name}`
                    : 'Select a project to organize your content'
                  }
                </FormHelperText>
              </FormControl>

              {/* Submit for Approval button (for enterprise users needing approval) */}
              {analysis && isEnterpriseWorkspace && userPermissions !== null && userPermissions.needs_approval && !userPermissions.can_publish_directly && (
                <Tooltip
                  label={
                    !analysis 
                      ? 'Please analyze your content first' 
                      : (analysis?.overall_score ?? analysis?.score ?? 0) < 80 
                        ? `Score ${Math.round(analysis?.overall_score ?? analysis?.score ?? 0)}/100 is below the minimum of 80. Use "Rewrite & Improve" or edit manually.`
                        : 'Submit your content for manager review'
                  }
                  placement="top"
                  isDisabled={(analysis?.overall_score ?? analysis?.score ?? 0) >= 80}
                >
                  <Button 
                    leftIcon={<FaPaperPlane />}
                    colorScheme="orange"
                    onClick={handleSubmitForApproval}
                    isLoading={submittingForApproval}
                    loadingText="Submitting..."
                    size="sm"
                    isDisabled={!analysis || (analysis?.overall_score ?? analysis?.score ?? 0) < 80}
                    mt={2}
                  >
                    Submit for Approval
                  </Button>
                </Tooltip>
              )}
              
              {/* Show score warning/success banner for ALL users when analyzed */}
              {analysis && typeof analysis.overall_score === 'number' && (
                <>
                  {/* Show warning when score is below 80 - ONLY on Enterprise Workspace */}
                  {isEnterpriseWorkspace && analysis.overall_score < 80 && (
                    <Alert status="warning" mt={2} borderRadius="md" size="sm">
                      <AlertIcon />
                      <AlertDescription fontSize="sm">
                        <strong>Score too low for submission:</strong> Your content scored {Math.round(analysis.overall_score)}/100. 
                        A minimum score of 80 is required. {pendingAutoRewrite ? 'Auto-rewriting...' : 'Please use the "Rewrite" button or edit manually and re-analyze.'}
                      </AlertDescription>
                    </Alert>
                  )}
                  {/* Show success when score is 80 or above */}
                  {analysis.overall_score >= 80 && (
                    <Alert status="success" mt={2} borderRadius="md" size="sm">
                      <AlertIcon />
                      <AlertDescription fontSize="sm">
                        Your content scored {Math.round(analysis.overall_score)}/100 and meets the quality threshold!
                        {userPermissions?.needs_approval && ' Click "Submit for Approval" to send it for manager review.'}
                      </AlertDescription>
                    </Alert>
                  )}
                </>
              )}
              
              {/* Show approval workflow info for users who need approval */}
              {userPermissions?.needs_approval && !userPermissions?.can_publish_directly && !analysis && (
                <Alert status="info" mt={2} borderRadius="md" size="sm">
                  <AlertIcon />
                  <AlertDescription fontSize="sm">
                    Your content will be reviewed by a manager before publishing. Analyze your content first, then use &quot;Submit for Approval&quot; when ready.
                  </AlertDescription>
                </Alert>
              )}

              {mediaFile && (
                <Box p={3} bg={platformBg} borderRadius="md">
                  <Text fontSize="sm" color={textColorSecondary}>Uploaded: {mediaFile.filename}</Text>
                </Box>
              )}

              {/* Image display moved to right of content box */}
            </VStack>
          </CardBody>
        </Card>

      {/* Media Analysis Results */}
      {mediaAnalysis && (
        <Card mb={4} borderWidth="2px" borderColor={mediaAnalysis.safety_status === 'safe' ? 'green.400' : mediaAnalysis.safety_status === 'questionable' ? 'orange.400' : 'red.400'}>
          <CardBody>
            <Flex justify="space-between" align="center" mb={4}>
              <HStack spacing={2}>
                <Icon as={mediaAnalysis.is_video ? FaUpload : FaImage} color={mediaAnalysis.safety_status === 'safe' ? 'green.500' : 'orange.500'} boxSize={5} />
                <Text fontWeight="700" fontSize="lg" color={textColor}>
                  {mediaAnalysis.is_video ? 'Video' : 'Image'} Analysis
                </Text>
                <Badge 
                  colorScheme={mediaAnalysis.safety_status === 'safe' ? 'green' : mediaAnalysis.safety_status === 'questionable' ? 'orange' : 'red'}
                  fontSize="sm"
                >
                  {mediaAnalysis.risk_level?.toUpperCase()} RISK
                </Badge>
              </HStack>
            </Flex>

            {/* Summary */}
            <Box p={3} bg={mediaAnalysis.safety_status === 'safe' ? 'green.50' : mediaAnalysis.safety_status === 'questionable' ? 'orange.50' : 'red.50'} borderRadius="md" mb={4} _dark={{ bg: mediaAnalysis.safety_status === 'safe' ? 'green.900' : 'orange.900' }}>
              <Text fontWeight="500">{mediaAnalysis.summary || mediaAnalysis.description}</Text>
            </Box>

            {/* Safe Search Results */}
            {mediaAnalysis.safe_search && (
              <Box mb={4}>
                <Text fontWeight="600" fontSize="sm" mb={2}>Safety Check:</Text>
                <HStack spacing={3} flexWrap="wrap">
                  <Badge colorScheme={mediaAnalysis.safe_search.adult === 'VERY_UNLIKELY' || mediaAnalysis.safe_search.adult === 'UNLIKELY' ? 'green' : 'orange'} px={2} py={1}>
                    Adult: {mediaAnalysis.safe_search.adult}
                  </Badge>
                  <Badge colorScheme={mediaAnalysis.safe_search.violence === 'VERY_UNLIKELY' || mediaAnalysis.safe_search.violence === 'UNLIKELY' ? 'green' : 'orange'} px={2} py={1}>
                    Violence: {mediaAnalysis.safe_search.violence}
                  </Badge>
                  <Badge colorScheme={mediaAnalysis.safe_search.racy === 'VERY_UNLIKELY' || mediaAnalysis.safe_search.racy === 'UNLIKELY' ? 'green' : 'orange'} px={2} py={1}>
                    Racy: {mediaAnalysis.safe_search.racy}
                  </Badge>
                  {mediaAnalysis.safe_search.explicit && (
                    <Badge colorScheme={mediaAnalysis.safe_search.explicit === 'VERY_UNLIKELY' || mediaAnalysis.safe_search.explicit === 'UNLIKELY' ? 'green' : 'orange'} px={2} py={1}>
                      Explicit: {mediaAnalysis.safe_search.explicit}
                    </Badge>
                  )}
                </HStack>
                {mediaAnalysis.frames_analyzed && (
                  <Text fontSize="xs" color="gray.500" mt={2}>
                    Analyzed {mediaAnalysis.frames_analyzed} video frames
                  </Text>
                )}
              </Box>
            )}

            {/* Detected Labels */}
            {mediaAnalysis.labels && mediaAnalysis.labels.length > 0 && (
              <Box mb={4}>
                <Text fontWeight="600" fontSize="sm" mb={2}>Detected Content:</Text>
                <HStack spacing={2} flexWrap="wrap">
                  {mediaAnalysis.labels.slice(0, 8).map((label, idx) => (
                    <Badge key={idx} colorScheme="blue" fontSize="xs">
                      {label.description} ({Math.round(label.score)}%)
                    </Badge>
                  ))}
                </HStack>
              </Box>
            )}

            {/* AI Analysis Findings - GPT-4o Vision detailed analysis */}
            {mediaAnalysis.gpt_analysis && (
              <Box mb={4} p={4} bg={mediaAnalysis.risk_level === 'critical' || mediaAnalysis.risk_level === 'high' ? 'red.50' : 'orange.50'} borderRadius="md" borderWidth="1px" borderColor={mediaAnalysis.risk_level === 'critical' || mediaAnalysis.risk_level === 'high' ? 'red.200' : 'orange.200'} _dark={{ bg: mediaAnalysis.risk_level === 'critical' || mediaAnalysis.risk_level === 'high' ? 'red.900' : 'orange.900' }}>
                <HStack spacing={2} mb={3}>
                  <Icon as={FaExclamationTriangle} color={mediaAnalysis.risk_level === 'critical' || mediaAnalysis.risk_level === 'high' ? 'red.500' : 'orange.500'} />
                  <Text fontWeight="700" fontSize="md" color={mediaAnalysis.risk_level === 'critical' || mediaAnalysis.risk_level === 'high' ? 'red.700' : 'orange.700'} _dark={{ color: mediaAnalysis.risk_level === 'critical' || mediaAnalysis.risk_level === 'high' ? 'red.200' : 'orange.200' }}>
                    AI Content Analysis Findings
                  </Text>
                </HStack>
                
                {/* Specific Concerns */}
                {mediaAnalysis.gpt_analysis.specific_concerns && mediaAnalysis.gpt_analysis.specific_concerns.length > 0 && (
                  <Box mb={3}>
                    <Text fontWeight="600" fontSize="sm" mb={2} color="gray.700" _dark={{ color: 'gray.200' }}>
                      Identified Issues:
                    </Text>
                    <VStack align="start" spacing={2}>
                      {mediaAnalysis.gpt_analysis.specific_concerns.map((concern, idx) => (
                        <HStack key={idx} spacing={2} align="start">
                          <Icon as={FaTimesCircle} color="red.500" boxSize={4} mt={0.5} />
                          <Text fontSize="sm" color="gray.800" _dark={{ color: 'gray.100' }}>{concern}</Text>
                        </HStack>
                      ))}
                    </VStack>
                  </Box>
                )}
                
                {/* Detailed Frame Analyses */}
                {mediaAnalysis.gpt_analysis.detailed_analyses && mediaAnalysis.gpt_analysis.detailed_analyses.length > 0 && (
                  <Box>
                    <Text fontWeight="600" fontSize="sm" mb={2} color="gray.700" _dark={{ color: 'gray.200' }}>
                      Frame-by-Frame Analysis:
                    </Text>
                    <VStack align="start" spacing={3}>
                      {mediaAnalysis.gpt_analysis.detailed_analyses.slice(0, 5).map((frame, idx) => (
                        <Box key={idx} p={3} bg="white" borderRadius="md" borderWidth="1px" borderColor="gray.200" w="100%" _dark={{ bg: 'gray.700', borderColor: 'gray.600' }}>
                          <HStack justify="space-between" mb={2}>
                            <Badge colorScheme={frame.risk_level === 'critical' ? 'red' : frame.risk_level === 'high' ? 'orange' : 'yellow'} fontSize="xs">
                              Frame {frame.frame_index || idx + 1}: {frame.risk_level?.toUpperCase() || 'UNKNOWN'} RISK
                            </Badge>
                            {frame.harm_type && frame.harm_type !== 'none' && (
                              <Badge colorScheme="purple" fontSize="xs">
                                {frame.harm_type.replace(/_/g, ' ')}
                              </Badge>
                            )}
                          </HStack>
                          {frame.description && (
                            <Text fontSize="sm" color="gray.700" _dark={{ color: 'gray.200' }} mb={2}>
                              {frame.description}
                            </Text>
                          )}
                          {frame.explanation && (
                            <Text fontSize="xs" color="gray.600" _dark={{ color: 'gray.300' }} fontStyle="italic">
                              {frame.explanation}
                            </Text>
                          )}
                          {frame.specific_concerns && frame.specific_concerns.length > 0 && (
                            <VStack align="start" spacing={1} mt={2}>
                              {frame.specific_concerns.map((c, cidx) => (
                                <HStack key={cidx} spacing={1}>
                                  <Icon as={FaExclamationTriangle} color="orange.400" boxSize={3} />
                                  <Text fontSize="xs" color="gray.600" _dark={{ color: 'gray.300' }}>{c}</Text>
                                </HStack>
                              ))}
                            </VStack>
                          )}
                        </Box>
                      ))}
                    </VStack>
                  </Box>
                )}
              </Box>
            )}

            {/* Suspicious Objects Detected */}
            {mediaAnalysis.suspicious_objects && mediaAnalysis.suspicious_objects.length > 0 && (
              <Box mb={4}>
                <Text fontWeight="600" fontSize="sm" mb={2}>Suspicious Objects Detected:</Text>
                <HStack spacing={2} flexWrap="wrap">
                  {mediaAnalysis.suspicious_objects.map((obj, idx) => (
                    <Badge key={idx} colorScheme="red" fontSize="xs">
                      {obj.item || obj.name} ({obj.category})
                    </Badge>
                  ))}
                </HStack>
              </Box>
            )}

            {/* Risk Indicators */}
            {mediaAnalysis.risk_indicators && mediaAnalysis.risk_indicators.length > 0 && (
              <Box mb={4}>
                <Text fontWeight="600" fontSize="sm" mb={2}>Risk Indicators:</Text>
                <VStack align="start" spacing={1}>
                  {mediaAnalysis.risk_indicators.slice(0, 5).map((indicator, idx) => (
                    <HStack key={idx} spacing={2}>
                      <Icon as={FaExclamationTriangle} color="orange.500" boxSize={3} />
                      <Text fontSize="sm">{indicator}</Text>
                    </HStack>
                  ))}
                </VStack>
              </Box>
            )}

            {/* Recommendations */}
            {mediaAnalysis.recommendations && mediaAnalysis.recommendations.length > 0 && (
              <Box>
                <Text fontWeight="600" fontSize="sm" mb={2}>Recommendations:</Text>
                <VStack align="start" spacing={1}>
                  {mediaAnalysis.recommendations.map((rec, idx) => (
                    <HStack key={idx} spacing={2}>
                      <Icon as={FaCheckCircle} color="blue.500" boxSize={3} />
                      <Text fontSize="sm">{rec}</Text>
                    </HStack>
                  ))}
                </VStack>
              </Box>
            )}
          </CardBody>
        </Card>
      )}

      {/* Overall Analysis Summary - Shown BELOW Settings when score < 80 (needs improvement) */}
      {analysis && !showRewriteComparison && (analysis.overall_score < 80) && (
        <Card borderWidth="3px" borderColor={`${getFlagColor(analysis.flagged_status)}.500`}>
          <CardBody>
            {/* Analysis Header with Export Button - Aligned on same row */}
            <Flex justify="space-between" align="center" mb={4}>
              <HStack spacing={2}>
                <Icon as={FaCheckCircle} color="blue.500" boxSize={5} />
                <Text fontWeight="700" fontSize="lg" color={textColor}>Overall Analysis Summary</Text>
              </HStack>
              <Menu>
                <MenuButton
                  as={Button}
                  size="sm"
                  leftIcon={<Icon as={FaDownload} />}
                  colorScheme="brand"
                  variant="outline"
                >
                  Export Analysis
                </MenuButton>
                <MenuList>
                  <MenuItem 
                    icon={<Icon as={FaFileAlt} />}
                    onClick={() => {
                      exportToJSON(analysis, content);
                      toast({ title: 'Analysis exported as JSON', status: 'success', duration: 2000 });
                    }}
                  >
                    Export as JSON
                  </MenuItem>
                  <MenuItem 
                    icon={<Icon as={FaFilePdf} />}
                    onClick={() => {
                      exportToPDF(analysis, content);
                      toast({ title: 'Opening print dialog for PDF', status: 'info', duration: 2000 });
                    }}
                  >
                    Export as PDF
                  </MenuItem>
                </MenuList>
              </Menu>
            </Flex>
            <AnalysisResults analysis={analysis} title="" compact={false} />
            {user && <FeedbackSection analysis={analysis} content={content} userId={user.id} />}
          </CardBody>
        </Card>
      )}

      {/* Post to Social Modal - Pass generated image for publishing */}
      <PostToSocialModal
        isOpen={isSocialModalOpen}
        onClose={() => {
          onSocialModalClose();
          setOpenModalInScheduleMode(false);
        }}
        content={content}
        userId={user?.id}
        imageBase64={generatedImage?.base64}
        imageMimeType={generatedImage?.mimeType || 'image/png'}
        mediaUrl={generatedImage?.url}
        defaultSchedule={openModalInScheduleMode}
        onPostSuccess={() => {
          setContent('');
          setAnalysisResult(null);
          setMediaFile(null);
          setGeneratedImage(null);
          setOpenModalInScheduleMode(false);
        }}
      />

      {/* Media Analyzer Modal for Image/Video Upload */}
      <Modal isOpen={isMediaOpen} onClose={onMediaClose} size="xl" isCentered closeOnOverlayClick={false}>
        <ModalOverlay bg="blackAlpha.600" zIndex={10000} />
        <ModalContent bg={cardBg} zIndex={10001}>
          <ModalHeader>{t('contentModeration.uploadMedia')}</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <MediaUploader 
              onFileSelected={(file, previewUrl) => {
                setMediaFile(file);
                setMediaPreviewUrl(previewUrl);
                setMediaAnalysis(null); // Reset any previous analysis
              }}
              onFileRemoved={() => {
                setMediaFile(null);
                setMediaPreviewUrl(null);
                setMediaAnalysis(null);
              }}
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onMediaClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={() => {
                onMediaClose();
                toast({
                  title: 'Media attached',
                  description: mediaFile?.name || 'File ready for analysis',
                  status: 'success',
                  duration: 2000
                });
              }}
              isDisabled={!mediaFile}
            >
              Attach Media
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Promotional Content Pre-Check Dialog */}
      <AlertDialog 
        isOpen={showPromotionalDialog} 
        leastDestructiveRef={promotionalCancelRef}
        onClose={() => setShowPromotionalDialog(false)}
      >
        <AlertDialogOverlay bg="blackAlpha.600">
          <AlertDialogContent bg="white" _dark={{ bg: 'gray.800' }}>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Promotional Content Detected
            </AlertDialogHeader>
            <AlertDialogBody>
              <VStack align="start" spacing={3}>
                <Text>
                  This content appears to contain promotional or sponsored material.
                </Text>
                {promotionalDetails?.indicators && (
                  <Box bg="yellow.50" p={3} borderRadius="md" w="full">
                    <Text fontSize="sm" fontWeight="600" color="yellow.800" mb={2}>
                      Detected promotional indicators:
                    </Text>
                    <VStack align="start" spacing={1}>
                      {promotionalDetails.indicators.map((indicator, idx) => (
                        <Text key={idx} fontSize="sm" color="yellow.700">• {indicator}</Text>
                      ))}
                    </VStack>
                  </Box>
                )}
                <Box bg="blue.50" p={3} borderRadius="md" w="full">
                  <Text fontSize="sm" color="blue.800">
                    <strong>Recommended disclosure:</strong>
                  </Text>
                  <Text fontSize="sm" color="blue.700" mt={1} fontStyle="italic">
                    {promotionalDetails?.suggested_disclosure || '#ad #sponsored'}
                  </Text>
                </Box>
                <Text fontSize="sm" color="gray.600">
                  Would you like to add the disclosure to your content before analysis?
                </Text>
              </VStack>
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button 
                ref={promotionalCancelRef}
                onClick={() => handlePromotionalResponse(false)}
              >
                No, Continue Without
              </Button>
              <Button
                colorScheme="brand"
                onClick={() => handlePromotionalResponse(true)}
                ml={3}
              >
                Yes, Add Disclosure
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      {/* Sponsored Content Alert - Disclosure Confirmation */}
      <AlertDialog isOpen={showSponsoredAlert} onClose={() => setShowSponsoredAlert(false)}>
        <AlertDialogOverlay bg="blackAlpha.600">
          <AlertDialogContent bg="white" _dark={{ bg: 'gray.800' }}>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Promotional Content Detected
            </AlertDialogHeader>
            <AlertDialogBody>
              <VStack align="start" spacing={3}>
                <Text>
                  {analysis?.disclosure_message || 
                   "This content appears to be promotional. Are you a paid influencer, brand ambassador, or receiving any compensation for this post?"}
                </Text>
                <Box bg="orange.50" p={3} borderRadius="md" w="full">
                  <Text fontSize="sm" color="orange.800">
                    <strong>Why we&apos;re asking:</strong> If this is sponsored content, proper disclosure 
                    (#ad, #sponsored, or &quot;Paid partnership&quot;) is required by FTC, EU, and Norway regulations.
                    Without disclosure, your compliance score may be affected.
                  </Text>
                </Box>
                <Box bg="blue.50" p={3} borderRadius="md" w="full">
                  <Text fontSize="sm" color="blue.800">
                    <strong>Note:</strong> If you&apos;re NOT receiving any compensation, affiliate links, 
                    free products, or brand partnerships for this post, you can safely select &quot;No&quot;.
                  </Text>
                </Box>
              </VStack>
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button 
                onClick={async () => { 
                  // User confirms they are NOT sponsored - recalculate without penalty
                  try {
                    const API = getApiUrl();
                    const response = await api.post(`/content/confirm-disclosure`, {
                      is_sponsored: false,
                      analysis_id: analysis?.id,
                      original_analysis: analysis
                    });
                    
                    setAnalysisResult({
                      ...analysis,
                      ...response.data,
                      summary: cleanSummaryText(response.data.summary || analysis.summary)
                    });
                    
                    toast({
                      title: 'Analysis updated',
                      description: 'No disclosure required for non-sponsored content.',
                      status: 'success',
                      duration: 3000,
                    });
                  } catch (error) {
                    console.error('Disclosure confirmation failed:', error);
                  }
                  
                  setAddWatermark(false); 
                  setShowSponsoredAlert(false); 
                }}
              >
                No, This is NOT Sponsored
              </Button>
              <Button
                colorScheme="brand"
                onClick={async () => {
                  // User confirms they ARE sponsored - add disclosure
                  try {
                    const API = getApiUrl();
                    const response = await api.post(`/content/confirm-disclosure`, {
                      is_sponsored: true,
                      analysis_id: analysis?.id,
                      original_analysis: analysis
                    });
                    
                    setAnalysisResult({
                      ...analysis,
                      ...response.data,
                      summary: cleanSummaryText(response.data.summary || analysis.summary)
                    });
                    
                    setAddWatermark(true);
                    toast({
                      title: 'Disclosure Required',
                      description: '#ad #sponsored will be added when you save or publish to ensure compliance.',
                      status: 'warning',
                      duration: 5000,
                    });
                  } catch (error) {
                    console.error('Disclosure confirmation failed:', error);
                    toast({
                      title: 'Watermark will be added',
                      description: '#ad #sponsored will be added when you save or publish',
                      status: 'info',
                      duration: 5000,
                    });
                  }
                  
                  setShowSponsoredAlert(false);
                }}
                ml={3}
              >
                Yes, Add Disclosure
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      {/* Image Feedback Modal for regeneration */}
      <Modal isOpen={isImageFeedbackOpen} onClose={onImageFeedbackClose} size="md">
        <ModalOverlay zIndex={10000} />
        <ModalContent bg={cardBg} zIndex={10001}>
          <ModalHeader color={textColor}>Regenerate Image</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4} align="stretch">
              <Box>
                <Text fontSize="sm" fontWeight="600" mb={2} color={textColor}>Style</Text>
                <Select
                  value={imageStyle}
                  onChange={(e) => setImageStyle(e.target.value)}
                  size="sm"
                  bg={cardBg}
                >
                  <option value="simple">Simple/Clean</option>
                  <option value="creative">Creative</option>
                  <option value="photorealistic">Photorealistic</option>
                  <option value="illustration">Illustration</option>
                </Select>
              </Box>
              <Box>
                <Text fontSize="sm" fontWeight="600" mb={2} color={textColor}>Feedback (optional)</Text>
                <Textarea
                  value={imageFeedback}
                  onChange={(e) => setImageFeedback(e.target.value)}
                  placeholder="Describe what you'd like to change about the image..."
                  size="sm"
                  rows={3}
                  bg={cardBg}
                  borderColor={borderColorDefault}
                  _focus={{ borderColor: 'blue.500', boxShadow: '0 0 0 1px var(--chakra-colors-blue-500)' }}
                />
              </Box>
              <Button
                colorScheme="blue"
                onClick={handleRegenerateImage}
                isLoading={regeneratingImage}
                loadingText="Generating..."
                leftIcon={<FaSyncAlt />}
              >
                Regenerate Image
              </Button>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
      
      {/* Image Expand Modal - Full screen view */}
      <Modal isOpen={isImageExpandOpen} onClose={onImageExpandClose} size="6xl" isCentered>
        <ModalOverlay bg="blackAlpha.800" zIndex={10000} />
        <ModalContent bg="transparent" boxShadow="none" maxW="95vw" maxH="95vh" zIndex={10001}>
          <ModalCloseButton color="white" bg="blackAlpha.600" borderRadius="full" _hover={{ bg: 'blackAlpha.800' }} />
          <ModalBody p={0} display="flex" justifyContent="center" alignItems="center">
            {generatedImage && (
              <Image
                src={generatedImage.base64 
                  ? `data:${generatedImage.mimeType || 'image/png'};base64,${generatedImage.base64}`
                  : generatedImage.url}
                alt="Generated content image - expanded view"
                maxW="95vw"
                maxH="90vh"
                objectFit="contain"
                borderRadius="lg"
              />
            )}
          </ModalBody>
          <ModalFooter justifyContent="center" pt={2}>
            <HStack spacing={4}>
              <Badge colorScheme="blue" fontSize="sm" px={3} py={1}>
                {generatedImage?.style || 'Generated'} style
              </Badge>
              <Text fontSize="sm" color="white">
                Model: {generatedImage?.model || 'Unknown'}
              </Text>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
