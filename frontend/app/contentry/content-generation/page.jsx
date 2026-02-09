'use client';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Card,
  CardBody,
  Heading,
  Text,
  Textarea,
  VStack,
  HStack,
  Input,
  Select,
  Grid,
  Checkbox,
  CheckboxGroup,
  Stack,
  Icon,
  IconButton,
  Tooltip,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  useDisclosure,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  FormControl,
  FormLabel,
  useToast,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
} from '@chakra-ui/react';
import { FaMagic, FaCopy, FaEdit, FaUpload, FaClock, FaHistory, FaTrash, FaToggleOn, FaToggleOff, FaCalendarAlt } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useRouter } from 'next/navigation';
import VoiceDictation from '@/components/voice/VoiceDictation';
import VoiceAssistant from '@/components/voice/VoiceAssistant';
import MediaAnalyzer from '@/components/media/MediaAnalyzer';
import useLanguage from '@/hooks/useLanguage';
import FeedbackSection from '../content-moderation/components/FeedbackSection';

export default function ContentGeneration() {
  const { t } = useTranslation();
  const router = useRouter();
  const language = useLanguage();
  const [user, setUser] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentTone, setCurrentTone] = useState('professional');
  const [currentJobTitle, setCurrentJobTitle] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  // Scheduled content state
  const [scheduledPrompts, setScheduledPrompts] = useState([]);
  const [generatedHistory, setGeneratedHistory] = useState([]);
  const [scheduleData, setScheduleData] = useState({
    prompt: '',
    schedule_type: 'daily',
    schedule_time: '09:00',
    schedule_days: [],
    timezone: 'UTC'
  });
  const [isScheduling, setIsScheduling] = useState(false);
  const toast = useToast();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const brandColor = useColorModeValue('brand.500', 'brand.300');
  const contentBoxBg = useColorModeValue('gray.50', 'gray.700');
  const contentBoxBorderColor = useColorModeValue('gray.200', 'gray.600');

  useEffect(() => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      setCurrentTone(userData.default_tone || 'professional');
      setCurrentJobTitle(userData.job_title || '');
    }
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast({
        title: t('common.error'),
        description: t('contentGeneration.errors.enterPrompt'),
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    setGeneratedContent('');
    
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/content/generate`, {
        prompt,
        tone: currentTone,
        job_title: currentJobTitle,
        user_id: user?.id,
        platforms: selectedPlatforms,
        language: language
      });
      
      setGeneratedContent(response.data.generated_content);
    } catch (error) {
      toast({
        title: t('common.error'),
        description: t('contentGeneration.errors.generationFailed'),
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopyContent = () => {
    if (generatedContent) {
      navigator.clipboard.writeText(generatedContent);
      toast({
        title: t('common.copied'),
        status: 'success',
        duration: 2000,
      });
    }
  };

  const handleUseInModeration = () => {
    if (generatedContent) {
      localStorage.setItem('draft_content', generatedContent);
      router.push('/contentry/content-moderation');
    }
  };

  // Scheduled content functions
  const loadScheduledPrompts = async () => {
    if (!user) return;
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/scheduled-prompts`, {
        headers: { 'user_id': user.id }
      });
      setScheduledPrompts(response.data.scheduled_prompts);
    } catch (error) {
      console.error('Error loading scheduled prompts:', error);
    }
  };

  const loadGeneratedHistory = async () => {
    if (!user) return;
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/generated-content`, {
        headers: { 'user_id': user.id }
      });
      setGeneratedHistory(response.data.generated_content);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const createSchedule = async () => {
    if (!scheduleData.prompt) {
      toast({
        title: t('common.error'),
        description: t('contentGeneration.errors.enterPrompt'),
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setIsScheduling(true);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/scheduled-prompts`, scheduleData, {
        headers: { 'user_id': user.id }
      });
      
      toast({
        title: t('contentGeneration.toasts.scheduleCreated'),
        description: t('contentGeneration.toasts.scheduleCreatedDesc'),
        status: 'success',
        duration: 3000,
      });
      
      setScheduleData({
        prompt: '',
        schedule_type: 'daily',
        schedule_time: '09:00',
        schedule_days: [],
        timezone: 'UTC'
      });
      
      loadScheduledPrompts();
    } catch (error) {
      toast({
        title: t('common.error'),
        description: t('contentGeneration.errors.createScheduleFailed'),
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsScheduling(false);
    }
  };

  const deleteSchedule = async (id) => {
    try {
      const API = getApiUrl();
      await axios.delete(`${API}/scheduled-prompts/${id}`, {
        headers: { 'user_id': user.id }
      });
      
      toast({
        title: t('contentGeneration.toasts.deleted'),
        description: t('contentGeneration.toasts.scheduleRemoved'),
        status: 'success',
        duration: 2000,
      });
      
      loadScheduledPrompts();
    } catch (error) {
      toast({
        title: t('common.error'),
        description: t('contentGeneration.errors.deleteScheduleFailed'),
        status: 'error',
        duration: 3000,
      });
    }
  };

  const toggleSchedule = async (id) => {
    try {
      const API = getApiUrl();
      await axios.patch(`${API}/scheduled-prompts/${id}/toggle`, {}, {
        headers: { 'user_id': user.id }
      });
      
      loadScheduledPrompts();
    } catch (error) {
      toast({
        title: t('common.error'),
        description: t('contentGeneration.errors.toggleScheduleFailed'),
        status: 'error',
        duration: 3000,
      });
    }
  };

  useEffect(() => {
    if (user) {
      loadScheduledPrompts();
      loadGeneratedHistory();
    }
  }, [user]);

  const promptSuggestions = [
    t('contentGeneration.suggestions.productLaunch'),
    t('contentGeneration.suggestions.milestone'),
    t('contentGeneration.suggestions.event'),
    t('contentGeneration.suggestions.insights'),
    t('contentGeneration.suggestions.motivational'),
    t('contentGeneration.suggestions.successStory'),
    t('contentGeneration.suggestions.jobOpening'),
    t('contentGeneration.suggestions.culture')
  ];

  return (
    <Box pt={{ base: '10px', md: '10px', xl: '10px' }} px={{ base: 2, md: 4 }}>
      <Heading size={{ base: "md", md: "lg" }} mb={{ base: 4, md: 6 }}>{t('contentGeneration.title')}</Heading>
      <Text color={textColorSecondary} mb={{ base: 4, md: 6 }} fontSize={{ base: "sm", md: "md" }}>
        {t('contentGeneration.subtitle')}
      </Text>

      <Tabs colorScheme="brand" variant="enclosed">
        <TabList>
          <Tab><Icon as={FaMagic} mr={2} /> {t('contentGeneration.generateNow')}</Tab>
          <Tab><Icon as={FaClock} mr={2} /> {t('contentGeneration.schedule')}</Tab>
          <Tab><Icon as={FaHistory} mr={2} /> {t('contentGeneration.history')}</Tab>
        </TabList>

        <TabPanels>
          {/* Tab 1: Generate Now */}
          <TabPanel px={0}>
            {/* Prompt Section */}
            <Card mb={{ base: 4, md: 6 }} bg={cardBg}>
        <CardBody p={{ base: 3, md: 4 }}>
          <VStack align="stretch" spacing={{ base: 3, md: 4 }}>
            <Box>
              <Text mb={2} fontWeight="600" fontSize={{ base: "sm", md: "md" }}>{t('contentGeneration.whatToPost')}</Text>
              <Box position="relative">
                <Textarea
                  placeholder={t('contentGeneration.promptPlaceholder')}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  minH={{ base: "100px", md: "120px" }}
                  fontSize={{ base: "sm", md: "md" }}
                  pr={{ base: "60px", md: "150px" }}
                />
                <Box position="absolute" bottom="12px" right="12px" zIndex={1}>
                  <HStack spacing={{ base: 1, md: 2 }}>
                    <Tooltip label={t('contentGeneration.uploadMedia')} placement="top">
                      <IconButton
                        icon={<FaUpload />}
                        onClick={onOpen}
                        colorScheme="green"
                        variant="ghost"
                        size={{ base: "sm", md: "md" }}
                        aria-label="Upload media"
                      />
                    </Tooltip>
                    <VoiceDictation onTranscript={(text) => setPrompt(prompt + (prompt ? ' ' : '') + text)} />
                  </HStack>
                </Box>
              </Box>
            </Box>

            {/* Quick Suggestions */}
            <Box>
              <Text fontSize={{ base: "xs", md: "sm" }} mb={2} color={textColorSecondary}>{t('contentGeneration.quickSuggestions')}</Text>
              <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)' }} gap={{ base: 1, md: 2 }}>
                {promptSuggestions.map((suggestion, idx) => (
                  <Button
                    key={idx}
                    size="xs"
                    variant="ghost"
                    justifyContent="flex-start"
                    onClick={() => setPrompt(suggestion)}
                    color={brandColor}
                  >
                    • {suggestion}
                  </Button>
                ))}
              </Grid>
            </Box>

            {/* Settings */}
            <Grid templateColumns={{ base: '1fr', md: '1fr 1fr' }} gap={4}>
              <Box>
                <Text mb={2} fontSize="sm" fontWeight="600" color={textColor}>
                  {t('contentGeneration.writingTone')}
                </Text>
                <Select 
                  value={currentTone}
                  onChange={(e) => setCurrentTone(e.target.value)}
                  size="sm"
                >
                  <option value="professional">{t('tones.professional')}</option>
                  <option value="casual">{t('tones.casual')}</option>
                  <option value="formal">{t('tones.formal')}</option>
                  <option value="friendly">{t('tones.friendly')}</option>
                  <option value="confident">{t('tones.confident')}</option>
                  <option value="direct">{t('tones.direct')}</option>
                </Select>
                <Text fontSize="xs" color={textColorSecondary} mt={1}>
                  {user?.default_tone === currentTone ? t('contentGeneration.yourDefault') : t('contentGeneration.overrideGeneration')}
                </Text>
              </Box>
              <Box>
                <Text mb={2} fontSize="sm" fontWeight="600" color={textColor}>
                  {t('contentGeneration.jobTitle')}
                </Text>
                <Input 
                  value={currentJobTitle}
                  onChange={(e) => setCurrentJobTitle(e.target.value)}
                  size="sm"
                  placeholder="e.g., Marketing Manager"
                />
                <Text fontSize="xs" color={textColorSecondary} mt={1}>
                  {user?.job_title === currentJobTitle ? t('contentGeneration.yourDefault') : t('contentGeneration.overrideGeneration')}
                </Text>
              </Box>
            </Grid>

            {/* Platform Selection */}
            <Box>
              <Text mb={2} fontSize="sm" fontWeight="600" color={textColor}>
                {t('contentGeneration.targetPlatforms')}
              </Text>
              <CheckboxGroup value={selectedPlatforms} onChange={setSelectedPlatforms}>
                <Stack direction="row" spacing={4} flexWrap="wrap">
                  <Checkbox value="Facebook">{t('platforms.facebook')}</Checkbox>
                  <Checkbox value="Twitter">{t('platforms.twitter')}</Checkbox>
                  <Checkbox value="LinkedIn">{t('platforms.linkedin')}</Checkbox>
                  <Checkbox value="Instagram">{t('platforms.instagram')}</Checkbox>
                </Stack>
              </CheckboxGroup>
            </Box>

            <Button
              leftIcon={<FaMagic />}
              colorScheme="brand"
              size="sm"
              onClick={handleGenerate}
              isLoading={loading}
              loadingText={t('contentGeneration.generating')}
            >
              {t('contentGeneration.generateContent')}
            </Button>
          </VStack>
        </CardBody>
      </Card>

      {/* Generated Content Section */}
      {generatedContent && (
        <Card bg={cardBg}>
          <CardBody>
            <VStack align="stretch" spacing={4}>
              <HStack justify="space-between">
                <Heading size="md">{t('contentGeneration.generatedContent')}</Heading>
                <HStack>
                  <Button
                    size="sm"
                    leftIcon={<FaCopy />}
                    variant="outline"
                    onClick={handleCopyContent}
                  >
                    {t('common.copy')}
                  </Button>
                  <Button
                    size="sm"
                    leftIcon={<FaEdit />}
                    colorScheme="brand"
                    onClick={handleUseInModeration}
                  >
                    {t('contentGeneration.useInModeration')}
                  </Button>
                </HStack>
              </HStack>

              <Box
                p={6}
                borderRadius="md"
                bg={contentBoxBg}
                borderWidth="1px"
                borderColor={contentBoxBorderColor}
              >
                <Text whiteSpace="pre-wrap" lineHeight="1.8">
                  {generatedContent}
                </Text>
              </Box>

              <Text fontSize="sm" color={textColorSecondary}>
                💡 {t('contentGeneration.tip')}
              </Text>
              
              {/* Teach AI - Feedback Section */}
              {user && <FeedbackSection analysis={null} content={generatedContent} userId={user.id} />}
            </VStack>
          </CardBody>
        </Card>
      )}
      
      {/* Media Upload & Analysis Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent bg={cardBg}>
          <ModalHeader>{t('contentGeneration.uploadMedia')}</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <MediaAnalyzer 
              onMediaAnalyzed={(data) => {
                console.log('Media analyzed:', data.analysis);
                onClose();
              }}
            />
          </ModalBody>
        </ModalContent>
      </Modal>
      
      {/* ElevenLabs Voice Assistant */}
      <VoiceAssistant />
          </TabPanel>

          {/* Tab 2: Schedule Generation */}
          <TabPanel>
            <Card bg={cardBg}>
              <CardBody>
                <VStack align="stretch" spacing={6}>
                  <Heading size="md">{t('contentGeneration.scheduleTitle')}</Heading>
                  
                  <FormControl>
                    <FormLabel>{t('contentGeneration.prompt')}</FormLabel>
                    <Textarea
                      placeholder={t('contentGeneration.promptDesc')}
                      value={scheduleData.prompt}
                      onChange={(e) => setScheduleData({...scheduleData, prompt: e.target.value})}
                      minH="120px"
                    />
                  </FormControl>

                  <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)' }} gap={4}>
                    <FormControl>
                      <FormLabel>{t('contentGeneration.scheduleType')}</FormLabel>
                      <Select 
                        value={scheduleData.schedule_type}
                        onChange={(e) => setScheduleData({...scheduleData, schedule_type: e.target.value})}
                      >
                        <option value="once">{t('contentGeneration.once')}</option>
                        <option value="daily">{t('contentGeneration.daily')}</option>
                        <option value="weekly">{t('contentGeneration.weekly')}</option>
                        <option value="monthly">{t('contentGeneration.monthly')}</option>
                      </Select>
                    </FormControl>

                    <FormControl>
                      <FormLabel>{t('common.time')}</FormLabel>
                      <Input 
                        type="time"
                        value={scheduleData.schedule_time}
                        onChange={(e) => setScheduleData({...scheduleData, schedule_time: e.target.value})}
                      />
                    </FormControl>
                  </Grid>

                  {scheduleData.schedule_type === 'weekly' && (
                    <FormControl>
                      <FormLabel>{t('contentGeneration.selectDays')}</FormLabel>
                      <CheckboxGroup 
                        value={scheduleData.schedule_days}
                        onChange={(values) => setScheduleData({...scheduleData, schedule_days: values})}
                      >
                        <Stack spacing={2} direction={{ base: 'column', md: 'row' }} flexWrap="wrap">
                          <Checkbox value="monday">{t('days.monday')}</Checkbox>
                          <Checkbox value="tuesday">{t('days.tuesday')}</Checkbox>
                          <Checkbox value="wednesday">{t('days.wednesday')}</Checkbox>
                          <Checkbox value="thursday">{t('days.thursday')}</Checkbox>
                          <Checkbox value="friday">{t('days.friday')}</Checkbox>
                          <Checkbox value="saturday">{t('days.saturday')}</Checkbox>
                          <Checkbox value="sunday">{t('days.sunday')}</Checkbox>
                        </Stack>
                      </CheckboxGroup>
                    </FormControl>
                  )}

                  <Button
                    colorScheme="brand"
                    size="sm"
                    leftIcon={<FaCalendarAlt />}
                    onClick={createSchedule}
                    isLoading={isScheduling}
                  >
                    {t('contentGeneration.createSchedule')}
                  </Button>

                  {/* Scheduled Prompts Table */}
                  <Box mt={8}>
                    <Heading size="md" mb={4}>{t('contentGeneration.yourScheduled')} ({scheduledPrompts.length})</Heading>
                    {scheduledPrompts.length === 0 ? (
                      <Text color="gray.500">{t('contentGeneration.noScheduled')}</Text>
                    ) : (
                      <Box overflowX="auto">
                        <Table variant="simple">
                          <Thead>
                            <Tr>
                              <Th>{t('contentGeneration.prompt')}</Th>
                              <Th>{t('contentGeneration.schedule')}</Th>
                              <Th>{t('contentGeneration.nextRun')}</Th>
                              <Th>{t('contentGeneration.runs')}</Th>
                              <Th>{t('common.status')}</Th>
                              <Th>{t('common.actions')}</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {scheduledPrompts.map((scheduled) => (
                              <Tr key={scheduled.id}>
                                <Td maxW="300px" isTruncated>{scheduled.prompt}</Td>
                                <Td>
                                  <Text fontSize="sm">
                                    {scheduled.schedule_type} at {scheduled.schedule_time}
                                  </Text>
                                  {scheduled.schedule_type === 'weekly' && (
                                    <Text fontSize="xs" color="gray.500">
                                      {scheduled.schedule_days.join(', ')}
                                    </Text>
                                  )}
                                </Td>
                                <Td fontSize="sm">
                                  {scheduled.next_run ? new Date(scheduled.next_run).toLocaleString() : 'N/A'}
                                </Td>
                                <Td>
                                  <Badge>{scheduled.run_count}</Badge>
                                </Td>
                                <Td>
                                  <Badge colorScheme={scheduled.is_active ? 'green' : 'gray'}>
                                    {scheduled.is_active ? t('contentGeneration.active') : t('contentGeneration.inactive')}
                                  </Badge>
                                </Td>
                                <Td>
                                  <HStack spacing={2}>
                                    <Tooltip label={scheduled.is_active ? t('contentGeneration.deactivate') : t('contentGeneration.activate')}>
                                      <IconButton
                                        size="sm"
                                        icon={scheduled.is_active ? <FaToggleOn /> : <FaToggleOff />}
                                        onClick={() => toggleSchedule(scheduled.id)}
                                        colorScheme={scheduled.is_active ? 'green' : 'gray'}
                                      />
                                    </Tooltip>
                                    <Tooltip label={t('common.delete')}>
                                      <IconButton
                                        size="sm"
                                        icon={<FaTrash />}
                                        onClick={() => deleteSchedule(scheduled.id)}
                                        colorScheme="red"
                                        variant="ghost"
                                      />
                                    </Tooltip>
                                  </HStack>
                                </Td>
                              </Tr>
                            ))}
                          </Tbody>
                        </Table>
                      </Box>
                    )}
                  </Box>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>

          {/* Tab 3: History */}
          <TabPanel>
            <Card bg={cardBg}>
              <CardBody>
                <VStack align="stretch" spacing={6}>
                  <Heading size="md">{t('contentGeneration.historyTitle')} ({generatedHistory.length})</Heading>
                  
                  {generatedHistory.length === 0 ? (
                    <Text color="gray.500">{t('contentGeneration.noHistory')}</Text>
                  ) : (
                    <Box overflowX="auto">
                      <Table variant="simple">
                        <Thead>
                          <Tr>
                            <Th>{t('dashboard.content')}</Th>
                            <Th>{t('contentGeneration.prompt')}</Th>
                            <Th>{t('contentGeneration.type')}</Th>
                            <Th>{t('contentGeneration.generated')}</Th>
                            <Th>{t('common.actions')}</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {generatedHistory.map((content) => (
                            <Tr key={content.id}>
                              <Td maxW="400px">
                                <Text isTruncated fontSize="sm">{content.content}</Text>
                              </Td>
                              <Td maxW="200px" isTruncated fontSize="sm">{content.prompt}</Td>
                              <Td>
                                <Badge colorScheme={content.generation_type === 'scheduled' ? 'blue' : 'blue'}>
                                  {content.generation_type === 'scheduled' ? t('contentGeneration.scheduled') : t('contentGeneration.manual')}
                                </Badge>
                              </Td>
                              <Td fontSize="sm">
                                {new Date(content.created_at).toLocaleDateString()}
                              </Td>
                              <Td>
                                <Tooltip label={t('contentGeneration.copyContent')}>
                                  <IconButton
                                    size="sm"
                                    icon={<FaCopy />}
                                    onClick={() => {
                                      navigator.clipboard.writeText(content.content);
                                      toast({
                                        title: t('common.copied'),
                                        status: 'success',
                                        duration: 2000,
                                      });
                                    }}
                                  />
                                </Tooltip>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </Box>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
}
