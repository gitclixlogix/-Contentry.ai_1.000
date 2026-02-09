'use client';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useColorModeValue,
  Box,
} from '@chakra-ui/react';

export default function ChartModal({ isOpen, onClose, title, children }) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl" isCentered>
      <ModalOverlay bg="blackAlpha.600" />
      <ModalContent bg={bgColor} mx={4} maxH="90vh">
        <ModalHeader color={textColor} fontSize={{ base: 'md', md: 'lg' }}>
          {title}
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6} overflowY="auto">
          <Box minH="400px" h={{ base: '350px', md: '450px', lg: '500px' }}>
            {children}
          </Box>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}
