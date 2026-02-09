'use client';
import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  Flex,
  Text,
  Input,
  FormControl,
  FormLabel,
  SimpleGrid,
  VStack,
  Select,
  useColorModeValue,
  HStack,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Icon,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react';
import { FaTrash, FaDownload, FaCamera, FaImage, FaExclamationTriangle, FaUpload, FaFileAlt, FaShieldAlt, FaUserShield } from 'react-icons/fa';
import Card from '@/components/card/Card';
import { Avatar, useToast } from '@chakra-ui/react';
import InputField from '@/components/fields/InputField';
import LanguageSelector from '@/components/LanguageSelector';
import SocialConnections from '@/components/settings/SocialConnections';
import AIKnowledgeExtractor from '@/components/profiles/AIKnowledgeExtractor';
import api, { getApiUrl, getImageUrl } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';

// My Personal Compliance Rules Component (Level 2 - User-Level Knowledge Base)
function MyUniversalDocuments({ user, cardBg, textColorPrimary, textColorSecondary, t }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [stats, setStats] = useState({ document_count: 0, chunk_count: 0 });
  const toast = useToast();
  
  const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.md', '.csv'];
  
  const loadDocuments = async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const [docsRes, statsRes] = await Promise.all([
        api.get('/user-knowledge/documents'),
        api.get('/user-knowledge/stats')
      ]);
      setDocuments(docsRes.data.documents || []);
      setStats(statsRes.data || { document_count: 0, chunk_count: 0 });
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadDocuments();
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !user?.id) return;
    
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      toast({
        title: 'Invalid file type',
        description: `Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`,
        status: 'error',
        duration: 5000,
      });
      return;
    }
    
    if (file.size > 50 * 1024 * 1024) {
      toast({
        title: 'File too large',
        description: 'Maximum file size is 50MB',
        status: 'error',
        duration: 5000,
      });
      return;
    }
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/user-knowledge/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.success) {
        toast({
          title: 'Document uploaded',
          description: `${file.name} has been processed and added to your universal knowledge base.`,
          status: 'success',
          duration: 4000,
        });
        loadDocuments();
      } else {
        throw new Error(response.data.error || 'Upload failed');
      }
    } catch (error) {
      toast({
        title: 'Upload failed',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };
  
  const handleDeleteDocument = async (documentId) => {
    if (!user?.id) return;
    
    try {
      await api.delete(`/user-knowledge/documents/${documentId}`);
      
      toast({
        title: 'Document deleted',
        status: 'success',
        duration: 3000,
      });
      loadDocuments();
    } catch (error) {
      toast({
        title: 'Delete failed',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };
  
  return (
    <Card bg={cardBg} mb="20px">
      <Flex direction="column" mb="20px">
        <HStack mb="6px">
          <Icon as={FaUserShield} color="brand.500" />
          <Text
            fontSize="xl"
            color={textColorPrimary}
            fontWeight="bold"
          >
            {t('settings.myUniversalDocuments')}
          </Text>
        </HStack>
        <Text fontSize="md" fontWeight="500" color={textColorSecondary}>
          {t('settings.universalDocsDescription')}
        </Text>
      </Flex>
      
      {/* Info Alert about Three-Tier System */}
      <Alert status="info" borderRadius="md" mb={4}>
        <AlertIcon />
        <Box>
          <AlertTitle fontSize="sm">Level 2 - Personal Rules</AlertTitle>
          <AlertDescription fontSize="xs">
            {t('settings.personalComplianceInfo')}
          </AlertDescription>
        </Box>
      </Alert>
      
      {/* Stats */}
      <HStack spacing={4} mb={4}>
        <Box px={3} py={1} bg="blue.50" borderRadius="md">
          <Text fontSize="sm" color="blue.700">
            <strong>{stats.document_count}</strong> {stats.document_count === 1 ? t('enterprise.document', 'document') : t('enterprise.documents', 'documents')}
          </Text>
        </Box>
        <Box px={3} py={1} bg="green.50" borderRadius="md">
          <Text fontSize="sm" color="green.700">
            <strong>{stats.chunk_count}</strong> {t('enterprise.indexedChunks')}
          </Text>
        </Box>
      </HStack>
      
      {/* AI Knowledge Extractor */}
      <AIKnowledgeExtractor
        profileId={user?.id}
        userId={user?.id}
        onKnowledgeAdded={loadDocuments}
      />
      
      <Text fontSize="sm" color="gray.500" textAlign="center" my={3}>
        — or upload documents manually —
      </Text>
      
      {/* Manual Upload Area */}
      <Box
        border="2px dashed"
        borderColor="gray.300"
        borderRadius="xl"
        p={6}
        textAlign="center"
        mb={4}
        _hover={{ borderColor: 'brand.400', bg: 'gray.50' }}
        transition="all 0.2s"
      >
        <Icon as={FaUpload} fontSize="2xl" color="gray.400" mb={3} />
        <Text mb={2} color="gray.600" fontWeight="500">{t('settings.uploadPersonalDocs')}</Text>
        <Text fontSize="xs" color="gray.400" mb={3}>
          PDF, DOCX, XLSX, PPTX, TXT, CSV • Max 50MB
        </Text>
        <Input
          type="file"
          id="universal-doc-upload"
          accept={ALLOWED_EXTENSIONS.join(',')}
          onChange={handleFileUpload}
          display="none"
        />
        <Button
          colorScheme="brand"
          size="sm"
          onClick={() => document.getElementById('universal-doc-upload').click()}
          isLoading={uploading}
          loadingText={t('enterprise.processing')}
        >
          {t('enterprise.chooseFile')}
        </Button>
      </Box>
      
      {/* Document List */}
      {loading ? (
        <Text color="gray.500" textAlign="center">Loading documents...</Text>
      ) : documents.length > 0 ? (
        <VStack spacing={2} align="stretch">
          {documents.map((doc) => (
            <Flex
              key={doc.id}
              justify="space-between"
              align="center"
              p={3}
              bg="gray.50"
              borderRadius="md"
              _hover={{ bg: 'gray.100' }}
            >
              <HStack>
                <Icon as={FaFileAlt} color="brand.500" />
                <Box>
                  <Text fontWeight="500" fontSize="sm">{doc.filename}</Text>
                  <Text fontSize="xs" color="gray.500">
                    {(doc.file_size / 1024).toFixed(1)} KB • {doc.chunk_count} chunks • {new Date(doc.created_at).toLocaleDateString()}
                  </Text>
                </Box>
              </HStack>
              <Button
                size="xs"
                colorScheme="red"
                variant="ghost"
                onClick={() => handleDeleteDocument(doc.id)}
              >
                <FaTrash />
              </Button>
            </Flex>
          ))}
        </VStack>
      ) : (
        <Box textAlign="center" py={4}>
          <Text color="gray.500" fontSize="sm">
            No documents uploaded yet. Add documents to create your personal knowledge base.
          </Text>
        </Box>
      )}
    </Card>
  );
}

export default function ProfileSettings() {
  const router = useRouter();
  const toast = useToast();
  const { t } = useTranslation();
  const [user, setUser] = useState(null);
  const [profileData, setProfileData] = useState({
    name: '',
    company_name: '',
    username: '',
    job_title: '',
    country: '',
    default_homepage: '/dashboard'
  });
  const [profilePicture, setProfilePicture] = useState(null);
  
  // Password change state
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  
  // Camera capture state
  const { isOpen: isCameraOpen, onOpen: onCameraOpen, onClose: onCameraClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  
  // Use the shared getImageUrl from api.js as getAvatarUrl
  const getAvatarUrl = getImageUrl;
  
  // Start camera
  const startCamera = async () => {
    setCameraError(null);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (error) {
      console.error('Camera error:', error);
      setCameraError('Unable to access camera. Please ensure you have granted camera permissions.');
    }
  };
  
  // Stop camera
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };
  
  // Handle camera modal open
  const handleOpenCamera = () => {
    onCameraOpen();
    setTimeout(() => startCamera(), 100);
  };
  
  // Handle camera modal close
  const handleCloseCamera = () => {
    stopCamera();
    onCameraClose();
  };
  
  // Capture photo from camera
  const capturePhoto = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Set canvas size to video size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to blob
    canvas.toBlob(async (blob) => {
      if (!blob) {
        alert('Failed to capture image');
        return;
      }
      
      // Create a file from the blob
      const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
      
      // Close camera
      handleCloseCamera();
      
      // Upload the captured image
      await uploadProfilePicture(file);
    }, 'image/jpeg', 0.9);
  };
  
  // Upload profile picture (shared between file upload and camera capture)
  const uploadProfilePicture = async (file) => {
    // Create a local URL for immediate display
    const imageUrl = URL.createObjectURL(file);
    setProfilePicture(imageUrl);
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', user.id);
      
      // Upload to backend
      const response = await api.post('/auth/upload-avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      // Clean up blob URL
      URL.revokeObjectURL(imageUrl);
      
      // Update with the server URL
      const serverAvatarUrl = response.data.avatar_url;
      setProfilePicture(serverAvatarUrl);
      
      const updatedUser = {
        ...user,
        profile_picture: serverAvatarUrl
      };
      localStorage.setItem('contentry_user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      
      // Dispatch custom event to notify navbar and other components
      window.dispatchEvent(new Event('profileUpdated'));
      
      alert('Profile picture updated successfully!');
    } catch (error) {
      console.error('Error uploading profile picture:', error);
      alert('Failed to upload profile picture: ' + (error.response?.data?.detail || error.message));
      // Clean up blob URL and revert to old picture
      URL.revokeObjectURL(imageUrl);
      setProfilePicture(user.profile_picture || null);
    }
  };

  // Delete account function
  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE') {
      toast({
        title: 'Confirmation required',
        description: 'Please type DELETE to confirm',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsDeleting(true);
    try {
      await api.delete('/auth/account');

      toast({
        title: 'Account deleted',
        description: 'Your account has been permanently deleted',
        status: 'success',
        duration: 5000,
      });

      // Clear local storage and redirect to login
      localStorage.removeItem('contentry_user');
      localStorage.removeItem('token');
      router.push('/contentry/auth/login');
    } catch (error) {
      toast({
        title: 'Error deleting account',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const countries = [
    { name: 'United States', timezone: 'America/New_York (UTC-5)' },
    { name: 'United Kingdom', timezone: 'Europe/London (UTC+0)' },
    { name: 'India', timezone: 'Asia/Kolkata (UTC+5:30)' },
    { name: 'Australia', timezone: 'Australia/Sydney (UTC+10)' },
    { name: 'Canada', timezone: 'America/Toronto (UTC-5)' },
    { name: 'Germany', timezone: 'Europe/Berlin (UTC+1)' },
    { name: 'France', timezone: 'Europe/Paris (UTC+1)' },
    { name: 'Japan', timezone: 'Asia/Tokyo (UTC+9)' },
    { name: 'China', timezone: 'Asia/Shanghai (UTC+8)' },
    { name: 'Brazil', timezone: 'America/Sao_Paulo (UTC-3)' },
    { name: 'Singapore', timezone: 'Asia/Singapore (UTC+8)' },
    { name: 'UAE', timezone: 'Asia/Dubai (UTC+4)' },
  ];

  // Chakra Color Mode
  const textColorPrimary = useColorModeValue('navy.700', 'white');
  const textColorSecondary = 'gray.500';
  const cardBg = useColorModeValue('white', 'gray.800');
  const banner = 'linear-gradient(15.46deg, #1e40af 26.3%, #60a5fa 86.4%)';

   
  useEffect(() => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      setProfileData({
        name: userData.full_name || '',
        company_name: userData.company_name || '',
        username: userData.email ? userData.email.split('@')[0] : '',
        job_title: userData.job_title || '',
        country: userData.country || '',
        default_homepage: userData.default_homepage || '/dashboard'
      });
      
      // Load profile picture if available
      if (userData.profile_picture) {
        setProfilePicture(userData.profile_picture);
      }
    }
  }, []);
   

  const handleInputChange = (e) => {
    setProfileData({ ...profileData, [e.target.name]: e.target.value });
  };

  const handleSaveChanges = async () => {
    try {
      // Save to backend (excluding profile picture as it's uploaded separately)
      const response = await api.put('/auth/profile', {
        user_id: user.id,
        full_name: profileData.name,
        company_name: profileData.company_name,
        job_title: profileData.job_title,
        country: profileData.country,
        default_homepage: profileData.default_homepage
      });
      
      // Update localStorage with response from backend
      const updatedUser = response.data.user;
      localStorage.setItem('contentry_user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      
      // Dispatch custom event to notify other components
      window.dispatchEvent(new Event('profileUpdated'));
      
      alert('Profile updated successfully! Your settings have been saved.');
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle password change
  const handlePasswordChange = async () => {
    // Validate inputs
    if (!passwordData.oldPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      toast({
        title: 'All password fields are required',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast({
        title: 'New passwords do not match',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    if (passwordData.newPassword.length < 8) {
      toast({
        title: 'Password must be at least 8 characters',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    setIsChangingPassword(true);
    try {
      await api.post('/auth/change-password', {
        old_password: passwordData.oldPassword,
        new_password: passwordData.newPassword
      });
      
      toast({
        title: 'Password updated successfully!',
        status: 'success',
        duration: 3000,
      });
      
      // Clear password fields
      setPasswordData({
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    } catch (error) {
      console.error('Error changing password:', error);
      toast({
        title: 'Failed to change password',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleProfilePictureUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select a valid image file');
      return;
    }
    
    await uploadProfilePicture(file);
  };

  const getUserRole = () => {
    if (!user) return 'User';
    if (user.is_enterprise_admin) return 'Enterprise Admin';
    if (user.role === 'admin') return 'Administrator';
    return 'User';
  };

  return (
    <Box mt={{ base: '70px', md: '0px', xl: '0px' }}>
      <SimpleGrid columns={{ sm: 1, lg: 2 }} spacing="20px" mb="20px">
        {/* Column Left */}
        <Flex direction="column">
          {/* Profile Card with Gradient Banner */}
          <Card mb="20px" alignItems="center">
            <Flex bg={banner} w="100%" h="129px" borderRadius="16px" />
            <Box position="relative" mt="-43px" mb="15px">
              <Avatar
                src={getAvatarUrl(profilePicture || user?.profile_picture)}
                name={user?.full_name}
                size="xl"
                border="3px solid"
                borderColor="gray.200"
              />
            </Box>
            <Text
              fontSize="2xl"
              textColor={textColorPrimary}
              fontWeight="700"
              mb="4px"
            >
              {user?.full_name || 'User'}
            </Text>
            <Flex align="center" mx="auto" px="14px" mb="20px">
              <Text
                color={textColorSecondary}
                fontSize="sm"
                fontWeight="500"
                lineHeight="100%"
              >
                Account type:
              </Text>
              <Select
                ms="-4px"
                id="user_type"
                w="unset"
                h="100%"
                variant="transparent"
                display="flex"
                textColor={textColorPrimary}
                color={textColorPrimary}
                alignItems="center"
                value={getUserRole()}
                isDisabled
              >
                <option value="Administrator">Administrator</option>
                <option value="Enterprise Admin">Enterprise Admin</option>
                <option value="User">User</option>
              </Select>
            </Flex>
            
            {/* Profile Picture Upload Options */}
            <VStack spacing={3} mb="15px" w="full" px={4}>
              <HStack spacing={3} justify="center" w="full">
                <Input
                  type="file"
                  id="profile-picture-upload"
                  accept="image/*"
                  onChange={handleProfilePictureUpload}
                  display="none"
                />
                <Button
                  leftIcon={<FaImage />}
                  colorScheme="brand"
                  variant="outline"
                  size="sm"
                  onClick={() => document.getElementById('profile-picture-upload').click()}
                >
                  {t('settings.uploadPhoto')}
                </Button>
                <Button
                  leftIcon={<FaCamera />}
                  colorScheme="brand"
                  size="sm"
                  onClick={handleOpenCamera}
                >
                  {t('common.camera', 'Take Photo')}
                </Button>
              </HStack>
              <Text fontSize="xs" color={textColorSecondary} textAlign="center">
                Recommended: Square image, at least 200x200px
              </Text>
            </VStack>
          </Card>

          {/* Account Settings Card */}
          <Card>
            <Flex direction="column" mb="40px">
              <Text
                fontSize="xl"
                color={textColorPrimary}
                mb="6px"
                fontWeight="bold"
              >
                {t('settings.account')}
              </Text>
              <Text fontSize="md" fontWeight="500" color={textColorSecondary}>
                {t('settings.accountHelp', 'Here you can change user account information')}
              </Text>
            </Flex>
            <SimpleGrid
              columns={{ sm: 1, md: 2 }}
              spacing={{ base: '20px', xl: '20px' }}
            >
              <InputField
                mb="10px"
                me="30px"
                id="username"
                label={t('common.username', 'Username')}
                placeholder="@username"
                value={profileData.username}
                onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
              />
              <InputField
                mb="10px"
                id="name"
                label={t('common.fullName', 'Full Name')}
                placeholder={t('common.fullName', 'Full Name')}
                value={profileData.name}
                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
              />
              <InputField
                mb="10px"
                me="30px"
                id="company_name"
                label={t('settings.company')}
                placeholder={t('settings.company')}
                value={profileData.company_name}
                onChange={(e) => setProfileData({ ...profileData, company_name: e.target.value })}
              />
              <InputField
                mb="20px"
                id="job_title"
                label={t('settings.jobTitle')}
                placeholder={t('settings.jobTitle')}
                value={profileData.job_title}
                onChange={(e) => setProfileData({ ...profileData, job_title: e.target.value })}
              />
            </SimpleGrid>
            
            <FormControl mb="20px">
              <Text fontSize="sm" fontWeight="500" color={textColorPrimary} mb="8px">
                {t('common.countryTimezone', 'Country & Timezone')}
              </Text>
              <Select 
                name="country" 
                value={profileData.country} 
                onChange={handleInputChange}
                placeholder={t('common.selectCountry', 'Select country & timezone')}
              >
                {countries.map((country) => (
                  <option key={country.name} value={`${country.name} - ${country.timezone}`}>
                    {country.name} - {country.timezone}
                  </option>
                ))}
              </Select>
            </FormControl>

            <FormControl mb="20px">
              <Text fontSize="sm" fontWeight="500" color={textColorPrimary} mb="8px">
                {t('settings.defaultHomepage')}
              </Text>
              <Select 
                name="default_homepage" 
                value={profileData.default_homepage} 
                onChange={handleInputChange}
              >
                <option value="/dashboard">{t('navigation.dashboard')} - {t('analytics.overview')}</option>
                <option value="/content-moderation">{t('navigation.contentIntelligence')} - {t('contentGeneration.subtitle', 'Analyze & Generate content')}</option>
                <option value="/posts">{t('navigation.posts')} - {t('posts.subtitle', 'View all your posts')}</option>
              </Select>
              <Text fontSize="xs" color={textColorSecondary} mt={1}>
                {t('settings.defaultHomepageHelp', 'This page will open when you log in')}
              </Text>
            </FormControl>

            <FormControl mb="40px">
              <Text fontSize="sm" fontWeight="500" color={textColorPrimary} mb="8px">
                {t('settings.languagePreference')}
              </Text>
              <LanguageSelector />
              <Text fontSize="xs" color={textColorSecondary} mt={1}>
                {t('settings.languageHelp')}
              </Text>
            </FormControl>

            <Button 
              colorScheme="brand" 
              onClick={handleSaveChanges}
              w="100%"
              size="sm"
            >
              {t('settings.saveChanges').toUpperCase()}
            </Button>
          </Card>
        </Flex>

        {/* Column Right */}
        <Flex direction="column" gap="20px">
          {/* Social Profiles Card - Using new SocialConnections component */}
          <SocialConnections />

          {/* Password Change Card */}
          <Card>
            <Flex direction="column" mb="40px">
              <Text
                fontSize="xl"
                color={textColorPrimary}
                mb="6px"
                fontWeight="bold"
              >
                {t('settings.changePassword')}
              </Text>
              <Text fontSize="md" fontWeight="500" color={textColorSecondary}>
                {t('settings.changePasswordHelp', 'Here you can set your new password')}
              </Text>
            </Flex>
            <FormControl>
              <Flex flexDirection="column">
                <InputField
                  mb="25px"
                  id="old"
                  label={t('settings.oldPassword')}
                  placeholder={t('settings.oldPassword')}
                  type="password"
                  value={passwordData.oldPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, oldPassword: e.target.value })}
                />
                <InputField
                  mb="25px"
                  id="new"
                  label={t('settings.newPassword')}
                  placeholder={t('settings.newPassword')}
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                />
                <InputField
                  mb="25px"
                  id="confirm"
                  label={t('settings.confirmNewPassword')}
                  placeholder={t('settings.confirmNewPassword')}
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                />
                <Button 
                  colorScheme="brand" 
                  w="100%" 
                  size="sm"
                  onClick={handlePasswordChange}
                  isLoading={isChangingPassword}
                >
                  {t('settings.updatePassword').toUpperCase()}
                </Button>
              </Flex>
            </FormControl>
          </Card>
        </Flex>
      </SimpleGrid>

      {/* My Universal Documents - Tier 1 Knowledge Base */}
      <MyUniversalDocuments user={user} cardBg={cardBg} textColorPrimary={textColorPrimary} textColorSecondary={textColorSecondary} t={t} />

      {/* Reports & Analytics - Full Width */}
      <Card bg={cardBg}>
        <Flex direction="column" mb="40px">
          <Text
            fontSize="xl"
            color={textColorPrimary}
            mb="6px"
            fontWeight="bold"
          >
            {t('settings.reportsAnalytics')}
          </Text>
          <Text fontSize="md" fontWeight="500" color={textColorSecondary}>
            {t('settings.reportsDescription')}
          </Text>
        </Flex>

        <VStack spacing={4} align="stretch">
          <Flex
            p={4}
            border="2px solid"
            borderColor="blue.300"
            borderRadius="md"
            bg="blue.50"
            justify="space-between"
            align="center"
          >
            <Box>
              <Text fontWeight="600" fontSize="md">{t('settings.comprehensivePdfReport')}</Text>
              <Text fontSize="sm" color="gray.600">
                {t('settings.pdfReportDescription')}
              </Text>
            </Box>
            <Button 
              leftIcon={<FaDownload />}
              colorScheme="blue"
              size="sm"
              onClick={() => {
                // Use user.id if available, report page will use localStorage as fallback
                const reportUrl = user?.id 
                  ? `/contentry/report?user_id=${user.id}` 
                  : '/contentry/report';
                window.open(reportUrl, '_blank');
              }}
            >
              {t('settings.viewReport')}
            </Button>
          </Flex>

          <Flex
            p={4}
            border="2px solid"
            borderColor="gray.200"
            borderRadius="md"
            justify="space-between"
            align="center"
          >
            <Box>
              <Text fontWeight="600" fontSize="md">{t('settings.reportFeatures')}</Text>
              <VStack align="start" spacing={1} mt={2}>
                <Text fontSize="xs" color="gray.600">✓ {t('settings.executiveSummary')}</Text>
                <Text fontSize="xs" color="gray.600">✓ {t('settings.profileOverview')}</Text>
                <Text fontSize="xs" color="gray.600">✓ {t('settings.riskAssessment')}</Text>
                <Text fontSize="xs" color="gray.600">✓ {t('settings.detailedContentAnalysis')}</Text>
                <Text fontSize="xs" color="gray.600">✓ {t('settings.themeDistribution')}</Text>
                <Text fontSize="xs" color="gray.600">✓ {t('settings.reputationInsights')}</Text>
              </VStack>
            </Box>
          </Flex>
        </VStack>
      </Card>

      {/* Danger Zone - Delete Account */}
      <Card bg={cardBg} borderWidth="2px" borderColor="red.200" mt="20px">
        <Flex direction="column" mb="20px">
          <HStack mb="6px">
            <Icon as={FaExclamationTriangle} color="red.500" />
            <Text
              fontSize="xl"
              color="red.500"
              fontWeight="bold"
            >
              {t('settings.dangerZone')}
            </Text>
          </HStack>
          <Text fontSize="md" fontWeight="500" color={textColorSecondary}>
            {t('settings.dangerZoneDescription')}
          </Text>
        </Flex>

        <Box p={4} bg="red.50" borderRadius="md" borderWidth="1px" borderColor="red.200">
          <Text fontWeight="600" mb={2} color="red.700">{t('settings.deleteAccount')}</Text>
          <Text fontSize="sm" color="red.600" mb={4}>
            {t('settings.deleteAccountDescription')}
          </Text>
          <Button
            colorScheme="red"
            variant="outline"
            leftIcon={<FaTrash />}
            onClick={onDeleteOpen}
          >
            {t('settings.deleteMyAccount')}
          </Button>
        </Box>
      </Card>
      
      {/* Camera Capture Modal */}
      <Modal isOpen={isCameraOpen} onClose={handleCloseCamera} size="lg" isCentered>
        <ModalOverlay bg="blackAlpha.700" />
        <ModalContent bg={cardBg}>
          <ModalHeader color={textColorPrimary}>Take Profile Photo</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {cameraError ? (
              <Box textAlign="center" py={8}>
                <Text color="red.500" mb={4}>{cameraError}</Text>
                <Button colorScheme="brand" size="sm" onClick={startCamera}>
                  Try Again
                </Button>
              </Box>
            ) : (
              <Box position="relative">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  style={{
                    width: '100%',
                    borderRadius: '8px',
                    transform: 'scaleX(-1)' // Mirror effect for selfie
                  }}
                />
                <canvas ref={canvasRef} style={{ display: 'none' }} />
              </Box>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} size="sm" onClick={handleCloseCamera}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
              size="sm"
              leftIcon={<FaCamera />}
              onClick={capturePhoto}
              isDisabled={!!cameraError || !stream}
            >
              Capture Photo
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Account Confirmation Modal */}
      <Modal isOpen={isDeleteOpen} onClose={onDeleteClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader color="red.500">Delete Account</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Box p={4} bg="red.50" borderRadius="md" borderWidth="1px" borderColor="red.200">
                <Text fontWeight="600" color="red.700" mb={2}>
                  ⚠️ This action cannot be undone
                </Text>
                <Text fontSize="sm" color="red.600">
                  This will permanently delete:
                </Text>
                <VStack align="start" mt={2} spacing={1}>
                  <Text fontSize="sm" color="red.600">• Your user account and profile</Text>
                  <Text fontSize="sm" color="red.600">• All posts and content analyses</Text>
                  <Text fontSize="sm" color="red.600">• Scheduled posts and drafts</Text>
                  <Text fontSize="sm" color="red.600">• Notifications and activity history</Text>
                  <Text fontSize="sm" color="red.600">• All uploaded policy documents</Text>
                </VStack>
              </Box>
              
              <FormControl>
                <FormLabel fontSize="sm" color="gray.600">
                  Type <Text as="span" fontWeight="bold">DELETE</Text> to confirm
                </FormLabel>
                <Input
                  placeholder="DELETE"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  borderColor={deleteConfirmation === 'DELETE' ? 'green.300' : 'gray.200'}
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => {
              onDeleteClose();
              setDeleteConfirmation('');
            }}>
              Cancel
            </Button>
            <Button
              colorScheme="red"
              onClick={handleDeleteAccount}
              isLoading={isDeleting}
              isDisabled={deleteConfirmation !== 'DELETE'}
            >
              Delete My Account
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
