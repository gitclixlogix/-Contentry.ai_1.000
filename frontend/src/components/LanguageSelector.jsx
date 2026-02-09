'use client';
import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  VStack,
  HStack,
  Text,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Badge,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  SimpleGrid,
  useColorModeValue,
  Icon,
  Tooltip,
} from '@chakra-ui/react';
import { FiGlobe, FiSearch, FiCheck } from 'react-icons/fi';
import { useTranslation } from 'react-i18next';
import { 
  SUPPORTED_LANGUAGES, 
  setUserLanguage, 
  loadLanguage,
  isRTL,
  getLanguagesByRegion 
} from '@/i18n/config';

// Compact selector for header/navbar
export function LanguageSelectorCompact() {
  const { i18n } = useTranslation();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const currentLang = SUPPORTED_LANGUAGES[i18n.language] || SUPPORTED_LANGUAGES['en'];
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <>
      <Tooltip label="Change language" placement="bottom">
        <Button
          onClick={onOpen}
          size="sm"
          variant="ghost"
          leftIcon={<Icon as={FiGlobe} />}
          px={2}
        >
          <Text fontSize="sm">{currentLang.flag}</Text>
        </Button>
      </Tooltip>

      <LanguageSelectorModal 
        isOpen={isOpen} 
        onClose={onClose} 
        currentLanguage={i18n.language}
      />
    </>
  );
}

// Full language selector modal with search and regions
export function LanguageSelectorModal({ isOpen, onClose, currentLanguage }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(null);
  const { i18n, t } = useTranslation();
  const searchRef = useRef(null);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const selectedBg = useColorModeValue('blue.50', 'blue.900');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  
  // Get all languages and regions
  const allLanguages = Object.values(SUPPORTED_LANGUAGES);
  const regions = getLanguagesByRegion();

  // Filter languages based on search
  const filteredLanguages = searchQuery.trim()
    ? allLanguages.filter(lang => 
        lang.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lang.native.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lang.code.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : null;

  const handleSelectLanguage = async (langCode) => {
    setLoading(langCode);
    try {
      await loadLanguage(langCode);
      await setUserLanguage(langCode);
      onClose();
    } catch (error) {
      console.error('Failed to load language:', error);
    } finally {
      setLoading(null);
    }
  };

  // Focus search on open
  useEffect(() => {
    if (isOpen && searchRef.current) {
      setTimeout(() => searchRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Reset search on close
  useEffect(() => {
    if (!isOpen) {
      setSearchQuery('');
    }
  }, [isOpen]);

  const renderLanguageItem = (lang) => {
    const isSelected = lang.code === currentLanguage;
    const isLoading = loading === lang.code;
    const rtl = isRTL(lang.code);

    return (
      <Button
        key={lang.code}
        onClick={() => handleSelectLanguage(lang.code)}
        isLoading={isLoading}
        variant="ghost"
        justifyContent="flex-start"
        py={2}
        px={3}
        h="auto"
        width="100%"
        bg={isSelected ? selectedBg : 'transparent'}
        _hover={{ bg: isSelected ? selectedBg : hoverBg }}
        borderRadius="md"
      >
        <HStack spacing={2} width="100%">
          <Text fontSize="lg">{lang.flag}</Text>
          <VStack align="start" spacing={0} flex={1}>
            <HStack>
              <Text fontSize="sm" fontWeight={isSelected ? '600' : '400'}>
                {lang.native}
              </Text>
              {rtl && (
                <Badge size="xs" colorScheme="purple" fontSize="9px">
                  RTL
                </Badge>
              )}
            </HStack>
            <Text fontSize="xs" color="gray.500">
              {lang.name}
            </Text>
          </VStack>
          {isSelected && (
            <Icon as={FiCheck} color="blue.500" />
          )}
        </HStack>
      </Button>
    );
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      size="xl"
      scrollBehavior="inside"
    >
      <ModalOverlay bg="blackAlpha.300" backdropFilter="blur(10px)" />
      <ModalContent bg={bgColor} maxH="80vh">
        <ModalHeader pb={2}>
          <HStack>
            <Icon as={FiGlobe} />
            <Text>{t('common.selectLanguage', 'Select Language')}</Text>
          </HStack>
          <Text fontSize="sm" fontWeight="normal" color="gray.500" mt={1}>
            {t('common.languageCount', '130+ languages available')}
          </Text>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody pb={6}>
          {/* Search Input */}
          <InputGroup mb={4}>
            <InputLeftElement pointerEvents="none">
              <Icon as={FiSearch} color="gray.400" />
            </InputLeftElement>
            <Input
              ref={searchRef}
              placeholder={t('common.searchLanguages', 'Search languages...')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              borderRadius="lg"
            />
          </InputGroup>

          {/* Search Results */}
          {filteredLanguages ? (
            <Box>
              <Text fontSize="sm" color="gray.500" mb={2}>
                {filteredLanguages.length} {t('common.resultsFound', 'results found')}
              </Text>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={1}>
                {filteredLanguages.map(renderLanguageItem)}
              </SimpleGrid>
              {filteredLanguages.length === 0 && (
                <Box textAlign="center" py={8} color="gray.500">
                  <Text>{t('common.noLanguagesFound', 'No languages found')}</Text>
                </Box>
              )}
            </Box>
          ) : (
            /* Grouped by Region */
            <Accordion allowMultiple defaultIndex={[0]}>
              {regions.map((region, idx) => (
                <AccordionItem key={region.name} border="none">
                  <AccordionButton 
                    px={2} 
                    py={2}
                    _hover={{ bg: hoverBg }}
                    borderRadius="md"
                  >
                    <Box flex={1} textAlign="left">
                      <HStack>
                        <Text fontWeight="600" fontSize="sm">
                          {region.name}
                        </Text>
                        <Badge colorScheme="gray" fontSize="xs">
                          {region.languages.length}
                        </Badge>
                      </HStack>
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel pb={2} px={0}>
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={1}>
                      {region.languages.map(renderLanguageItem)}
                    </SimpleGrid>
                  </AccordionPanel>
                </AccordionItem>
              ))}
            </Accordion>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}

// Default export - dropdown style for backwards compatibility
export default function LanguageSelector() {
  const { i18n } = useTranslation();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const currentLang = SUPPORTED_LANGUAGES[i18n.language] || SUPPORTED_LANGUAGES['en'];
  
  const bgColor = useColorModeValue('transparent', 'transparent');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.300');
  const textColor = useColorModeValue('gray.700', 'white');

  return (
    <>
      <Button
        onClick={onOpen}
        variant="ghost"
        size="sm"
        leftIcon={<Text>{currentLang.flag}</Text>}
        bg={bgColor}
        color={textColor}
        border="1px solid"
        borderColor={borderColor}
        borderRadius="md"
        _hover={{
          bg: useColorModeValue('gray.100', 'whiteAlpha.100'),
        }}
        fontWeight="500"
        maxW="180px"
      >
        <Text isTruncated>{currentLang.native}</Text>
      </Button>

      <LanguageSelectorModal 
        isOpen={isOpen} 
        onClose={onClose} 
        currentLanguage={i18n.language}
      />
    </>
  );
}
