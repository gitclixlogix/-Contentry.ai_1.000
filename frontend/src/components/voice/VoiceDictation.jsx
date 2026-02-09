'use client';
import { useState, useEffect, useRef } from 'react';
import {
  IconButton,
  Tooltip,
  Box,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  VStack,
  Text,
  HStack,
  Button,
  useDisclosure,
  useColorModeValue
} from '@chakra-ui/react';
import { FaMicrophone, FaStop, FaHeadphones } from 'react-icons/fa';

export default function VoiceDictation({ onTranscript, placeholder = "Click microphone to start dictation" }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const recognitionRef = useRef(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const bgColor = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    // Initialize Speech Recognition
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = 'en-US';

        recognitionRef.current.onresult = (event) => {
          let interim = '';
          let final = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcriptPiece = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              final += transcriptPiece + ' ';
            } else {
              interim += transcriptPiece;
            }
          }

          if (final) {
            setTranscript(prev => prev + final);
            setInterimTranscript('');
          } else {
            setInterimTranscript(interim);
          }
        };

        recognitionRef.current.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          if (event.error === 'no-speech') {
            // Continue listening
            return;
          }
          setIsListening(false);
        };

        recognitionRef.current.onend = () => {
          if (isListening) {
            // Restart if still supposed to be listening
            try {
              recognitionRef.current.start();
            } catch (e) {
              console.log('Recognition restart failed:', e);
            }
          }
        };
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isListening]);

  const startListening = () => {
    if (recognitionRef.current) {
      setTranscript('');
      setInterimTranscript('');
      setIsListening(true);
      onOpen();
      
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.log('Recognition already started');
      }
    } else {
      alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const handleDone = () => {
    stopListening();
    const finalText = transcript + interimTranscript;
    if (finalText.trim() && onTranscript) {
      onTranscript(finalText.trim());
    }
    onClose();
  };

  const handleCancel = () => {
    stopListening();
    setTranscript('');
    setInterimTranscript('');
    onClose();
  };

  const openVoiceAgent = () => {
    // Trigger the ElevenLabs widget to open
    const widget = document.querySelector('elevenlabs-convai');
    if (widget) {
      // Different methods to open the widget based on version
      if (typeof widget.open === 'function') {
        widget.open();
      } else if (typeof widget.click === 'function') {
        widget.click();
      } else {
        // Dispatch a click event on the widget
        const clickEvent = new MouseEvent('click', {
          bubbles: true,
          cancelable: true,
          view: window
        });
        widget.dispatchEvent(clickEvent);
      }
    } else {
      // Widget not loaded yet - it will appear as floating button
      console.log('Olivia Voice Agent widget will appear shortly...');
    }
  };

  return (
    <>
      <Tooltip label="Voice Dictation (Speech-to-Text)" placement="top">
        <IconButton
          icon={<FaMicrophone />}
          onClick={startListening}
          colorScheme="blue"
          variant="ghost"
          size="md"
          aria-label="Start voice dictation"
        />
      </Tooltip>

      {/* Dictation Modal */}
      <Modal isOpen={isOpen} onClose={handleCancel} size="xl" isCentered>
        <ModalOverlay backdropFilter="blur(10px)" />
        <ModalContent bg={bgColor}>
          <ModalHeader>Voice Dictation</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={6} align="stretch">
              {/* Microphone Animation */}
              <Box textAlign="center" py={6}>
                <Box
                  as={FaMicrophone}
                  fontSize="64px"
                  color={isListening ? "red.500" : "gray.400"}
                  transition="all 0.3s"
                  sx={{
                    '@keyframes pulse': {
                      '0%': { transform: 'scale(1)', opacity: 1 },
                      '50%': { transform: 'scale(1.1)', opacity: 0.8 },
                      '100%': { transform: 'scale(1)', opacity: 1 }
                    },
                    animation: isListening ? 'pulse 1.5s ease-in-out infinite' : 'none'
                  }}
                />
                <Text mt={4} fontWeight="600" fontSize="lg">
                  {isListening ? "Listening..." : "Click microphone to start"}
                </Text>
                <Text fontSize="sm" color="gray.500" mt={2}>
                  Speak clearly into your microphone
                </Text>
              </Box>

              {/* Transcript Display */}
              <Box
                minH="120px"
                maxH="300px"
                overflowY="auto"
                p={4}
                borderWidth="1px"
                borderRadius="md"
                borderColor={useColorModeValue('gray.200', 'gray.600')}
                bg={useColorModeValue('gray.50', 'gray.700')}
              >
                <Text whiteSpace="pre-wrap">
                  {transcript}
                  <Text as="span" color="gray.400">
                    {interimTranscript}
                  </Text>
                  {!transcript && !interimTranscript && (
                    <Text color="gray.400" fontStyle="italic">
                      Your speech will appear here...
                    </Text>
                  )}
                </Text>
              </Box>

              {/* Action Buttons */}
              <HStack justify="space-between">
                <HStack>
                  {isListening ? (
                    <Button
                      leftIcon={<FaStop />}
                      colorScheme="red"
                      onClick={stopListening}
                      size="md"
                    >
                      Stop
                    </Button>
                  ) : (
                    <Button
                      leftIcon={<FaMicrophone />}
                      colorScheme="blue"
                      onClick={startListening}
                      size="md"
                    >
                      Start Recording
                    </Button>
                  )}
                </HStack>
                
                <HStack>
                  <Button variant="ghost" onClick={handleCancel}>
                    Cancel
                  </Button>
                  <Button
                    colorScheme="brand"
                    onClick={handleDone}
                    isDisabled={!transcript.trim()}
                  >
                    Use Text
                  </Button>
                </HStack>
              </HStack>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
}
