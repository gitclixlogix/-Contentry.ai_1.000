/**
 * ConfirmationModal - Reusable modal for confirmation actions
 * 
 * Standardized modal for delete, approve, reject, and other confirmation actions.
 * 
 * Props:
 * - isOpen (boolean, required): Whether modal is open
 * - onClose (function, required): Close handler
 * - onConfirm (function, required): Confirm action handler
 * - title (string, required): Modal title
 * - message (string | ReactNode): Modal body content
 * - confirmText (string): Confirm button text (default: 'Confirm')
 * - cancelText (string): Cancel button text (default: 'Cancel')
 * - confirmColor (string): Confirm button color scheme (default: 'red')
 * - isLoading (boolean): Loading state for confirm button
 * - icon (IconType): Optional icon to display
 */

import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  HStack,
  Icon,
  Text,
  VStack
} from '@chakra-ui/react';
import { FiAlertTriangle } from 'react-icons/fi';

export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmColor = 'red',
  isLoading = false,
  icon,
  size = 'md'
}) {
  const handleConfirm = async () => {
    await onConfirm();
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      size={size}
      isCentered
    >
      <ModalOverlay bg="blackAlpha.600" />
      <ModalContent mx={4}>
        <ModalHeader pb={2}>{title}</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <HStack spacing={4} align="start">
            {icon && (
              <Icon 
                as={icon} 
                boxSize={6} 
                color={`${confirmColor}.500`}
                mt={1}
              />
            )}
            <VStack align="start" spacing={2} flex={1}>
              {typeof message === 'string' ? (
                <Text color="gray.600">{message}</Text>
              ) : (
                message
              )}
            </VStack>
          </HStack>
        </ModalBody>
        <ModalFooter pt={4}>
          <HStack spacing={3}>
            <Button 
              variant="ghost" 
              onClick={onClose}
              isDisabled={isLoading}
            >
              {cancelText}
            </Button>
            <Button
              colorScheme={confirmColor}
              onClick={handleConfirm}
              isLoading={isLoading}
              loadingText="Processing..."
            >
              {confirmText}
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

// Pre-configured delete modal with customizable props
export function DeleteConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  itemName = 'this item',
  isLoading = false,
  title = 'Delete Confirmation',
  confirmText = 'Delete',
  confirmColorScheme = 'red'
}) {
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      title={title}
      message={`Are you sure you want to delete ${itemName}? This action cannot be undone.`}
      confirmText={confirmText}
      confirmColor={confirmColorScheme}
      isLoading={isLoading}
      icon={FiAlertTriangle}
    />
  );
}

// Pre-configured approve modal
export function ApproveConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  itemName = 'this item',
  isLoading = false
}) {
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Approve Confirmation"
      message={`Are you sure you want to approve ${itemName}?`}
      confirmText="Approve"
      confirmColor="green"
      isLoading={isLoading}
    />
  );
}

export default ConfirmationModal;
