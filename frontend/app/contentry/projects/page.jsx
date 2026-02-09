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
  SimpleGrid,
  Card,
  CardBody,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  Textarea,
  Switch,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  Progress,
  Tooltip,
} from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  Plus,
  FolderKanban,
  Calendar,
  Users,
  MoreVertical,
  Archive,
  RotateCcw,
  Edit2,
  FileText,
  TrendingUp,
  Clock,
  ChevronRight,
} from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

export default function ProjectsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const router = useRouter();
  const toast = useToast();

  // State
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const { isOpen, onOpen, onClose } = useDisclosure();

  // Form state for create/edit
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    start_date: '',
    end_date: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingProject, setEditingProject] = useState(null);

  // Colors
  const bgColor = useColorModeValue('white', 'navy.800');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');
  const textColor = useColorModeValue('gray.800', 'white');
  const textSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('white', 'navy.700');
  const cardHoverBg = useColorModeValue('gray.50', 'navy.600');

  // Fetch projects
  const fetchProjects = useCallback(async () => {
    if (!user?.id) return;

    setIsLoading(true);
    try {
      const response = await api.get('/projects', {
        params: {
          include_archived: showArchived,
          search: searchQuery || undefined,
        },
      });
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error('Error fetching projects:', error);
      toast({
        title: 'Error',
        description: 'Failed to load projects',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, showArchived, searchQuery, toast]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Handle create/update project
  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast({
        title: 'Error',
        description: 'Project name is required',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setIsSubmitting(true);
    try {
      if (editingProject) {
        // Update existing project
        await api.put(`/projects/${editingProject.project_id}`, formData);
        toast({
          title: 'Success',
          description: 'Project updated successfully',
          status: 'success',
          duration: 3000,
        });
      } else {
        // Create new project
        await api.post('/projects', formData);
        toast({
          title: 'Success',
          description: 'Project created successfully',
          status: 'success',
          duration: 3000,
        });
      }

      onClose();
      resetForm();
      fetchProjects();
    } catch (error) {
      console.error('Error saving project:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save project',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle archive/unarchive
  const handleArchive = async (project, archive = true) => {
    try {
      const endpoint = archive ? 'archive' : 'unarchive';
      await api.post(`/projects/${project.project_id}/${endpoint}`, {});
      toast({
        title: 'Success',
        description: archive ? 'Project archived' : 'Project restored',
        status: 'success',
        duration: 3000,
      });
      fetchProjects();
    } catch (error) {
      console.error('Error archiving project:', error);
      toast({
        title: 'Error',
        description: 'Failed to update project status',
        status: 'error',
        duration: 3000,
      });
    }
  };

  // Open edit modal
  const handleEdit = (project) => {
    setEditingProject(project);
    setFormData({
      name: project.name,
      description: project.description || '',
      start_date: project.start_date || '',
      end_date: project.end_date || '',
    });
    onOpen();
  };

  // Reset form
  const resetForm = () => {
    setFormData({ name: '', description: '', start_date: '', end_date: '' });
    setEditingProject(null);
  };

  // Format date for display
  const formatDate = (dateStr) => {
    if (!dateStr) return 'Not set';
    return new Date(dateStr).toLocaleDateString();
  };

  // Calculate project progress
  const getProjectProgress = (project) => {
    if (!project.start_date || !project.end_date) return null;
    const start = new Date(project.start_date);
    const end = new Date(project.end_date);
    const now = new Date();
    
    if (now < start) return 0;
    if (now > end) return 100;
    
    const total = end - start;
    const elapsed = now - start;
    return Math.round((elapsed / total) * 100);
  };

  // Get status color
  const getStatusColor = (status) => {
    return status === 'active' ? 'green' : 'gray';
  };

  if (isLoading && projects.length === 0) {
    return (
      <Flex justify="center" align="center" minH="400px">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }

  return (
    <Box p={{ base: 4, md: 6 }} maxW="1400px" mx="auto">
      {/* Header */}
      <Flex
        direction={{ base: 'column', md: 'row' }}
        justify="space-between"
        align={{ base: 'stretch', md: 'center' }}
        mb={6}
        gap={4}
      >
        <Box>
          <HStack mb={1}>
            <Icon as={FolderKanban} boxSize={6} color="brand.500" />
            <Text fontSize="2xl" fontWeight="bold" color={textColor}>
              Projects
            </Text>
          </HStack>
          <Text color={textSecondary} fontSize="sm">
            Organize your content campaigns and track performance
          </Text>
        </Box>

        <Button
          leftIcon={<Plus size={18} />}
          colorScheme="brand"
          onClick={() => {
            resetForm();
            onOpen();
          }}
        >
          New Project
        </Button>
      </Flex>

      {/* Filters */}
      <Flex gap={4} mb={6} direction={{ base: 'column', md: 'row' }} align={{ base: 'stretch', md: 'center' }}>
        <InputGroup maxW={{ base: '100%', md: '300px' }}>
          <InputLeftElement pointerEvents="none">
            <Search size={18} color="gray" />
          </InputLeftElement>
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            bg={bgColor}
            borderColor={borderColor}
          />
        </InputGroup>

        <HStack>
          <Switch
            isChecked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
            colorScheme="brand"
          />
          <Text fontSize="sm" color={textSecondary}>
            Show archived
          </Text>
        </HStack>
      </Flex>

      {/* Projects Grid */}
      {projects.length === 0 ? (
        <Card bg={cardBg} borderRadius="xl" border="1px solid" borderColor={borderColor}>
          <CardBody>
            <VStack py={10} spacing={4}>
              <Icon as={FolderKanban} boxSize={12} color="gray.400" />
              <Text color={textSecondary} fontSize="lg">
                No projects yet
              </Text>
              <Text color={textSecondary} fontSize="sm" textAlign="center">
                Create your first project to start organizing your content campaigns
              </Text>
              <Button
                leftIcon={<Plus size={18} />}
                colorScheme="brand"
                onClick={() => {
                  resetForm();
                  onOpen();
                }}
              >
                Create Project
              </Button>
            </VStack>
          </CardBody>
        </Card>
      ) : (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
          {projects.map((project) => {
            const progress = getProjectProgress(project);
            
            return (
              <Card
                key={project.project_id}
                bg={cardBg}
                borderRadius="xl"
                border="1px solid"
                borderColor={borderColor}
                cursor="pointer"
                transition="all 0.2s"
                _hover={{ bg: cardHoverBg, transform: 'translateY(-2px)', shadow: 'md' }}
                onClick={() => router.push(`/contentry/projects/${project.project_id}`)}
              >
                <CardBody>
                  <Flex justify="space-between" align="flex-start" mb={3}>
                    <VStack align="start" spacing={1} flex={1}>
                      <HStack>
                        <Text fontWeight="bold" fontSize="lg" color={textColor} noOfLines={1}>
                          {project.name}
                        </Text>
                        <Badge colorScheme={getStatusColor(project.status)} size="sm">
                          {project.status}
                        </Badge>
                      </HStack>
                      {project.description && (
                        <Text fontSize="sm" color={textSecondary} noOfLines={2}>
                          {project.description}
                        </Text>
                      )}
                    </VStack>

                    <Menu>
                      <MenuButton
                        as={IconButton}
                        icon={<MoreVertical size={16} />}
                        variant="ghost"
                        size="sm"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <MenuList onClick={(e) => e.stopPropagation()}>
                        <MenuItem icon={<Edit2 size={16} />} onClick={() => handleEdit(project)}>
                          Edit
                        </MenuItem>
                        {project.status === 'active' ? (
                          <MenuItem
                            icon={<Archive size={16} />}
                            onClick={() => handleArchive(project, true)}
                          >
                            Archive
                          </MenuItem>
                        ) : (
                          <MenuItem
                            icon={<RotateCcw size={16} />}
                            onClick={() => handleArchive(project, false)}
                          >
                            Restore
                          </MenuItem>
                        )}
                      </MenuList>
                    </Menu>
                  </Flex>

                  {/* Project Stats */}
                  <SimpleGrid columns={2} spacing={3} mb={3}>
                    <HStack spacing={2}>
                      <Icon as={FileText} boxSize={4} color={textSecondary} />
                      <Text fontSize="sm" color={textSecondary}>
                        {project.content_count || 0} items
                      </Text>
                    </HStack>
                    <HStack spacing={2}>
                      <Icon as={Users} boxSize={4} color={textSecondary} />
                      <Text fontSize="sm" color={textSecondary}>
                        {project.team_members?.length || 0} members
                      </Text>
                    </HStack>
                  </SimpleGrid>

                  {/* Date Range */}
                  <HStack spacing={2} mb={3}>
                    <Icon as={Calendar} boxSize={4} color={textSecondary} />
                    <Text fontSize="xs" color={textSecondary}>
                      {formatDate(project.start_date)} - {formatDate(project.end_date)}
                    </Text>
                  </HStack>

                  {/* Progress Bar */}
                  {progress !== null && (
                    <Box>
                      <Flex justify="space-between" mb={1}>
                        <Text fontSize="xs" color={textSecondary}>
                          Timeline Progress
                        </Text>
                        <Text fontSize="xs" color={textSecondary}>
                          {progress}%
                        </Text>
                      </Flex>
                      <Progress
                        value={progress}
                        size="sm"
                        colorScheme={progress >= 100 ? 'orange' : 'brand'}
                        borderRadius="full"
                      />
                    </Box>
                  )}

                  {/* View Arrow */}
                  <Flex justify="flex-end" mt={3}>
                    <HStack spacing={1} color="brand.500" fontSize="sm">
                      <Text>View Dashboard</Text>
                      <ChevronRight size={16} />
                    </HStack>
                  </Flex>
                </CardBody>
              </Card>
            );
          })}
        </SimpleGrid>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent bg={bgColor}>
          <ModalHeader>
            {editingProject ? 'Edit Project' : 'Create New Project'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Project Name</FormLabel>
                <Input
                  placeholder="e.g., Q4 Holiday Campaign"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Description</FormLabel>
                <Textarea
                  placeholder="Describe the purpose of this project..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </FormControl>

              <SimpleGrid columns={2} spacing={4} w="100%">
                <FormControl>
                  <FormLabel>Start Date</FormLabel>
                  <Input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>End Date</FormLabel>
                  <Input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  />
                </FormControl>
              </SimpleGrid>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
              onClick={handleSubmit}
              isLoading={isSubmitting}
            >
              {editingProject ? 'Save Changes' : 'Create Project'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
