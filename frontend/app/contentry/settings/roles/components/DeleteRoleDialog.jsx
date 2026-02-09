'use client';

import {
  Box,
  Flex,
  Text,
  Button,
  Icon,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
} from '@chakra-ui/react';
import { AlertTriangle } from 'lucide-react';
import { useRef } from 'react';

export default function DeleteRoleDialog({
  isOpen,
  onClose,
  selectedRole,
  onDelete,
  isSubmitting,
}) {
  const cancelRef = useRef();

  return (
    <AlertDialog isOpen={isOpen} onClose={onClose} isCentered leastDestructiveRef={cancelRef}>
      <AlertDialogOverlay>
        <AlertDialogContent>
          <AlertDialogHeader fontSize="lg" fontWeight="bold">
            Delete Role
          </AlertDialogHeader>
          <AlertDialogBody>
            Are you sure you want to delete the role "{selectedRole?.name}"?
            {selectedRole?.user_count > 0 && (
              <Box mt={3} p={3} bg="orange.50" borderRadius="md">
                <Flex align="center" gap={2}>
                  <Icon as={AlertTriangle} color="orange.500" />
                  <Text fontSize="sm" color="orange.700">
                    {selectedRole.user_count} user(s) currently have this role. They will lose all
                    permissions associated with this role.
                  </Text>
                </Flex>
              </Box>
            )}
          </AlertDialogBody>
          <AlertDialogFooter>
            <Button ref={cancelRef} onClick={onClose}>Cancel</Button>
            <Button colorScheme="red" onClick={onDelete} ml={3} isLoading={isSubmitting}>
              Delete
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialogOverlay>
    </AlertDialog>
  );
}
