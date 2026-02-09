'use client';
import { useEffect, useState, useRef, useCallback } from 'react';
import { 
  IconButton, 
  Tooltip, 
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Box,
  Text,
  VStack,
  HStack,
  Icon
} from '@chakra-ui/react';
import { FaHeadphones } from 'react-icons/fa';

export default function VoiceAssistant({ compact = true }) {
  const [isScriptLoaded, setIsScriptLoaded] = useState(false);
  const [widgetReady, setWidgetReady] = useState(false);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const widgetContainerRef = useRef(null);
  const widgetRef = useRef(null);

  useEffect(() => {
    // Check if the ElevenLabs script is loaded
    const checkScript = () => {
      // The script creates the custom element
      if (typeof window !== 'undefined' && window.customElements) {
        const isDefined = window.customElements.get('elevenlabs-convai');
        if (isDefined) {
          setIsScriptLoaded(true);
          return true;
        }
      }
      return false;
    };

    if (checkScript()) return;
    
    // Poll for script loading
    const interval = setInterval(() => {
      if (checkScript()) {
        clearInterval(interval);
      }
    }, 500);
    
    // Timeout after 10 seconds
    const timeout = setTimeout(() => {
      clearInterval(interval);
      // Set loaded anyway to show fallback message
      setIsScriptLoaded(true);
    }, 10000);
    
    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, []);

  // When modal opens, create the widget
  useEffect(() => {
    if (!isOpen) return;
    if (!widgetContainerRef.current) return;
    
    // Small delay to ensure modal is rendered
    const timer = setTimeout(() => {
      if (widgetContainerRef.current) {
        // Clear any existing widget
        widgetContainerRef.current.innerHTML = '';
        
        // Create new widget element
        const widget = document.createElement('elevenlabs-convai');
        widget.setAttribute('agent-id', 'agent_2101k2bjmvmnee9r91bsv9cnh9gg');
        widget.style.width = '100%';
        widget.style.minHeight = '300px';
        widget.style.display = 'block';
        
        widgetRef.current = widget;
        widgetContainerRef.current.appendChild(widget);
        setWidgetReady(true);
      }
    }, 300);
    
    return () => clearTimeout(timer);
  }, [isOpen]);

  // Cleanup when modal closes
  const handleClose = useCallback(() => {
    if (widgetContainerRef.current) {
      widgetContainerRef.current.innerHTML = '';
    }
    widgetRef.current = null;
    setWidgetReady(false);
    onClose();
  }, [onClose]);

  return (
    <>
      <Tooltip label="Talk with Olivia AI" placement="top">
        <IconButton
          icon={<FaHeadphones />}
          onClick={onOpen}
          colorScheme="brand"
          variant="ghost"
          size="sm"
          aria-label="Open Olivia Voice Assistant"
          data-testid="talk-olivia-btn"
        />
      </Tooltip>

      <Modal isOpen={isOpen} onClose={handleClose} size="lg" isCentered closeOnOverlayClick={false}>
        <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(8px)" zIndex={10000} />
        <ModalContent zIndex={10001} bg="white" _dark={{ bg: 'gray.800' }}>
          <ModalHeader borderBottom="1px" borderColor="gray.200" _dark={{ borderColor: 'gray.600' }}>
            <HStack spacing={3}>
              <Icon as={FaHeadphones} color="brand.500" />
              <Text fontWeight="600">Talk with Olivia AI</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody py={6}>
            <VStack spacing={4} align="center">
              {!isScriptLoaded ? (
                <VStack spacing={3} py={8}>
                  <Box className="loading-spinner" w="40px" h="40px" borderRadius="full" border="3px solid" borderColor="brand.200" borderTopColor="brand.500" />
                  <Text color="gray.500" fontSize="sm">Loading voice assistant...</Text>
                </VStack>
              ) : (
                <>
                  <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }} textAlign="center" mb={2}>
                    Click the microphone below to start talking with Olivia, your AI content assistant.
                  </Text>
                  <Box 
                    ref={widgetContainerRef} 
                    w="100%" 
                    minH="350px"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    bg="gray.50"
                    _dark={{ bg: 'gray.700' }}
                    borderRadius="lg"
                    border="1px dashed"
                    borderColor="gray.300"
                    p={4}
                  />
                  {!widgetReady && (
                    <Text fontSize="xs" color="gray.400">
                      Initializing voice interface...
                    </Text>
                  )}
                </>
              )}
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
}
