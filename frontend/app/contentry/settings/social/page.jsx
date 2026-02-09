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
} from '@chakra-ui/react';
// Updated to Lucide icons for modern outline style
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
// Keep social platform icons from react-icons (Lucide doesn't have TikTok, Pinterest, YouTube, Threads)
import { FaTiktok, FaPinterest, FaYoutube } from 'react-icons/fa';
import { SiThreads } from 'react-icons/si';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { TONE_OPTIONS } from '@/constants/toneOptions';
import { SUPPORTED_LANGUAGES } from '@/lib/i18n';
import { DeleteConfirmationModal } from '@/components/shared';
import PlatformSelector, { PLATFORM_CONFIG } from '@/components/social/PlatformSelector';
import ConnectedSocialAccounts from '@/components/social/ConnectedSocialAccounts';

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

// Target Countries for cultural analysis (51 Cultural Lenses)
const TARGET_COUNTRIES = [
  { value: 'Global', label: '🌍 Global', description: 'Safest for all markets worldwide' },
  { value: 'USA', label: '🇺🇸 United States', description: 'US market' },
  { value: 'United Kingdom', label: '🇬🇧 United Kingdom', description: 'UK market' },
  { value: 'Canada', label: '🇨🇦 Canada', description: 'Canadian market' },
  { value: 'Australia', label: '🇦🇺 Australia', description: 'Australian market' },
  { value: 'Germany', label: '🇩🇪 Germany', description: 'German market' },
  { value: 'France', label: '🇫🇷 France', description: 'French market' },
  { value: 'Spain', label: '🇪🇸 Spain', description: 'Spanish market' },
  { value: 'Italy', label: '🇮🇹 Italy', description: 'Italian market' },
  { value: 'Netherlands', label: '🇳🇱 Netherlands', description: 'Dutch market' },
  { value: 'Sweden', label: '🇸🇪 Sweden', description: 'Swedish market' },
  { value: 'Norway', label: '🇳🇴 Norway', description: 'Norwegian market' },
  { value: 'Switzerland', label: '🇨🇭 Switzerland', description: 'Swiss market' },
  { value: 'Japan', label: '🇯🇵 Japan', description: 'Japanese market' },
  { value: 'China', label: '🇨🇳 China', description: 'Chinese market' },
  { value: 'South Korea', label: '🇰🇷 South Korea', description: 'Korean market' },
  { value: 'India', label: '🇮🇳 India', description: 'Indian market' },
  { value: 'Brazil', label: '🇧🇷 Brazil', description: 'Brazilian market' },
  { value: 'Mexico', label: '🇲🇽 Mexico', description: 'Mexican market' },
  { value: 'Russia', label: '🇷🇺 Russia', description: 'Russian market' },
  { value: 'Saudi Arabia', label: '🇸🇦 Saudi Arabia', description: 'Saudi market' },
  { value: 'UAE', label: '🇦🇪 UAE', description: 'Emirates market' },
  { value: 'South Africa', label: '🇿🇦 South Africa', description: 'South African market' },
  { value: 'Nigeria', label: '🇳🇬 Nigeria', description: 'Nigerian market' },
  { value: 'Indonesia', label: '🇮🇩 Indonesia', description: 'Indonesian market' },
  { value: 'Turkey', label: '🇹🇷 Turkey', description: 'Turkish market' },
  { value: 'Israel', label: '🇮🇱 Israel', description: 'Israeli market' },
];

// Platform configuration
const PLATFORMS = {
  twitter: { name: 'Twitter/X', icon: Twitter, color: '#1DA1F2' },
  facebook: { name: 'Facebook', icon: Facebook, color: '#4267B2' },
  instagram: { name: 'Instagram', icon: Instagram, color: '#E4405F' },
  linkedin: { name: 'LinkedIn', icon: Linkedin, color: '#0A66C2' },
  tiktok: { name: 'TikTok', icon: FaTiktok, color: '#000000' },
  pinterest: { name: 'Pinterest', icon: FaPinterest, color: '#E60023' },
  youtube: { name: 'YouTube', icon: FaYoutube, color: '#FF0000' },
  threads: { name: 'Threads', icon: SiThreads, color: '#000000' },
};

// Allowed file types for knowledge base
const ALLOWED_FILE_TYPES = '.pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.md,.csv';

export default function StrategicProfilesPage() {
  const { t } = useTranslation();
  const { user, isLoading: authLoading, isHydrated } = useAuth();
  const toast = useToast();
  const fileInputRef = useRef(null);
  
  // Strategic profiles state
  const [strategicProfiles, setStrategicProfiles] = useState([]);
  const [socialProfiles, setSocialProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // In-place editing state - tracks modified versions of profiles
  const [editedProfiles, setEditedProfiles] = useState({}); // { profileId: { ...modifiedFields } }
  const [keywordInputs, setKeywordInputs] = useState({}); // { profileId: 'current input' }
  const [savingProfiles, setSavingProfiles] = useState({}); // { profileId: boolean }
  const [scrapingProfiles, setScrapingProfiles] = useState({}); // { profileId: boolean }
  
  // Profile Type Options
  const PROFILE_TYPES = [
    { value: 'personal', label: 'Personal', description: "For your own brand or voice" },
    { value: 'company', label: 'Company/Brand', description: "For corporate, product, or campaign content" }
  ];
  
  // Create profile modal
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const [newProfile, setNewProfile] = useState({
    name: '',
    profile_type: 'personal',
    writing_tone: 'professional',
    seo_keywords: [],
    description: '',
    language: '',  // Empty string means "Use Default"
    default_platforms: [],  // Platform-Aware Content Engine
    target_countries: ['Global'],  // Default to Global for safest analysis
  });
  const [keywordInput, setKeywordInput] = useState('');
  const [creating, setCreating] = useState(false);
  
  // AI Keyword Suggestion state (per profile)
  const [suggestingKeywords, setSuggestingKeywords] = useState({});
  
  // Link social modal
  const { isOpen: isLinkOpen, onOpen: onLinkOpen, onClose: onLinkClose } = useDisclosure();
  const [linkingProfile, setLinkingProfile] = useState(null);
  
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
  
  // View Content modals
  const { isOpen: isViewContentOpen, onOpen: onViewContentOpen, onClose: onViewContentClose } = useDisclosure();
  const [viewingContent, setViewingContent] = useState(null); // { type: 'website'|'document', data: {...} }
  const [loadingContent, setLoadingContent] = useState(false);
  
  // AI Description generation state (per profile)
  const [generatingDescription, setGeneratingDescription] = useState({});
  
  // Upload state
  const [uploadingToProfile, setUploadingToProfile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Maximum reference websites per profile
  const MAX_REFERENCE_WEBSITES = 3;
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const defaultProfileBg = useColorModeValue('blue.50', 'blue.900');
  const defaultProfileBorder = useColorModeValue('blue.200', 'blue.700');
  const knowledgeBg = useColorModeValue('blue.50', 'blue.900');
  const sourcesItemBg = useColorModeValue('gray.50', 'gray.700');
  
  // Load strategic profiles
  const loadStrategicProfiles = useCallback(async () => {
    if (!user?.id) return;
    
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/profiles/strategic`, {
        headers: { 'X-User-ID': user.id }
      });
      setStrategicProfiles(response.data.profiles || []);
    } catch (error) {
      console.error('Error loading strategic profiles:', error);
      toast({
        title: t('strategicProfiles.toasts.errorLoadingProfiles'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  }, [user?.id, toast, t]);
  
  // Load social profiles (Ayrshare)
  const loadSocialProfiles = useCallback(async () => {
    if (!user?.id) return;
    
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/social/profiles`, {
        headers: { 'X-User-ID': user.id }
      });
      setSocialProfiles(response.data.profiles || []);
    } catch (error) {
      console.error('Error loading social profiles:', error);
    }
  }, [user?.id]);
  
  // Load all data
  const loadAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([loadStrategicProfiles(), loadSocialProfiles()]);
    setLoading(false);
  }, [loadStrategicProfiles, loadSocialProfiles]);
  
  useEffect(() => {
    if (user?.id) {
      loadAll();
    }
  }, [user?.id, loadAll]);
  
  // Create new strategic profile
  const handleCreateProfile = async () => {
    if (!newProfile.name.trim()) {
      toast({
        title: t('strategicProfiles.toasts.profileNameRequired'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setCreating(true);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/profiles/strategic`, {
        ...newProfile,
        language: newProfile.language || null,  // Send null if empty to use default
        default_platforms: newProfile.default_platforms || [],  // Platform-Aware Content Engine
      }, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: t('strategicProfiles.toasts.profileCreated'),
        description: `"${newProfile.name}" ${t('strategicProfiles.toasts.profileCreatedDesc')}`,
        status: 'success',
        duration: 3000,
      });
      
      onCreateClose();
      setNewProfile({ name: '', profile_type: 'personal', writing_tone: 'professional', seo_keywords: [], description: '', language: '', default_platforms: [] });
      setKeywordInput('');
      loadStrategicProfiles();
    } catch (error) {
      toast({
        title: t('strategicProfiles.toasts.failedToCreate'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setCreating(false);
    }
  };
  
  // Update/Save strategic profile (in-place editing)
  const handleSaveProfile = async (profileId) => {
    const editedData = editedProfiles[profileId];
    if (!editedData) return;
    
    setSavingProfiles(prev => ({ ...prev, [profileId]: true }));
    try {
      const API = getApiUrl();
      const originalProfile = strategicProfiles.find(p => p.id === profileId);
      const mergedData = { ...originalProfile, ...editedData };
      
      await axios.put(`${API}/profiles/strategic/${profileId}`, {
        name: mergedData.name,
        profile_type: mergedData.profile_type,
        writing_tone: mergedData.writing_tone,
        seo_keywords: mergedData.seo_keywords,
        description: mergedData.description,
        linked_social_profile_id: mergedData.linked_social_profile_id,
        language: mergedData.language || null,
        voice_dialect: mergedData.voice_dialect || null,
        target_audience: mergedData.target_audience || null,
        reference_websites: mergedData.reference_websites || [],  // New array format
        primary_region: mergedData.primary_region || null,
        default_platforms: mergedData.default_platforms || [],  // Platform-Aware Content Engine
      }, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: t('strategicProfiles.toasts.profileUpdated'),
        status: 'success',
        duration: 3000,
      });
      
      // Clear edited state for this profile
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
        title: t('strategicProfiles.toasts.failedToUpdate'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSavingProfiles(prev => ({ ...prev, [profileId]: false }));
    }
  };
  
  // Cancel changes for a specific profile
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
  
  // Update a field for a specific profile (in-place editing)
  const updateProfileField = (profileId, field, value) => {
    setEditedProfiles(prev => ({
      ...prev,
      [profileId]: {
        ...(prev[profileId] || {}),
        [field]: value,
      }
    }));
  };
  
  // Get the current value of a field (edited or original)
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
        `${API}/profiles/strategic/${profileId}/suggest-keywords`,
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
      id: `temp_${Date.now()}`, // Temporary ID until saved
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
    
    // If this is a saved website (not temp), delete from backend
    if (!websiteId.startsWith('temp_')) {
      try {
        const API = getApiUrl();
        await axios.delete(
          `${API}/profiles/strategic/${profileId}/website/${websiteId}`,
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
        `${API}/profiles/strategic/${profileId}/scrape-website`,
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
        `${API}/profiles/strategic/${profileId}/website/${websiteId}/content`,
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
  
  // View document content (chunks)
  const viewDocumentContent = async (documentId) => {
    if (!sourcesProfileId) return;
    
    setLoadingContent(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/profiles/strategic/${sourcesProfileId}/knowledge/${documentId}/content`,
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
        `${API}/profiles/strategic/${profileId}/generate-description`,
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
  
  // Open delete confirmation modal
  const openDeleteModal = (profile) => {
    if (profile.is_default) {
      toast({
        title: t('strategicProfiles.toasts.cannotDeleteDefault'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    setProfileToDelete(profile);
    onDeleteOpen();
  };
  
  // Delete strategic profile
  const handleDeleteProfile = async () => {
    if (!profileToDelete) return;
    
    setDeleting(true);
    try {
      const API = getApiUrl();
      await axios.delete(`${API}/profiles/strategic/${profileToDelete.id}`, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: t('strategicProfiles.toasts.profileDeleted'),
        status: 'success',
        duration: 3000,
      });
      
      loadStrategicProfiles();
      onDeleteClose();
    } catch (error) {
      toast({
        title: t('strategicProfiles.toasts.failedToDelete'),
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
        `${API}/profiles/strategic/${profileId}/knowledge`,
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
          title: t('strategicProfiles.toasts.documentUploaded'),
          description: `"${file.name}" ${t('strategicProfiles.toasts.documentUploadedDesc')}`,
          status: 'success',
          duration: 4000,
        });
      } else {
        throw new Error(response.data.error || 'Upload failed');
      }
      
      loadStrategicProfiles();
    } catch (error) {
      toast({
        title: t('strategicProfiles.toasts.uploadFailed'),
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
  
  // Remove keyword from new profile (creation modal)
  const removeNewProfileKeyword = (keyword) => {
    setNewProfile(prev => ({
      ...prev,
      seo_keywords: prev.seo_keywords.filter(k => k !== keyword)
    }));
  };
  
  // AI-powered SEO keyword suggestions for NEW profiles (from description only)
  const [suggestingNewKeywords, setSuggestingNewKeywords] = useState(false);
  
  const suggestKeywordsForNewProfile = async () => {
    if (!newProfile.description?.trim()) {
      toast({
        title: 'Description required',
        description: 'Please add a description before generating keywords.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setSuggestingNewKeywords(true);
    
    try {
      const API = getApiUrl();
      const response = await axios.post(
        `${API}/profiles/strategic/suggest-keywords-from-description`,
        {
          profile_name: newProfile.name || 'New Profile',
          description: newProfile.description,
          max_keywords: 15
        },
        {
          headers: { 'X-User-ID': user.id }
        }
      );
      
      const suggestedKeywords = response.data.keywords || [];
      const contextUsed = response.data.context_used || {};
      
      if (suggestedKeywords.length === 0) {
        toast({
          title: 'No keywords generated',
          description: 'Please add more detail to your description.',
          status: 'warning',
          duration: 5000,
        });
        return;
      }
      
      // Merge with existing keywords
      const existingKeywords = newProfile.seo_keywords || [];
      const newKeywords = suggestedKeywords.filter(
        kw => !existingKeywords.map(k => k.toLowerCase()).includes(kw.toLowerCase())
      );
      
      setNewProfile(prev => ({
        ...prev,
        seo_keywords: [...existingKeywords, ...newKeywords]
      }));
      
      // Build context description for toast
      const contextParts = [];
      if (contextUsed.profile_description) contextParts.push('description');
      if (contextUsed.user_profile) contextParts.push('your profile');
      if (contextUsed.company) contextParts.push('company');
      const contextDesc = contextParts.length > 0 ? ` Based on: ${contextParts.join(', ')}` : '';
      
      toast({
        title: t('strategicProfiles.toasts.keywordsSuggested'),
        description: `${t('strategicProfiles.toasts.addedKeywords')}${contextDesc}`,
        status: 'success',
        duration: 4000,
      });
      
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      toast({
        title: t('strategicProfiles.toasts.suggestionFailed'),
        description: errorMsg,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSuggestingNewKeywords(false);
    }
  };
  
  // Load knowledge sources for a profile
  const loadKnowledgeSources = async (profileId) => {
    setLoadingSources(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/profiles/strategic/${profileId}/knowledge`, {
        headers: { 'X-User-ID': user.id }
      });
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
      await axios.delete(`${API}/profiles/strategic/${sourcesProfileId}/knowledge/${documentId}`, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: 'Document deleted',
        description: 'The document and its knowledge have been removed.',
        status: 'success',
        duration: 3000,
      });
      
      // Reload sources
      loadKnowledgeSources(sourcesProfileId);
      loadStrategicProfiles(); // Refresh profile stats
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
  
  // Link social profile
  const handleLinkSocialProfile = async (strategicProfileId, socialProfileId) => {
    try {
      const API = getApiUrl();
      await axios.put(`${API}/profiles/strategic/${strategicProfileId}`, {
        linked_social_profile_id: socialProfileId || null
      }, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: socialProfileId ? t('strategicProfiles.toasts.socialLinked') : t('strategicProfiles.toasts.socialUnlinked'),
        status: 'success',
        duration: 3000,
      });
      
      onLinkClose();
      loadStrategicProfiles();
    } catch (error) {
      toast({
        title: t('strategicProfiles.toasts.linkFailed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };
  
  // Get linked social profile name
  const getLinkedSocialProfileName = (linkedId) => {
    if (!linkedId) return null;
    const socialProfile = socialProfiles.find(p => p.id === linkedId);
    return socialProfile?.title || 'Unknown Profile';
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
              <Icon as={Brain} boxSize={6} color="brand.500" />
              <Heading size="lg" color={textColor}>{t('strategicProfiles.pageTitle')}</Heading>
            </HStack>
            <Text color={textColorSecondary} mt={1}>
              {t('strategicProfiles.pageDescription')}
            </Text>
          </Box>
          <Button
            leftIcon={<Plus />}
            colorScheme="brand"
            onClick={onCreateOpen}
          >
            {t('strategicProfiles.addProfile')}
          </Button>
        </Flex>

        {/* Info Alert */}
        <Alert status="info" borderRadius="lg">
          <AlertIcon as={Brain} />
          <Box>
            <AlertTitle>{t('strategicProfiles.alertTitle')}</AlertTitle>
            <AlertDescription>
              {t('strategicProfiles.alertDescription')}
            </AlertDescription>
          </Box>
        </Alert>

        {/* Connected Social Accounts Section */}
        <ConnectedSocialAccounts 
          workspaceType="personal" 
        />

        {/* Loading State */}
        {loading ? (
          <Box textAlign="center" py={10}>
            <Spinner size="xl" />
            <Text mt={4} color={textColorSecondary}>{t('strategicProfiles.loading')}</Text>
          </Box>
        ) : (
          /* Profiles Grid - In-Place Editing */
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
                        bg={profile.is_default ? 'blue.500' : 'brand.500'}
                        color="white"
                        icon={<Brain />}
                      />
                      <Box flex={1}>
                        <HStack>
                          <Heading size="md" color={textColor}>{profile.name}</Heading>
                          {profile.is_default && (
                            <Badge colorScheme="blue" fontSize="xs">{t('strategicProfiles.default')}</Badge>
                          )}
                          {hasUnsavedChanges(profile.id) && (
                            <Badge colorScheme="orange" fontSize="xs">Unsaved</Badge>
                          )}
                        </HStack>
                      </Box>
                    </HStack>
                    
                    {/* Delete button - only for non-default profiles */}
                    <HStack spacing={2}>
                      {/* Link Social Account Button */}
                      <Tooltip label={t('strategicProfiles.linkSocialAccounts')}>
                        <IconButton
                          icon={<LinkIcon />}
                          variant="ghost"
                          size="sm"
                          onClick={() => { setLinkingProfile(profile); onLinkOpen(); }}
                          aria-label="Link social account"
                        />
                      </Tooltip>
                      
                      {!profile.is_default && (
                        <Tooltip label={t('strategicProfiles.deleteProfile')}>
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
                    </HStack>
                  </Flex>
                </CardHeader>
                
                <CardBody pt={0}>
                  <VStack spacing={4} align="stretch">
                    {/* Description - Always Editable with AI Generate */}
                    <FormControl>
                      <FormLabel fontSize="sm" color={textColorSecondary}>
                        <HStack justify="space-between" w="full">
                          <Text>{t('strategicProfiles.description')}</Text>
                          <Tooltip label="Generate description using AI based on profile content">
                            <Button
                              size="xs"
                              leftIcon={generatingDescription[profile.id] ? <Spinner size="xs" /> : <Sparkles />}
                              colorScheme="blue"
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
                        placeholder={t('strategicProfiles.descriptionPlaceholder')}
                        rows={2}
                        bg={cardBg}
                      />
                    </FormControl>
                    
                    {/* Two Column Layout for Dropdowns - Responsive */}
                    <SimpleGrid columns={{ base: 1, sm: 1, md: 2 }} gap={3} w="full">
                      {/* Profile Type */}
                      <FormControl minW={0}>
                        <FormLabel fontSize="sm" color={textColorSecondary}>{t('strategicProfiles.profileType')}</FormLabel>
                        <HStack spacing={2} flexWrap="wrap">
                          <Button
                            size="sm"
                            variant={getFieldValue(profile, 'profile_type') !== 'company' ? 'solid' : 'outline'}
                            colorScheme="brand"
                            leftIcon={<User size={14} />}
                            onClick={() => updateProfileField(profile.id, 'profile_type', 'personal')}
                            minW="auto"
                            whiteSpace="nowrap"
                            flex={{ base: 1, md: 'none' }}
                          >
                            {t('strategicProfiles.personal')}
                          </Button>
                          <Button
                            size="sm"
                            variant={getFieldValue(profile, 'profile_type') === 'company' ? 'solid' : 'outline'}
                            colorScheme="green"
                            leftIcon={<Building2 size={14} />}
                            onClick={() => updateProfileField(profile.id, 'profile_type', 'company')}
                            minW="auto"
                            whiteSpace="nowrap"
                            flex={{ base: 1, md: 'none' }}
                          >
                            {t('strategicProfiles.company')}
                          </Button>
                        </HStack>
                      </FormControl>
                      
                      {/* Writing Tone */}
                      <FormControl minW={0}>
                        <FormLabel fontSize="sm" color={textColorSecondary}>{t('strategicProfiles.writingTone')}</FormLabel>
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
                      <FormControl minW={0}>
                        <FormLabel fontSize="sm" color={textColorSecondary}>
                          <HStack spacing={1}>
                            <Icon as={Globe} boxSize={3} color="blue.500" />
                            <Text>{t('strategicProfiles.contentLanguage')}</Text>
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
                      
                      {/* Target Countries - Multi-select for cultural analysis */}
                      <FormControl minW={0}>
                        <FormLabel fontSize="sm" color={textColorSecondary}>
                          <HStack spacing={1}>
                            <Text>🎯</Text>
                            <Text>Target Countries</Text>
                          </HStack>
                        </FormLabel>
                        <Select
                          size="sm"
                          value=""
                          onChange={(e) => {
                            const value = e.target.value;
                            if (!value) return;
                            const currentTargets = getFieldValue(profile, 'target_countries') || ['Global'];
                            // If selecting Global, clear other selections
                            if (value === 'Global') {
                              updateProfileField(profile.id, 'target_countries', ['Global']);
                            } else {
                              // If Global was selected, remove it when adding specific country
                              const filtered = currentTargets.filter(c => c !== 'Global');
                              if (!filtered.includes(value)) {
                                updateProfileField(profile.id, 'target_countries', [...filtered, value]);
                              }
                            }
                          }}
                          bg={cardBg}
                          placeholder="Add target country..."
                        >
                          {TARGET_COUNTRIES.map(country => (
                            <option key={country.value} value={country.value}>
                              {country.label}
                            </option>
                          ))}
                        </Select>
                        {/* Display selected countries as tags */}
                        {(getFieldValue(profile, 'target_countries') || ['Global']).length > 0 && (
                          <Wrap mt={2} spacing={1}>
                            {(getFieldValue(profile, 'target_countries') || ['Global']).map((country) => (
                              <WrapItem key={country}>
                                <Tag size="sm" colorScheme={country === 'Global' ? 'purple' : 'blue'} borderRadius="full">
                                  <TagLabel fontSize="xs">{TARGET_COUNTRIES.find(c => c.value === country)?.label || country}</TagLabel>
                                  <TagCloseButton 
                                    onClick={() => {
                                      const currentTargets = getFieldValue(profile, 'target_countries') || ['Global'];
                                      const filtered = currentTargets.filter(c => c !== country);
                                      // If removing last country, default to Global
                                      updateProfileField(profile.id, 'target_countries', filtered.length > 0 ? filtered : ['Global']);
                                    }}
                                  />
                                </Tag>
                              </WrapItem>
                            ))}
                          </Wrap>
                        )}
                      </FormControl>
                      
                      {/* Voice & Dialect */}
                      <FormControl minW={0}>
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
                    </SimpleGrid>
                    
                    {/* SEO Keywords */}
                    <FormControl>
                      <FormLabel fontSize="sm" color={textColorSecondary}>{t('strategicProfiles.seoKeywords')}</FormLabel>
                      <HStack>
                        <Input
                          size="sm"
                          placeholder={t('strategicProfiles.addKeyword')}
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
                            colorScheme="blue"
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
                              <Tag size="sm" colorScheme="green">
                                <TagLabel>{keyword}</TagLabel>
                                <TagCloseButton onClick={() => removeKeyword(profile.id, keyword)} />
                              </Tag>
                            </WrapItem>
                          ))}
                        </Wrap>
                      )}
                    </FormControl>
                    
                    {/* Reference Websites (Multiple) */}
                    <FormControl>
                      <FormLabel fontSize="sm" color={textColorSecondary}>
                        <HStack spacing={1} justify="space-between" w="full">
                          <HStack>
                            <Icon as={Globe} boxSize={3} color="green.500" />
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
                              placeholder="https://yourbrand.com"
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
                                    colorScheme="green"
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
                                    colorScheme="blue"
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
                                colorScheme="blue"
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
                        Add up to {MAX_REFERENCE_WEBSITES} websites for AI to learn your brand voice
                      </FormHelperText>
                    </FormControl>
                    
                    {/* Platform-Aware Content Engine: Default Platforms */}
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
                    
                    {/* Linked Social Account */}
                    <Box>
                      <Text fontSize="sm" fontWeight="500" color={textColorSecondary} mb={2}>{t('strategicProfiles.linkedSocialAccount')}:</Text>
                      {profile.linked_social_profile_id ? (
                        <HStack>
                          <Icon as={CheckCircle} color="green.500" />
                          <Text fontSize="sm">{getLinkedSocialProfileName(profile.linked_social_profile_id)}</Text>
                          <Button 
                            size="xs" 
                            variant="ghost" 
                            colorScheme="red"
                            leftIcon={<Unlink />}
                            onClick={() => handleLinkSocialProfile(profile.id, null)}
                          >
                            Unlink
                          </Button>
                        </HStack>
                      ) : (
                        <Button 
                          size="sm" 
                          leftIcon={<LinkIcon />} 
                          variant="outline" 
                          colorScheme="blue"
                          onClick={() => { setLinkingProfile(profile); onLinkOpen(); }}
                        >
                          {t('strategicProfiles.linkAccount')}
                        </Button>
                      )}
                    </Box>
                    
                    <Divider />
                    
                    {/* Knowledge Base Section - Unchanged */}
                    <Box bg={knowledgeBg} p={3} borderRadius="md">
                      <HStack justify="space-between" mb={2}>
                        <HStack>
                          <Icon as={FileText} color="blue.500" />
                          <Text fontWeight="600" fontSize="sm" color={textColor}>{t('strategicProfiles.knowledgeBase')}</Text>
                        </HStack>
                        <HStack spacing={2}>
                          <Badge colorScheme={profile.knowledge_stats?.has_knowledge ? 'green' : 'gray'}>
                            {profile.knowledge_stats?.document_count || 0} {t('strategicProfiles.documents')} | {profile.knowledge_stats?.chunk_count || 0} chunks
                          </Badge>
                          {profile.knowledge_stats?.document_count > 0 && (
                            <Button
                              size="xs"
                              variant="ghost"
                              colorScheme="blue"
                              onClick={() => openSourcesModal(profile.id)}
                            >
                              Manage
                            </Button>
                          )}
                        </HStack>
                      </HStack>
                      
                      {uploadingToProfile === profile.id ? (
                        <Box>
                          <Text fontSize="xs" color={textColorSecondary} mb={1}>{t('strategicProfiles.uploading')}</Text>
                          <Progress value={uploadProgress} size="sm" colorScheme="blue" borderRadius="full" />
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
                            colorScheme="blue"
                            variant="outline"
                            cursor="pointer"
                            w="full"
                          >
                            {t('strategicProfiles.uploadDocument')}
                          </Button>
                          <Text fontSize="xs" color={textColorSecondary} mt={1} textAlign="center">
                            {t('strategicProfiles.supportedFormats')}
                          </Text>
                        </Box>
                      )}
                    </Box>
                    
                    {/* Save/Cancel Buttons - Only show when there are unsaved changes */}
                    {hasUnsavedChanges(profile.id) && (
                      <HStack justify="flex-end" pt={2} borderTop="1px solid" borderColor={borderColor}>
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          onClick={() => handleCancelChanges(profile.id)}
                        >
                          {t('strategicProfiles.cancel')}
                        </Button>
                        <Button 
                          size="sm" 
                          colorScheme="brand" 
                          onClick={() => handleSaveProfile(profile.id)}
                          isLoading={savingProfiles[profile.id]}
                          leftIcon={<CheckCircle />}
                        >
                          {t('strategicProfiles.saveChanges')}
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
            <ModalHeader color={textColor}>{t('strategicProfiles.createNewProfile')}</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>{t('strategicProfiles.profileName')}</FormLabel>
                  <Input
                    placeholder={t('strategicProfiles.profileNamePlaceholder')}
                    value={newProfile.name}
                    onChange={(e) => setNewProfile(prev => ({ ...prev, name: e.target.value }))}
                  />
                </FormControl>
                
                <FormControl isRequired>
                  <FormLabel>{t('strategicProfiles.profileType')}</FormLabel>
                  <RadioGroup 
                    value={newProfile.profile_type} 
                    onChange={(value) => setNewProfile(prev => ({ ...prev, profile_type: value }))}
                  >
                    <Stack direction="row" spacing={6}>
                      <Box 
                        p={3} 
                        borderRadius="md" 
                        border="2px solid" 
                        borderColor={newProfile.profile_type === 'personal' ? 'brand.500' : 'gray.200'}
                        bg={newProfile.profile_type === 'personal' ? 'brand.50' : 'transparent'}
                        cursor="pointer"
                        onClick={() => setNewProfile(prev => ({ ...prev, profile_type: 'personal' }))}
                        transition="all 0.2s"
                      >
                        <Radio value="personal" colorScheme="brand">
                          <HStack spacing={2}>
                            <Icon as={User} color="brand.500" />
                            <Box>
                              <Text fontWeight="600">{t('strategicProfiles.personal')}</Text>
                              <Text fontSize="xs" color="gray.500">{t('strategicProfiles.personalDesc')}</Text>
                            </Box>
                          </HStack>
                        </Radio>
                      </Box>
                      <Box 
                        p={3} 
                        borderRadius="md" 
                        border="2px solid" 
                        borderColor={newProfile.profile_type === 'company' ? 'green.500' : 'gray.200'}
                        bg={newProfile.profile_type === 'company' ? 'green.50' : 'transparent'}
                        cursor="pointer"
                        onClick={() => setNewProfile(prev => ({ ...prev, profile_type: 'company' }))}
                        transition="all 0.2s"
                      >
                        <Radio value="company" colorScheme="green">
                          <HStack spacing={2}>
                            <Icon as={Building2} color="green.500" />
                            <Box>
                              <Text fontWeight="600">{t('strategicProfiles.company')}</Text>
                              <Text fontSize="xs" color="gray.500">{t('strategicProfiles.companyDesc')}</Text>
                            </Box>
                          </HStack>
                        </Radio>
                      </Box>
                    </Stack>
                  </RadioGroup>
                </FormControl>
                
                <FormControl>
                  <FormLabel>{t('strategicProfiles.writingTone')}</FormLabel>
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
                  <FormLabel>{t('strategicProfiles.seoKeywords')}</FormLabel>
                  <HStack>
                    <Input
                      placeholder={t('strategicProfiles.addKeyword')}
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addNewProfileKeyword())}
                    />
                    <Button onClick={addNewProfileKeyword} size="md">{t('strategicProfiles.addKeyword')}</Button>
                  </HStack>
                  {newProfile.seo_keywords.length > 0 && (
                    <>
                      <Wrap mt={2}>
                        {newProfile.seo_keywords.map((keyword, i) => (
                          <WrapItem key={i}>
                            <Tag size="md" colorScheme="green">
                              <TagLabel>{keyword}</TagLabel>
                              <TagCloseButton onClick={() => removeNewProfileKeyword(keyword)} />
                            </Tag>
                          </WrapItem>
                        ))}
                      </Wrap>
                      <Button
                        mt={2}
                        size="xs"
                        variant="ghost"
                        colorScheme="red"
                        onClick={() => setNewProfile(prev => ({ ...prev, seo_keywords: [] }))}
                      >
                        Clear All
                      </Button>
                    </>
                  )}
                  <HStack mt={3} spacing={2}>
                    <Button
                      size="sm"
                      variant="outline"
                      colorScheme="blue"
                      leftIcon={suggestingNewKeywords ? <Spinner size="xs" /> : <Brain />}
                      onClick={suggestKeywordsForNewProfile}
                      isLoading={suggestingNewKeywords}
                      loadingText="..."
                      isDisabled={!newProfile.description?.trim()}
                    >
                      ✨ {t('strategicProfiles.suggestKeywordsAI')}
                    </Button>
                    {!newProfile.description?.trim() && (
                      <Text fontSize="xs" color="orange.500">
                        {t('strategicProfiles.description')} first
                      </Text>
                    )}
                  </HStack>
                  <FormHelperText>
                    {t('strategicProfiles.seoKeywordsHelper')}
                  </FormHelperText>
                </FormControl>
                
                <FormControl>
                  <FormLabel>{t('strategicProfiles.description')}</FormLabel>
                  <Textarea
                    placeholder={t('strategicProfiles.descriptionPlaceholder')}
                    value={newProfile.description}
                    onChange={(e) => setNewProfile(prev => ({ ...prev, description: e.target.value }))}
                    rows={4}
                  />
                </FormControl>
                
                <FormControl>
                  <FormLabel>
                    <HStack spacing={1}>
                      <Icon as={Globe} boxSize={3} color="blue.500" />
                      <Text>{t('strategicProfiles.contentLanguage')}</Text>
                    </HStack>
                  </FormLabel>
                  <Select
                    value={newProfile.language || ''}
                    onChange={(e) => setNewProfile(prev => ({ ...prev, language: e.target.value }))}
                  >
                    {CONTENT_LANGUAGES.map(lang => (
                      <option key={lang.code} value={lang.code}>
                        {lang.flag ? `${lang.flag} ${lang.native}` : lang.native}
                      </option>
                    ))}
                  </Select>
                  <FormHelperText>
                    {t('strategicProfiles.contentLanguageHelper')}
                  </FormHelperText>
                </FormControl>
                
                {/* Target Countries for Cultural Analysis */}
                <FormControl>
                  <FormLabel>
                    <HStack spacing={1}>
                      <Text>🎯</Text>
                      <Text>Target Countries</Text>
                    </HStack>
                  </FormLabel>
                  <Select
                    value=""
                    onChange={(e) => {
                      const value = e.target.value;
                      if (!value) return;
                      const currentTargets = newProfile.target_countries || ['Global'];
                      // If selecting Global, clear other selections
                      if (value === 'Global') {
                        setNewProfile(prev => ({ ...prev, target_countries: ['Global'] }));
                      } else {
                        // If Global was selected, remove it when adding specific country
                        const filtered = currentTargets.filter(c => c !== 'Global');
                        if (!filtered.includes(value)) {
                          setNewProfile(prev => ({ ...prev, target_countries: [...filtered, value] }));
                        }
                      }
                    }}
                    placeholder="Add target country..."
                  >
                    {TARGET_COUNTRIES.map(country => (
                      <option key={country.value} value={country.value}>
                        {country.label}
                      </option>
                    ))}
                  </Select>
                  {/* Display selected countries as tags */}
                  {(newProfile.target_countries || ['Global']).length > 0 && (
                    <Wrap mt={2} spacing={1}>
                      {(newProfile.target_countries || ['Global']).map((country) => (
                        <WrapItem key={country}>
                          <Tag size="sm" colorScheme={country === 'Global' ? 'purple' : 'blue'} borderRadius="full">
                            <TagLabel fontSize="xs">{TARGET_COUNTRIES.find(c => c.value === country)?.label || country}</TagLabel>
                            <TagCloseButton 
                              onClick={() => {
                                const currentTargets = newProfile.target_countries || ['Global'];
                                const filtered = currentTargets.filter(c => c !== country);
                                // If removing last country, default to Global
                                setNewProfile(prev => ({ ...prev, target_countries: filtered.length > 0 ? filtered : ['Global'] }));
                              }}
                            />
                          </Tag>
                        </WrapItem>
                      ))}
                    </Wrap>
                  )}
                  <FormHelperText>
                    Select target markets for culturally-aware content. "Global" uses strictest cultural rules.
                  </FormHelperText>
                </FormControl>
                
                {/* Platform-Aware Content Engine: Default Platforms */}
                <FormControl>
                  <FormLabel>
                    <HStack spacing={1}>
                      <Icon as={Globe} boxSize={3} color="purple.500" />
                      <Text>Default Target Platforms</Text>
                    </HStack>
                  </FormLabel>
                  <Text fontSize="xs" color={textColorSecondary} mb={2}>
                    Pre-select platforms when using this profile. Content will be optimized for these platforms.
                  </Text>
                  <PlatformSelector
                    selectedPlatforms={newProfile.default_platforms || []}
                    onChange={(platforms) => setNewProfile(prev => ({ ...prev, default_platforms: platforms }))}
                    showAllPlatforms={true}
                    showConnectLink={false}
                    showCharLimits={true}
                    compact={true}
                  />
                  <FormHelperText>
                    When you select this profile, these platforms will be auto-selected in the Platform Selector.
                  </FormHelperText>
                </FormControl>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onCreateClose}>{t('strategicProfiles.cancel')}</Button>
              <Button colorScheme="brand" onClick={handleCreateProfile} isLoading={creating}>
                {t('strategicProfiles.create')}
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Link Social Account Modal */}
        <Modal isOpen={isLinkOpen} onClose={onLinkClose} size="md">
          <ModalOverlay />
          <ModalContent bg={cardBg}>
            <ModalHeader color={textColor}>{t('strategicProfiles.linkSocialAccountTitle')}</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {linkingProfile && (
                <VStack spacing={4} align="stretch">
                  <Text color={textColorSecondary}>
                    {t('strategicProfiles.selectSocialAccount')} <strong>{linkingProfile.name}</strong>.
                  </Text>
                  
                  {socialProfiles.length === 0 ? (
                    <Alert status="warning" borderRadius="md">
                      <AlertIcon />
                      <Box>
                        <Text fontWeight="500">{t('strategicProfiles.noSocialAccounts')}</Text>
                        <Text fontSize="sm">{t('strategicProfiles.settings')}</Text>
                      </Box>
                    </Alert>
                  ) : (
                    <VStack spacing={2} align="stretch">
                      {/* Option to unlink */}
                      <Button
                        variant={!linkingProfile.linked_social_profile_id ? 'solid' : 'outline'}
                        colorScheme="gray"
                        justifyContent="flex-start"
                        onClick={() => handleLinkSocialProfile(linkingProfile.id, null)}
                      >
                        <HStack>
                          <Icon as={Unlink} />
                          <Text>{t('strategicProfiles.unlinkAccount')}</Text>
                        </HStack>
                      </Button>
                      
                      {socialProfiles.map(sp => (
                        <Button
                          key={sp.id}
                          variant={linkingProfile.linked_social_profile_id === sp.id ? 'solid' : 'outline'}
                          colorScheme="brand"
                          justifyContent="flex-start"
                          onClick={() => handleLinkSocialProfile(linkingProfile.id, sp.id)}
                        >
                          <HStack>
                            <Avatar size="xs" name={sp.title} />
                            <Text>{sp.title}</Text>
                            {linkingProfile.linked_social_profile_id === sp.id && (
                              <Icon as={CheckCircle} color="green.400" />
                            )}
                          </HStack>
                        </Button>
                      ))}
                    </VStack>
                  )}
                </VStack>
              )}
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" onClick={onLinkClose}>{t('strategicProfiles.cancel')}</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Delete Profile Confirmation Modal */}
        <DeleteConfirmationModal
          isOpen={isDeleteOpen}
          onClose={() => { onDeleteClose(); setProfileToDelete(null); }}
          onConfirm={handleDeleteProfile}
          itemName={profileToDelete?.name || t('strategicProfiles.thisProfile', 'this profile')}
          isLoading={deleting}
        />

        {/* Knowledge Sources Management Modal */}
        <Modal isOpen={isSourcesOpen} onClose={onSourcesClose} size="lg">
          <ModalOverlay />
          <ModalContent bg={cardBg}>
            <ModalHeader color={textColor}>
              <HStack>
                <Icon as={FileText} color="blue.500" />
                <Text>Manage Knowledge Sources</Text>
              </HStack>
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {loadingSources ? (
                <Box textAlign="center" py={8}>
                  <Spinner size="lg" />
                  <Text mt={2} color={textColorSecondary}>Loading documents...</Text>
                </Box>
              ) : knowledgeSources.length === 0 ? (
                <Box textAlign="center" py={8}>
                  <Icon as={FileText} boxSize={12} color="gray.400" mb={4} />
                  <Text color={textColorSecondary}>No documents uploaded yet.</Text>
                  <Text fontSize="sm" color={textColorSecondary} mt={2}>
                    Upload documents to build your knowledge base.
                  </Text>
                </Box>
              ) : (
                <VStack spacing={3} align="stretch">
                  <Text fontSize="sm" color={textColorSecondary} mb={2}>
                    {knowledgeSources.length} document{knowledgeSources.length !== 1 ? 's' : ''} in knowledge base
                  </Text>
                  {knowledgeSources.map((doc) => (
                    <HStack 
                      key={doc.id} 
                      p={3} 
                      bg={sourcesItemBg} 
                      borderRadius="md"
                      justify="space-between"
                    >
                      <HStack flex={1} minW={0}>
                        <Icon as={FileText} color="blue.500" />
                        <VStack align="start" spacing={0} flex={1} minW={0}>
                          <Text fontSize="sm" fontWeight="500" isTruncated maxW="100%">
                            {doc.filename}
                          </Text>
                          <Text fontSize="xs" color={textColorSecondary}>
                            {doc.chunk_count} chunks • Uploaded {new Date(doc.created_at).toLocaleDateString()}
                          </Text>
                        </VStack>
                      </HStack>
                      <HStack spacing={2}>
                        <Tooltip label="View extracted content">
                          <IconButton
                            icon={<Eye />}
                            size="sm"
                            colorScheme="blue"
                            variant="ghost"
                            onClick={() => viewDocumentContent(doc.id)}
                            aria-label="View content"
                          />
                        </Tooltip>
                        <IconButton
                          icon={deletingSource === doc.id ? <Spinner size="sm" /> : <Trash2 />}
                          size="sm"
                          colorScheme="red"
                          variant="ghost"
                          onClick={() => deleteKnowledgeSource(doc.id)}
                          isLoading={deletingSource === doc.id}
                          aria-label="Delete document"
                        />
                      </HStack>
                    </HStack>
                  ))}
                </VStack>
              )}
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" onClick={onSourcesClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* View Content Modal - For Website and Document content */}
        <Modal isOpen={isViewContentOpen} onClose={onViewContentClose} size="xl" scrollBehavior="inside">
          <ModalOverlay />
          <ModalContent bg={cardBg} maxH="80vh">
            <ModalHeader color={textColor}>
              <HStack>
                <Icon as={viewingContent?.type === 'website' ? Globe : FileText} color={viewingContent?.type === 'website' ? 'green.500' : 'blue.500'} />
                <VStack align="start" spacing={0}>
                  <Text>
                    {viewingContent?.type === 'website' ? 'Website Content' : 'Document Content'}
                  </Text>
                  <Text fontSize="sm" fontWeight="normal" color={textColorSecondary}>
                    {viewingContent?.type === 'website' 
                      ? viewingContent?.data?.url 
                      : viewingContent?.data?.filename}
                  </Text>
                </VStack>
              </HStack>
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {loadingContent ? (
                <Box textAlign="center" py={8}>
                  <Spinner size="lg" />
                  <Text mt={2} color={textColorSecondary}>Loading content...</Text>
                </Box>
              ) : viewingContent?.type === 'website' ? (
                /* Website Content View */
                <Box>
                  {viewingContent?.data?.scraped_at && (
                    <Text fontSize="xs" color={textColorSecondary} mb={4}>
                      Scraped: {new Date(viewingContent.data.scraped_at).toLocaleString()}
                    </Text>
                  )}
                  <Box 
                    bg={sourcesItemBg} 
                    p={4} 
                    borderRadius="md" 
                    maxH="50vh" 
                    overflowY="auto"
                    fontSize="sm"
                    whiteSpace="pre-wrap"
                    fontFamily="mono"
                  >
                    {viewingContent?.data?.content || 'No content available'}
                  </Box>
                </Box>
              ) : (
                /* Document Content View with Chunks */
                <Box>
                  <Text fontSize="sm" color={textColorSecondary} mb={4}>
                    {viewingContent?.data?.total_chunks || 0} chunks extracted from this document
                  </Text>
                  <VStack spacing={4} align="stretch" maxH="50vh" overflowY="auto">
                    {(viewingContent?.data?.chunks || []).map((chunk, index) => (
                      <Box key={index} bg={sourcesItemBg} p={4} borderRadius="md">
                        <HStack justify="space-between" mb={2}>
                          <Badge colorScheme="blue">
                            Chunk {chunk.chunk_number} of {chunk.total_chunks}
                          </Badge>
                        </HStack>
                        <Divider mb={2} />
                        <Text fontSize="sm" whiteSpace="pre-wrap">
                          {chunk.content}
                        </Text>
                      </Box>
                    ))}
                  </VStack>
                </Box>
              )}
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" onClick={onViewContentClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </VStack>
    </Box>
  );
}
