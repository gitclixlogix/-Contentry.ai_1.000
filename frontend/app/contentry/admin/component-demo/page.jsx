'use client';

/**
 * Component Library Demo Page
 * 
 * Showcases the reusable components from @/components/shared
 * Use this as a reference for implementing components across the app.
 */

import { useState } from 'react';
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  HStack,
  useDisclosure,
  useColorModeValue,
  Badge,
  IconButton,
  Divider,
  useToast,
} from '@chakra-ui/react';
import { FaPlus, FaEdit, FaTrash, FaEye, FaBan, FaCheck } from 'react-icons/fa';
import { Trash2, CheckCircle, XCircle } from 'lucide-react';
import {
  DataTable,
  FormModal,
  FormField,
  ConfirmationModal,
  DeleteConfirmationModal,
  UserInfoCell,
  StatusBadge,
} from '@/components/shared';

// Sample data for the demo
const sampleUsers = [
  { id: '1', name: 'John Doe', email: 'john@example.com', role: 'admin', status: 'active', joined: '2024-01-15' },
  { id: '2', name: 'Jane Smith', email: 'jane@example.com', role: 'user', status: 'active', joined: '2024-02-20' },
  { id: '3', name: 'Bob Wilson', email: 'bob@example.com', role: 'user', status: 'inactive', joined: '2024-03-10' },
  { id: '4', name: 'Alice Brown', email: 'alice@example.com', role: 'manager', status: 'active', joined: '2024-01-25' },
  { id: '5', name: 'Charlie Davis', email: 'charlie@example.com', role: 'user', status: 'pending', joined: '2024-04-05' },
  { id: '6', name: 'Eva Martinez', email: 'eva@example.com', role: 'user', status: 'active', joined: '2024-02-14' },
  { id: '7', name: 'Frank Miller', email: 'frank@example.com', role: 'admin', status: 'active', joined: '2024-03-22' },
  { id: '8', name: 'Grace Lee', email: 'grace@example.com', role: 'user', status: 'inactive', joined: '2024-01-08' },
  { id: '9', name: 'Henry Taylor', email: 'henry@example.com', role: 'manager', status: 'active', joined: '2024-05-12' },
  { id: '10', name: 'Ivy Chen', email: 'ivy@example.com', role: 'user', status: 'pending', joined: '2024-06-01' },
  { id: '11', name: 'Jack Robinson', email: 'jack@example.com', role: 'user', status: 'active', joined: '2024-04-18' },
  { id: '12', name: 'Kate Williams', email: 'kate@example.com', role: 'admin', status: 'active', joined: '2024-02-28' },
];

export default function ComponentDemoPage() {
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const toast = useToast();
  
  // DataTable state
  const [selectedIds, setSelectedIds] = useState([]);
  
  // FormModal state
  const { isOpen: isFormOpen, onOpen: onFormOpen, onClose: onFormClose } = useDisclosure();
  const [formData, setFormData] = useState({ name: '', email: '', role: 'user' });
  const [formLoading, setFormLoading] = useState(false);
  
  // ConfirmationModal state
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const [deleteLoading, setDeleteLoading] = useState(false);
  
  // DataTable columns configuration
  const columns = [
    {
      key: 'name',
      label: 'User',
      sortable: true,
      render: (value, row) => (
        <UserInfoCell 
          name={row.name} 
          email={row.email}
          size="sm"
        />
      )
    },
    {
      key: 'email',
      label: 'Email',
      sortable: true,
      exportable: true, // Include in exports
    },
    {
      key: 'role',
      label: 'Role',
      sortable: true,
      render: (value) => (
        <Badge colorScheme={value === 'admin' ? 'purple' : value === 'manager' ? 'blue' : 'gray'}>
          {value}
        </Badge>
      )
    },
    {
      key: 'status',
      label: 'Status',
      sortable: true,
      render: (value) => (
        <StatusBadge 
          status={value} 
          colorScheme={value === 'active' ? 'green' : value === 'pending' ? 'yellow' : 'red'}
        />
      )
    },
    {
      key: 'joined',
      label: 'Joined',
      sortable: true,
      render: (value) => new Date(value).toLocaleDateString()
    }
  ];
  
  // Bulk actions configuration
  const bulkActions = [
    {
      label: 'Delete',
      icon: Trash2,
      colorScheme: 'red',
      onClick: (ids) => {
        onDeleteOpen();
      }
    },
    {
      label: 'Activate',
      icon: CheckCircle,
      colorScheme: 'green',
      variant: 'outline',
      onClick: (ids) => {
        toast({
          title: 'Bulk Action',
          description: `Activating ${ids.length} users...`,
          status: 'info',
          duration: 2000,
        });
      }
    },
    {
      label: 'Deactivate',
      icon: XCircle,
      colorScheme: 'orange',
      variant: 'outline',
      onClick: (ids) => {
        toast({
          title: 'Bulk Action',
          description: `Deactivating ${ids.length} users...`,
          status: 'info',
          duration: 2000,
        });
      }
    },
  ];
  
  // Form submit handler
  const handleFormSubmit = async () => {
    setFormLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('Form submitted:', formData);
    toast({
      title: 'User Created',
      description: `${formData.name} has been added.`,
      status: 'success',
      duration: 3000,
    });
    setFormLoading(false);
    onFormClose();
    setFormData({ name: '', email: '', role: 'user' });
  };
  
  // Delete handler
  const handleDelete = async () => {
    setDeleteLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    toast({
      title: 'Users Deleted',
      description: `${selectedIds.length} users have been deleted.`,
      status: 'success',
      duration: 3000,
    });
    setDeleteLoading(false);
    onDeleteClose();
    setSelectedIds([]);
  };
  
  // Row actions renderer
  const renderActions = (row) => (
    <HStack spacing={1}>
      <IconButton
        icon={<FaEye />}
        size="sm"
        variant="ghost"
        aria-label="View"
        onClick={() => toast({ title: 'View User', description: row.name, status: 'info', duration: 2000 })}
      />
      <IconButton
        icon={<FaEdit />}
        size="sm"
        variant="ghost"
        aria-label="Edit"
        onClick={() => toast({ title: 'Edit User', description: row.name, status: 'info', duration: 2000 })}
      />
      <IconButton
        icon={<FaTrash />}
        size="sm"
        variant="ghost"
        colorScheme="red"
        aria-label="Delete"
        onClick={() => toast({ title: 'Delete User', description: row.name, status: 'warning', duration: 2000 })}
      />
    </HStack>
  );

  return (
    <Box minH="100vh" bg={bgColor} p={{ base: 4, md: 8 }} pt={{ base: '100px', md: '100px' }}>
      <VStack spacing={8} align="stretch" maxW="1400px" mx="auto">
        {/* Header */}
        <Box>
          <Heading size="lg" color={textColor} mb={2}>
            Reusable Component Library Demo
          </Heading>
          <Text color="gray.500">
            This page demonstrates the shared components from Phase 10.1 with advanced features
          </Text>
        </Box>

        {/* DataTable Demo with Advanced Features */}
        <Box>
          <VStack align="stretch" spacing={4}>
            <HStack justify="space-between">
              <Box>
                <Heading size="md" color={textColor}>DataTable with Export & Bulk Actions</Heading>
                <Text fontSize="sm" color="gray.500" mt={1}>
                  Try selecting rows, exporting data, or using bulk actions
                </Text>
              </Box>
              <Button
                colorScheme="brand"
                size="sm"
                leftIcon={<FaPlus />}
                onClick={onFormOpen}
              >
                Add User
              </Button>
            </HStack>
            
            <DataTable
              title="User Management"
              data={sampleUsers}
              columns={columns}
              pagination={{ type: 'client', pageSize: 5 }}
              filtering={{ enabled: true, placeholder: 'Search users...' }}
              sorting={{ enabled: true }}
              selectable={{
                enabled: true,
                selectedIds,
                onSelectionChange: setSelectedIds
              }}
              actions={renderActions}
              bulkActions={bulkActions}
              exportable={{
                enabled: true,
                filename: 'users-export',
                formats: ['csv', 'json']
              }}
              emptyMessage="No users found"
            />
          </VStack>
        </Box>

        <Divider />

        {/* Feature Highlights */}
        <Box bg={cardBg} p={6} borderRadius="xl" shadow="sm">
          <VStack align="stretch" spacing={4}>
            <Heading size="md" color={textColor}>Advanced DataTable Features</Heading>
            <HStack spacing={4} flexWrap="wrap">
              <Badge colorScheme="green" p={2}>✓ CSV Export</Badge>
              <Badge colorScheme="green" p={2}>✓ JSON Export</Badge>
              <Badge colorScheme="green" p={2}>✓ Bulk Actions</Badge>
              <Badge colorScheme="green" p={2}>✓ Row Selection</Badge>
              <Badge colorScheme="green" p={2}>✓ Sorting</Badge>
              <Badge colorScheme="green" p={2}>✓ Filtering</Badge>
              <Badge colorScheme="green" p={2}>✓ Pagination</Badge>
            </HStack>
            <Text fontSize="sm" color="gray.500">
              The DataTable now supports exporting to CSV/JSON, bulk actions on selected rows, 
              and a customizable toolbar with title support.
            </Text>
          </VStack>
        </Box>

        {/* FormModal Demo */}
        <Box bg={cardBg} p={6} borderRadius="xl" shadow="sm">
          <VStack align="stretch" spacing={4}>
            <Heading size="md" color={textColor}>FormModal Component</Heading>
            <Text color="gray.500">
              Click the &quot;Add User&quot; button above to see the FormModal in action.
            </Text>
            <Text fontSize="sm" color="gray.400">
              Features: Async submit, validation support, customizable buttons, loading states
            </Text>
          </VStack>
        </Box>

        {/* Usage Examples */}
        <Box bg={cardBg} p={6} borderRadius="xl" shadow="sm">
          <VStack align="stretch" spacing={4}>
            <Heading size="md" color={textColor}>Component Import</Heading>
            <Box 
              bg={useColorModeValue('gray.100', 'gray.700')} 
              p={4} 
              borderRadius="md"
              fontFamily="mono"
              fontSize="sm"
            >
              <Text color="purple.500">import</Text>
              <Text pl={4}>{`{ DataTable, FormModal, FormField, ConfirmationModal }`}</Text>
              <Text color="purple.500">from</Text>
              <Text color="green.500">&apos;@/components/shared&apos;</Text>
            </Box>
          </VStack>
        </Box>
      </VStack>

      {/* FormModal */}
      <FormModal
        isOpen={isFormOpen}
        onClose={onFormClose}
        onSubmit={handleFormSubmit}
        title="Add New User"
        submitText="Create User"
        isLoading={formLoading}
        isDisabled={!formData.name || !formData.email}
      >
        <VStack spacing={4}>
          <FormField
            label="Full Name"
            name="name"
            value={formData.name}
            onChange={(val) => setFormData(prev => ({ ...prev, name: val }))}
            placeholder="Enter full name"
            isRequired
          />
          <FormField
            label="Email Address"
            name="email"
            type="email"
            value={formData.email}
            onChange={(val) => setFormData(prev => ({ ...prev, email: val }))}
            placeholder="Enter email address"
            isRequired
          />
          <FormField
            label="Role"
            name="role"
            type="select"
            value={formData.role}
            onChange={(val) => setFormData(prev => ({ ...prev, role: val }))}
            options={[
              { value: 'user', label: 'User' },
              { value: 'manager', label: 'Manager' },
              { value: 'admin', label: 'Administrator' }
            ]}
          />
        </VStack>
      </FormModal>

      {/* DeleteConfirmationModal */}
      <DeleteConfirmationModal
        isOpen={isDeleteOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        itemName={`${selectedIds.length} user(s)`}
        isLoading={deleteLoading}
      />
    </Box>
  );
}
