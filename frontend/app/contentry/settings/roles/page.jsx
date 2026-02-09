'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Flex,
  Text,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  useColorModeValue,
  VStack,
  HStack,
  Badge,
  Icon,
  Spinner,
  useToast,
  useDisclosure,
  Tooltip,
  IconButton,
} from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  Plus,
  Shield,
  Users,
  Edit2,
  Trash2,
  ChevronLeft,
  Lock,
  Copy,
  Activity,
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

// Import modal components
import { RoleFormModal, DeleteRoleDialog, DuplicateRoleModal } from './components';

// Role icon mappings
const ROLE_ICONS = {
  shield: Shield,
  pencil: Edit2,
  briefcase: Users,
  scale: Shield,
  user: Users,
};

export default function RolesManagementPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const router = useRouter();
  const toast = useToast();

  // State
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [featureEnabled, setFeatureEnabled] = useState(false);

  // Modal states
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const { isOpen: isDuplicateOpen, onOpen: onDuplicateOpen, onClose: onDuplicateClose } = useDisclosure();
  const [selectedRole, setSelectedRole] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [inheritanceRules, setInheritanceRules] = useState([]);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: [],
    color: '#3b82f6',
    icon: 'user',
  });

  // Duplicate form state
  const [duplicateForm, setDuplicateForm] = useState({
    new_name: '',
    new_description: '',
  });

  // Colors
  const bgColor = useColorModeValue('white', 'navy.800');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');
  const textColor = useColorModeValue('gray.800', 'white');
  const textSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('white', 'navy.700');
  const cardHoverBg = useColorModeValue('gray.50', 'navy.600');

  // Fetch roles and permissions
  const fetchData = useCallback(async () => {
    if (!user?.id) return;

    setIsLoading(true);
    try {
      const [rolesRes, permsRes, featureRes, inheritanceRes] = await Promise.all([
        axios.get(`${getApiUrl()}/roles/`, {
          headers: { 'X-User-ID': user.id },
        }),
        axios.get(`${getApiUrl()}/roles/permissions`, {
          headers: { 'X-User-ID': user.id },
        }),
        axios.get(`${getApiUrl()}/roles/feature-status`, {
          headers: { 'X-User-ID': user.id },
        }),
        axios.get(`${getApiUrl()}/roles/inheritance-rules`, {
          headers: { 'X-User-ID': user.id },
        }),
      ]);

      setRoles(rolesRes.data.roles || []);
      setPermissions(permsRes.data.categories || []);
      setFeatureEnabled(featureRes.data.enabled);
      setInheritanceRules(inheritanceRes.data.inheritance_rules || []);
    } catch (error) {
      console.error('Error fetching roles data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load roles data',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, toast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter roles by search
  const filteredRoles = roles.filter((role) =>
    role.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (role.description || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Open edit modal
  const openEditModal = (role) => {
    setSelectedRole(role);
    setFormData({
      name: role.name,
      description: role.description || '',
      permissions: role.permissions || [],
      color: role.color || '#3b82f6',
      icon: role.icon || 'user',
    });
    onCreateOpen();
  };

  // Open create modal
  const openCreateModal = () => {
    setSelectedRole(null);
    setFormData({
      name: '',
      description: '',
      permissions: [],
      color: '#3b82f6',
      icon: 'user',
    });
    onCreateOpen();
  };

  // Open delete dialog
  const openDeleteDialog = (role) => {
    setSelectedRole(role);
    onDeleteOpen();
  };

  // Open duplicate modal
  const openDuplicateModal = (role) => {
    setSelectedRole(role);
    setDuplicateForm({
      new_name: `${role.name} (Copy)`,
      new_description: role.description || '',
    });
    onDuplicateOpen();
  };

  // Handle save role (create or update)
  const handleSaveRole = async () => {
    setIsSubmitting(true);
    try {
      if (selectedRole) {
        // Update existing role
        await axios.put(
          `${getApiUrl()}/roles/${selectedRole.role_id}`,
          formData,
          { headers: { 'X-User-ID': user.id } }
        );
        toast({
          title: 'Success',
          description: 'Role updated successfully',
          status: 'success',
          duration: 3000,
        });
      } else {
        // Create new role
        await axios.post(
          `${getApiUrl()}/roles/`,
          formData,
          { headers: { 'X-User-ID': user.id } }
        );
        toast({
          title: 'Success',
          description: 'Role created successfully',
          status: 'success',
          duration: 3000,
        });
      }
      onCreateClose();
      fetchData();
    } catch (error) {
      console.error('Error saving role:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save role',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle delete role
  const handleDeleteRole = async () => {
    setIsSubmitting(true);
    try {
      await axios.delete(
        `${getApiUrl()}/roles/${selectedRole.role_id}`,
        { headers: { 'X-User-ID': user.id } }
      );
      toast({
        title: 'Success',
        description: 'Role deleted successfully',
        status: 'success',
        duration: 3000,
      });
      onDeleteClose();
      fetchData();
    } catch (error) {
      console.error('Error deleting role:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete role',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle duplicate role
  const submitDuplicateRole = async () => {
    setIsSubmitting(true);
    try {
      await axios.post(
        `${getApiUrl()}/roles/${selectedRole.role_id}/duplicate`,
        duplicateForm,
        { headers: { 'X-User-ID': user.id } }
      );
      toast({
        title: 'Success',
        description: 'Role duplicated successfully',
        status: 'success',
        duration: 3000,
      });
      onDuplicateClose();
      fetchData();
    } catch (error) {
      console.error('Error duplicating role:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to duplicate role',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <Flex justify="center" align="center" minH="400px">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }

  return (
    <Box p={{ base: 4, md: 6 }} maxW="1200px" mx="auto">
      {/* Header */}
      <Box mb={6}>
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<ChevronLeft size={16} />}
          onClick={() => router.push('/contentry/settings')}
          p={0}
          h="auto"
          minW="auto"
          color={textSecondary}
          _hover={{ color: textColor }}
          mb={2}
        >
          Settings
        </Button>

        <Flex justify="space-between" align="center" mb={2}>
          <HStack spacing={3}>
            <Icon as={Shield} boxSize={6} color="brand.500" />
            <Text fontSize="2xl" fontWeight="bold" color={textColor}>
              Role Management
            </Text>
          </HStack>
          <HStack spacing={2}>
            <Button
              variant="outline"
              leftIcon={<Activity size={16} />}
              onClick={() => router.push('/contentry/settings/roles/audit')}
              size="sm"
            >
              Audit Log
            </Button>
            <Button
              leftIcon={<Plus size={16} />}
              colorScheme="brand"
              onClick={openCreateModal}
              size="sm"
            >
              Create New Role
            </Button>
          </HStack>
        </Flex>
        <Text color={textSecondary} fontSize="sm">
          Manage roles and permissions for your enterprise team
        </Text>
      </Box>

      {/* Search */}
      <Box mb={6}>
        <InputGroup maxW="400px">
          <InputLeftElement pointerEvents="none">
            <Search size={18} color="gray" />
          </InputLeftElement>
          <Input
            placeholder="Search roles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            bg={bgColor}
            borderColor={borderColor}
          />
        </InputGroup>
      </Box>

      {/* Roles List */}
      <VStack spacing={3} align="stretch">
        {filteredRoles.length === 0 ? (
          <Box textAlign="center" py={12} color={textSecondary}>
            <Icon as={Shield} boxSize={12} mb={4} opacity={0.5} />
            <Text>No roles found</Text>
          </Box>
        ) : (
          filteredRoles.map((role) => {
            const RoleIcon = ROLE_ICONS[role.icon] || Users;
            const isSystemRole = role.is_system_role;

            return (
              <Box
                key={role.role_id}
                bg={cardBg}
                p={4}
                borderRadius="lg"
                border="1px solid"
                borderColor={borderColor}
                _hover={{ bg: cardHoverBg }}
                transition="all 0.2s"
              >
                <Flex justify="space-between" align="center">
                  <HStack spacing={4} flex="1">
                    {/* Role Color & Icon */}
                    <Box
                      w="40px"
                      h="40px"
                      borderRadius="lg"
                      bg={role.color || 'brand.500'}
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                    >
                      <Icon as={RoleIcon} color="white" boxSize={5} />
                    </Box>

                    {/* Role Info */}
                    <Box flex="1">
                      <HStack spacing={2} mb={1}>
                        <Text fontWeight="bold" color={textColor}>
                          {role.name}
                        </Text>
                        {isSystemRole && (
                          <Badge colorScheme="blue" variant="subtle" fontSize="xs">
                            <HStack spacing={1}>
                              <Lock size={10} />
                              <span>System</span>
                            </HStack>
                          </Badge>
                        )}
                        <Badge colorScheme="brand" variant="outline" fontSize="xs">
                          {role.permissions?.includes('*')
                            ? 'All Permissions'
                            : `${role.permissions?.length || 0} permissions`}
                        </Badge>
                      </HStack>
                      {role.description && (
                        <Text fontSize="sm" color={textSecondary} noOfLines={1}>
                          {role.description}
                        </Text>
                      )}
                    </Box>
                  </HStack>

                  {/* Actions */}
                  <HStack spacing={1}>
                    {/* Duplicate - available for all roles */}
                    <Tooltip label="Duplicate Role">
                      <IconButton
                        icon={<Copy size={16} />}
                        variant="ghost"
                        size="sm"
                        colorScheme="blue"
                        onClick={() => openDuplicateModal(role)}
                      />
                    </Tooltip>

                    {isSystemRole ? (
                      <Tooltip label="View Role">
                        <IconButton
                          icon={<Edit2 size={16} />}
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditModal(role)}
                        />
                      </Tooltip>
                    ) : (
                      <>
                        <Tooltip label="Edit Role">
                          <IconButton
                            icon={<Edit2 size={16} />}
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditModal(role)}
                          />
                        </Tooltip>
                        <Tooltip label="Delete Role">
                          <IconButton
                            icon={<Trash2 size={16} />}
                            variant="ghost"
                            size="sm"
                            colorScheme="red"
                            onClick={() => openDeleteDialog(role)}
                          />
                        </Tooltip>
                      </>
                    )}
                  </HStack>
                </Flex>
              </Box>
            );
          })
        )}
      </VStack>

      {/* Create/Edit Role Modal */}
      <RoleFormModal
        isOpen={isCreateOpen}
        onClose={onCreateClose}
        selectedRole={selectedRole}
        formData={formData}
        setFormData={setFormData}
        permissions={permissions}
        inheritanceRules={inheritanceRules}
        onSave={handleSaveRole}
        isSubmitting={isSubmitting}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteRoleDialog
        isOpen={isDeleteOpen}
        onClose={onDeleteClose}
        selectedRole={selectedRole}
        onDelete={handleDeleteRole}
        isSubmitting={isSubmitting}
      />

      {/* Duplicate Role Modal */}
      <DuplicateRoleModal
        isOpen={isDuplicateOpen}
        onClose={onDuplicateClose}
        selectedRole={selectedRole}
        duplicateForm={duplicateForm}
        setDuplicateForm={setDuplicateForm}
        onSubmit={submitDuplicateRole}
        isSubmitting={isSubmitting}
      />
    </Box>
  );
}
