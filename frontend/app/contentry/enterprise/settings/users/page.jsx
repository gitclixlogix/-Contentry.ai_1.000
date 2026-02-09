'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import {
  Box, Button, Card, CardBody, Table, Thead, Tbody, Tr, Th, Td,
  Text, useColorModeValue, Heading, Icon, Badge, Flex, Avatar,
  useToast, useDisclosure, Modal, ModalOverlay, ModalContent,
  ModalHeader, ModalBody, ModalFooter, ModalCloseButton,
  VStack, HStack, Input, Select, FormControl, FormLabel,
  IconButton, Spinner, SimpleGrid, InputGroup, InputLeftElement,
  Tooltip, Divider, Alert, AlertIcon
} from '@chakra-ui/react';
import { FaUsers, FaArrowLeft, FaUserPlus, FaTrash, FaEdit, FaSearch, FaUserMinus, FaCopy } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
// Import shared reusable components
import { UserInfoCell } from '@/components/shared';

export default function CompanyUsersPage() {
  const [user, setUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [tempPassword, setTempPassword] = useState(null);
  const router = useRouter();
  const toast = useToast();
  
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
    role: 'user',
    password: ''
  });
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  useEffect(() => {
    const storedUser = localStorage.getItem('contentry_user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      setUser(userData);
      
      // Check if user is enterprise admin (accept both 'admin' and 'enterprise_admin' roles)
      const isEnterpriseAdmin = userData.enterprise_role === 'enterprise_admin' || 
                                 userData.enterprise_role === 'admin' ||
                                 userData.is_enterprise_admin === true;
      
      if (!isEnterpriseAdmin || !userData.enterprise_id) {
        router.push('/contentry/dashboard');
        return;
      }
      
      loadUsers(userData.enterprise_id, userData.id);
    } else {
      router.push('/contentry/auth/login');
    }
  }, [router]);

  useEffect(() => {
    if (searchQuery) {
      setFilteredUsers(users.filter(u => 
        u.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        u.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        u.department?.toLowerCase().includes(searchQuery.toLowerCase())
      ));
    } else {
      setFilteredUsers(users);
    }
  }, [searchQuery, users]);

  const loadUsers = async (enterpriseId, userId) => {
    try {
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/enterprises/${enterpriseId}/users`,
        { headers: { 'X-User-ID': userId } }
      );
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast({
        title: 'Error loading users',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

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
        newUser,
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: response.data.is_new ? 'User created' : 'User added',
        description: response.data.message,
        status: 'success',
        duration: 5000,
      });

      // Store temp password if generated
      if (response.data.temp_password) {
        setTempPassword(response.data.temp_password);
      }

      // Reset form and reload users
      setNewUser({ full_name: '', email: '', department: '', job_title: '', role: 'user', password: '' });
      loadUsers(user.enterprise_id, user.id);
      
      if (!response.data.temp_password) {
        onAddClose();
      }
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
          : `${selectedUser.full_name} has been removed from the enterprise`,
        status: 'success',
        duration: 5000,
      });

      loadUsers(user.enterprise_id, user.id);
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

  const handleUpdateRole = async () => {
    if (!selectedUser) return;

    setIsSubmitting(true);
    try {
      const API = getApiUrl();
      await axios.put(
        `${API}/enterprises/${user.enterprise_id}/users/${selectedUser.id}/role`,
        {
          enterprise_role: selectedUser.enterprise_role,
          department: selectedUser.department,
          job_title: selectedUser.job_title
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'User updated',
        description: 'User role and details have been updated',
        status: 'success',
        duration: 3000,
      });

      loadUsers(user.enterprise_id, user.id);
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

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied!',
      description: 'Password copied to clipboard',
      status: 'success',
      duration: 2000,
    });
  };

  if (!user) return null;

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      <Button
        leftIcon={<Icon as={FaArrowLeft} />}
        variant="ghost"
        mb={4}
        onClick={() => router.push('/contentry/enterprise/settings')}
      >
        Back to Company Settings
      </Button>

      <Card bg={bgColor} boxShadow="lg">
        <CardBody p={{ base: 4, md: 6 }}>
          <Flex align="center" justify="space-between" mb={6} wrap="wrap" gap={4}>
            <Flex align="center" gap={3}>
              <Icon as={FaUsers} boxSize={6} color="brand.500" />
              <Heading size="lg" color={textColor}>Team Members</Heading>
              <Badge colorScheme="blue" fontSize="sm">{users.length} users</Badge>
            </Flex>
            <Button
              colorScheme="brand"
              leftIcon={<FaUserPlus />}
              onClick={onAddOpen}
            >
              Add User
            </Button>
          </Flex>

          {/* Search */}
          <InputGroup maxW="400px" mb={4}>
            <InputLeftElement>
              <FaSearch color="gray.400" />
            </InputLeftElement>
            <Input
              placeholder="Search by name, email, or department..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </InputGroup>

          {loading ? (
            <Flex justify="center" py={10}>
              <Spinner size="xl" color="brand.500" />
            </Flex>
          ) : filteredUsers.length === 0 ? (
            <Flex justify="center" py={10}>
              <Text color={textColorSecondary}>
                {searchQuery ? 'No users match your search' : 'No users found'}
              </Text>
            </Flex>
          ) : (
            <Box overflowX="auto">
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th borderColor={borderColor}>User</Th>
                    <Th borderColor={borderColor}>Email</Th>
                    <Th borderColor={borderColor}>Role</Th>
                    <Th borderColor={borderColor}>Department</Th>
                    <Th borderColor={borderColor}>Job Title</Th>
                    <Th borderColor={borderColor}>Joined</Th>
                    <Th borderColor={borderColor}>Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {filteredUsers.map((u) => (
                    <Tr key={u.id}>
                      <Td borderColor={borderColor}>
                        <UserInfoCell
                          name={u.full_name}
                          avatar={u.profile_picture}
                          showEmail={false}
                          size="sm"
                          badge={u.id === user.id ? (
                            <Badge colorScheme="green" fontSize="xs">You</Badge>
                          ) : null}
                        />
                      </Td>
                      <Td borderColor={borderColor}>
                        <Text fontSize="sm">{u.email}</Text>
                      </Td>
                      <Td borderColor={borderColor}>
                        <Badge
                          colorScheme={u.enterprise_role === 'enterprise_admin' ? 'blue' : 'blue'}
                        >
                          {u.enterprise_role === 'enterprise_admin' ? 'Admin' : u.enterprise_role || 'User'}
                        </Badge>
                      </Td>
                      <Td borderColor={borderColor}>
                        <Text fontSize="sm">{u.department || '-'}</Text>
                      </Td>
                      <Td borderColor={borderColor}>
                        <Text fontSize="sm">{u.job_title || '-'}</Text>
                      </Td>
                      <Td borderColor={borderColor}>
                        <Text fontSize="sm">
                          {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                        </Text>
                      </Td>
                      <Td borderColor={borderColor}>
                        <HStack spacing={1}>
                          <Tooltip label="Edit user">
                            <IconButton
                              icon={<FaEdit />}
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setSelectedUser({...u});
                                onEditOpen();
                              }}
                              isDisabled={u.id === user.id}
                              aria-label="Edit user"
                            />
                          </Tooltip>
                          <Tooltip label={u.id === user.id ? "You cannot remove yourself" : "Remove user"}>
                            <IconButton
                              icon={<FaTrash />}
                              size="sm"
                              variant="ghost"
                              colorScheme="red"
                              onClick={() => {
                                setSelectedUser(u);
                                onDeleteOpen();
                              }}
                              isDisabled={u.id === user.id}
                              aria-label="Remove user"
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
        </CardBody>
      </Card>

      {/* Add User Modal */}
      <Modal isOpen={isAddOpen} onClose={() => { onAddClose(); setTempPassword(null); }} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add New Team Member</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {tempPassword ? (
              <VStack spacing={4} align="stretch">
                <Alert status="success">
                  <AlertIcon />
                  User created successfully!
                </Alert>
                <Box p={4} bg="gray.50" borderRadius="md" borderWidth="1px">
                  <Text fontWeight="600" mb={2}>Temporary Password</Text>
                  <Text fontSize="sm" color="gray.600" mb={3}>
                    Please share this password with the user. They will be required to change it on first login.
                  </Text>
                  <HStack>
                    <Input value={tempPassword} isReadOnly />
                    <IconButton
                      icon={<FaCopy />}
                      onClick={() => copyToClipboard(tempPassword)}
                      aria-label="Copy password"
                    />
                  </HStack>
                </Box>
                <Button onClick={() => { onAddClose(); setTempPassword(null); }}>
                  Done
                </Button>
              </VStack>
            ) : (
              <VStack spacing={4} align="stretch">
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <FormControl isRequired>
                    <FormLabel>Full Name</FormLabel>
                    <Input
                      placeholder="John Doe"
                      value={newUser.full_name}
                      onChange={(e) => setNewUser({...newUser, full_name: e.target.value})}
                    />
                  </FormControl>
                  <FormControl isRequired>
                    <FormLabel>Email</FormLabel>
                    <Input
                      type="email"
                      placeholder="john@company.com"
                      value={newUser.email}
                      onChange={(e) => setNewUser({...newUser, email: e.target.value})}
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
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel>Job Title</FormLabel>
                    <Input
                      placeholder="Content Manager"
                      value={newUser.job_title}
                      onChange={(e) => setNewUser({...newUser, job_title: e.target.value})}
                    />
                  </FormControl>
                </SimpleGrid>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <FormControl>
                    <FormLabel>Role</FormLabel>
                    <Select
                      value={newUser.role}
                      onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                    >
                      <option value="user">User</option>
                      <option value="manager">Manager</option>
                      <option value="enterprise_admin">Admin</option>
                    </Select>
                  </FormControl>
                  <FormControl>
                    <FormLabel>Password (optional)</FormLabel>
                    <Input
                      type="password"
                      placeholder="Leave blank to auto-generate"
                      value={newUser.password}
                      onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                    />
                  </FormControl>
                </SimpleGrid>
                <Text fontSize="sm" color="gray.500">
                  If password is left blank, a temporary password will be generated and shown after creation.
                </Text>
              </VStack>
            )}
          </ModalBody>
          {!tempPassword && (
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onAddClose}>
                Cancel
              </Button>
              <Button
                colorScheme="brand"
                onClick={handleAddUser}
                isLoading={isSubmitting}
              >
                Add User
              </Button>
            </ModalFooter>
          )}
        </ModalContent>
      </Modal>

      {/* Edit User Modal */}
      <Modal isOpen={isEditOpen} onClose={onEditClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Edit Team Member</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedUser && (
              <VStack spacing={4} align="stretch">
                <HStack>
                  <Avatar size="md" name={selectedUser.full_name} />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="600">{selectedUser.full_name}</Text>
                    <Text fontSize="sm" color="gray.500">{selectedUser.email}</Text>
                  </VStack>
                </HStack>
                <Divider />
                <FormControl>
                  <FormLabel>Role</FormLabel>
                  <Select
                    value={selectedUser.enterprise_role || 'user'}
                    onChange={(e) => setSelectedUser({...selectedUser, enterprise_role: e.target.value})}
                  >
                    <option value="user">User</option>
                    <option value="manager">Manager</option>
                    <option value="enterprise_admin">Admin</option>
                  </Select>
                </FormControl>
                <FormControl>
                  <FormLabel>Department</FormLabel>
                  <Input
                    value={selectedUser.department || ''}
                    onChange={(e) => setSelectedUser({...selectedUser, department: e.target.value})}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Job Title</FormLabel>
                  <Input
                    value={selectedUser.job_title || ''}
                    onChange={(e) => setSelectedUser({...selectedUser, job_title: e.target.value})}
                  />
                </FormControl>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onEditClose}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
              onClick={handleUpdateRole}
              isLoading={isSubmitting}
            >
              Save Changes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteOpen} onClose={onDeleteClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader color="red.500">Remove Team Member</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedUser && (
              <VStack spacing={4} align="stretch">
                <HStack>
                  <Avatar size="md" name={selectedUser.full_name} />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="600">{selectedUser.full_name}</Text>
                    <Text fontSize="sm" color="gray.500">{selectedUser.email}</Text>
                  </VStack>
                </HStack>
                <Divider />
                <Text>How would you like to handle this user?</Text>
                <VStack spacing={3} align="stretch">
                  <Button
                    variant="outline"
                    colorScheme="orange"
                    leftIcon={<FaUserMinus />}
                    onClick={() => handleDeleteUser(false)}
                    isLoading={isSubmitting}
                  >
                    Remove from Enterprise Only
                  </Button>
                  <Text fontSize="xs" color="gray.500" textAlign="center">
                    User will keep their account but lose access to enterprise features
                  </Text>
                  <Button
                    variant="solid"
                    colorScheme="red"
                    leftIcon={<FaTrash />}
                    onClick={() => handleDeleteUser(true)}
                    isLoading={isSubmitting}
                  >
                    Delete Account Permanently
                  </Button>
                  <Text fontSize="xs" color="gray.500" textAlign="center">
                    User account and all their data will be permanently deleted
                  </Text>
                </VStack>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={onDeleteClose}>
              Cancel
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
