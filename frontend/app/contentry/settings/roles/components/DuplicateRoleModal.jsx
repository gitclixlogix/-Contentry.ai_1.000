'use client';

import {
  Box,
  Flex,
  Text,
  Button,
  Input,
  VStack,
  HStack,
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
  Textarea,
} from '@chakra-ui/react';
import { Copy, GitBranch } from 'lucide-react';

export default function DuplicateRoleModal({
  isOpen,
  onClose,
  selectedRole,
  duplicateForm,
  setDuplicateForm,
  onSubmit,
  isSubmitting,
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md" isCentered>
      <ModalOverlay backdropFilter="blur(4px)" />
      <ModalContent>
        <ModalHeader>
          <HStack spacing={2}>
            <Icon as={Copy} color="brand.500" />
            <Text>Duplicate Role</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4} align="stretch">
            <Box p={3} bg="blue.50" borderRadius="md">
              <Flex align="center" gap={2}>
                <Icon as={GitBranch} color="blue.500" />
                <Text fontSize="sm" color="blue.700">
                  Creating a copy of <strong>{selectedRole?.name}</strong> with{' '}
                  {selectedRole?.permissions?.length || 0} permissions
                </Text>
              </Flex>
            </Box>

            <FormControl isRequired>
              <FormLabel>New Role Name</FormLabel>
              <Input
                value={duplicateForm.new_name}
                onChange={(e) => setDuplicateForm({ ...duplicateForm, new_name: e.target.value })}
                placeholder="Enter new role name"
              />
            </FormControl>

            <FormControl>
              <FormLabel>Description</FormLabel>
              <Textarea
                value={duplicateForm.new_description}
                onChange={(e) => setDuplicateForm({ ...duplicateForm, new_description: e.target.value })}
                placeholder="Optional description"
                rows={2}
              />
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            leftIcon={<Copy size={16} />}
            onClick={onSubmit}
            isLoading={isSubmitting}
            isDisabled={!duplicateForm.new_name.trim()}
          >
            Create Copy
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
