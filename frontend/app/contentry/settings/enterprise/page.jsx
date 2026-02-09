'use client';

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Flex,
  Text,
  Input,
  FormControl,
  FormLabel,
  VStack,
  HStack,
  useColorModeValue,
  Icon,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Avatar,
  Select,
  Textarea,
  Alert,
  AlertIcon,
  AlertDescription,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  useToast,
  Spinner,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
} from '@chakra-ui/react';
import {
  FaBuilding,
  FaUsers,
  FaFileAlt,
  FaUpload,
  FaTrash,
  FaUserShield,
  FaCrown,
  FaUserPlus,
  FaSignOutAlt,
  FaEnvelope,
  FaClock,
  FaTimes,
  FaPaperPlane,
  FaCheckCircle,
} from 'react-icons/fa';
import Card from '@/components/card/Card';
import { getApiUrl } from '@/lib/api';
import axios from 'axios';
import { useRouter } from 'next/navigation';

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.md', '.csv'];

// ==================== INVITE TEAM MEMBER SECTION ====================
function InviteTeamMemberSection({ user, onInviteSent, toast, t }) {
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('creator');
  const [inviteMessage, setInviteMessage] = useState('');
  const [inviting, setInviting] = useState(false);
  const [pendingInvites, setPendingInvites] = useState([]);
  const [loadingInvites, setLoadingInvites] = useState(true);
  
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const inputBg = useColorModeValue('white', 'gray.700');
  
  // Load pending invitations
  useEffect(() => {
    const loadPendingInvites = async () => {
      if (!user?.id) return;
      
      try {
        const API = getApiUrl();
        const response = await axios.get(`${API}/team-management/members`, {
          headers: { 'X-User-ID': user.id }
        });
        
        // Filter for pending invitations only
        const pending = (response.data.members || []).filter(m => m.status === 'invited');
        setPendingInvites(pending);
      } catch (error) {
        console.error('Failed to load pending invites:', error);
      } finally {
        setLoadingInvites(false);
      }
    };
    
    loadPendingInvites();
  }, [user?.id]);
  
  // Handle sending invitation
  const handleSendInvite = async () => {
    if (!inviteEmail.trim()) {
      toast({
        title: t('enterprise.emailRequired', 'Email required'),
        description: t('enterprise.enterEmailAddress', 'Please enter the email address of the person you want to invite.'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(inviteEmail.trim())) {
      toast({
        title: t('enterprise.invalidEmail', 'Invalid email'),
        description: t('enterprise.enterValidEmail', 'Please enter a valid email address.'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setInviting(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/team-management/invite`, {
        email: inviteEmail.trim().toLowerCase(),
        role: inviteRole,
        message: inviteMessage.trim() || null
      }, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: t('enterprise.invitationSent', 'Invitation sent!'),
        description: t('enterprise.invitationSentTo', 'An invitation has been sent to {{email}}').replace('{{email}}', inviteEmail),
        status: 'success',
        duration: 5000,
      });
      
      // Add to pending invites list
      setPendingInvites(prev => [...prev, {
        id: response.data.invitation_id,
        email: inviteEmail.trim().toLowerCase(),
        role: inviteRole,
        status: 'invited',
        invited_at: new Date().toISOString()
      }]);
      
      // Clear form
      setInviteEmail('');
      setInviteRole('creator');
      setInviteMessage('');
      
      // Notify parent to refresh
      if (onInviteSent) {
        onInviteSent();
      }
      
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      toast({
        title: t('enterprise.failedToSendInvitation', 'Failed to send invitation'),
        description: errorMessage,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setInviting(false);
    }
  };
  
  // Handle cancelling invitation
  const handleCancelInvite = async (invitationId) => {
    try {
      const API = getApiUrl();
      await axios.delete(`${API}/team-management/invitation/${invitationId}`, {
        headers: { 'X-User-ID': user.id }
      });
      
      setPendingInvites(prev => prev.filter(i => i.id !== invitationId));
      
      toast({
        title: t('enterprise.invitationCancelled', 'Invitation cancelled'),
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: t('enterprise.failedToCancelInvitation', 'Failed to cancel invitation'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };
  
  return (
    <Box mb={6}>
      {/* Invite Form */}
      <Box
        p={4}
        borderWidth="1px"
        borderColor={borderColor}
        borderRadius="lg"
        mb={4}
      >
        <HStack mb={3} align="center">
          <Icon as={FaUserPlus} color="brand.500" />
          <Text fontWeight="600" fontSize="md">{t('enterprise.inviteTeamMember')}</Text>
        </HStack>
        
        <VStack spacing={4} align="stretch">
          <HStack spacing={4} flexWrap={{ base: 'wrap', md: 'nowrap' }}>
            <FormControl flex="2" minW="200px">
              <FormLabel fontSize="sm">{t('enterprise.email')}</FormLabel>
              <Input
                type="email"
                placeholder="colleague@company.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                bg={inputBg}
                size="sm"
              />
            </FormControl>
            
            <FormControl flex="1" minW="120px">
              <FormLabel fontSize="sm">{t('enterprise.role')}</FormLabel>
              <Select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                bg={inputBg}
                size="sm"
              >
                <option value="creator">{t('enterprise.creator')}</option>
                <option value="manager">{t('enterprise.manager')}</option>
                <option value="admin">{t('enterprise.admin')}</option>
              </Select>
            </FormControl>
          </HStack>
          
          <FormControl>
            <FormLabel fontSize="sm">{t('enterprise.personalMessage')}</FormLabel>
            <Textarea
              placeholder={t('enterprise.addPersonalNote', 'Add a personal note to your invitation...')}
              value={inviteMessage}
              onChange={(e) => setInviteMessage(e.target.value)}
              bg={inputBg}
              size="sm"
              rows={2}
              maxLength={500}
            />
          </FormControl>
          
          <HStack justify="space-between" align="center">
            <Text fontSize="xs" color="gray.500">
              {t('enterprise.invitationExpires')}
            </Text>
            <Button
              colorScheme="brand"
              size="sm"
              leftIcon={<FaPaperPlane />}
              onClick={handleSendInvite}
              isLoading={inviting}
              loadingText={t('common.sending', 'Sending...')}
            >
              {t('enterprise.sendInvitation')}
            </Button>
          </HStack>
        </VStack>
      </Box>
      
      {/* Pending Invitations */}
      {loadingInvites ? (
        <Flex justify="center" py={4}>
          <Spinner size="sm" />
        </Flex>
      ) : pendingInvites.length > 0 && (
        <Box
          p={4}
          borderWidth="1px"
          borderColor="orange.200"
          borderRadius="lg"
          bg="orange.50"
          _dark={{ bg: 'orange.900', borderColor: 'orange.700' }}
        >
          <HStack mb={3} align="center">
            <Icon as={FaClock} color="orange.500" />
            <Text fontWeight="600" fontSize="sm" color="orange.700" _dark={{ color: 'orange.200' }}>
              {t('enterprise.pendingInvitations')} ({pendingInvites.length})
            </Text>
          </HStack>
          
          <VStack spacing={2} align="stretch">
            {pendingInvites.map((invite) => (
              <Flex
                key={invite.id}
                justify="space-between"
                align="center"
                p={2}
                bg="white"
                _dark={{ bg: 'gray.800' }}
                borderRadius="md"
                fontSize="sm"
              >
                <HStack spacing={3}>
                  <Icon as={FaEnvelope} color="gray.400" />
                  <Box>
                    <Text fontWeight="500">{invite.email}</Text>
                    <Text fontSize="xs" color="gray.500">
                      {t('enterprise.invitedAs')} {invite.role?.charAt(0).toUpperCase() + invite.role?.slice(1)} • 
                      {invite.invited_at && ` ${new Date(invite.invited_at).toLocaleDateString()}`}
                    </Text>
                  </Box>
                </HStack>
                <Button
                  size="xs"
                  colorScheme="red"
                  variant="ghost"
                  onClick={() => handleCancelInvite(invite.id)}
                  title={t('enterprise.cancelInvitation')}
                >
                  <FaTimes />
                </Button>
              </Flex>
            ))}
          </VStack>
        </Box>
      )}
    </Box>
  );
}

export default function EnterpriseDashboard() {
  const { t } = useTranslation();
  const router = useRouter();
  const toast = useToast();
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const { isOpen: isLeaveOpen, onOpen: onLeaveOpen, onClose: onLeaveClose } = useDisclosure();
  
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adminStatus, setAdminStatus] = useState({ is_admin: false, has_company: false });
  const [company, setCompany] = useState(null);
  const [members, setMembers] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  
  // Company creation form
  const [newCompanyName, setNewCompanyName] = useState('');
  const [newCompanyDescription, setNewCompanyDescription] = useState('');
  const [creating, setCreating] = useState(false);
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColorPrimary = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  
  // Load user and company data
  useEffect(() => {
    const loadData = async () => {
      const savedUser = localStorage.getItem('contentry_user');
      if (!savedUser) {
        router.push('/contentry/auth/login');
        return;
      }
      
      const userData = JSON.parse(savedUser);
      setUser(userData);
      
      try {
        const API = getApiUrl();
        
        // Check admin status
        const statusRes = await axios.get(`${API}/company/admin-status`, {
          headers: { 'X-User-ID': userData.id }
        });
        setAdminStatus(statusRes.data);
        
        if (statusRes.data.has_company) {
          // Load company details
          const companyRes = await axios.get(`${API}/company/my-company`, {
            headers: { 'X-User-ID': userData.id }
          });
          setCompany(companyRes.data);
          
          // Load members
          const membersRes = await axios.get(`${API}/company/members`, {
            headers: { 'X-User-ID': userData.id }
          });
          setMembers(membersRes.data);
          
          // Load documents (only for admins)
          if (statusRes.data.is_admin) {
            const docsRes = await axios.get(`${API}/company/knowledge/documents`, {
              headers: { 'X-User-ID': userData.id }
            });
            setDocuments(docsRes.data.documents || []);
          }
        }
      } catch (error) {
        console.error('Failed to load company data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [router]);
  
  // Create company
  const handleCreateCompany = async () => {
    if (!newCompanyName.trim()) {
      toast({
        title: 'Company name required',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setCreating(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/company/create`, {
        name: newCompanyName.trim(),
        description: newCompanyDescription.trim() || null
      }, {
        headers: { 'X-User-ID': user.id }
      });
      
      setCompany(response.data);
      setAdminStatus({ is_admin: true, has_company: true, company_role: 'admin' });
      
      toast({
        title: 'Company created!',
        description: `${response.data.name} has been created. You are now the Company Admin.`,
        status: 'success',
        duration: 5000,
      });
      
      onCreateClose();
      setNewCompanyName('');
      setNewCompanyDescription('');
      
      // Reload members
      const membersRes = await axios.get(`${API}/company/members`, {
        headers: { 'X-User-ID': user.id }
      });
      setMembers(membersRes.data);
      
    } catch (error) {
      toast({
        title: 'Failed to create company',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setCreating(false);
    }
  };
  
  // Leave company
  const handleLeaveCompany = async () => {
    try {
      const API = getApiUrl();
      await axios.post(`${API}/company/leave`, {}, {
        headers: { 'X-User-ID': user.id }
      });
      
      setCompany(null);
      setAdminStatus({ is_admin: false, has_company: false });
      setMembers([]);
      setDocuments([]);
      
      toast({
        title: 'Left company',
        description: 'You have left the company.',
        status: 'info',
        duration: 4000,
      });
      
      onLeaveClose();
    } catch (error) {
      toast({
        title: 'Failed to leave company',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };
  
  // Upload company document
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
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const API = getApiUrl();
      const response = await axios.post(`${API}/company/knowledge/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-User-ID': user.id
        }
      });
      
      if (response.data.success) {
        toast({
          title: t('enterprise.documentUploaded', 'Document uploaded'),
          description: t('enterprise.documentAddedToKnowledge', '{{filename}} has been added to the company knowledge base.').replace('{{filename}}', file.name),
          status: 'success',
          duration: 4000,
        });
        
        // Reload documents
        const docsRes = await axios.get(`${API}/company/knowledge/documents`, {
          headers: { 'X-User-ID': user.id }
        });
        setDocuments(docsRes.data.documents || []);
        
        // Reload company for updated stats
        const companyRes = await axios.get(`${API}/company/my-company`, {
          headers: { 'X-User-ID': user.id }
        });
        setCompany(companyRes.data);
      }
    } catch (error) {
      toast({
        title: t('enterprise.uploadFailed', 'Upload failed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };
  
  // Delete company document
  const handleDeleteDocument = async (documentId) => {
    try {
      const API = getApiUrl();
      await axios.delete(`${API}/company/knowledge/documents/${documentId}`, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: t('enterprise.documentDeleted', 'Document deleted'),
        status: 'success',
        duration: 3000,
      });
      
      // Reload documents
      const docsRes = await axios.get(`${API}/company/knowledge/documents`, {
        headers: { 'X-User-ID': user.id }
      });
      setDocuments(docsRes.data.documents || []);
      
      // Reload company for updated stats
      const companyRes = await axios.get(`${API}/company/my-company`, {
        headers: { 'X-User-ID': user.id }
      });
      setCompany(companyRes.data);
    } catch (error) {
      toast({
        title: t('enterprise.deleteFailed', 'Delete failed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };
  
  // Update member role
  const handleUpdateMemberRole = async (memberId, newRole) => {
    try {
      const API = getApiUrl();
      await axios.put(`${API}/company/members/${memberId}/role`, 
        { company_role: newRole },
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: t('enterprise.roleUpdated', 'Role updated'),
        description: t('enterprise.memberRoleChanged', 'Member role changed to {{role}}').replace('{{role}}', newRole),
        status: 'success',
        duration: 3000,
      });
      
      // Reload members
      const membersRes = await axios.get(`${API}/company/members`, {
        headers: { 'X-User-ID': user.id }
      });
      setMembers(membersRes.data);
    } catch (error) {
      toast({
        title: t('enterprise.failedToUpdateRole', 'Failed to update role'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };
  
  // Remove member
  const handleRemoveMember = async (memberId) => {
    try {
      const API = getApiUrl();
      await axios.delete(`${API}/company/members/${memberId}`, {
        headers: { 'X-User-ID': user.id }
      });
      
      toast({
        title: 'Member removed',
        status: 'success',
        duration: 3000,
      });
      
      // Reload members
      const membersRes = await axios.get(`${API}/company/members`, {
        headers: { 'X-User-ID': user.id }
      });
      setMembers(membersRes.data);
    } catch (error) {
      toast({
        title: 'Failed to remove member',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };
  
  if (loading) {
    return (
      <Flex justify="center" align="center" minH="400px">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }
  
  // No company - show create company prompt
  if (!adminStatus.has_company) {
    return (
      <Box p={6}>
        <Card bg={cardBg} p={8} textAlign="center">
          <Icon as={FaBuilding} fontSize="5xl" color="gray.300" mb={4} />
          <Text fontSize="2xl" fontWeight="bold" color={textColorPrimary} mb={2}>
            {t('enterprise.title')}
          </Text>
          <Text color={textColorSecondary} mb={6} maxW="500px" mx="auto">
            {t('enterprise.createCompanyDesc')}
          </Text>
          
          <VStack spacing={4}>
            <Button
              colorScheme="brand"
              size="lg"
              leftIcon={<FaBuilding />}
              onClick={onCreateOpen}
            >
              {t('enterprise.createCompany')}
            </Button>
            <Text fontSize="sm" color="gray.500">
              {t('enterprise.becomeAdmin')}
            </Text>
          </VStack>
        </Card>
        
        {/* Create Company Modal */}
        <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="md">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>{t('enterprise.createCompany')}</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>{t('enterprise.companyName')}</FormLabel>
                  <Input
                    placeholder={t('enterprise.enterCompanyName')}
                    value={newCompanyName}
                    onChange={(e) => setNewCompanyName(e.target.value)}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>{t('enterprise.companyDescription')}</FormLabel>
                  <Textarea
                    placeholder={t('enterprise.companyDescPlaceholder')}
                    value={newCompanyDescription}
                    onChange={(e) => setNewCompanyDescription(e.target.value)}
                  />
                </FormControl>
                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  <AlertDescription fontSize="sm">
                    {t('enterprise.createAsAdminNote')}
                  </AlertDescription>
                </Alert>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onCreateClose}>
                {t('enterprise.cancel')}
              </Button>
              <Button
                colorScheme="brand"
                onClick={handleCreateCompany}
                isLoading={creating}
                loadingText={t('enterprise.creating')}
              >
                {t('enterprise.createCompanyBtn')}
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Box>
    );
  }
  
  // Has company but not admin - show limited view
  if (!adminStatus.is_admin) {
    return (
      <Box p={6}>
        <Card bg={cardBg}>
          <Flex direction="column" mb={6}>
            <HStack mb={2}>
              <Icon as={FaBuilding} color="brand.500" />
              <Text fontSize="xl" fontWeight="bold" color={textColorPrimary}>
                {company?.name || t('enterprise.yourCompany', 'Your Company')}
              </Text>
              <Badge colorScheme="gray">{t('enterprise.member')}</Badge>
            </HStack>
            <Text color={textColorSecondary}>
              {company?.description || t('enterprise.noDescription')}
            </Text>
          </Flex>
          
          <Alert status="info" mb={4}>
            <AlertIcon />
            <AlertDescription>
              {t('enterprise.onlyAdminsCanManage')}
            </AlertDescription>
          </Alert>
          
          <Button
            colorScheme="red"
            variant="outline"
            size="sm"
            leftIcon={<FaSignOutAlt />}
            onClick={onLeaveOpen}
          >
            {t('enterprise.leaveCompany')}
          </Button>
        </Card>
        
        {/* Leave Company Modal */}
        <Modal isOpen={isLeaveOpen} onClose={onLeaveClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>{t('enterprise.leaveCompany')}</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <Text>{t('enterprise.confirmLeave')} <strong>{company?.name}</strong>?</Text>
              <Text color="gray.500" mt={2} fontSize="sm">
                {t('enterprise.loseAccessWarning')}
              </Text>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onLeaveClose}>{t('enterprise.cancel')}</Button>
              <Button colorScheme="red" onClick={handleLeaveCompany}>{t('enterprise.leave')}</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Box>
    );
  }
  
  // Admin view - full enterprise dashboard
  return (
    <Box p={6}>
      {/* Company Header */}
      <Card bg={cardBg} mb={6}>
        <Flex direction="column">
          <HStack mb={2}>
            <Icon as={FaBuilding} color="brand.500" fontSize="2xl" />
            <Text fontSize="2xl" fontWeight="bold" color={textColorPrimary}>
              {company?.name}
            </Text>
            <Badge colorScheme="blue" fontSize="sm">
              <HStack spacing={1}>
                <FaCrown />
                <span>{t('enterprise.companyAdmin')}</span>
              </HStack>
            </Badge>
          </HStack>
          <Text color={textColorSecondary} mb={4}>
            {company?.description || t('enterprise.noDescriptionSet', 'No description set')}
          </Text>
          <HStack spacing={4}>
            <Box px={3} py={1} bg="blue.50" borderRadius="md">
              <Text fontSize="sm" color="blue.700">
                <strong>{company?.member_count || 1}</strong> {company?.member_count === 1 ? t('enterprise.teamMember') : t('enterprise.teamMembersCount')}
              </Text>
            </Box>
            <Box px={3} py={1} bg="green.50" borderRadius="md">
              <Text fontSize="sm" color="green.700">
                <strong>{company?.knowledge_stats?.document_count || 0}</strong> {t('enterprise.documents')}
              </Text>
            </Box>
            <Box px={3} py={1} bg="blue.50" borderRadius="md">
              <Text fontSize="sm" color="blue.700">
                <strong>{company?.knowledge_stats?.chunk_count || 0}</strong> {t('enterprise.indexedChunks')}
              </Text>
            </Box>
          </HStack>
        </Flex>
      </Card>
      
      {/* Tabs for Knowledge Base and Team Management */}
      <Tabs colorScheme="brand" variant="enclosed">
        <TabList>
          <Tab><HStack><FaFileAlt /><Text>{t('enterprise.companyKnowledgeBase')}</Text></HStack></Tab>
          <Tab><HStack><FaUsers /><Text>{t('enterprise.teamManagement')}</Text></HStack></Tab>
        </TabList>
        
        <TabPanels>
          {/* Knowledge Base Tab */}
          <TabPanel px={0}>
            <Card bg={cardBg}>
              <Flex direction="column" mb={4}>
                <HStack mb={2}>
                  <Icon as={FaUserShield} color="green.500" />
                  <Text fontSize="lg" fontWeight="bold" color={textColorPrimary}>
                    {t('enterprise.companyWideKnowledgeBase')}
                  </Text>
                  <Badge colorScheme="green">{t('enterprise.tier2HighestPriority')}</Badge>
                </HStack>
                <Text color={textColorSecondary} fontSize="sm">
                  {t('enterprise.knowledgeBaseDesc')}
                </Text>
              </Flex>
              
              {/* Upload Area */}
              <Box
                border="2px dashed"
                borderColor="green.300"
                borderRadius="xl"
                p={6}
                textAlign="center"
                mb={4}
                bg="green.50"
                _hover={{ borderColor: 'green.500' }}
              >
                <Icon as={FaUpload} fontSize="2xl" color="green.400" mb={3} />
                <Text mb={2} color="green.700" fontWeight="500">
                  {t('enterprise.uploadCompanyDocs')}
                </Text>
                <Text fontSize="xs" color="green.600" mb={3}>
                  {t('enterprise.uploadCompanyDocsHint')}
                </Text>
                <Input
                  type="file"
                  id="company-doc-upload"
                  accept={ALLOWED_EXTENSIONS.join(',')}
                  onChange={handleFileUpload}
                  display="none"
                />
                <Button
                  colorScheme="green"
                  size="sm"
                  onClick={() => document.getElementById('company-doc-upload').click()}
                  isLoading={uploading}
                  loadingText={t('enterprise.processing')}
                >
                  {t('enterprise.chooseFile')}
                </Button>
              </Box>
              
              {/* Document List */}
              {documents.length > 0 ? (
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
                        <Icon as={FaFileAlt} color="green.500" />
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
                <Box textAlign="center" py={6}>
                  <Text color="gray.500" fontSize="sm">
                    {t('enterprise.noCompanyDocs')}
                  </Text>
                </Box>
              )}
            </Card>
          </TabPanel>
          
          {/* Team Management Tab */}
          <TabPanel px={0}>
            <Card bg={cardBg}>
              <Flex direction="column" mb={4}>
                <HStack mb={2}>
                  <Icon as={FaUsers} color="brand.500" />
                  <Text fontSize="lg" fontWeight="bold" color={textColorPrimary}>
                    {t('enterprise.teamMembersTitle')}
                  </Text>
                </HStack>
                <Text color={textColorSecondary} fontSize="sm">
                  {t('enterprise.teamMembersDesc')}
                </Text>
              </Flex>
              
              {/* Team Invitation Section */}
              <InviteTeamMemberSection 
                user={user}
                onInviteSent={async () => {
                  // Reload members after invitation
                  const API = getApiUrl();
                  const membersRes = await axios.get(`${API}/company/members`, {
                    headers: { 'X-User-ID': user.id }
                  });
                  setMembers(membersRes.data);
                }}
                toast={toast}
                t={t}
              />
              
              {/* Members Table */}
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>{t('enterprise.member', 'Member')}</Th>
                    <Th>{t('enterprise.email')}</Th>
                    <Th>{t('enterprise.companyRole')}</Th>
                    <Th>{t('common.actions', 'Actions')}</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {members.map((member) => (
                    <Tr key={member.id}>
                      <Td>
                        <HStack>
                          <Avatar size="sm" name={member.full_name} />
                          <Text fontWeight="500">{member.full_name}</Text>
                          {member.id === user?.id && (
                            <Badge colorScheme="blue" size="sm">{t('enterprise.you')}</Badge>
                          )}
                        </HStack>
                      </Td>
                      <Td>{member.email}</Td>
                      <Td>
                        {member.id !== user?.id ? (
                          <Select
                            size="sm"
                            value={member.company_role}
                            onChange={(e) => handleUpdateMemberRole(member.id, e.target.value)}
                            w="120px"
                          >
                            <option value="admin">{t('enterprise.admin')}</option>
                            <option value="member">{t('enterprise.member')}</option>
                          </Select>
                        ) : (
                          <Badge colorScheme={member.company_role === 'admin' ? 'blue' : 'gray'}>
                            {member.company_role === 'admin' ? t('enterprise.admin') : t('enterprise.member')}
                          </Badge>
                        )}
                      </Td>
                      <Td>
                        {member.id !== user?.id && (
                          <Button
                            size="xs"
                            colorScheme="red"
                            variant="ghost"
                            onClick={() => handleRemoveMember(member.id)}
                          >
                            {t('enterprise.removeBtn')}
                          </Button>
                        )}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
      
      {/* Leave Company Section */}
      <Card bg={cardBg} mt={6} borderColor="red.200" borderWidth="1px">
        <HStack justify="space-between">
          <Box>
            <Text fontWeight="600" color="red.500">{t('enterprise.dangerZone')}</Text>
            <Text fontSize="sm" color={textColorSecondary}>
              {t('enterprise.leaveCompanyWarning')}
            </Text>
          </Box>
          <Button
            colorScheme="red"
            variant="outline"
            size="sm"
            leftIcon={<FaSignOutAlt />}
            onClick={onLeaveOpen}
          >
            {t('enterprise.leaveCompany')}
          </Button>
        </HStack>
      </Card>
      
      {/* Leave Company Modal */}
      <Modal isOpen={isLeaveOpen} onClose={onLeaveClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{t('enterprise.leaveCompany')}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>{t('enterprise.confirmLeave')} <strong>{company?.name}</strong>?</Text>
            <Text color="gray.500" mt={2} fontSize="sm">
              {t('enterprise.adminLeaveWarning')}
            </Text>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onLeaveClose}>{t('enterprise.cancel')}</Button>
            <Button colorScheme="red" onClick={handleLeaveCompany}>{t('enterprise.leave')}</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
