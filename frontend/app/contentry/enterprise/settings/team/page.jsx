'use client';

/**
 * Consolidated Team Management Page
 * 
 * Combines user administration and role management into a single interface:
 * - Add/invite new users with email invitation
 * - Edit user details and roles
 * - Remove users from the enterprise
 * - Manage approval workflow roles (Creator, Manager, Admin)
 */

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
  Select,
  Alert,
  AlertIcon,
  AlertDescription,
  Avatar,
  Flex,
  Divider,
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
  IconButton,
  Tooltip,
  InputGroup,
  InputLeftElement,
  Checkbox,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
} from '@chakra-ui/react';
import {
  FaUsers,
  FaUserPlus,
  FaUserCog,
  FaEdit,
  FaShieldAlt,
  FaCheckCircle,
  FaTrash,
  FaSearch,
  FaUserMinus,
  FaCopy,
  FaEnvelope,
  FaInfoCircle,
  FaPaperPlane,
} from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useTranslation } from 'react-i18next';
import { UserInfoCell } from '@/components/shared';

// Role configuration for the approval workflow
const WORKFLOW_ROLES = {
  creator: {
    label: 'Creator',
    value: 'creator',
    description: 'Can create content and submit for approval. Cannot publish directly.',
    color: 'purple',
    icon: FaEdit,
  },
  manager: {
    label: 'Manager',
    value: 'manager',
    description: 'Can approve/reject content from Creators and publish.',
    color: 'green',
    icon: FaUserCog,
  },
  admin: {
    label: 'Admin',
    value: 'enterprise_admin',
    description: 'Full access including team management and role assignments.',
    color: 'blue',
    icon: FaShieldAlt,
  },
};

export default function TeamManagementPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const toast = useToast();
  
  const [members, setMembers] = useState([]);
  const [filteredMembers, setFilteredMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [updatingRole, setUpdatingRole] = useState(null);
  const [tempPassword, setTempPassword] = useState(null);
  const [sendInviteEmail, setSendInviteEmail] = useState(true);
  
  // Modal states
  const { isOpen: isAddOpen, onOpen: onAddOpen, onClose: onAddClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure();
  
  // Form state for adding new user
  const [newUser, setNewUser] = useState({
    full_name: '',
    email: '',
    department: '',
    job_title: '',
    role: 'creator',
    password: ''
  });
  
  // Theme colors
  const cardBg = useColorModeValue('white', 'gray.800');
  const modalBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const tableHoverBg = useColorModeValue('gray.50', 'gray.700');
  const roleBoxBg = useColorModeValue('gray.50', 'gray.700');
  const infoBg = useColorModeValue('blue.50', 'blue.900');

  // Check if current user can manage team
  const canManageTeam = user?.role === 'admin' || 
                        user?.role === 'Administrator' || 
                        user?.enterprise_role === 'enterprise_admin' ||
                        user?.enterprise_role === 'admin';

  // Load team members
  const loadMembers = useCallback(async () => {
    if (!user?.id || !user?.enterprise_id) return;
    
    try {
      setLoading(true);
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/enterprises/${user.enterprise_id}/users`,
        { headers: { 'X-User-ID': user.id } }
      );
      setMembers(response.data.users || []);
    } catch (error) {
      console.error('Failed to load team members:', error);
      if (error.response?.status !== 404) {
        toast({
          title: 'Failed to load team',
          description: error.response?.data?.detail || error.message,
          status: 'error',
          duration: 5000,
        });
      }
    } finally {
      setLoading(false);
    }
  }, [user?.id, user?.enterprise_id, toast]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  // Filter members based on search
  useEffect(() => {
    if (searchQuery) {
      setFilteredMembers(members.filter(m => 
        m.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.department?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.job_title?.toLowerCase().includes(searchQuery.toLowerCase())
      ));
    } else {
      setFilteredMembers(members);
    }
  }, [searchQuery, members]);

  // Handle adding new user
  const handleAddUser = async () => {
    if (!newUser.full_name || !newUser.email) {
      toast({
        title: 'Missing fields',
        description: 'Name and email are required',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(
        `${API}/enterprises/${user.enterprise_id}/users`,
        {
          ...newUser,
          send_invite_email: sendInviteEmail
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      const successMessage = sendInviteEmail 
        ? `Invitation email sent to ${newUser.email}`
        : response.data.message;
      
      toast({
        title: response.data.is_new ? 'User created' : 'User added',
        description: successMessage,
        status: 'success',
        duration: 5000,
      });

      // Store temp password if generated (only shown when not sending invite email)
      if (response.data.temp_password && !sendInviteEmail) {
        setTempPassword(response.data.temp_password);
      } else {
        // Reset form and close modal
        setNewUser({ full_name: '', email: '', department: '', job_title: '', role: 'creator', password: '' });
        onAddClose();
      }

      loadMembers();
    } catch (error) {
      toast({
        title: 'Error adding user',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle role change
  const handleRoleChange = async (memberId, newRole) => {
    if (!canManageTeam) return;
    
    const member = members.find(m => m.id === memberId);
    if (!member) return;
    
    try {
      setUpdatingRole(memberId);
      const API = getApiUrl();
      
      await axios.put(
        `${API}/enterprises/${user.enterprise_id}/users/${memberId}/role`,
        {
          enterprise_role: newRole,
          department: member.department,
          job_title: member.job_title
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      const roleLabel = Object.values(WORKFLOW_ROLES).find(r => r.value === newRole)?.label || newRole;
      toast({
        title: `Role updated`,
        description: `${member.full_name} is now a ${roleLabel}`,
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
    } finally {
      setUpdatingRole(null);
    }
  };

  // Handle updating user details
  const handleUpdateUser = async () => {
    if (!selectedUser) return;

    setIsSubmitting(true);
    try {
      const API = getApiUrl();
      await axios.put(
        `${API}/enterprises/${user.enterprise_id}/users/${selectedUser.id}/role`,
        {
          enterprise_role: selectedUser.enterprise_role,
          department: selectedUser.department,
          job_title: selectedUser.job_title,
          reports_to: selectedUser.reports_to || null  // Include manager assignment
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'User updated',
        description: selectedUser.reports_to 
          ? 'User details and manager assignment saved'
          : 'User details have been saved',
        status: 'success',
        duration: 3000,
      });

      loadMembers();
      onEditClose();
    } catch (error) {
      toast({
        title: 'Error updating user',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle deleting user
  const handleDeleteUser = async (deleteAccount = false) => {
    if (!selectedUser) return;

    setIsSubmitting(true);
    try {
      const API = getApiUrl();
      await axios.delete(
        `${API}/enterprises/${user.enterprise_id}/users/${selectedUser.id}?delete_account=${deleteAccount}`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: deleteAccount ? 'User deleted' : 'User removed',
        description: deleteAccount 
          ? `${selectedUser.full_name}'s account has been permanently deleted`
          : `${selectedUser.full_name} has been removed from the team`,
        status: 'success',
        duration: 5000,
      });

      loadMembers();
      onDeleteClose();
      setSelectedUser(null);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied!',
      description: 'Password copied to clipboard',
      status: 'success',
      duration: 2000,
    });
  };

  const getRoleDisplay = (member) => {
    const role = member.enterprise_role || member.role || 'user';
    if (role === 'enterprise_admin' || role === 'admin') {
      return { label: 'Admin', color: 'blue', value: 'enterprise_admin' };
    } else if (role === 'manager') {
      return { label: 'Manager', color: 'green', value: 'manager' };
    } else if (role === 'creator') {
      return { label: 'Creator', color: 'purple', value: 'creator' };
    }
    return { label: 'User', color: 'gray', value: 'user' };
  };

  const closeAddModal = () => {
    onAddClose();
    setTempPassword(null);
    setNewUser({ full_name: '', email: '', department: '', job_title: '', role: 'creator', password: '' });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minH="400px">
        <Spinner size="xl" color="brand.500" />
      </Box>
    );
  }

  return (
    <Box>
      <VStack align="stretch" spacing={6}>
        {/* Page Header */}
        <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
          <Box>
            <HStack mb={2}>
              <Icon as={FaUsers} boxSize={6} color="brand.500" />
              <Heading size="lg" color={textColor}>
                {t('settings.teamManagement.title', 'Team Management')}
              </Heading>
              <Badge colorScheme="blue" fontSize="md">{members.length} members</Badge>
            </HStack>
            <Text color={textColorSecondary}>
              Manage team members and assign roles for the content approval workflow
            </Text>
          </Box>
          {canManageTeam && (
            <Button
              colorScheme="brand"
              leftIcon={<FaUserPlus />}
              onClick={onAddOpen}
              data-testid="add-user-btn"
            >
              Add Team Member
            </Button>
          )}
        </Flex>

        {/* Role Explanation Card */}
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardHeader pb={2}>
            <HStack>
              <Icon as={FaInfoCircle} color="blue.500" />
              <Text fontWeight="600" color={textColor}>Role Permissions</Text>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
              {Object.entries(WORKFLOW_ROLES).map(([key, role]) => (
                <Box key={key} p={3} borderRadius="md" bg={roleBoxBg} borderWidth="1px" borderColor={borderColor}>
                  <HStack mb={2}>
                    <Icon as={role.icon} color={`${role.color}.500`} />
                    <Badge colorScheme={role.color} fontSize="sm">{role.label}</Badge>
                  </HStack>
                  <Text fontSize="sm" color={textColorSecondary}>
                    {role.description}
                  </Text>
                </Box>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* Search */}
        <InputGroup maxW="400px">
          <InputLeftElement>
            <FaSearch color="gray" />
          </InputLeftElement>
          <Input
            placeholder="Search by name, email, department..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            bg={cardBg}
          />
        </InputGroup>

        {/* Team Members Table */}
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardBody p={0}>
            {filteredMembers.length === 0 ? (
              <Flex justify="center" py={10}>
                <VStack spacing={3}>
                  <Icon as={FaUsers} boxSize={10} color="gray.400" />
                  <Text color={textColorSecondary}>
                    {searchQuery ? 'No members match your search' : 'No team members yet'}
                  </Text>
                  {!searchQuery && canManageTeam && (
                    <Button size="sm" colorScheme="brand" leftIcon={<FaUserPlus />} onClick={onAddOpen}>
                      Add your first team member
                    </Button>
                  )}
                </VStack>
              </Flex>
            ) : (
              <Box overflowX="auto">
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th borderColor={borderColor}>User</Th>
                      <Th borderColor={borderColor}>Department</Th>
                      <Th borderColor={borderColor}>Job Title</Th>
                      <Th borderColor={borderColor} width="180px">Role</Th>
                      <Th borderColor={borderColor}>Reports To</Th>
                      <Th borderColor={borderColor}>Joined</Th>
                      <Th borderColor={borderColor} width="100px">Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredMembers.map((member) => {
                      const roleInfo = getRoleDisplay(member);
                      return (
                        <Tr key={member.id} _hover={{ bg: tableHoverBg }}>
                          <Td borderColor={borderColor}>
                            <HStack spacing={3}>
                              <Avatar
                                size="sm"
                                name={member.full_name}
                                src={member.profile_picture}
                                bg={`${roleInfo.color}.500`}
                              />
                              <VStack align="start" spacing={0}>
                                <HStack>
                                  <Text fontWeight="500" color={textColor}>
                                    {member.full_name}
                                  </Text>
                                  {member.id === user?.id && (
                                    <Badge colorScheme="green" fontSize="xs">You</Badge>
                                  )}
                                </HStack>
                                <Text fontSize="xs" color={textColorSecondary}>
                                  {member.email}
                                </Text>
                              </VStack>
                            </HStack>
                          </Td>
                          <Td borderColor={borderColor}>
                            <Text fontSize="sm" color={textColorSecondary}>
                              {member.department || '-'}
                            </Text>
                          </Td>
                          <Td borderColor={borderColor}>
                            <Text fontSize="sm" color={textColorSecondary}>
                              {member.job_title || '-'}
                            </Text>
                          </Td>
                          <Td borderColor={borderColor}>
                            {canManageTeam && member.id !== user?.id ? (
                              <Select
                                size="sm"
                                width="150px"
                                value={roleInfo.value}
                                onChange={(e) => handleRoleChange(member.id, e.target.value)}
                                isDisabled={updatingRole === member.id}
                                borderColor={`${roleInfo.color}.300`}
                                fontWeight="500"
                              >
                                <option value="creator">Creator</option>
                                <option value="manager">Manager</option>
                                <option value="enterprise_admin">Admin</option>
                              </Select>
                            ) : (
                              <Badge colorScheme={roleInfo.color} fontSize="sm" px={3} py={1}>
                                {roleInfo.label}
                              </Badge>
                            )}
                          </Td>
                          <Td borderColor={borderColor}>
                            {(() => {
                              // Find manager name from reports_to
                              const manager = member.reports_to 
                                ? members.find(m => m.id === member.reports_to)
                                : null;
                              return manager ? (
                                <HStack spacing={2}>
                                  <Avatar size="xs" name={manager.full_name} />
                                  <Text fontSize="sm" color={textColorSecondary}>
                                    {manager.full_name}
                                  </Text>
                                </HStack>
                              ) : (
                                <Text fontSize="sm" color={textColorSecondary}>
                                  {['manager', 'enterprise_admin'].includes(member.enterprise_role) ? '-' : 'Not assigned'}
                                </Text>
                              );
                            })()}
                          </Td>
                          <Td borderColor={borderColor}>
                            <Text fontSize="sm" color={textColorSecondary}>
                              {member.created_at ? new Date(member.created_at).toLocaleDateString() : 'N/A'}
                            </Text>
                          </Td>
                          <Td borderColor={borderColor}>
                            <HStack spacing={1}>
                              <Tooltip label="Edit details">
                                <IconButton
                                  icon={<FaEdit />}
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => {
                                    setSelectedUser({...member});
                                    onEditOpen();
                                  }}
                                  isDisabled={member.id === user?.id}
                                  aria-label="Edit user"
                                />
                              </Tooltip>
                              <Tooltip label={member.id === user?.id ? "You cannot remove yourself" : "Remove user"}>
                                <IconButton
                                  icon={<FaTrash />}
                                  size="sm"
                                  variant="ghost"
                                  colorScheme="red"
                                  onClick={() => {
                                    setSelectedUser(member);
                                    onDeleteOpen();
                                  }}
                                  isDisabled={member.id === user?.id}
                                  aria-label="Remove user"
                                />
                              </Tooltip>
                            </HStack>
                          </Td>
                        </Tr>
                      );
                    })}
                  </Tbody>
                </Table>
              </Box>
            )}
          </CardBody>
        </Card>

        {/* Approval Workflow Info */}
        <Card bg={infoBg} borderWidth="1px" borderColor="blue.200">
          <CardBody>
            <HStack align="flex-start" spacing={4}>
              <Icon as={FaCheckCircle} color="blue.500" boxSize={6} mt={1} />
              <Box>
                <Text fontWeight="600" color={textColor} mb={2}>
                  How the Approval Workflow Works
                </Text>
                <VStack align="stretch" spacing={2} fontSize="sm" color={textColorSecondary}>
                  <Text>
                    <strong>1.</strong> <Badge colorScheme="purple" size="sm">Creators</Badge> write content and submit it for approval (minimum score: 80)
                  </Text>
                  <Text>
                    <strong>2.</strong> <Badge colorScheme="green" size="sm">Managers</Badge> review submitted content and can approve or request changes
                  </Text>
                  <Text>
                    <strong>3.</strong> <Badge colorScheme="blue" size="sm">Admins</Badge> have full access and can publish content directly
                  </Text>
                </VStack>
              </Box>
            </HStack>
          </CardBody>
        </Card>
      </VStack>

      {/* Add User Modal */}
      <Modal isOpen={isAddOpen} onClose={closeAddModal} size="lg" isCentered>
        <ModalOverlay bg="blackAlpha.600" />
        <ModalContent bg={modalBg}>
          <ModalHeader borderBottomWidth="1px" borderColor={borderColor}>
            <HStack>
              <Icon as={FaUserPlus} color="brand.500" />
              <Text>Add New Team Member</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody py={6}>
            {tempPassword ? (
              <VStack spacing={4} align="stretch">
                <Alert status="success" borderRadius="md">
                  <AlertIcon />
                  <AlertDescription>User created successfully!</AlertDescription>
                </Alert>
                <Box p={4} bg={roleBoxBg} borderRadius="md" borderWidth="1px" borderColor={borderColor}>
                  <Text fontWeight="600" mb={2}>Temporary Password</Text>
                  <Text fontSize="sm" color={textColorSecondary} mb={3}>
                    Please share this password with the user. They will be required to change it on first login.
                  </Text>
                  <HStack>
                    <Input value={tempPassword} isReadOnly bg={cardBg} />
                    <IconButton
                      icon={<FaCopy />}
                      onClick={() => copyToClipboard(tempPassword)}
                      aria-label="Copy password"
                      colorScheme="brand"
                    />
                  </HStack>
                </Box>
                <Button onClick={closeAddModal} colorScheme="brand">
                  Done
                </Button>
              </VStack>
            ) : (
              <VStack spacing={5} align="stretch">
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <FormControl isRequired>
                    <FormLabel>Full Name</FormLabel>
                    <Input
                      placeholder="John Doe"
                      value={newUser.full_name}
                      onChange={(e) => setNewUser({...newUser, full_name: e.target.value})}
                      bg={cardBg}
                    />
                  </FormControl>
                  <FormControl isRequired>
                    <FormLabel>Email</FormLabel>
                    <Input
                      type="email"
                      placeholder="john@company.com"
                      value={newUser.email}
                      onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                      bg={cardBg}
                    />
                  </FormControl>
                </SimpleGrid>
                
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <FormControl>
                    <FormLabel>Department</FormLabel>
                    <Input
                      placeholder="Marketing"
                      value={newUser.department}
                      onChange={(e) => setNewUser({...newUser, department: e.target.value})}
                      bg={cardBg}
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel>Job Title</FormLabel>
                    <Input
                      placeholder="Content Manager"
                      value={newUser.job_title}
                      onChange={(e) => setNewUser({...newUser, job_title: e.target.value})}
                      bg={cardBg}
                    />
                  </FormControl>
                </SimpleGrid>
                
                <FormControl>
                  <FormLabel>Role</FormLabel>
                  <Select
                    value={newUser.role}
                    onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                    bg={cardBg}
                  >
                    <option value="creator">Creator - Can create and submit content</option>
                    <option value="manager">Manager - Can approve content</option>
                    <option value="enterprise_admin">Admin - Full access</option>
                  </Select>
                  <FormHelperText>
                    {WORKFLOW_ROLES[newUser.role]?.description || WORKFLOW_ROLES.admin.description}
                  </FormHelperText>
                </FormControl>
                
                <Divider />
                
                <Box p={4} bg={infoBg} borderRadius="md">
                  <Checkbox
                    isChecked={sendInviteEmail}
                    onChange={(e) => setSendInviteEmail(e.target.checked)}
                    colorScheme="brand"
                  >
                    <HStack spacing={2}>
                      <Icon as={FaEnvelope} color="blue.500" />
                      <Text fontWeight="500">Send invitation email</Text>
                    </HStack>
                  </Checkbox>
                  <Text fontSize="sm" color={textColorSecondary} ml={6} mt={1}>
                    {sendInviteEmail 
                      ? "User will receive an email with login instructions and a link to set their password."
                      : "You'll receive a temporary password to share with the user manually."}
                  </Text>
                </Box>
                
                {!sendInviteEmail && (
                  <FormControl>
                    <FormLabel>Password (optional)</FormLabel>
                    <Input
                      type="password"
                      placeholder="Leave blank to auto-generate"
                      value={newUser.password}
                      onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                      bg={cardBg}
                    />
                    <FormHelperText>
                      If left blank, a secure temporary password will be generated.
                    </FormHelperText>
                  </FormControl>
                )}
              </VStack>
            )}
          </ModalBody>
          {!tempPassword && (
            <ModalFooter borderTopWidth="1px" borderColor={borderColor}>
              <Button variant="ghost" mr={3} onClick={closeAddModal}>
                Cancel
              </Button>
              <Button
                colorScheme="brand"
                onClick={handleAddUser}
                isLoading={isSubmitting}
                leftIcon={sendInviteEmail ? <FaPaperPlane /> : <FaUserPlus />}
              >
                {sendInviteEmail ? 'Send Invitation' : 'Add User'}
              </Button>
            </ModalFooter>
          )}
        </ModalContent>
      </Modal>

      {/* Edit User Modal */}
      <Modal isOpen={isEditOpen} onClose={onEditClose} size="md" isCentered>
        <ModalOverlay bg="blackAlpha.600" />
        <ModalContent bg={modalBg}>
          <ModalHeader borderBottomWidth="1px" borderColor={borderColor}>
            Edit Team Member
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody py={6}>
            {selectedUser && (
              <VStack spacing={4} align="stretch">
                <HStack spacing={4} pb={4} borderBottomWidth="1px" borderColor={borderColor}>
                  <Avatar size="lg" name={selectedUser.full_name} src={selectedUser.profile_picture} />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="600" fontSize="lg">{selectedUser.full_name}</Text>
                    <Text fontSize="sm" color={textColorSecondary}>{selectedUser.email}</Text>
                  </VStack>
                </HStack>
                
                <FormControl>
                  <FormLabel>Role</FormLabel>
                  <Select
                    value={selectedUser.enterprise_role || 'creator'}
                    onChange={(e) => setSelectedUser({...selectedUser, enterprise_role: e.target.value})}
                    bg={cardBg}
                  >
                    <option value="creator">Creator</option>
                    <option value="manager">Manager</option>
                    <option value="enterprise_admin">Admin</option>
                  </Select>
                </FormControl>
                
                <FormControl>
                  <FormLabel>Department</FormLabel>
                  <Input
                    value={selectedUser.department || ''}
                    onChange={(e) => setSelectedUser({...selectedUser, department: e.target.value})}
                    placeholder="e.g., Marketing"
                    bg={cardBg}
                  />
                </FormControl>
                
                <FormControl>
                  <FormLabel>Job Title</FormLabel>
                  <Input
                    value={selectedUser.job_title || ''}
                    onChange={(e) => setSelectedUser({...selectedUser, job_title: e.target.value})}
                    placeholder="e.g., Content Manager"
                    bg={cardBg}
                  />
                </FormControl>
                
                {/* Reports To - Only show for non-manager/admin roles */}
                {selectedUser.enterprise_role !== 'enterprise_admin' && (
                  <FormControl>
                    <FormLabel>Reports To (Manager)</FormLabel>
                    <Select
                      value={selectedUser.reports_to || ''}
                      onChange={(e) => setSelectedUser({...selectedUser, reports_to: e.target.value || null})}
                      bg={cardBg}
                      placeholder="Select a manager..."
                    >
                      <option value="">No manager assigned</option>
                      {members
                        .filter(m => 
                          m.id !== selectedUser.id && 
                          ['manager', 'enterprise_admin'].includes(m.enterprise_role)
                        )
                        .map(manager => (
                          <option key={manager.id} value={manager.id}>
                            {manager.full_name} ({manager.enterprise_role === 'enterprise_admin' ? 'Admin' : 'Manager'})
                          </option>
                        ))
                      }
                    </Select>
                    <Text fontSize="xs" color={textColorSecondary} mt={1}>
                      Content approvals will be sent to this manager
                    </Text>
                  </FormControl>
                )}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter borderTopWidth="1px" borderColor={borderColor}>
            <Button variant="ghost" mr={3} onClick={onEditClose}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
              onClick={handleUpdateUser}
              isLoading={isSubmitting}
            >
              Save Changes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteOpen} onClose={onDeleteClose} size="md" isCentered>
        <ModalOverlay bg="blackAlpha.600" />
        <ModalContent bg={modalBg}>
          <ModalHeader color="red.500" borderBottomWidth="1px" borderColor={borderColor}>
            Remove Team Member
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody py={6}>
            {selectedUser && (
              <VStack spacing={4} align="stretch">
                <HStack spacing={4}>
                  <Avatar size="md" name={selectedUser.full_name} src={selectedUser.profile_picture} />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="600">{selectedUser.full_name}</Text>
                    <Text fontSize="sm" color={textColorSecondary}>{selectedUser.email}</Text>
                  </VStack>
                </HStack>
                
                <Alert status="warning" borderRadius="md">
                  <AlertIcon />
                  <Text fontSize="sm">This action cannot be undone.</Text>
                </Alert>
                
                <VStack spacing={3} align="stretch">
                  <Button
                    variant="outline"
                    colorScheme="orange"
                    leftIcon={<FaUserMinus />}
                    onClick={() => handleDeleteUser(false)}
                    isLoading={isSubmitting}
                  >
                    Remove from Team Only
                  </Button>
                  <Text fontSize="xs" color={textColorSecondary} textAlign="center">
                    User keeps their account but loses access to team features
                  </Text>
                  
                  <Divider />
                  
                  <Button
                    variant="solid"
                    colorScheme="red"
                    leftIcon={<FaTrash />}
                    onClick={() => handleDeleteUser(true)}
                    isLoading={isSubmitting}
                  >
                    Delete Account Permanently
                  </Button>
                  <Text fontSize="xs" color={textColorSecondary} textAlign="center">
                    User&apos;s account and all their data will be permanently deleted
                  </Text>
                </VStack>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter borderTopWidth="1px" borderColor={borderColor}>
            <Button variant="ghost" onClick={onDeleteClose}>
              Cancel
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
