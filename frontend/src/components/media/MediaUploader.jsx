'use client';
import { useState } from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Text,
  Icon,
  Image,
  useColorModeValue,
} from '@chakra-ui/react';
import { FaImage, FaTimes, FaVideo } from 'react-icons/fa';

export default function MediaUploader({ onFileSelected, onFileRemoved }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      if (onFileSelected) {
        onFileSelected(file, url);
      }
    }
  };

  const handleRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    if (onFileRemoved) {
      onFileRemoved();
    }
  };

  const isVideo = selectedFile?.type?.startsWith('video/');

  return (
    <Box>
      <VStack align="stretch" spacing={4}>
        {/* Upload Section */}
        {!previewUrl && (
          <Box
            borderWidth="2px"
            borderStyle="dashed"
            borderColor={borderColor}
            borderRadius="md"
            p={6}
            textAlign="center"
            cursor="pointer"
            _hover={{ borderColor: 'brand.500', bg: hoverBg }}
            onClick={() => document.getElementById('media-upload-input').click()}
          >
            <input
              id="media-upload-input"
              type="file"
              accept="image/*,video/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            <Icon as={FaImage} boxSize={10} color="gray.400" mb={3} />
            <Text fontWeight="600" mb={1}>Upload Image or Video</Text>
            <Text fontSize="sm" color="gray.500">
              Click to browse or drag & drop
            </Text>
            <Text fontSize="xs" color="gray.400" mt={2}>
              Supported: JPG, PNG, GIF, MP4, MOV
            </Text>
          </Box>
        )}

        {/* Preview */}
        {previewUrl && (
          <Box position="relative">
            <HStack justify="space-between" mb={2}>
              <HStack>
                <Icon as={isVideo ? FaVideo : FaImage} color="brand.500" />
                <Text fontWeight="600" fontSize="sm" noOfLines={1}>
                  {selectedFile?.name}
                </Text>
              </HStack>
              <Button
                size="xs"
                variant="ghost"
                colorScheme="red"
                leftIcon={<FaTimes />}
                onClick={handleRemove}
              >
                Remove
              </Button>
            </HStack>
            
            {isVideo ? (
              <Box
                as="video"
                src={previewUrl}
                controls
                maxH="200px"
                width="100%"
                objectFit="contain"
                borderRadius="md"
                borderWidth="1px"
                borderColor={borderColor}
              />
            ) : (
              <Image
                src={previewUrl}
                alt="Preview"
                maxH="200px"
                objectFit="contain"
                borderRadius="md"
                borderWidth="1px"
                borderColor={borderColor}
              />
            )}
            
            <Text fontSize="xs" color="green.500" mt={2}>
              ✓ Media attached - will be analyzed with your content
            </Text>
          </Box>
        )}
      </VStack>
    </Box>
  );
}
