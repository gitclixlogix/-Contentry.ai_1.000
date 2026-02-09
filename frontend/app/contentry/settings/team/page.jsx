'use client';

import { useState, useEffect, useCallback } from 'react';
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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
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
  Select,
  Textarea,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Avatar,
  Flex,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Tooltip,
  InputGroup,
  InputLeftElement,
} from '@chakra-ui/react';
import {
  FaPlus,
  FaUsers,
  FaUserPlus,
  FaUserCog,
  FaEnvelope,
  FaTrash,
  FaEllipsisV,
  FaCheckCircle,
  FaClock,
  FaShieldAlt,
  FaEdit,
  FaCopy,
} from 'react-icons/fa';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { UserInfoCell, StatusBadge, DeleteConfirmationModal } from '@/components/shared';

export default function TeamManagementPage() {
  const { t } = useTranslation();
  const { user, isLoading: authLoading, isHydrated } = useAuth();
  const toast = useToast();
  
  // Role configuration with translations
  const ROLES = {
    creator: {
      label: t('settings.teamPage.roles.creator'),
      description: t('settings.teamPage.roles.creatorDesc'),
      color: 'blue',
      icon: FaEdit,
    },
    manager: {
      label: t('settings.teamPage.roles.manager'),
      description: t('settings.teamPage.roles.managerDesc'),
      color: 'green',
      icon: FaUserCog,
    },
    admin: {
      label: t('settings.teamPage.roles.admin'),
      description: t('settings.teamPage.roles.adminDesc'),
      color: 'blue',
      icon: FaShieldAlt,
    },
    user: {
      label: t('settings.teamPage.roles.user'),
      description: t('settings.teamPage.roles.userDesc'),
      color: 'gray',
      icon: FaUsers,
    },
  };
  
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userRole, setUserRole] = useState('user');
  const [userPermissions, setUserPermissions] = useState({});
  
  // Invite modal
  const { isOpen: isInviteOpen, onOpen: onInviteOpen, onClose: onInviteClose } = useDisclosure();
  const [inviteData, setInviteData] = useState({ email: '', role: 'creator', message: '' });
  const [inviting, setInviting] = useState(false);
  const [lastInviteLink, setLastInviteLink] = useState(null);
  
  // Role change modal
  const { isOpen: isRoleOpen, onOpen: onRoleOpen, onClose: onRoleClose } = useDisclosure();
  const [selectedMember, setSelectedMember] = useState(null);
  const [newRole, setNewRole] = useState('');
  const [changingRole, setChangingRole] = useState(false);
  
  // Remove member confirmation modal
  const { isOpen: isRemoveOpen, onOpen: onRemoveOpen, onClose: onRemoveClose } = useDisclosure();
  const [memberToRemove, setMemberToRemove] = useState(null);
  const [removing, setRemoving] = useState(false);
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const tableBg = useColorModeValue('white', 'gray.800');
  
  // Load user permissions
  const loadUserPermissions = useCallback(async () => {
    if (!user?.id) return;
    
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/approval/user-permissions`, {
        headers: { 'X-User-ID': user.id }
      });
      setUserRole(response.data.role);
      setUserPermissions(response.data.permissions);
    } catch (error) {
      console.error('Failed to load permissions:', error);
    }
  }, [user?.id]);
  
  // Load team members
  const loadMembers = useCallback(async () => {
    if (!user?.id) return;
    
    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/team-management/members`, {
        headers: { 'X-User-ID': user.id }
      });
      setMembers(response.data.members || []);
    } catch (error) {
      console.error('Failed to load members:', error);
      toast({
        title: t('settings.teamPage.toasts.loadFailed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  }, [user?.id, toast, t]);
  
  useEffect(() => {
    if (user?.id) {
      loadUserPermissions();
      loadMembers();
    }
  }, [user?.id, loadUserPermissions, loadMembers]);
  
  // Send invitation
  const handleInvite = async () => {
    if (!inviteData.email) {
      toast({
        title: t('settings.teamPage.toasts.emailRequired'),
        description: t('settings.teamPage.toasts.emailRequiredDesc'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setInviting(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/team-management/invite`, inviteData, {
        headers: { 'X-User-ID': user.id }
      });
      
      setLastInviteLink(response.data.invitation_link);
      
      toast({
        title: t('settings.teamPage.toasts.invitationSent'),
        description: response.data.email_sent 
          ? t('settings.teamPage.toasts.invitationSentEmail', { email: inviteData.email })
          : t('settings.teamPage.toasts.invitationSentLink'),
        status: 'success',
        duration: 5000,
      });
      
      loadMembers();
    } catch (error) {
      toast({
        title: t('settings.teamPage.toasts.invitationFailed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setInviting(false);
    }
  };
  
  // Copy invitation link
  const copyInviteLink = () => {
    if (lastInviteLink) {
      navigator.clipboard.writeText(lastInviteLink);
      toast({
        title: t('settings.teamPage.toasts.linkCopied'),
        description: t('settings.teamPage.toasts.linkCopiedDesc'),
        status: 'success',
        duration: 2000,
      });
    }
  };
  
  // Change member role
  const handleRoleChange = async () => {
    if (!selectedMember || !newRole) return;
    
    setChangingRole(true);
    try {
      const API = getApiUrl();
      await axios.put(
        `${API}/team-management/members/${selectedMember.id}/role`,
        { role: newRole },
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: t('settings.teamPage.toasts.roleUpdated'),
        description: t('settings.teamPage.toasts.roleUpdatedDesc', { 
          name: selectedMember.full_name, 
          role: ROLES[newRole]?.label || newRole 
        }),
        status: 'success',
        duration: 3000,
      });
      
      onRoleClose();
      loadMembers();
    } catch (error) {
      toast({
        title: t('settings.teamPage.toasts.roleUpdateFailed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setChangingRole(false);
    }
  };
  
  // Remove member
  const openRemoveModal = (member) => {
    setMemberToRemove(member);
    onRemoveOpen();
  };
  
  const handleRemoveMember = async () => {
    if (!memberToRemove) return;
    
    setRemoving(true);
    try {
      const API = getApiUrl();
      await axios.delete(
        `${API}/team-management/members/${memberToRemove.id}`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: t('settings.teamPage.toasts.memberRemoved'),
        status: 'success',
        duration: 3000,
      });
      
      loadMembers();
      onRemoveClose();
    } catch (error) {
      toast({
        title: t('settings.teamPage.toasts.memberRemoveFailed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setRemoving(false);
      setMemberToRemove(null);
    }
  };
  
  // Cancel invitation
  const handleCancelInvitation = async (invitationId) => {
    try {
      const API = getApiUrl();
      await axios.delete(
        `${API}/team-management/invitation/${invitationId}`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: t('settings.teamPage.toasts.invitationCancelled'),
        status: 'success',
        duration: 3000,
      });
      
      loadMembers();
    } catch (error) {
      toast({
        title: t('settings.teamPage.toasts.invitationFailed'),
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };
  
  // Open role change modal
  const openRoleModal = (member) => {
    setSelectedMember(member);
    setNewRole(member.role);
    onRoleOpen();
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

  const canManageTeam = userRole === 'admin' || userRole === 'manager';

  return (
    <Box minH="100vh" bg={bgColor} p={{ base: 4, md: 8 }}>
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        {/* Header */}
        <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
          <Box>
            <HStack spacing={2}>
              <Icon as={FaUsers} boxSize={6} color="brand.500" />
              <Heading size="lg" color={textColor}>{t('settings.teamPage.title')}</Heading>
            </HStack>
            <Text color={textColorSecondary} mt={1}>
              {t('settings.teamPage.subtitle')}
            </Text>
          </Box>
          {canManageTeam && (
            <Button
              leftIcon={<FaUserPlus />}
              colorScheme="brand"
              onClick={onInviteOpen}
            >
              {t('settings.teamPage.inviteButton')}
            </Button>
          )}
        </Flex>

        {/* Your Role Card */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <HStack spacing={4}>
              <Avatar
                size="md"
                name={user.full_name}
                bg={ROLES[userRole]?.color + '.500' || 'gray.500'}
                color="white"
              />
              <Box flex={1}>
                <Text fontWeight="600" color={textColor}>{user.full_name}</Text>
                <Text fontSize="sm" color={textColorSecondary}>{user.email}</Text>
              </Box>
              <Badge colorScheme={ROLES[userRole]?.color || 'gray'} fontSize="sm" px={3} py={1}>
                <HStack spacing={1}>
                  <Icon as={ROLES[userRole]?.icon || FaUsers} />
                  <Text>{ROLES[userRole]?.label || userRole}</Text>
                </HStack>
              </Badge>
            </HStack>
          </CardBody>
        </Card>

        {/* Role Permissions Info */}
        <Alert status="info" borderRadius="lg" bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <AlertIcon />
          <Box>
            <AlertTitle>{t('settings.teamPage.roleModal.title')}</AlertTitle>
            <AlertDescription>
              <Text fontSize="sm" mt={2}>
                <strong>{t('settings.teamPage.roles.creator')}:</strong> {t('settings.teamPage.roles.creatorDesc')}
              </Text>
              <Text fontSize="sm">
                <strong>{t('settings.teamPage.roles.manager')}:</strong> {t('settings.teamPage.roles.managerDesc')}
              </Text>
              <Text fontSize="sm">
                <strong>{t('settings.teamPage.roles.admin')}:</strong> {t('settings.teamPage.roles.adminDesc')}
              </Text>
            </AlertDescription>
          </Box>
        </Alert>

        {/* Team Members Table */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md" color={textColor}>Team Members</Heading>
          </CardHeader>
          <CardBody pt={0}>
            {loading ? (
              <Box textAlign="center" py={8}>
                <Spinner size="lg" />
              </Box>
            ) : members.length === 0 ? (
              <Box textAlign="center" py={8} color={textColorSecondary}>
                <Icon as={FaUsers} boxSize={12} mb={4} opacity={0.5} />
                <Text>No team members yet</Text>
                <Text fontSize="sm">Invite your first team member to get started</Text>
              </Box>
            ) : (
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Member</Th>
                    <Th>Role</Th>
                    <Th>Status</Th>
                    <Th>Joined</Th>
                    {canManageTeam && <Th width="50px">Actions</Th>}
                  </Tr>
                </Thead>
                <Tbody>
                  {members.map((member) => (
                    <Tr key={member.id}>
                      <Td>
                        <HStack>
                          <Avatar
                            size="sm"
                            name={member.full_name}
                            bg={member.status === 'invited' ? 'gray.400' : ROLES[member.role]?.color + '.500'}
                          />
                          <Box>
                            <Text fontWeight="500" color={textColor}>
                              {member.full_name}
                              {member.id === user.id && (
                                <Badge ml={2} colorScheme="blue" fontSize="xs">You</Badge>
                              )}
                            </Text>
                            <Text fontSize="sm" color={textColorSecondary}>{member.email}</Text>
                          </Box>
                        </HStack>
                      </Td>
                      <Td>
                        {/* Direct role dropdown for active members - easier role management */}
                        {canManageTeam && member.status === 'active' && member.id !== user.id && userRole === 'admin' ? (
                          <Select
                            size="sm"
                            width="130px"
                            value={member.role}
                            onChange={async (e) => {
                              const newRole = e.target.value;
                              if (newRole !== member.role) {
                                try {
                                  const API = getApiUrl();
                                  await axios.put(
                                    `${API}/team-management/members/${member.id}/role`,
                                    { role: newRole },
                                    { headers: { 'X-User-ID': user.id } }
                                  );
                                  toast({
                                    title: 'Role updated',
                                    description: `${member.full_name}'s role has been changed to ${ROLES[newRole]?.label || newRole}`,
                                    status: 'success',
                                    duration: 3000,
                                  });
                                  loadMembers();
                                } catch (error) {
                                  toast({
                                    title: 'Failed to update role',
                                    description: error.response?.data?.detail || error.message,
                                    status: 'error',
                                    duration: 5000,
                                  });
                                }
                              }
                            }}
                            colorScheme={ROLES[member.role]?.color || 'gray'}
                            borderColor={ROLES[member.role]?.color ? `${ROLES[member.role].color}.300` : 'gray.300'}
                            _hover={{ borderColor: ROLES[member.role]?.color ? `${ROLES[member.role].color}.400` : 'gray.400' }}
                          >
                            <option value="creator">Creator</option>
                            <option value="manager">Manager</option>
                            <option value="admin">Admin</option>
                          </Select>
                        ) : (
                          <Badge colorScheme={ROLES[member.role]?.color || 'gray'}>
                            {ROLES[member.role]?.label || member.role}
                          </Badge>
                        )}
                      </Td>
                      <Td>
                        <HStack>
                          <Icon
                            as={member.status === 'active' ? FaCheckCircle : FaClock}
                            color={member.status === 'active' ? 'green.500' : 'orange.500'}
                          />
                          <Text fontSize="sm" textTransform="capitalize">
                            {member.status}
                          </Text>
                        </HStack>
                      </Td>
                      <Td>
                        <Text fontSize="sm" color={textColorSecondary}>
                          {member.joined_at 
                            ? new Date(member.joined_at).toLocaleDateString()
                            : member.invited_at 
                            ? `Invited ${new Date(member.invited_at).toLocaleDateString()}`
                            : '-'
                          }
                        </Text>
                      </Td>
                      {canManageTeam && (
                        <Td>
                          {member.id !== user.id && (
                            <Menu>
                              <MenuButton
                                as={IconButton}
                                icon={<FaEllipsisV />}
                                variant="ghost"
                                size="sm"
                              />
                              <MenuList>
                                {member.status === 'active' ? (
                                  <>
                                    <MenuItem
                                      icon={<FaUserCog />}
                                      onClick={() => openRoleModal(member)}
                                      isDisabled={userRole !== 'admin'}
                                    >
                                      Change Role
                                    </MenuItem>
                                    <MenuItem
                                      icon={<FaTrash />}
                                      color="red.500"
                                      onClick={() => openRemoveModal(member)}
                                      isDisabled={userRole !== 'admin'}
                                    >
                                      Remove from Team
                                    </MenuItem>
                                  </>
                                ) : (
                                  <MenuItem
                                    icon={<FaTrash />}
                                    color="red.500"
                                    onClick={() => handleCancelInvitation(member.id)}
                                  >
                                    Cancel Invitation
                                  </MenuItem>
                                )}
                              </MenuList>
                            </Menu>
                          )}
                        </Td>
                      )}
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </CardBody>
        </Card>

        {/* Invite Modal */}
        <Modal isOpen={isInviteOpen} onClose={onInviteClose} size="lg">
          <ModalOverlay />
          <ModalContent bg={cardBg}>
            <ModalHeader color={textColor}>Invite Team Member</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Email Address</FormLabel>
                  <InputGroup>
                    <InputLeftElement>
                      <Icon as={FaEnvelope} color="gray.400" />
                    </InputLeftElement>
                    <Input
                      type="email"
                      placeholder="colleague@company.com"
                      value={inviteData.email}
                      onChange={(e) => setInviteData(prev => ({ ...prev, email: e.target.value }))}
                    />
                  </InputGroup>
                </FormControl>
                
                <FormControl isRequired>
                  <FormLabel>Role</FormLabel>
                  <Select
                    value={inviteData.role}
                    onChange={(e) => setInviteData(prev => ({ ...prev, role: e.target.value }))}
                  >
                    <option value="creator">Creator - Can create content, needs approval</option>
                    <option value="manager">Manager - Can approve content and publish</option>
                    {userRole === 'admin' && (
                      <option value="admin">Admin - Full access including team management</option>
                    )}
                  </Select>
                  <FormHelperText>
                    {ROLES[inviteData.role]?.description}
                  </FormHelperText>
                </FormControl>
                
                <FormControl>
                  <FormLabel>Personal Message (Optional)</FormLabel>
                  <Textarea
                    placeholder="Add a personal message to your invitation..."
                    value={inviteData.message}
                    onChange={(e) => setInviteData(prev => ({ ...prev, message: e.target.value }))}
                    rows={3}
                  />
                </FormControl>
                
                {lastInviteLink && (
                  <Alert status="success" borderRadius="md">
                    <AlertIcon />
                    <Box flex={1}>
                      <Text fontWeight="500">Invitation link created!</Text>
                      <Text fontSize="sm" noOfLines={1}>{lastInviteLink}</Text>
                    </Box>
                    <IconButton
                      icon={<FaCopy />}
                      size="sm"
                      onClick={copyInviteLink}
                      aria-label="Copy link"
                    />
                  </Alert>
                )}
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={() => { onInviteClose(); setLastInviteLink(null); setInviteData({ email: '', role: 'creator', message: '' }); }}>
                {lastInviteLink ? 'Done' : 'Cancel'}
              </Button>
              {!lastInviteLink && (
                <Button colorScheme="brand" onClick={handleInvite} isLoading={inviting}>
                  Send Invitation
                </Button>
              )}
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Role Change Modal */}
        <Modal isOpen={isRoleOpen} onClose={onRoleClose}>
          <ModalOverlay />
          <ModalContent bg={cardBg}>
            <ModalHeader color={textColor}>Change Role</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {selectedMember && (
                <VStack spacing={4} align="stretch">
                  <HStack>
                    <Avatar size="sm" name={selectedMember.full_name} />
                    <Box>
                      <Text fontWeight="500">{selectedMember.full_name}</Text>
                      <Text fontSize="sm" color={textColorSecondary}>{selectedMember.email}</Text>
                    </Box>
                  </HStack>
                  
                  <FormControl>
                    <FormLabel>New Role</FormLabel>
                    <Select
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value)}
                    >
                      <option value="user">User - Standard access</option>
                      <option value="creator">Creator - Needs approval</option>
                      <option value="manager">Manager - Can approve</option>
                      <option value="admin">Admin - Full access</option>
                    </Select>
                  </FormControl>
                </VStack>
              )}
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onRoleClose}>Cancel</Button>
              <Button colorScheme="brand" onClick={handleRoleChange} isLoading={changingRole}>
                Update Role
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Remove Member Confirmation Modal */}
        <DeleteConfirmationModal
          isOpen={isRemoveOpen}
          onClose={() => { onRemoveClose(); setMemberToRemove(null); }}
          onConfirm={handleRemoveMember}
          itemName={memberToRemove?.full_name || 'this member'}
          isLoading={removing}
        />
      </VStack>
    </Box>
  );
}
