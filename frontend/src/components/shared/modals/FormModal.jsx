/**
 * FormModal - Reusable modal for form-based dialogs
 * 
 * Standardized modal for create/edit forms with validation and async submit.
 * 
 * Props:
 * - isOpen (boolean, required): Whether modal is open
 * - onClose (function, required): Close handler
 * - onSubmit (function, required): Form submit handler (async supported)
 * - title (string, required): Modal title
 * - children (ReactNode, required): Form content
 * - submitText (string): Submit button text (default: 'Save')
 * - cancelText (string): Cancel button text (default: 'Cancel')
 * - submitColor (string): Submit button color scheme (default: 'brand')
 * - isLoading (boolean): Loading state for submit button
 * - isDisabled (boolean): Disable submit button
 * - size (string): Modal size - 'sm', 'md', 'lg', 'xl', 'full'
 * - showFooter (boolean): Whether to show footer buttons (default: true)
 * - scrollBehavior (string): 'inside' or 'outside' (default: 'inside')
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
  useColorModeValue
} from '@chakra-ui/react';

export function FormModal({
  isOpen,
  onClose,
  onSubmit,
  title,
  children,
  submitText = 'Save',
  cancelText = 'Cancel',
  submitColor = 'brand',
  isLoading = false,
  isDisabled = false,
  size = 'md',
  showFooter = true,
  scrollBehavior = 'inside',
  maxH = '90vh'
}) {
  const overlayBg = useColorModeValue('blackAlpha.600', 'blackAlpha.700');
  
  const handleSubmit = async (e) => {
    e?.preventDefault();
    await onSubmit();
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      size={size}
      scrollBehavior={scrollBehavior}
      isCentered
    >
      <ModalOverlay bg={overlayBg} backdropFilter="blur(4px)" />
      <ModalContent mx={4} maxH={maxH}>
        <ModalHeader pb={2}>{title}</ModalHeader>
        <ModalCloseButton />
        <ModalBody as="form" onSubmit={handleSubmit}>
          {children}
        </ModalBody>
        {showFooter && (
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
                colorScheme={submitColor}
                onClick={handleSubmit}
                isLoading={isLoading}
                isDisabled={isDisabled}
                loadingText="Saving..."
              >
                {submitText}
              </Button>
            </HStack>
          </ModalFooter>
        )}
      </ModalContent>
    </Modal>
  );
}

// Pre-configured create modal
export function CreateFormModal({
  isOpen,
  onClose,
  onSubmit,
  entityName = 'Item',
  children,
  isLoading = false,
  isDisabled = false,
  size = 'md'
}) {
  return (
    <FormModal
      isOpen={isOpen}
      onClose={onClose}
      onSubmit={onSubmit}
      title={`Create ${entityName}`}
      submitText="Create"
      submitColor="brand"
      isLoading={isLoading}
      isDisabled={isDisabled}
      size={size}
    >
      {children}
    </FormModal>
  );
}

// Pre-configured edit modal
export function EditFormModal({
  isOpen,
  onClose,
  onSubmit,
  entityName = 'Item',
  children,
  isLoading = false,
  isDisabled = false,
  size = 'md'
}) {
  return (
    <FormModal
      isOpen={isOpen}
      onClose={onClose}
      onSubmit={onSubmit}
      title={`Edit ${entityName}`}
      submitText="Save Changes"
      submitColor="brand"
      isLoading={isLoading}
      isDisabled={isDisabled}
      size={size}
    >
      {children}
    </FormModal>
  );
}

export default FormModal;
