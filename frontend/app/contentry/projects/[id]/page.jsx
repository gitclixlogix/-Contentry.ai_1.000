'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  Text,
  Button,
  useColorModeValue,
  VStack,
  HStack,
  Badge,
  Icon,
  Spinner,
  useToast,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Avatar,
  AvatarGroup,
  Tooltip,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Divider,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
} from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';
import {
  ChevronLeft,
  Calendar,
  Users,
  FileText,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  Shield,
  Globe,
  Zap,
  MoreVertical,
  Edit2,
  Archive,
  ExternalLink,
  ChevronRight,
  ChevronDown,
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

// Calendar Component
function ProjectCalendar({ scheduledPosts, projectStartDate, projectEndDate }) {
  const bgColor = useColorModeValue('white', 'navy.700');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');
  const textColor = useColorModeValue('gray.800', 'white');
  const textSecondary = useColorModeValue('gray.600', 'gray.400');
  const todayBg = useColorModeValue('brand.50', 'brand.900');
  const eventBg = useColorModeValue('brand.100', 'brand.800');

  const [currentMonth, setCurrentMonth] = useState(new Date());

  // Get days in month
  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    const days = [];
    
    // Previous month padding
    for (let i = 0; i < startingDay; i++) {
      days.push({ day: null, isCurrentMonth: false });
    }
    
    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
      const postsOnDay = scheduledPosts?.filter(p => p.post_time?.startsWith(dateStr)) || [];
      days.push({
        day: i,
        isCurrentMonth: true,
        date: dateStr,
        posts: postsOnDay,
        isToday: new Date().toDateString() === new Date(year, month, i).toDateString(),
      });
    }
    
    return days;
  };

  const days = getDaysInMonth(currentMonth);
  const monthName = currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  return (
    <Box>
      {/* Calendar Header */}
      <Flex justify="space-between" align="center" mb={4}>
        <Button variant="ghost" size="sm" onClick={prevMonth}>
          <ChevronLeft size={16} />
        </Button>
        <Text fontWeight="bold" fontSize="lg" color={textColor}>
          {monthName}
        </Text>
        <Button variant="ghost" size="sm" onClick={nextMonth}>
          <ChevronRight size={16} />
        </Button>
      </Flex>

      {/* Day Headers */}
      <SimpleGrid columns={7} gap={1} mb={2}>
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <Text key={day} fontSize="xs" fontWeight="bold" textAlign="center" color={textSecondary}>
            {day}
          </Text>
        ))}
      </SimpleGrid>

      {/* Calendar Grid */}
      <SimpleGrid columns={7} gap={1}>
        {days.map((dayInfo, idx) => (
          <Box
            key={idx}
            h="80px"
            p={1}
            bg={dayInfo.isToday ? todayBg : 'transparent'}
            borderRadius="md"
            border="1px solid"
            borderColor={dayInfo.isCurrentMonth ? borderColor : 'transparent'}
            opacity={dayInfo.isCurrentMonth ? 1 : 0.3}
          >
            {dayInfo.day && (
              <VStack align="stretch" spacing={0.5}>
                <Text fontSize="xs" fontWeight={dayInfo.isToday ? 'bold' : 'normal'} color={textColor}>
                  {dayInfo.day}
                </Text>
                {dayInfo.posts?.slice(0, 2).map((post, i) => (
                  <Tooltip key={i} label={post.title || post.content?.slice(0, 50)} placement="top">
                    <Box
                      bg={eventBg}
                      px={1}
                      py={0.5}
                      borderRadius="sm"
                      fontSize="2xs"
                      noOfLines={1}
                      cursor="pointer"
                    >
                      {post.title || 'Post'}
                    </Box>
                  </Tooltip>
                ))}
                {dayInfo.posts?.length > 2 && (
                  <Text fontSize="2xs" color={textSecondary}>
                    +{dayInfo.posts.length - 2} more
                  </Text>
                )}
              </VStack>
            )}
          </Box>
        ))}
      </SimpleGrid>
    </Box>
  );
}

// Score Card Component
function ScoreCard({ title, score, icon, colorScheme, helpText }) {
  const bgColor = useColorModeValue('white', 'navy.700');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');

  const getScoreColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'yellow';
    return 'red';
  };

  return (
    <Card bg={bgColor} border="1px solid" borderColor={borderColor} borderRadius="xl">
      <CardBody>
        <Stat>
          <Flex justify="space-between" align="flex-start">
            <Box>
              <StatLabel fontSize="sm" color="gray.500">
                {title}
              </StatLabel>
              <StatNumber fontSize="3xl" color={`${colorScheme || getScoreColor(score)}.500`}>
                {score}
              </StatNumber>
              {helpText && <StatHelpText fontSize="xs">{helpText}</StatHelpText>}
            </Box>
            <Icon as={icon} boxSize={8} color={`${colorScheme || getScoreColor(score)}.400`} />
          </Flex>
        </Stat>
      </CardBody>
    </Card>
  );
}

export default function ProjectDashboardPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const toast = useToast();
  const projectId = params.id;

  // State
  const [project, setProject] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [calendar, setCalendar] = useState(null);
  const [content, setContent] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);

  // Colors
  const bgColor = useColorModeValue('white', 'navy.800');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');
  const textColor = useColorModeValue('gray.800', 'white');
  const textSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('white', 'navy.700');

  // Fetch all project data
  const fetchData = useCallback(async () => {
    if (!user?.id || !projectId) return;

    setIsLoading(true);
    try {
      const [projectRes, metricsRes, calendarRes, contentRes] = await Promise.all([
        axios.get(`${getApiUrl()}/projects/${projectId}`, {
          headers: { 'X-User-ID': user.id },
        }),
        axios.get(`${getApiUrl()}/projects/${projectId}/metrics`, {
          headers: { 'X-User-ID': user.id },
        }),
        axios.get(`${getApiUrl()}/projects/${projectId}/calendar`, {
          headers: { 'X-User-ID': user.id },
        }),
        axios.get(`${getApiUrl()}/projects/${projectId}/content`, {
          headers: { 'X-User-ID': user.id },
          params: { limit: 50 },
        }),
      ]);

      setProject(projectRes.data.project);
      setMetrics(metricsRes.data);
      setCalendar(calendarRes.data);
      setContent(contentRes.data.content || []);
    } catch (error) {
      console.error('Error fetching project data:', error);
      if (error.response?.status === 404) {
        toast({
          title: 'Project not found',
          status: 'error',
          duration: 3000,
        });
        router.push('/contentry/projects');
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load project data',
          status: 'error',
          duration: 3000,
        });
      }
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, projectId, toast, router]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return 'Not set';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Get score badge color
  const getScoreColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'yellow';
    return 'red';
  };

  if (isLoading) {
    return (
      <Flex justify="center" align="center" minH="400px">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }

  if (!project) {
    return (
      <Flex justify="center" align="center" minH="400px">
        <Text color={textSecondary}>Project not found</Text>
      </Flex>
    );
  }

  return (
    <Box p={{ base: 4, md: 6 }} maxW="1400px" mx="auto">
      {/* Header */}
      <Box mb={6}>
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<ChevronLeft size={16} />}
          onClick={() => router.push('/contentry/projects')}
          p={0}
          h="auto"
          minW="auto"
          color={textSecondary}
          _hover={{ color: textColor }}
          mb={2}
        >
          Back to Projects
        </Button>

        <Flex justify="space-between" align="flex-start" wrap="wrap" gap={4}>
          <Box>
            <HStack mb={2}>
              <Text fontSize="2xl" fontWeight="bold" color={textColor}>
                {project.name}
              </Text>
              <Badge colorScheme={project.status === 'active' ? 'green' : 'gray'}>
                {project.status}
              </Badge>
            </HStack>
            {project.description && (
              <Text color={textSecondary} fontSize="sm" mb={2}>
                {project.description}
              </Text>
            )}
            <HStack spacing={4} color={textSecondary} fontSize="sm">
              <HStack>
                <Calendar size={14} />
                <Text>
                  {formatDate(project.start_date)} - {formatDate(project.end_date)}
                </Text>
              </HStack>
              <HStack>
                <FileText size={14} />
                <Text>{metrics?.content_count || 0} items</Text>
              </HStack>
              <HStack>
                <Users size={14} />
                <Text>{metrics?.team_members?.length || 0} contributors</Text>
              </HStack>
            </HStack>
          </Box>

          <HStack spacing={2}>
            {/* Quick Add Buttons - Pre-select this project */}
            <Button
              colorScheme="brand"
              size="sm"
              leftIcon={<FileText size={16} />}
              onClick={() => router.push(`/contentry/content-moderation?tab=generate&project=${projectId}`)}
            >
              + New Post
            </Button>
            <Button
              variant="outline"
              colorScheme="brand"
              size="sm"
              leftIcon={<Zap size={16} />}
              onClick={() => router.push(`/contentry/content-moderation?tab=analyze&project=${projectId}`)}
            >
              + Analyze Content
            </Button>
            
            <Menu>
              <MenuButton as={Button} rightIcon={<ChevronDown size={16} />} variant="outline">
                Actions
              </MenuButton>
              <MenuList>
                <MenuItem icon={<Edit2 size={16} />} onClick={() => router.push(`/contentry/projects?edit=${projectId}`)}>
                  Edit Project
                </MenuItem>
                <MenuItem icon={<Archive size={16} />}>
                  {project.status === 'active' ? 'Archive' : 'Restore'}
                </MenuItem>
              </MenuList>
            </Menu>
          </HStack>
        </Flex>
      </Box>

      {/* Score Cards */}
      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} mb={6}>
        <ScoreCard
          title="Overall Score"
          score={metrics?.avg_overall_score || 0}
          icon={Target}
          helpText="Average across all content"
        />
        <ScoreCard
          title="Compliance"
          score={metrics?.avg_compliance_score || 0}
          icon={Shield}
          helpText="Policy adherence"
        />
        <ScoreCard
          title="Cultural Sensitivity"
          score={metrics?.avg_cultural_score || 0}
          icon={Globe}
          helpText="Cultural awareness"
        />
        <ScoreCard
          title="Accuracy"
          score={metrics?.avg_accuracy_score || 0}
          icon={Zap}
          helpText="Factual correctness"
        />
      </SimpleGrid>

      {/* Main Content Tabs */}
      <Tabs index={activeTab} onChange={setActiveTab} colorScheme="brand">
        <TabList mb={4}>
          <Tab>Overview</Tab>
          <Tab>Content ({content.length})</Tab>
          <Tab>Calendar</Tab>
          <Tab>Team</Tab>
        </TabList>

        <TabPanels>
          {/* Overview Tab */}
          <TabPanel p={0}>
            <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
              {/* Top Performing Posts */}
              <Card bg={cardBg} border="1px solid" borderColor={borderColor} borderRadius="xl">
                <CardHeader pb={2}>
                  <HStack>
                    <Icon as={TrendingUp} color="green.500" />
                    <Text fontWeight="bold" color={textColor}>
                      Top Performing Content
                    </Text>
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  {metrics?.top_posts?.length > 0 ? (
                    <VStack align="stretch" spacing={2}>
                      {metrics.top_posts.map((post, idx) => (
                        <Flex
                          key={post.id || idx}
                          justify="space-between"
                          align="center"
                          p={2}
                          borderRadius="md"
                          _hover={{ bg: useColorModeValue('gray.50', 'navy.600') }}
                        >
                          <VStack align="start" spacing={0} flex={1}>
                            <Text fontSize="sm" fontWeight="medium" noOfLines={1}>
                              {post.title || post.content?.slice(0, 40) || 'Untitled'}
                            </Text>
                            <Text fontSize="xs" color={textSecondary}>
                              {formatDate(post.created_at)}
                            </Text>
                          </VStack>
                          <Badge colorScheme="green" fontSize="sm">
                            {post.overall_score}
                          </Badge>
                        </Flex>
                      ))}
                    </VStack>
                  ) : (
                    <Text color={textSecondary} fontSize="sm" textAlign="center" py={4}>
                      No content yet
                    </Text>
                  )}
                </CardBody>
              </Card>

              {/* Bottom Performing Posts */}
              <Card bg={cardBg} border="1px solid" borderColor={borderColor} borderRadius="xl">
                <CardHeader pb={2}>
                  <HStack>
                    <Icon as={TrendingDown} color="red.500" />
                    <Text fontWeight="bold" color={textColor}>
                      Needs Improvement
                    </Text>
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  {metrics?.bottom_posts?.length > 0 ? (
                    <VStack align="stretch" spacing={2}>
                      {metrics.bottom_posts.map((post, idx) => (
                        <Flex
                          key={post.id || idx}
                          justify="space-between"
                          align="center"
                          p={2}
                          borderRadius="md"
                          _hover={{ bg: useColorModeValue('gray.50', 'navy.600') }}
                        >
                          <VStack align="start" spacing={0} flex={1}>
                            <Text fontSize="sm" fontWeight="medium" noOfLines={1}>
                              {post.title || post.content?.slice(0, 40) || 'Untitled'}
                            </Text>
                            <Text fontSize="xs" color={textSecondary}>
                              {formatDate(post.created_at)}
                            </Text>
                          </VStack>
                          <Badge colorScheme="red" fontSize="sm">
                            {post.overall_score}
                          </Badge>
                        </Flex>
                      ))}
                    </VStack>
                  ) : (
                    <Text color={textSecondary} fontSize="sm" textAlign="center" py={4}>
                      All content performing well!
                    </Text>
                  )}
                </CardBody>
              </Card>

              {/* Status Breakdown */}
              <Card bg={cardBg} border="1px solid" borderColor={borderColor} borderRadius="xl">
                <CardHeader pb={2}>
                  <HStack>
                    <Icon as={BarChart3} color="brand.500" />
                    <Text fontWeight="bold" color={textColor}>
                      Content Status
                    </Text>
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  <VStack align="stretch" spacing={3}>
                    {Object.entries(metrics?.status_breakdown || {}).map(([status, count]) => (
                      <Box key={status}>
                        <Flex justify="space-between" mb={1}>
                          <Text fontSize="sm" textTransform="capitalize">
                            {status.replace(/_/g, ' ')}
                          </Text>
                          <Text fontSize="sm" fontWeight="bold">
                            {count}
                          </Text>
                        </Flex>
                        <Progress
                          value={(count / (metrics?.content_count || 1)) * 100}
                          size="sm"
                          colorScheme={
                            status === 'published' ? 'green' :
                            status === 'scheduled' ? 'blue' :
                            status === 'draft' ? 'gray' : 'orange'
                          }
                          borderRadius="full"
                        />
                      </Box>
                    ))}
                    {Object.keys(metrics?.status_breakdown || {}).length === 0 && (
                      <Text color={textSecondary} fontSize="sm" textAlign="center" py={4}>
                        No content status data
                      </Text>
                    )}
                  </VStack>
                </CardBody>
              </Card>

              {/* Quick Stats */}
              <Card bg={cardBg} border="1px solid" borderColor={borderColor} borderRadius="xl">
                <CardHeader pb={2}>
                  <Text fontWeight="bold" color={textColor}>
                    Quick Stats
                  </Text>
                </CardHeader>
                <CardBody pt={0}>
                  <SimpleGrid columns={2} spacing={4}>
                    <Stat>
                      <StatLabel fontSize="xs">Total Posts</StatLabel>
                      <StatNumber fontSize="2xl">{metrics?.content_count || 0}</StatNumber>
                    </Stat>
                    <Stat>
                      <StatLabel fontSize="xs">Scheduled</StatLabel>
                      <StatNumber fontSize="2xl">{calendar?.total_scheduled || 0}</StatNumber>
                    </Stat>
                    <Stat>
                      <StatLabel fontSize="xs">Team Members</StatLabel>
                      <StatNumber fontSize="2xl">{metrics?.team_members?.length || 0}</StatNumber>
                    </Stat>
                    <Stat>
                      <StatLabel fontSize="xs">Avg Score</StatLabel>
                      <StatNumber fontSize="2xl" color={`${getScoreColor(metrics?.avg_overall_score || 0)}.500`}>
                        {metrics?.avg_overall_score || 0}
                      </StatNumber>
                    </Stat>
                  </SimpleGrid>
                </CardBody>
              </Card>
            </SimpleGrid>
          </TabPanel>

          {/* Content Tab */}
          <TabPanel p={0}>
            <Card bg={cardBg} border="1px solid" borderColor={borderColor} borderRadius="xl">
              <CardBody>
                {content.length > 0 ? (
                  <TableContainer>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Title/Content</Th>
                          <Th>Type</Th>
                          <Th>Status</Th>
                          <Th isNumeric>Score</Th>
                          <Th>Created</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {content.map((item, idx) => (
                          <Tr key={item.id || idx} _hover={{ bg: useColorModeValue('gray.50', 'navy.600') }}>
                            <Td maxW="300px">
                              <Text noOfLines={1}>
                                {item.title || item.content?.slice(0, 50) || 'Untitled'}
                              </Text>
                            </Td>
                            <Td>
                              <Badge variant="outline">
                                {item.content_type || 'post'}
                              </Badge>
                            </Td>
                            <Td>
                              <Badge colorScheme={
                                item.status === 'published' ? 'green' :
                                item.status === 'scheduled' ? 'blue' : 'gray'
                              }>
                                {item.status || 'draft'}
                              </Badge>
                            </Td>
                            <Td isNumeric>
                              <Badge colorScheme={getScoreColor(item.overall_score || 0)}>
                                {item.overall_score || '-'}
                              </Badge>
                            </Td>
                            <Td fontSize="xs" color={textSecondary}>
                              {formatDate(item.created_at)}
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </TableContainer>
                ) : (
                  <VStack py={10} spacing={4}>
                    <Icon as={FileText} boxSize={12} color="gray.400" />
                    <Text color={textSecondary}>No content linked to this project yet</Text>
                    <Text color={textSecondary} fontSize="sm">
                      Assign content from the "All Posts" view to see it here
                    </Text>
                  </VStack>
                )}
              </CardBody>
            </Card>
          </TabPanel>

          {/* Calendar Tab */}
          <TabPanel p={0}>
            <Card bg={cardBg} border="1px solid" borderColor={borderColor} borderRadius="xl">
              <CardBody>
                <ProjectCalendar
                  scheduledPosts={calendar?.scheduled_posts || []}
                  projectStartDate={project.start_date}
                  projectEndDate={project.end_date}
                />
              </CardBody>
            </Card>
          </TabPanel>

          {/* Team Tab */}
          <TabPanel p={0}>
            <Card bg={cardBg} border="1px solid" borderColor={borderColor} borderRadius="xl">
              <CardBody>
                {metrics?.team_members?.length > 0 ? (
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
                    {metrics.team_members.map((member, idx) => (
                      <Flex
                        key={member.id || idx}
                        align="center"
                        p={3}
                        borderRadius="lg"
                        border="1px solid"
                        borderColor={borderColor}
                      >
                        <Avatar size="md" name={member.full_name || member.email} mr={3} />
                        <Box>
                          <Text fontWeight="medium">
                            {member.full_name || 'Team Member'}
                          </Text>
                          <Text fontSize="sm" color={textSecondary}>
                            {member.email}
                          </Text>
                        </Box>
                      </Flex>
                    ))}
                  </SimpleGrid>
                ) : (
                  <VStack py={10} spacing={4}>
                    <Icon as={Users} boxSize={12} color="gray.400" />
                    <Text color={textSecondary}>No team members yet</Text>
                    <Text color={textSecondary} fontSize="sm">
                      Team members are added when they contribute content
                    </Text>
                  </VStack>
                )}
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
}
