'use client';

import {
  Box,
  Flex,
  Text,
  Button,
  Input,
  VStack,
  HStack,
  Badge,
  Icon,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  FormHelperText,
  Textarea,
  Checkbox,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Tooltip,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  Sparkles,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  GitBranch,
} from 'lucide-react';

// Risk level colors and icons
const RISK_LEVELS = {
  low: { color: 'green', icon: CheckCircle, label: 'Low Risk' },
  medium: { color: 'yellow', icon: AlertCircle, label: 'Medium Risk' },
  high: { color: 'orange', icon: AlertTriangle, label: 'High Risk' },
  critical: { color: 'red', icon: AlertTriangle, label: 'Critical' },
};

// Color options for roles
const COLOR_OPTIONS = [
  { value: '#3b82f6', label: 'Blue' },
  { value: '#3B82F6', label: 'Blue' },
  { value: '#10B981', label: 'Green' },
  { value: '#F59E0B', label: 'Amber' },
  { value: '#EF4444', label: 'Red' },
  { value: '#EC4899', label: 'Pink' },
  { value: '#6366F1', label: 'Indigo' },
  { value: '#14B8A6', label: 'Teal' },
];

export default function RoleFormModal({
  isOpen,
  onClose,
  selectedRole,
  formData,
  setFormData,
  permissions,
  inheritanceRules,
  onSave,
  isSubmitting,
}) {
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textSecondary = useColorModeValue('gray.600', 'gray.400');

  // Get inherited permissions for a given permission key
  const getInheritedPermissions = (permKey) => {
    const rule = inheritanceRules?.find((r) => r.parent_permission === permKey);
    return rule?.grants_permissions || [];
  };

  // Toggle a single permission
  const togglePermission = (permKey) => {
    if (selectedRole?.is_system_role) return;
    
    setFormData((prev) => {
      const newPerms = prev.permissions.includes(permKey)
        ? prev.permissions.filter((p) => p !== permKey)
        : [...prev.permissions, permKey];
      return { ...prev, permissions: newPerms };
    });
  };

  // Toggle all permissions in a category
  const toggleCategoryPermissions = (category) => {
    if (selectedRole?.is_system_role) return;
    
    const categoryPermKeys = category.permissions.map((p) => p.key);
    const allSelected = categoryPermKeys.every((k) => formData.permissions.includes(k));

    setFormData((prev) => {
      const newPerms = allSelected
        ? prev.permissions.filter((p) => !categoryPermKeys.includes(p))
        : [...new Set([...prev.permissions, ...categoryPermKeys])];
      return { ...prev, permissions: newPerms };
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" scrollBehavior="inside">
      <ModalOverlay backdropFilter="blur(4px)" />
      <ModalContent maxH="90vh">
        <ModalHeader>
          {selectedRole
            ? selectedRole.is_system_role
              ? `View Role: ${selectedRole.name}`
              : `Edit Role: ${selectedRole.name}`
            : 'Create New Role'}
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={5} align="stretch">
            {/* Role Name */}
            <FormControl isRequired isDisabled={selectedRole?.is_system_role}>
              <FormLabel>Role Name</FormLabel>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Legal Reviewer"
              />
            </FormControl>

            {/* Description */}
            <FormControl isDisabled={selectedRole?.is_system_role}>
              <FormLabel>Description</FormLabel>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe what this role can do..."
                rows={2}
              />
            </FormControl>

            {/* Color Selection */}
            <FormControl isDisabled={selectedRole?.is_system_role}>
              <FormLabel>Role Color</FormLabel>
              <HStack spacing={2} flexWrap="wrap">
                {COLOR_OPTIONS.map((color) => (
                  <Box
                    key={color.value}
                    w="32px"
                    h="32px"
                    bg={color.value}
                    borderRadius="md"
                    cursor="pointer"
                    border={formData.color === color.value ? '3px solid' : '2px solid'}
                    borderColor={formData.color === color.value ? 'white' : 'transparent'}
                    boxShadow={formData.color === color.value ? '0 0 0 2px black' : 'none'}
                    onClick={() => setFormData({ ...formData, color: color.value })}
                    _hover={{ transform: 'scale(1.1)' }}
                    transition="all 0.2s"
                  />
                ))}
              </HStack>
            </FormControl>

            {/* Permissions */}
            <FormControl>
              <FormLabel>
                <Flex justify="space-between" align="center">
                  <Text>Permissions</Text>
                  <Badge colorScheme="brand">
                    {formData.permissions.includes('*')
                      ? 'All'
                      : formData.permissions.length}{' '}
                    selected
                  </Badge>
                </Flex>
              </FormLabel>
              <FormHelperText mb={3}>
                Select the permissions this role should have. High-risk permissions are highlighted.
              </FormHelperText>

              {selectedRole?.permissions?.includes('*') ? (
                <Box p={4} bg="brand.50" borderRadius="lg" textAlign="center">
                  <Icon as={Sparkles} color="brand.500" boxSize={6} mb={2} />
                  <Text color="brand.700" fontWeight="medium">
                    This role has all permissions
                  </Text>
                </Box>
              ) : (
                <Accordion allowMultiple defaultIndex={[0]}>
                  {permissions.map((category) => {
                    const categoryPermKeys = category.permissions.map((p) => p.key);
                    const selectedCount = categoryPermKeys.filter((k) =>
                      formData.permissions.includes(k)
                    ).length;
                    const allSelected = selectedCount === categoryPermKeys.length;

                    return (
                      <AccordionItem key={category.key} border="1px solid" borderColor={borderColor} borderRadius="lg" mb={2}>
                        <AccordionButton py={3}>
                          <Flex flex="1" justify="space-between" align="center" pr={2}>
                            <HStack spacing={3}>
                              <Text fontWeight="medium">{category.name}</Text>
                              <Badge colorScheme={selectedCount > 0 ? 'brand' : 'gray'} variant="subtle">
                                {selectedCount}/{category.permissions.length}
                              </Badge>
                            </HStack>
                            {!selectedRole?.is_system_role && (
                              <Button
                                size="xs"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleCategoryPermissions(category);
                                }}
                              >
                                {allSelected ? 'Clear All' : 'Select All'}
                              </Button>
                            )}
                          </Flex>
                          <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4}>
                          <VStack align="stretch" spacing={2}>
                            {category.permissions.map((perm) => {
                              const riskInfo = RISK_LEVELS[perm.risk_level] || RISK_LEVELS.low;
                              const RiskIcon = riskInfo.icon;
                              const inheritedPerms = getInheritedPermissions(perm.key);
                              const hasInheritance = inheritedPerms.length > 0;

                              return (
                                <Flex
                                  key={perm.key}
                                  justify="space-between"
                                  align="center"
                                  p={2}
                                  borderRadius="md"
                                  bg={formData.permissions.includes(perm.key) ? 'brand.50' : 'transparent'}
                                  _hover={{ bg: 'gray.50' }}
                                >
                                  <Checkbox
                                    isChecked={formData.permissions.includes(perm.key)}
                                    onChange={() => togglePermission(perm.key)}
                                    isDisabled={selectedRole?.is_system_role}
                                    flex="1"
                                  >
                                    <VStack align="start" spacing={0} ml={2}>
                                      <HStack spacing={2}>
                                        <Text fontSize="sm" fontWeight="medium">
                                          {perm.name}
                                        </Text>
                                        {hasInheritance && (
                                          <Tooltip label={`Also grants: ${inheritedPerms.join(', ')}`}>
                                            <Badge colorScheme="blue" variant="subtle" fontSize="xs">
                                              <HStack spacing={1}>
                                                <GitBranch size={8} />
                                                <span>+{inheritedPerms.length}</span>
                                              </HStack>
                                            </Badge>
                                          </Tooltip>
                                        )}
                                      </HStack>
                                      <Text fontSize="xs" color={textSecondary}>
                                        {perm.description}
                                      </Text>
                                    </VStack>
                                  </Checkbox>
                                  {(perm.risk_level === 'high' || perm.risk_level === 'critical') && (
                                    <Tooltip label={riskInfo.label}>
                                      <Badge
                                        colorScheme={riskInfo.color}
                                        variant="subtle"
                                        fontSize="xs"
                                      >
                                        <HStack spacing={1}>
                                          <RiskIcon size={10} />
                                          <span>{riskInfo.label}</span>
                                        </HStack>
                                      </Badge>
                                    </Tooltip>
                                  )}
                                </Flex>
                              );
                            })}
                          </VStack>
                        </AccordionPanel>
                      </AccordionItem>
                    );
                  })}
                </Accordion>
              )}
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          {!selectedRole?.is_system_role && (
            <Button
              variant="primary"
              onClick={onSave}
              isLoading={isSubmitting}
              isDisabled={!formData.name.trim()}
            >
              {selectedRole ? 'Save Changes' : 'Create Role'}
            </Button>
          )}
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
