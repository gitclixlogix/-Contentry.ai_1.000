'use client';
import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Flex,
  Text,
  Input,
  InputGroup,
  InputLeftElement,
  VStack,
  HStack,
  useColorModeValue,
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
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  Divider,
  Collapse,
  useToast,
} from '@chakra-ui/react';
import { 
  FaSearch, 
  FaPlus, 
  FaEllipsisV, 
  FaEdit, 
  FaTrash, 
  FaLightbulb,
  FaCheck,
  FaTimes,
  FaRobot,
  FaBook
} from 'react-icons/fa';
import Card from '@/components/card/Card';
import api from '@/lib/api';

/**
 * KnowledgeBase Component
 * 
 * A simple knowledge management interface similar to Manus/Claude.
 * Supports:
 * - Personal knowledge (user-specific)
 * - Company knowledge (enterprise-wide, admin only)
 * - AI suggestions based on detected patterns
 */
export default function KnowledgeBase({ 
  scope = 'personal', // 'personal' or 'company'
  userId,
  isAdmin = false,
  cardBg,
  textColorPrimary,
  textColorSecondary 
}) {
  // State
  const [entries, setEntries] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);
  
  // Edit/Create modal
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [editingEntry, setEditingEntry] = useState(null);
  const [formData, setFormData] = useState({ title: '', content: '' });
  const [saving, setSaving] = useState(false);
  
  // Theme
  const bgColor = cardBg || useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textPrimary = textColorPrimary || useColorModeValue('gray.800', 'white');
  const textSecondary = textColorSecondary || useColorModeValue('gray.600', 'gray.400');
  const suggestionBg = useColorModeValue('blue.50', 'blue.900');
  const suggestionBorder = useColorModeValue('blue.200', 'blue.700');
  
  const toast = useToast();
  
  // Load knowledge entries and suggestions
  useEffect(() => {
    loadKnowledge();
    loadSuggestions();
  }, [scope, userId]);
  
  const loadKnowledge = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/knowledge?scope=${scope}&include_disabled=true`);
      if (response.data.success) {
        setEntries(response.data.entries || []);
      }
    } catch (error) {
      console.error('Failed to load knowledge:', error);
      toast({
        title: 'Failed to load knowledge',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };
  
  const loadSuggestions = async () => {
    try {
      const response = await api.get(`/knowledge/suggestions?scope=${scope}`);
      if (response.data.success) {
        setSuggestions(response.data.suggestions || []);
      }
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };
  
  // Filter entries by search query
  const filteredEntries = entries.filter(entry => 
    entry.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entry.content.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  // Create/Update entry
  const handleSave = async () => {
    if (!formData.title.trim() || !formData.content.trim()) {
      toast({
        title: 'Title and content are required',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setSaving(true);
    try {
      if (editingEntry) {
        // Update existing
        await api.put(`/knowledge/${editingEntry.id}`, {
          title: formData.title,
          content: formData.content,
        });
        toast({
          title: 'Knowledge updated',
          status: 'success',
          duration: 2000,
        });
      } else {
        // Create new
        await api.post('/knowledge', {
          title: formData.title,
          content: formData.content,
          scope: scope,
        });
        toast({
          title: 'Knowledge added',
          status: 'success',
          duration: 2000,
        });
      }
      
      onClose();
      loadKnowledge();
      setFormData({ title: '', content: '' });
      setEditingEntry(null);
    } catch (error) {
      console.error('Failed to save knowledge:', error);
      toast({
        title: 'Failed to save',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setSaving(false);
    }
  };
  
  // Toggle entry enabled/disabled
  const handleToggle = async (entry) => {
    try {
      await api.patch(`/knowledge/${entry.id}/toggle?enabled=${!entry.enabled}`);
      setEntries(entries.map(e => 
        e.id === entry.id ? { ...e, enabled: !e.enabled } : e
      ));
    } catch (error) {
      console.error('Failed to toggle knowledge:', error);
      toast({
        title: 'Failed to toggle',
        status: 'error',
        duration: 2000,
      });
    }
  };
  
  // Delete entry
  const handleDelete = async (entry) => {
    if (!confirm('Are you sure you want to delete this knowledge entry?')) return;
    
    try {
      await api.delete(`/knowledge/${entry.id}`);
      setEntries(entries.filter(e => e.id !== entry.id));
      toast({
        title: 'Knowledge deleted',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      console.error('Failed to delete knowledge:', error);
      toast({
        title: 'Failed to delete',
        status: 'error',
        duration: 2000,
      });
    }
  };
  
  // Accept suggestion
  const handleAcceptSuggestion = async (suggestion) => {
    try {
      await api.post(`/knowledge/suggestions/${suggestion.id}/accept`);
      setSuggestions(suggestions.filter(s => s.id !== suggestion.id));
      loadKnowledge();
      toast({
        title: 'Suggestion accepted',
        description: 'Added to your knowledge base',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      console.error('Failed to accept suggestion:', error);
      toast({
        title: 'Failed to accept',
        status: 'error',
        duration: 2000,
      });
    }
  };
  
  // Dismiss suggestion
  const handleDismissSuggestion = async (suggestion) => {
    try {
      await api.post(`/knowledge/suggestions/${suggestion.id}/dismiss`);
      setSuggestions(suggestions.filter(s => s.id !== suggestion.id));
    } catch (error) {
      console.error('Failed to dismiss suggestion:', error);
    }
  };
  
  // Open edit modal
  const openEditModal = (entry = null) => {
    setEditingEntry(entry);
    setFormData(entry ? { title: entry.title, content: entry.content } : { title: '', content: '' });
    onOpen();
  };
  
  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };
  
  return (
    <Box>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={4}>
        <HStack spacing={2}>
          <FaBook color={scope === 'personal' ? '#3182ce' : '#805ad5'} />
          <Text fontSize="lg" fontWeight="600" color={textPrimary}>
            {scope === 'personal' ? 'My Knowledge' : 'Company Knowledge'}
          </Text>
          <Badge colorScheme={scope === 'personal' ? 'blue' : 'purple'} fontSize="xs">
            {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
          </Badge>
        </HStack>
        
        <Button
          leftIcon={<FaPlus />}
          colorScheme="brand"
          size="sm"
          onClick={() => openEditModal()}
          isDisabled={scope === 'company' && !isAdmin}
        >
          Add Knowledge
        </Button>
      </Flex>
      
      {/* Search */}
      <InputGroup mb={4}>
        <InputLeftElement pointerEvents="none">
          <FaSearch color="gray.400" />
        </InputLeftElement>
        <Input
          placeholder="Search knowledge..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          bg={bgColor}
          borderColor={borderColor}
        />
      </InputGroup>
      
      {/* AI Suggestions */}
      {suggestions.length > 0 && (
        <Box mb={4}>
          <Flex 
            align="center" 
            justify="space-between" 
            cursor="pointer"
            onClick={() => setShowSuggestions(!showSuggestions)}
            mb={2}
          >
            <HStack spacing={2}>
              <FaLightbulb color="#ECC94B" />
              <Text fontSize="sm" fontWeight="600" color={textPrimary}>
                Suggested for You
              </Text>
              <Badge colorScheme="yellow" fontSize="xs">{suggestions.length}</Badge>
            </HStack>
            <Text fontSize="xs" color={textSecondary}>
              {showSuggestions ? 'Hide' : 'Show'}
            </Text>
          </Flex>
          
          <Collapse in={showSuggestions}>
            <VStack spacing={2} align="stretch">
              {suggestions.map((suggestion) => (
                <Box
                  key={suggestion.id}
                  p={3}
                  bg={suggestionBg}
                  borderRadius="md"
                  borderWidth="1px"
                  borderColor={suggestionBorder}
                >
                  <Flex justify="space-between" align="start" mb={2}>
                    <HStack spacing={2}>
                      <FaRobot size={14} color="#3182ce" />
                      <Text fontSize="sm" fontWeight="600" color={textPrimary}>
                        {suggestion.title}
                      </Text>
                    </HStack>
                    <HStack spacing={1}>
                      <IconButton
                        icon={<FaCheck />}
                        size="xs"
                        colorScheme="green"
                        variant="ghost"
                        onClick={() => handleAcceptSuggestion(suggestion)}
                        title="Accept"
                        aria-label="Accept suggestion"
                      />
                      <IconButton
                        icon={<FaTimes />}
                        size="xs"
                        colorScheme="red"
                        variant="ghost"
                        onClick={() => handleDismissSuggestion(suggestion)}
                        title="Dismiss"
                        aria-label="Dismiss suggestion"
                      />
                    </HStack>
                  </Flex>
                  <Text fontSize="xs" color={textSecondary} noOfLines={2}>
                    {suggestion.content}
                  </Text>
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    Detected {suggestion.detection_count} times • {Math.round(suggestion.confidence * 100)}% confidence
                  </Text>
                </Box>
              ))}
            </VStack>
          </Collapse>
          
          <Divider my={4} />
        </Box>
      )}
      
      {/* Loading */}
      {loading ? (
        <Flex justify="center" py={8}>
          <Spinner size="lg" color="brand.500" />
        </Flex>
      ) : filteredEntries.length === 0 ? (
        <Box textAlign="center" py={8}>
          <Text color={textSecondary}>
            {searchQuery ? 'No matching knowledge found' : 'No knowledge entries yet'}
          </Text>
          <Text fontSize="sm" color={textSecondary} mt={1}>
            {scope === 'personal' 
              ? 'Add knowledge that will be used in your content generation and analysis.'
              : 'Add company-wide knowledge that applies to all team members.'}
          </Text>
        </Box>
      ) : (
        /* Knowledge Entries List */
        <VStack spacing={3} align="stretch">
          {filteredEntries.map((entry) => (
            <Card
              key={entry.id}
              p={4}
              bg={bgColor}
              borderWidth="1px"
              borderColor={borderColor}
              opacity={entry.enabled ? 1 : 0.6}
            >
              <Flex justify="space-between" align="start">
                <Box flex={1} mr={4}>
                  <HStack spacing={2} mb={1}>
                    <Text fontWeight="600" color={textPrimary}>
                      {entry.title}
                    </Text>
                    {entry.source === 'accepted_suggestion' && (
                      <Badge colorScheme="blue" fontSize="xs">AI Suggested</Badge>
                    )}
                  </HStack>
                  <Text fontSize="sm" color={textSecondary} noOfLines={2}>
                    {entry.content}
                  </Text>
                  <HStack spacing={4} mt={2}>
                    <Text fontSize="xs" color="gray.500">
                      Created {formatDate(entry.created_at)}
                    </Text>
                    {entry.usage_count > 0 && (
                      <Text fontSize="xs" color="gray.500">
                        Used {entry.usage_count} {entry.usage_count === 1 ? 'time' : 'times'}
                      </Text>
                    )}
                  </HStack>
                </Box>
                
                <HStack spacing={2}>
                  <Switch
                    isChecked={entry.enabled}
                    onChange={() => handleToggle(entry)}
                    colorScheme="brand"
                    size="md"
                  />
                  <Menu>
                    <MenuButton
                      as={IconButton}
                      icon={<FaEllipsisV />}
                      variant="ghost"
                      size="sm"
                    />
                    <MenuList>
                      <MenuItem icon={<FaEdit />} onClick={() => openEditModal(entry)}>
                        Edit
                      </MenuItem>
                      <MenuItem icon={<FaTrash />} color="red.500" onClick={() => handleDelete(entry)}>
                        Delete
                      </MenuItem>
                    </MenuList>
                  </Menu>
                </HStack>
              </Flex>
            </Card>
          ))}
        </VStack>
      )}
      
      {/* Create/Edit Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg" isCentered>
        <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
        <ModalContent bg={bgColor}>
          <ModalHeader>
            {editingEntry ? 'Edit Knowledge' : 'Add Knowledge'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Title</FormLabel>
                <Input
                  placeholder="e.g., Brand Terminology"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  maxLength={200}
                />
              </FormControl>
              
              <FormControl isRequired>
                <FormLabel>Content</FormLabel>
                <Textarea
                  placeholder="Describe the knowledge, rule, or preference..."
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={6}
                  maxLength={5000}
                />
                <Text fontSize="xs" color="gray.500" mt={1}>
                  This knowledge will be automatically applied when generating or analyzing content.
                </Text>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={handleSave}
              isLoading={saving}
            >
              {editingEntry ? 'Save Changes' : 'Add Knowledge'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
