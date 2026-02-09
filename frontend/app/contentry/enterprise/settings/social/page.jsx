'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Card,
  CardBody,
  CardHeader,
  useColorModeValue,
  useToast,
  Spinner,
  Badge,
  Icon,
  SimpleGrid,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Input,
  FormControl,
  FormLabel,
  FormHelperText,
  Divider,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Tooltip,
  Avatar,
  Flex,
  IconButton,
  Textarea,
  Select,
  Tag,
  TagLabel,
  TagCloseButton,
  Wrap,
  WrapItem,
  Progress,
  Link,
  Radio,
  RadioGroup,
  Stack,
  Center,
} from '@chakra-ui/react';
import {
  Twitter,
  Facebook,
  Instagram,
  Linkedin,
  Plus,
  Link as LinkIcon,
  Unlink,
  ExternalLink,
  Trash2,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  FileText,
  Upload,
  Brain,
  X,
  User,
  Building2,
  Globe,
  Sparkles,
  Eye,
} from 'lucide-react';
import { FaTiktok, FaPinterest, FaYoutube } from 'react-icons/fa';
import { SiThreads } from 'react-icons/si';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { TONE_OPTIONS } from '@/constants/toneOptions';
import { SUPPORTED_LANGUAGES } from '@/lib/i18n';
import { DeleteConfirmationModal } from '@/components/shared';
import PlatformSelector from '@/components/social/PlatformSelector';
import ConnectedSocialAccounts from '@/components/social/ConnectedSocialAccounts';
import { useWorkspace } from '@/context/WorkspaceContext';

// Get primary languages for content language dropdown
const CONTENT_LANGUAGES = [
  { code: '', name: 'Use Default (from Settings)', native: '— Default —' },
  ...['en', 'es', 'fr', 'de', 'no'].map(code => SUPPORTED_LANGUAGES[code]),
];

// Voice & Dialect options for AI generation
const VOICE_DIALECT_OPTIONS = [
  { value: '', label: '— Use Default —', description: 'No specific voice/dialect preference' },
  { value: 'en_us', label: 'English (US Native)', description: 'American English with US idioms and phrasing' },
  { value: 'en_uk', label: 'English (UK Native)', description: 'British English with UK spellings and expressions' },
  { value: 'en_au', label: 'English (Australian Native)', description: 'Australian English with local expressions' },
  { value: 'en_ca', label: 'English (Canadian Native)', description: 'Canadian English with Canadian conventions' },
  { value: 'es_es', label: 'Spanish (Spain)', description: 'Castilian Spanish from Spain' },
  { value: 'es_mx', label: 'Spanish (Mexican)', description: 'Mexican Spanish with local expressions' },
  { value: 'es_ar', label: 'Spanish (Argentine)', description: 'Argentine Spanish with regional nuances' },
  { value: 'pt_br', label: 'Portuguese (Brazil)', description: 'Brazilian Portuguese' },
  { value: 'pt_pt', label: 'Portuguese (Portugal)', description: 'European Portuguese' },
  { value: 'fr_fr', label: 'French (France)', description: 'Metropolitan French' },
  { value: 'fr_ca', label: 'French (Canadian)', description: 'Quebec French with Canadian expressions' },
  { value: 'de_de', label: 'German (Germany)', description: 'Standard German from Germany' },
  { value: 'de_at', label: 'German (Austrian)', description: 'Austrian German with regional variations' },
  { value: 'no_nb', label: 'Norwegian (Bokmål)', description: 'Written Norwegian standard' },
  { value: 'no_nn', label: 'Norwegian (Nynorsk)', description: 'New Norwegian written standard' },
];

// Allowed file types for knowledge base
const ALLOWED_FILE_TYPES = '.pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.md,.csv';

export default function CompanyStrategicProfilesPage() {
  const { t } = useTranslation();
  const { user: authUser, isLoading: authLoading, isHydrated } = useAuth();
  const { enterpriseInfo, isEnterpriseWorkspace } = useWorkspace();
  const router = useRouter();
  const toast = useToast();
  const fileInputRef = useRef(null);
  
  // Local user state (from localStorage for immediate access check)
  const [localUser, setLocalUser] = useState(null);
  
  // Use localUser as primary, fallback to authUser from context
  const user = localUser || authUser;
  
  // Strategic profiles state
  const [strategicProfiles, setStrategicProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // In-place editing state
  const [editedProfiles, setEditedProfiles] = useState({});
  const [keywordInputs, setKeywordInputs] = useState({});
  const [savingProfiles, setSavingProfiles] = useState({});
  const [scrapingProfiles, setScrapingProfiles] = useState({});
  
  // Create profile modal
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const [newProfile, setNewProfile] = useState({
    name: '',
    writing_tone: 'professional',
    seo_keywords: [],
    description: '',
    language: '',
    default_platforms: [],
  });
  const [keywordInput, setKeywordInput] = useState('');
  const [creating, setCreating] = useState(false);
  
  // AI Keyword Suggestion state
  const [suggestingKeywords, setSuggestingKeywords] = useState({});
  
  // Delete confirmation modal
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const [profileToDelete, setProfileToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  
  // Knowledge Sources modal
  const { isOpen: isSourcesOpen, onOpen: onSourcesOpen, onClose: onSourcesClose } = useDisclosure();
  const [sourcesProfileId, setSourcesProfileId] = useState(null);
  const [knowledgeSources, setKnowledgeSources] = useState([]);
  const [loadingSources, setLoadingSources] = useState(false);
  const [deletingSource, setDeletingSource] = useState(null);
  
  // View Content modal
  const { isOpen: isViewContentOpen, onOpen: onViewContentOpen, onClose: onViewContentClose } = useDisclosure();
  const [viewingContent, setViewingContent] = useState(null);
  const [loadingContent, setLoadingContent] = useState(false);
  
  // AI Description generation state
  const [generatingDescription, setGeneratingDescription] = useState({});
  
  // Upload state
  const [uploadingToProfile, setUploadingToProfile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Maximum reference websites per profile
  const MAX_REFERENCE_WEBSITES = 3;
  
  // Colors
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const defaultProfileBg = useColorModeValue('purple.50', 'purple.900');
  const defaultProfileBorder = useColorModeValue('purple.200', 'purple.700');
  const knowledgeBg = useColorModeValue('purple.50', 'purple.900');

  // Check authorization - use localStorage directly like Company Profile page
  useEffect(() => {
    const storedUser = localStorage.getItem('contentry_user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      setLocalUser(userData);
      
      // Check if user is enterprise admin (accept both 'admin' and 'enterprise_admin' roles)
      const isEnterpriseAdmin = userData.enterprise_role === 'enterprise_admin' || 
                                 userData.enterprise_role === 'admin' ||
                                 userData.is_enterprise_admin === true;
      
      if (!isEnterpriseAdmin || !userData.enterprise_id) {
        toast({
          title: 'Access Denied',
          description: 'Only enterprise administrators can manage company strategic profiles.',
          status: 'error',
          duration: 5000,
        });
        router.push('/contentry/dashboard');
        return;
      }
    } else {
      router.push('/contentry/auth/login');
    }
  }, [router, toast]);

  // Load company strategic profiles
  const loadStrategicProfiles = useCallback(async () => {
    if (!user?.enterprise_id) return;
    
    try {
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles`,
        { headers: { 'X-User-ID': user.id } }
      );
      setStrategicProfiles(response.data.profiles || []);
    } catch (error) {
      console.error('Error loading company strategic profiles:', error);
      // Don't show error for 404 - just means no profiles yet
      if (error.response?.status !== 404) {
        toast({
          title: 'Error loading profiles',
          description: error.response?.data?.detail || error.message,
          status: 'error',
          duration: 5000,
        });
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user, toast]);

  useEffect(() => {
    if (user?.enterprise_id) {
      loadStrategicProfiles();
    }
  }, [localUser, user, loadStrategicProfiles]);

  // Create new strategic profile
  const handleCreateProfile = async () => {
    if (!newProfile.name.trim()) {
      toast({
        title: 'Profile name required',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setCreating(true);
    try {
      const API = getApiUrl();
      await axios.post(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles`,
        {
          ...newProfile,
          language: newProfile.language || null,
          default_platforms: newProfile.default_platforms || [],
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'Profile created',
        description: `"${newProfile.name}" has been added to company profiles.`,
        status: 'success',
        duration: 3000,
      });
      
      onCreateClose();
      setNewProfile({ name: '', writing_tone: 'professional', seo_keywords: [], description: '', language: '', default_platforms: [] });
      setKeywordInput('');
      loadStrategicProfiles();
    } catch (error) {
      toast({
        title: 'Failed to create profile',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setCreating(false);
    }
  };

  // Update/Save strategic profile
  const handleSaveProfile = async (profileId) => {
    const editedData = editedProfiles[profileId];
    if (!editedData) return;
    
    setSavingProfiles(prev => ({ ...prev, [profileId]: true }));
    try {
      const API = getApiUrl();
      const originalProfile = strategicProfiles.find(p => p.id === profileId);
      const mergedData = { ...originalProfile, ...editedData };
      
      await axios.put(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileId}`,
        {
          name: mergedData.name,
          writing_tone: mergedData.writing_tone,
          seo_keywords: mergedData.seo_keywords,
          description: mergedData.description,
          language: mergedData.language || null,
          voice_dialect: mergedData.voice_dialect || null,
          target_audience: mergedData.target_audience || null,
          reference_websites: mergedData.reference_websites || [],
          primary_region: mergedData.primary_region || null,
          default_platforms: mergedData.default_platforms || [],
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'Profile updated',
        status: 'success',
        duration: 3000,
      });
      
      setEditedProfiles(prev => {
        const newState = { ...prev };
        delete newState[profileId];
        return newState;
      });
      setKeywordInputs(prev => {
        const newState = { ...prev };
        delete newState[profileId];
        return newState;
      });
      
      loadStrategicProfiles();
    } catch (error) {
      toast({
        title: 'Failed to update profile',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSavingProfiles(prev => ({ ...prev, [profileId]: false }));
    }
  };

  // Cancel changes
  const handleCancelChanges = (profileId) => {
    setEditedProfiles(prev => {
      const newState = { ...prev };
      delete newState[profileId];
      return newState;
    });
    setKeywordInputs(prev => {
      const newState = { ...prev };
      delete newState[profileId];
      return newState;
    });
  };

  // Update a field for a profile
  const updateProfileField = (profileId, field, value) => {
    setEditedProfiles(prev => ({
      ...prev,
      [profileId]: {
        ...(prev[profileId] || {}),
        [field]: value,
      }
    }));
  };

  // Get the current value of a field
  const getFieldValue = (profile, field) => {
    const edited = editedProfiles[profile.id];
    if (edited && field in edited) {
      return edited[field];
    }
    return profile[field];
  };

  // Check if a profile has unsaved changes
  const hasUnsavedChanges = (profileId) => {
    return editedProfiles[profileId] && Object.keys(editedProfiles[profileId]).length > 0;
  };

  // Add keyword to a profile
  const addKeyword = (profileId) => {
    const input = keywordInputs[profileId]?.trim().toLowerCase();
    if (!input) return;
    
    const profile = strategicProfiles.find(p => p.id === profileId);
    const currentKeywords = getFieldValue(profile, 'seo_keywords') || [];
    
    if (!currentKeywords.includes(input)) {
      updateProfileField(profileId, 'seo_keywords', [...currentKeywords, input]);
    }
    
    setKeywordInputs(prev => ({ ...prev, [profileId]: '' }));
  };

  // Remove keyword from a profile
  const removeKeyword = (profileId, keyword) => {
    const profile = strategicProfiles.find(p => p.id === profileId);
    const currentKeywords = getFieldValue(profile, 'seo_keywords') || [];
    updateProfileField(profileId, 'seo_keywords', currentKeywords.filter(k => k !== keyword));
  };

  // AI Keyword suggestion for a profile
  const suggestKeywordsForProfile = async (profileId) => {
    const profile = strategicProfiles.find(p => p.id === profileId);
    const description = getFieldValue(profile, 'description');
    
    if (!description?.trim()) {
      toast({
        title: 'Description required',
        description: 'Please add a description first to generate keyword suggestions.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setSuggestingKeywords(prev => ({ ...prev, [profileId]: true }));
    try {
      const API = getApiUrl();
      const response = await axios.post(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileId}/suggest-keywords`,
        { max_keywords: 10 },
        { headers: { 'X-User-ID': user.id } }
      );
      
      const suggestedKeywords = response.data.keywords || [];
      const currentKeywords = getFieldValue(profile, 'seo_keywords') || [];
      const newKeywords = suggestedKeywords.filter(k => !currentKeywords.includes(k));
      
      if (newKeywords.length > 0) {
        updateProfileField(profileId, 'seo_keywords', [...currentKeywords, ...newKeywords]);
        toast({
          title: `Added ${newKeywords.length} AI-suggested keywords`,
          status: 'success',
          duration: 3000,
        });
      } else {
        toast({
          title: 'No new keywords to add',
          description: 'All suggested keywords already exist.',
          status: 'info',
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: 'Suggestion failed',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSuggestingKeywords(prev => ({ ...prev, [profileId]: false }));
    }
  };

  // Add a new website to a profile
  const addWebsiteToProfile = (profileId) => {
    const profile = strategicProfiles.find(p => p.id === profileId);
    const currentWebsites = getFieldValue(profile, 'reference_websites') || [];
    
    if (currentWebsites.length >= MAX_REFERENCE_WEBSITES) {
      toast({
        title: `Maximum ${MAX_REFERENCE_WEBSITES} websites allowed`,
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    const newWebsite = {
      id: `temp_${Date.now()}`,
      url: '',
      content: null,
      scraped_at: null,
    };
    
    updateProfileField(profileId, 'reference_websites', [...currentWebsites, newWebsite]);
  };

  // Remove a website from a profile
  const removeWebsiteFromProfile = async (profileId, websiteId) => {
    const profile = strategicProfiles.find(p => p.id === profileId);
    const currentWebsites = getFieldValue(profile, 'reference_websites') || [];
    
    if (!websiteId.startsWith('temp_')) {
      try {
        const API = getApiUrl();
        await axios.delete(
          `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileId}/website/${websiteId}`,
          { headers: { 'X-User-ID': user.id } }
        );
      } catch (error) {
        console.error('Error deleting website:', error);
      }
    }
    
    updateProfileField(profileId, 'reference_websites', currentWebsites.filter(w => w.id !== websiteId));
  };

  // Update a website URL in a profile
  const updateWebsiteUrl = (profileId, websiteId, newUrl) => {
    const profile = strategicProfiles.find(p => p.id === profileId);
    const currentWebsites = getFieldValue(profile, 'reference_websites') || [];
    
    const updatedWebsites = currentWebsites.map(w => 
      w.id === websiteId ? { ...w, url: newUrl } : w
    );
    
    updateProfileField(profileId, 'reference_websites', updatedWebsites);
  };

  // Scrape a specific website for a profile
  const scrapeWebsiteForProfile = async (profileId, websiteId) => {
    const profile = strategicProfiles.find(p => p.id === profileId);
    const websites = getFieldValue(profile, 'reference_websites') || [];
    const website = websites.find(w => w.id === websiteId);
    
    if (!website?.url?.trim()) return;
    
    setScrapingProfiles(prev => ({ ...prev, [`${profileId}_${websiteId}`]: true }));
    try {
      const API = getApiUrl();
      const response = await axios.post(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileId}/scrape-website`,
        { 
          url: website.url,
          website_id: websiteId.startsWith('temp_') ? null : websiteId
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      if (response.data.success) {
        toast({
          title: 'Website scraped successfully',
          description: `Extracted ${response.data.content_length} characters.`,
          status: 'success',
          duration: 4000,
        });
        
        loadStrategicProfiles();
      } else {
        toast({
          title: 'Scraping failed',
          description: response.data.error || 'Unable to scrape the website.',
          status: 'error',
          duration: 5000,
        });
      }
    } catch (error) {
      toast({
        title: 'Error scraping website',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setScrapingProfiles(prev => ({ ...prev, [`${profileId}_${websiteId}`]: false }));
    }
  };

  // View website content
  const viewWebsiteContent = async (profileId, websiteId) => {
    setLoadingContent(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileId}/website/${websiteId}/content`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      setViewingContent({
        type: 'website',
        data: response.data
      });
      onViewContentOpen();
    } catch (error) {
      toast({
        title: 'Error loading content',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoadingContent(false);
    }
  };

  // View document content
  const viewDocumentContent = async (documentId) => {
    if (!sourcesProfileId) return;
    
    setLoadingContent(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${sourcesProfileId}/knowledge/${documentId}/content`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      setViewingContent({
        type: 'document',
        data: response.data
      });
      onViewContentOpen();
    } catch (error) {
      toast({
        title: 'Error loading document content',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoadingContent(false);
    }
  };

  // Generate AI description for a profile
  const generateAIDescription = async (profileId) => {
    setGeneratingDescription(prev => ({ ...prev, [profileId]: true }));
    try {
      const API = getApiUrl();
      const response = await axios.post(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileId}/generate-description`,
        {},
        { headers: { 'X-User-ID': user.id } }
      );
      
      if (response.data.success && response.data.description) {
        updateProfileField(profileId, 'description', response.data.description);
        toast({
          title: 'Description generated',
          description: 'AI has created a description based on your profile content.',
          status: 'success',
          duration: 3000,
        });
      } else {
        toast({
          title: 'Generation failed',
          description: response.data.error || 'Unable to generate description.',
          status: 'error',
          duration: 5000,
        });
      }
    } catch (error) {
      toast({
        title: 'Error generating description',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setGeneratingDescription(prev => ({ ...prev, [profileId]: false }));
    }
  };

  // Delete profile
  const openDeleteModal = (profile) => {
    if (profile.is_default) {
      toast({
        title: 'Cannot delete default profile',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    setProfileToDelete(profile);
    onDeleteOpen();
  };

  const handleDeleteProfile = async () => {
    if (!profileToDelete) return;
    
    setDeleting(true);
    try {
      const API = getApiUrl();
      await axios.delete(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileToDelete.id}`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'Profile deleted',
        status: 'success',
        duration: 3000,
      });
      
      loadStrategicProfiles();
      onDeleteClose();
    } catch (error) {
      toast({
        title: 'Failed to delete profile',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setDeleting(false);
      setProfileToDelete(null);
    }
  };

  // Upload knowledge base document
  const handleFileUpload = async (event, profileId) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    setUploadingToProfile(profileId);
    setUploadProgress(10);
    
    try {
      const API = getApiUrl();
      const formData = new FormData();
      formData.append('file', file);
      
      setUploadProgress(30);
      
      const response = await axios.post(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileId}/knowledge`,
        formData,
        {
          headers: {
            'X-User-ID': user.id,
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 70) / progressEvent.total) + 30;
            setUploadProgress(Math.min(percentCompleted, 95));
          },
        }
      );
      
      setUploadProgress(100);
      
      if (response.data.success) {
        toast({
          title: 'Document uploaded',
          description: `"${file.name}" has been processed and added to the knowledge base.`,
          status: 'success',
          duration: 4000,
        });
      } else {
        throw new Error(response.data.error || 'Upload failed');
      }
      
      loadStrategicProfiles();
    } catch (error) {
      toast({
        title: 'Upload failed',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setUploadingToProfile(null);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Add keyword to new profile (creation modal)
  const addNewProfileKeyword = () => {
    const keyword = keywordInput.trim();
    if (keyword && !newProfile.seo_keywords.includes(keyword)) {
      setNewProfile(prev => ({
        ...prev,
        seo_keywords: [...prev.seo_keywords, keyword]
      }));
      setKeywordInput('');
    }
  };

  // Remove keyword from new profile
  const removeNewProfileKeyword = (keyword) => {
    setNewProfile(prev => ({
      ...prev,
      seo_keywords: prev.seo_keywords.filter(k => k !== keyword)
    }));
  };

  // Load knowledge sources for a profile
  const loadKnowledgeSources = async (profileId) => {
    setLoadingSources(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${profileId}/knowledge`,
        { headers: { 'X-User-ID': user.id } }
      );
      setKnowledgeSources(response.data.documents || []);
    } catch (error) {
      console.error('Error loading knowledge sources:', error);
      toast({
        title: 'Error loading sources',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoadingSources(false);
    }
  };

  // Open knowledge sources modal
  const openSourcesModal = (profileId) => {
    setSourcesProfileId(profileId);
    loadKnowledgeSources(profileId);
    onSourcesOpen();
  };

  // Delete a knowledge source document
  const deleteKnowledgeSource = async (documentId) => {
    if (!sourcesProfileId) return;
    
    setDeletingSource(documentId);
    try {
      const API = getApiUrl();
      await axios.delete(
        `${API}/enterprises/${user.enterprise_id}/strategic-profiles/${sourcesProfileId}/knowledge/${documentId}`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'Document deleted',
        description: 'The document and its knowledge have been removed.',
        status: 'success',
        duration: 3000,
      });
      
      loadKnowledgeSources(sourcesProfileId);
      loadStrategicProfiles();
    } catch (error) {
      toast({
        title: 'Error deleting document',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setDeletingSource(null);
    }
  };

  if (!isHydrated || authLoading) {
    return (
      <Box minH="100vh" display="flex" alignItems="center" justifyContent="center">
        <Spinner size="xl" />
      </Box>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <Box minH="100vh" bg={bgColor} p={{ base: 4, md: 8 }}>
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        {/* Header */}
        <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
          <Box>
            <HStack spacing={2}>
              <Icon as={Building2} boxSize={6} color="purple.500" />
              <Heading size="lg" color={textColor}>Company Strategic Profiles</Heading>
            </HStack>
            <Text color={textColorSecondary} mt={1}>
              Create brand profiles with knowledge bases for AI-powered content generation
            </Text>
          </Box>
          <HStack spacing={3}>
            <Button
              leftIcon={<RefreshCw size={18} />}
              variant="outline"
              onClick={() => { setRefreshing(true); loadStrategicProfiles(); }}
              isLoading={refreshing}
              size="sm"
            >
              Refresh
            </Button>
            <Button
              leftIcon={<Plus />}
              colorScheme="purple"
              onClick={onCreateOpen}
            >
              Add Profile
            </Button>
          </HStack>
        </Flex>

        {/* Info Alert */}
        <Alert status="info" borderRadius="lg">
          <AlertIcon as={Brain} />
          <Box>
            <AlertTitle>Strategic Profiles are your Company Brand Brains</AlertTitle>
            <AlertDescription>
              Each profile contains unique knowledge, writing style, and SEO keywords. Upload documents to build a knowledge base that guides AI content generation for your company.
            </AlertDescription>
          </Box>
        </Alert>

        {/* Connected Social Accounts Section */}
        <ConnectedSocialAccounts 
          workspaceType="company" 
          enterpriseId={enterpriseInfo?.id || user?.enterprise_id || 'techcorp-international'}
        />

        {/* Loading State */}
        {loading ? (
          <Center py={10}>
            <VStack spacing={4}>
              <Spinner size="xl" color="purple.500" />
              <Text color={textColorSecondary}>Loading company strategic profiles...</Text>
            </VStack>
          </Center>
        ) : strategicProfiles.length === 0 ? (
          <Card bg={cardBg}>
            <CardBody>
              <Center py={10}>
                <VStack spacing={4}>
                  <Icon as={Building2} boxSize={12} color="gray.400" />
                  <Heading size="md" color={textColor}>No Company Strategic Profiles Yet</Heading>
                  <Text color={textColorSecondary} textAlign="center" maxW="md">
                    Create strategic profiles to enable AI-powered content generation with your company's unique brand voice and knowledge.
                  </Text>
                  <Button
                    leftIcon={<Plus size={18} />}
                    colorScheme="purple"
                    onClick={onCreateOpen}
                  >
                    Create First Profile
                  </Button>
                </VStack>
              </Center>
            </CardBody>
          </Card>
        ) : (
          /* Profiles Grid */
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            {strategicProfiles.map((profile) => (
              <Card 
                key={profile.id} 
                bg={profile.is_default ? defaultProfileBg : cardBg} 
                borderColor={hasUnsavedChanges(profile.id) ? 'orange.400' : (profile.is_default ? defaultProfileBorder : borderColor)} 
                borderWidth={hasUnsavedChanges(profile.id) ? '3px' : '2px'}
                transition="border-color 0.2s"
              >
                <CardHeader pb={2}>
                  <Flex justify="space-between" align="start">
                    <HStack spacing={3} align="start">
                      <Avatar
                        size="md"
                        name={profile.name}
                        bg={profile.is_default ? 'purple.500' : 'purple.500'}
                        color="white"
                        icon={<Building2 />}
                      />
                      <Box flex={1}>
                        <HStack>
                          <Heading size="md" color={textColor}>{profile.name}</Heading>
                          {profile.is_default && (
                            <Badge colorScheme="purple" fontSize="xs">Default</Badge>
                          )}
                          {hasUnsavedChanges(profile.id) && (
                            <Badge colorScheme="orange" fontSize="xs">Unsaved</Badge>
                          )}
                        </HStack>
                      </Box>
                    </HStack>
                    
                    {!profile.is_default && (
                      <Tooltip label="Delete profile">
                        <IconButton
                          icon={<Trash2 />}
                          variant="ghost"
                          size="sm"
                          colorScheme="red"
                          onClick={() => openDeleteModal(profile)}
                          aria-label="Delete profile"
                        />
                      </Tooltip>
                    )}
                  </Flex>
                </CardHeader>
                
                <CardBody pt={0}>
                  <VStack spacing={4} align="stretch">
                    {/* Description */}
                    <FormControl>
                      <FormLabel fontSize="sm" color={textColorSecondary}>
                        <HStack justify="space-between" w="full">
                          <Text>Description</Text>
                          <Tooltip label="Generate description using AI based on profile content">
                            <Button
                              size="xs"
                              leftIcon={generatingDescription[profile.id] ? <Spinner size="xs" /> : <Sparkles />}
                              colorScheme="purple"
                              variant="ghost"
                              onClick={() => generateAIDescription(profile.id)}
                              isLoading={generatingDescription[profile.id]}
                            >
                              Generate
                            </Button>
                          </Tooltip>
                        </HStack>
                      </FormLabel>
                      <Textarea
                        size="sm"
                        value={getFieldValue(profile, 'description') || ''}
                        onChange={(e) => updateProfileField(profile.id, 'description', e.target.value)}
                        placeholder="Describe this profile's purpose and brand voice..."
                        rows={2}
                        bg={cardBg}
                      />
                    </FormControl>
                    
                    {/* Two Column Layout for Dropdowns */}
                    <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                      {/* Writing Tone */}
                      <FormControl>
                        <FormLabel fontSize="sm" color={textColorSecondary}>Writing Tone</FormLabel>
                        <Select
                          size="sm"
                          value={getFieldValue(profile, 'writing_tone') || 'professional'}
                          onChange={(e) => updateProfileField(profile.id, 'writing_tone', e.target.value)}
                          bg={cardBg}
                        >
                          {TONE_OPTIONS.map(tone => (
                            <option key={tone.value} value={tone.value}>
                              {tone.label}
                            </option>
                          ))}
                        </Select>
                      </FormControl>
                      
                      {/* Content Language */}
                      <FormControl>
                        <FormLabel fontSize="sm" color={textColorSecondary}>
                          <HStack spacing={1}>
                            <Icon as={Globe} boxSize={3} color="purple.500" />
                            <Text>Content Language</Text>
                          </HStack>
                        </FormLabel>
                        <Select
                          size="sm"
                          value={getFieldValue(profile, 'language') || ''}
                          onChange={(e) => updateProfileField(profile.id, 'language', e.target.value)}
                          bg={cardBg}
                        >
                          {CONTENT_LANGUAGES.map(lang => (
                            <option key={lang.code} value={lang.code}>
                              {lang.flag ? `${lang.flag} ${lang.native}` : lang.native}
                            </option>
                          ))}
                        </Select>
                      </FormControl>
                      
                      {/* Voice & Dialect */}
                      <FormControl>
                        <FormLabel fontSize="sm" color={textColorSecondary}>
                          <HStack spacing={1}>
                            <Text>🗣️</Text>
                            <Text>Voice & Dialect</Text>
                          </HStack>
                        </FormLabel>
                        <Select
                          size="sm"
                          value={getFieldValue(profile, 'voice_dialect') || ''}
                          onChange={(e) => updateProfileField(profile.id, 'voice_dialect', e.target.value)}
                          bg={cardBg}
                        >
                          {VOICE_DIALECT_OPTIONS.map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Select>
                      </FormControl>
                      
                      {/* Target Audience */}
                      <FormControl>
                        <FormLabel fontSize="sm" color={textColorSecondary}>Target Audience</FormLabel>
                        <Input
                          size="sm"
                          value={getFieldValue(profile, 'target_audience') || ''}
                          onChange={(e) => updateProfileField(profile.id, 'target_audience', e.target.value)}
                          placeholder="e.g., B2B professionals, tech enthusiasts"
                          bg={cardBg}
                        />
                      </FormControl>
                    </SimpleGrid>
                    
                    {/* SEO Keywords */}
                    <FormControl>
                      <FormLabel fontSize="sm" color={textColorSecondary}>SEO Keywords</FormLabel>
                      <HStack>
                        <Input
                          size="sm"
                          placeholder="Add keyword..."
                          value={keywordInputs[profile.id] || ''}
                          onChange={(e) => setKeywordInputs(prev => ({ ...prev, [profile.id]: e.target.value }))}
                          onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword(profile.id))}
                          bg={cardBg}
                        />
                        <Button size="sm" onClick={() => addKeyword(profile.id)}>Add</Button>
                        <Tooltip label="AI Suggest Keywords">
                          <IconButton
                            size="sm"
                            icon={suggestingKeywords[profile.id] ? <Spinner size="xs" /> : <Brain />}
                            colorScheme="purple"
                            variant="outline"
                            onClick={() => suggestKeywordsForProfile(profile.id)}
                            isLoading={suggestingKeywords[profile.id]}
                            isDisabled={!getFieldValue(profile, 'description')?.trim()}
                            aria-label="AI suggest keywords"
                          />
                        </Tooltip>
                      </HStack>
                      {(getFieldValue(profile, 'seo_keywords') || []).length > 0 && (
                        <Wrap mt={2}>
                          {(getFieldValue(profile, 'seo_keywords') || []).map((keyword, i) => (
                            <WrapItem key={i}>
                              <Tag size="sm" colorScheme="purple">
                                <TagLabel>{keyword}</TagLabel>
                                <TagCloseButton onClick={() => removeKeyword(profile.id, keyword)} />
                              </Tag>
                            </WrapItem>
                          ))}
                        </Wrap>
                      )}
                    </FormControl>
                    
                    {/* Reference Websites */}
                    <FormControl>
                      <FormLabel fontSize="sm" color={textColorSecondary}>
                        <HStack spacing={1} justify="space-between" w="full">
                          <HStack>
                            <Icon as={Globe} boxSize={3} color="purple.500" />
                            <Text>Reference Websites</Text>
                          </HStack>
                          <Badge colorScheme="gray" fontSize="xs">
                            {(getFieldValue(profile, 'reference_websites') || []).length}/{MAX_REFERENCE_WEBSITES}
                          </Badge>
                        </HStack>
                      </FormLabel>
                      <VStack spacing={2} align="stretch">
                        {(getFieldValue(profile, 'reference_websites') || []).map((website) => (
                          <HStack key={website.id} spacing={2}>
                            <Input
                              size="sm"
                              value={website.url || ''}
                              onChange={(e) => updateWebsiteUrl(profile.id, website.id, e.target.value)}
                              placeholder="https://yourcompany.com"
                              bg={cardBg}
                              flex={1}
                            />
                            {website.scraped_at ? (
                              <>
                                <Tooltip label={`Scraped: ${new Date(website.scraped_at).toLocaleString()}`}>
                                  <Button
                                    size="sm"
                                    leftIcon={scrapingProfiles[`${profile.id}_${website.id}`] ? <Spinner size="xs" /> : <RefreshCw />}
                                    onClick={() => scrapeWebsiteForProfile(profile.id, website.id)}
                                    isLoading={scrapingProfiles[`${profile.id}_${website.id}`]}
                                    colorScheme="purple"
                                    variant="outline"
                                  >
                                    Refresh
                                  </Button>
                                </Tooltip>
                                <Tooltip label="View scraped content">
                                  <IconButton
                                    size="sm"
                                    icon={<Eye />}
                                    onClick={() => viewWebsiteContent(profile.id, website.id)}
                                    aria-label="View content"
                                    colorScheme="purple"
                                    variant="ghost"
                                  />
                                </Tooltip>
                              </>
                            ) : (
                              <Button
                                size="sm"
                                leftIcon={scrapingProfiles[`${profile.id}_${website.id}`] ? <Spinner size="xs" /> : <RefreshCw />}
                                onClick={() => scrapeWebsiteForProfile(profile.id, website.id)}
                                isLoading={scrapingProfiles[`${profile.id}_${website.id}`]}
                                isDisabled={!website.url?.trim()}
                                colorScheme="purple"
                              >
                                Scrape
                              </Button>
                            )}
                            <IconButton
                              size="sm"
                              icon={<Trash2 />}
                              onClick={() => removeWebsiteFromProfile(profile.id, website.id)}
                              aria-label="Remove website"
                              colorScheme="red"
                              variant="ghost"
                            />
                          </HStack>
                        ))}
                        {(getFieldValue(profile, 'reference_websites') || []).length < MAX_REFERENCE_WEBSITES && (
                          <Button
                            size="sm"
                            leftIcon={<Plus />}
                            variant="outline"
                            onClick={() => addWebsiteToProfile(profile.id)}
                          >
                            Add Website
                          </Button>
                        )}
                      </VStack>
                      <FormHelperText fontSize="xs">
                        Add up to {MAX_REFERENCE_WEBSITES} websites for AI to learn your company's brand voice
                      </FormHelperText>
                    </FormControl>
                    
                    {/* Default Target Platforms */}
                    <FormControl>
                      <FormLabel fontSize="sm">
                        <HStack spacing={1}>
                          <Icon as={Globe} boxSize={3} color="purple.500" />
                          <Text>Default Target Platforms</Text>
                        </HStack>
                      </FormLabel>
                      <PlatformSelector
                        selectedPlatforms={getFieldValue(profile, 'default_platforms') || []}
                        onChange={(platforms) => updateProfileField(profile.id, 'default_platforms', platforms)}
                        showAllPlatforms={true}
                        showConnectLink={false}
                        showCharLimits={true}
                        compact={true}
                      />
                      <FormHelperText fontSize="xs">
                        Auto-selected when you use this profile for content creation
                      </FormHelperText>
                    </FormControl>
                    
                    <Divider />
                    
                    {/* Knowledge Base Section */}
                    <Box bg={knowledgeBg} p={3} borderRadius="md">
                      <HStack justify="space-between" mb={2}>
                        <HStack>
                          <Icon as={FileText} color="purple.500" />
                          <Text fontWeight="600" fontSize="sm" color={textColor}>Knowledge Base</Text>
                        </HStack>
                        <HStack spacing={2}>
                          <Badge colorScheme={profile.knowledge_stats?.has_knowledge ? 'purple' : 'gray'}>
                            {profile.knowledge_stats?.document_count || 0} docs | {profile.knowledge_stats?.chunk_count || 0} chunks
                          </Badge>
                          {profile.knowledge_stats?.document_count > 0 && (
                            <Button
                              size="xs"
                              variant="ghost"
                              colorScheme="purple"
                              onClick={() => openSourcesModal(profile.id)}
                            >
                              Manage
                            </Button>
                          )}
                        </HStack>
                      </HStack>
                      
                      {uploadingToProfile === profile.id ? (
                        <Box>
                          <Text fontSize="xs" color={textColorSecondary} mb={1}>Uploading...</Text>
                          <Progress value={uploadProgress} size="sm" colorScheme="purple" borderRadius="full" />
                        </Box>
                      ) : (
                        <Box>
                          <input
                            type="file"
                            accept={ALLOWED_FILE_TYPES}
                            onChange={(e) => handleFileUpload(e, profile.id)}
                            style={{ display: 'none' }}
                            id={`file-upload-${profile.id}`}
                          />
                          <Button
                            as="label"
                            htmlFor={`file-upload-${profile.id}`}
                            size="sm"
                            leftIcon={<Upload />}
                            colorScheme="purple"
                            variant="outline"
                            cursor="pointer"
                            w="full"
                          >
                            Upload Document
                          </Button>
                          <Text fontSize="xs" color={textColorSecondary} mt={1} textAlign="center">
                            PDF, DOCX, TXT, CSV supported
                          </Text>
                        </Box>
                      )}
                    </Box>
                    
                    {/* Save/Cancel Buttons */}
                    {hasUnsavedChanges(profile.id) && (
                      <HStack justify="flex-end" pt={2} borderTop="1px solid" borderColor={borderColor}>
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          onClick={() => handleCancelChanges(profile.id)}
                        >
                          Cancel
                        </Button>
                        <Button 
                          size="sm" 
                          colorScheme="purple" 
                          onClick={() => handleSaveProfile(profile.id)}
                          isLoading={savingProfiles[profile.id]}
                          leftIcon={<CheckCircle />}
                        >
                          Save Changes
                        </Button>
                      </HStack>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        )}

        {/* Create Profile Modal */}
        <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="lg">
          <ModalOverlay />
          <ModalContent bg={cardBg}>
            <ModalHeader color={textColor}>Create Company Strategic Profile</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Profile Name</FormLabel>
                  <Input
                    placeholder="e.g., Marketing Content, Technical Documentation"
                    value={newProfile.name}
                    onChange={(e) => setNewProfile(prev => ({ ...prev, name: e.target.value }))}
                  />
                </FormControl>
                
                <FormControl>
                  <FormLabel>Writing Tone</FormLabel>
                  <Select
                    value={newProfile.writing_tone}
                    onChange={(e) => setNewProfile(prev => ({ ...prev, writing_tone: e.target.value }))}
                  >
                    {TONE_OPTIONS.map(tone => (
                      <option key={tone.value} value={tone.value}>{tone.label}</option>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    placeholder="Describe this profile's purpose and brand voice..."
                    value={newProfile.description}
                    onChange={(e) => setNewProfile(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                  />
                </FormControl>
                
                <FormControl>
                  <FormLabel>SEO Keywords</FormLabel>
                  <HStack>
                    <Input
                      placeholder="Add keyword..."
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addNewProfileKeyword())}
                    />
                    <Button onClick={addNewProfileKeyword} size="md">Add</Button>
                  </HStack>
                  {newProfile.seo_keywords.length > 0 && (
                    <Wrap mt={2}>
                      {newProfile.seo_keywords.map((keyword, i) => (
                        <WrapItem key={i}>
                          <Tag size="md" colorScheme="purple">
                            <TagLabel>{keyword}</TagLabel>
                            <TagCloseButton onClick={() => removeNewProfileKeyword(keyword)} />
                          </Tag>
                        </WrapItem>
                      ))}
                    </Wrap>
                  )}
                </FormControl>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onCreateClose}>
                Cancel
              </Button>
              <Button
                colorScheme="purple"
                onClick={handleCreateProfile}
                isLoading={creating}
                leftIcon={<Plus />}
              >
                Create Profile
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Delete Confirmation Modal */}
        <DeleteConfirmationModal
          isOpen={isDeleteOpen}
          onClose={() => { onDeleteClose(); setProfileToDelete(null); }}
          onConfirm={handleDeleteProfile}
          isLoading={deleting}
          title="Delete Strategic Profile"
          message={`Are you sure you want to delete "${profileToDelete?.name}"? This will also delete all associated knowledge base documents. This action cannot be undone.`}
        />

        {/* Knowledge Sources Modal */}
        <Modal isOpen={isSourcesOpen} onClose={onSourcesClose} size="lg">
          <ModalOverlay />
          <ModalContent bg={cardBg}>
            <ModalHeader color={textColor}>Knowledge Base Documents</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {loadingSources ? (
                <Center py={8}>
                  <Spinner size="lg" color="purple.500" />
                </Center>
              ) : knowledgeSources.length === 0 ? (
                <Center py={8}>
                  <VStack spacing={2}>
                    <Icon as={FileText} boxSize={8} color="gray.400" />
                    <Text color={textColorSecondary}>No documents uploaded yet</Text>
                  </VStack>
                </Center>
              ) : (
                <VStack spacing={3} align="stretch">
                  {knowledgeSources.map((doc) => (
                    <HStack
                      key={doc.id}
                      p={3}
                      bg={useColorModeValue('gray.50', 'gray.700')}
                      borderRadius="md"
                      justify="space-between"
                    >
                      <HStack spacing={3}>
                        <Icon as={FileText} color="purple.500" />
                        <Box>
                          <Text fontWeight="500" fontSize="sm">{doc.filename}</Text>
                          <Text fontSize="xs" color={textColorSecondary}>
                            {doc.chunk_count} chunks • Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}
                          </Text>
                        </Box>
                      </HStack>
                      <HStack spacing={2}>
                        <Tooltip label="View content">
                          <IconButton
                            size="sm"
                            icon={<Eye />}
                            variant="ghost"
                            onClick={() => viewDocumentContent(doc.id)}
                            aria-label="View content"
                          />
                        </Tooltip>
                        <Tooltip label="Delete document">
                          <IconButton
                            size="sm"
                            icon={deletingSource === doc.id ? <Spinner size="xs" /> : <Trash2 />}
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => deleteKnowledgeSource(doc.id)}
                            isLoading={deletingSource === doc.id}
                            aria-label="Delete document"
                          />
                        </Tooltip>
                      </HStack>
                    </HStack>
                  ))}
                </VStack>
              )}
            </ModalBody>
            <ModalFooter>
              <Button onClick={onSourcesClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* View Content Modal */}
        <Modal isOpen={isViewContentOpen} onClose={onViewContentClose} size="xl" scrollBehavior="inside">
          <ModalOverlay />
          <ModalContent bg={cardBg}>
            <ModalHeader color={textColor}>
              {viewingContent?.type === 'website' ? 'Website Content' : 'Document Content'}
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {loadingContent ? (
                <Center py={8}>
                  <Spinner size="lg" color="purple.500" />
                </Center>
              ) : viewingContent?.type === 'website' ? (
                <Box>
                  <Text fontWeight="600" mb={2}>URL: {viewingContent.data.url}</Text>
                  <Text fontSize="xs" color={textColorSecondary} mb={4}>
                    Scraped: {new Date(viewingContent.data.scraped_at).toLocaleString()}
                  </Text>
                  <Box
                    p={4}
                    bg={useColorModeValue('gray.50', 'gray.700')}
                    borderRadius="md"
                    maxH="400px"
                    overflowY="auto"
                    whiteSpace="pre-wrap"
                    fontSize="sm"
                  >
                    {viewingContent.data.content}
                  </Box>
                </Box>
              ) : viewingContent?.type === 'document' ? (
                <VStack spacing={4} align="stretch">
                  <Text fontWeight="600">Document Chunks ({viewingContent.data.chunks?.length || 0})</Text>
                  {viewingContent.data.chunks?.map((chunk, index) => (
                    <Box
                      key={index}
                      p={3}
                      bg={useColorModeValue('gray.50', 'gray.700')}
                      borderRadius="md"
                      fontSize="sm"
                    >
                      <Badge mb={2} colorScheme="purple">Chunk {index + 1}</Badge>
                      <Text whiteSpace="pre-wrap">{chunk.content}</Text>
                    </Box>
                  ))}
                </VStack>
              ) : null}
            </ModalBody>
            <ModalFooter>
              <Button onClick={onViewContentClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </VStack>
    </Box>
  );
}
