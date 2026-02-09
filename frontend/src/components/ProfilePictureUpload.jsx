'use client';
import { useState, useRef } from 'react';
import {
  Avatar,
  Box,
  IconButton,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  VStack,
  useDisclosure,
  Input,
  Text,
  useToast,
} from '@chakra-ui/react';
import { FaCamera, FaUpload } from 'react-icons/fa';
import { getImageUrl } from '@/lib/api';

export default function ProfilePictureUpload({ 
  user, 
  size = "lg", 
  showEditIcon = true,
  onUploadSuccess 
}) {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [showCamera, setShowCamera] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);
  const toast = useToast();

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'user' },
        audio: false 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
      setShowCamera(true);
    } catch (error) {
      toast({
        title: 'Camera Error',
        description: 'Could not access camera. Please check permissions.',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowCamera(false);
    setCapturedImage(null);
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      
      const imageData = canvas.toDataURL('image/jpeg');
      setCapturedImage(imageData);
      stopCamera();
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setCapturedImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const saveProfilePicture = () => {
    if (capturedImage) {
      // Update user's profile picture in localStorage
      const savedUser = localStorage.getItem('contentry_user');
      if (savedUser) {
        const userData = JSON.parse(savedUser);
        userData.profile_picture = capturedImage;
        localStorage.setItem('contentry_user', JSON.stringify(userData));
        
        toast({
          title: 'Profile Picture Updated',
          description: 'Your profile picture has been saved successfully!',
          status: 'success',
          duration: 3000,
        });

        if (onUploadSuccess) {
          onUploadSuccess(capturedImage);
        }

        onClose();
        setCapturedImage(null);
        
        // Reload page to show new picture
        window.location.reload();
      }
    }
  };

  const handleModalClose = () => {
    stopCamera();
    setCapturedImage(null);
    onClose();
  };

  return (
    <>
      <Box position="relative" display="inline-block">
        <Avatar
          size={size}
          name={user?.full_name || "User"}
          src={getImageUrl(user?.profile_picture) || "https://i.pravatar.cc/150?img=12"}
          border="3px solid"
          borderColor="brand.500"
          cursor={showEditIcon ? "pointer" : "default"}
          onClick={showEditIcon ? onOpen : undefined}
        />
        {showEditIcon && (
          <IconButton
            icon={<FaCamera />}
            size="sm"
            colorScheme="brand"
            borderRadius="full"
            position="absolute"
            bottom="0"
            right="0"
            onClick={onOpen}
            aria-label="Upload picture"
          />
        )}
      </Box>

      <Modal isOpen={isOpen} onClose={handleModalClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Update Profile Picture</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              {!showCamera && !capturedImage && (
                <>
                  <Text fontSize="sm" color="gray.600" textAlign="center">
                    Choose how you'd like to add your profile picture
                  </Text>
                  
                  <Button
                    leftIcon={<FaCamera />}
                    colorScheme="brand"
                    onClick={startCamera}
                    width="100%"
                    size="lg"
                  >
                    Take a Photo
                  </Button>

                  <Button
                    leftIcon={<FaUpload />}
                    colorScheme="blue"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    width="100%"
                    size="lg"
                  >
                    Upload from Device
                  </Button>

                  <Input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    display="none"
                    onChange={handleFileUpload}
                  />

                  <Text fontSize="xs" color="gray.500" textAlign="center">
                    Recommended: Square image, at least 200x200px
                  </Text>
                </>
              )}

              {showCamera && (
                <Box width="100%">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    style={{
                      width: '100%',
                      borderRadius: '8px',
                      transform: 'scaleX(-1)',
                    }}
                  />
                  <canvas ref={canvasRef} style={{ display: 'none' }} />
                  
                  <VStack spacing={2} mt={4}>
                    <Button
                      colorScheme="green"
                      onClick={capturePhoto}
                      width="100%"
                    >
                      📸 Capture Photo
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={stopCamera}
                      width="100%"
                    >
                      Cancel
                    </Button>
                  </VStack>
                </Box>
              )}

              {capturedImage && (
                <Box width="100%">
                  <Box
                    width="100%"
                    height="300px"
                    backgroundImage={`url(${capturedImage})`}
                    backgroundSize="cover"
                    backgroundPosition="center"
                    borderRadius="md"
                    border="2px solid"
                    borderColor="brand.500"
                  />
                  
                  <VStack spacing={2} mt={4}>
                    <Button
                      colorScheme="green"
                      onClick={saveProfilePicture}
                      width="100%"
                    >
                      ✅ Save Picture
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setCapturedImage(null);
                        startCamera();
                      }}
                      width="100%"
                    >
                      🔄 Retake
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => setCapturedImage(null)}
                      width="100%"
                    >
                      Cancel
                    </Button>
                  </VStack>
                </Box>
              )}
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
}
