'use client';

import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Card,
  CardBody,
  Badge,
  Icon,
  Divider,
  Grid,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Code,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
} from '@chakra-ui/react';
import {
  FaBrain,
  FaRobot,
  FaSearch,
  FaPen,
  FaBalanceScale,
  FaGlobe,
  FaShieldAlt,
  FaEye,
  FaFileAlt,
  FaExclamationTriangle,
  FaChartLine,
  FaArrowRight,
  FaDatabase,
  FaServer,
  FaCogs,
} from 'react-icons/fa';

export default function TechnicalDocumentation() {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.700', 'gray.200');
  const mutedColor = useColorModeValue('gray.500', 'gray.400');
  const accentBg = useColorModeValue('blue.50', 'blue.900');
  const agentBg = useColorModeValue('purple.50', 'purple.900');
  const flowBg = useColorModeValue('green.50', 'green.900');

  // Agent definitions for both systems
  const contentGenerationAgents = [
    {
      name: 'Orchestrator Agent',
      icon: FaBrain,
      color: 'purple',
      description: 'Coordinates the entire content generation workflow',
      responsibilities: [
        'Receives initial user prompt and context',
        'Determines which agents to invoke',
        'Manages agent communication and data flow',
        'Aggregates results and handles quality gates',
      ],
      file: 'orchestrator_agent.py',
    },
    {
      name: 'Research Agent',
      icon: FaSearch,
      color: 'blue',
      description: 'Gathers relevant news and trending topics',
      responsibilities: [
        'Queries NewsAPI for relevant current events',
        'Identifies trending topics in the industry',
        'Provides context for content relevance',
        'Ensures content is timely and newsworthy',
      ],
      file: 'research_agent.py',
    },
    {
      name: 'Writer Agent',
      icon: FaPen,
      color: 'green',
      description: 'Creates the initial content draft',
      responsibilities: [
        'Generates content based on prompt and research',
        'Applies strategic profile tone and style',
        'Incorporates specified hashtags',
        'Follows platform-specific character limits',
      ],
      file: 'writer_agent.py',
    },
    {
      name: 'Compliance Agent',
      icon: FaBalanceScale,
      color: 'orange',
      description: 'Ensures content meets legal and policy requirements',
      responsibilities: [
        'Checks for regulatory compliance',
        'Identifies potential legal issues',
        'Verifies disclosure requirements',
        'Flags promotional content appropriately',
      ],
      file: 'compliance_agent.py',
    },
    {
      name: 'Cultural Agent',
      icon: FaGlobe,
      color: 'teal',
      description: 'Ensures global cultural sensitivity',
      responsibilities: [
        'Analyzes content for cultural appropriateness',
        'Checks against target region sensitivities',
        'Identifies potential cultural issues',
        'Provides cultural score (must be ≥80)',
      ],
      file: 'cultural_agent.py',
    },
  ];

  const contentAnalysisAgents = [
    {
      name: 'Analysis Orchestrator',
      icon: FaBrain,
      color: 'purple',
      description: 'Coordinates the content analysis workflow',
      responsibilities: [
        'Receives content and media for analysis',
        'Dispatches to specialized analysis agents',
        'Aggregates scores and findings',
        'Generates comprehensive risk assessment',
      ],
      file: 'analysis_orchestrator.py',
    },
    {
      name: 'Visual Agent',
      icon: FaEye,
      color: 'blue',
      description: 'Analyzes images and video content',
      responsibilities: [
        'Performs image safety analysis',
        'Detects inappropriate visual content',
        'Analyzes video frames for compliance',
        'Uses Google Vision API for detection',
      ],
      file: 'visual_agent.py',
    },
    {
      name: 'Text Agent',
      icon: FaFileAlt,
      color: 'green',
      description: 'Analyzes text content for issues',
      responsibilities: [
        'Sentiment analysis',
        'Factual accuracy checking',
        'Grammar and style analysis',
        'Tone and voice consistency',
      ],
      file: 'text_agent.py',
    },
    {
      name: 'Compliance Agent',
      icon: FaShieldAlt,
      color: 'orange',
      description: 'Checks regulatory compliance',
      responsibilities: [
        'Employment law compliance',
        'Advertising standards check',
        'Data privacy considerations',
        'Industry-specific regulations',
      ],
      file: 'compliance_agent.py',
    },
    {
      name: 'Risk Agent',
      icon: FaExclamationTriangle,
      color: 'red',
      description: 'Generates overall risk assessment',
      responsibilities: [
        'Aggregates all agent findings',
        'Calculates overall risk score',
        'Prioritizes issues by severity',
        'Provides actionable recommendations',
      ],
      file: 'risk_agent.py',
    },
  ];

  return (
    <Box>
      {/* Header */}
      <VStack align="start" spacing={2} mb={8}>
        <HStack>
          <Icon as={FaCogs} boxSize={8} color="red.500" />
          <Heading size="lg" color={textColor}>Technical Documentation</Heading>
        </HStack>
        <Text color={mutedColor}>
          Multi-Agent System Architecture & Implementation Details
        </Text>
      </VStack>

      <Tabs colorScheme="red" variant="enclosed">
        <TabList>
          <Tab>Multi-Agent Overview</Tab>
          <Tab>Content Generation</Tab>
          <Tab>Content Analysis</Tab>
          <Tab>Data Flow</Tab>
        </TabList>

        <TabPanels>
          {/* Overview Tab */}
          <TabPanel p={0} pt={6}>
            <VStack spacing={6} align="stretch">
              {/* Architecture Diagram */}
              <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <Heading size="md" color={textColor}>System Architecture Overview</Heading>
                    <Text color={mutedColor} fontSize="sm">
                      Contentry.ai uses a custom Python-based multi-agent system for both content generation and analysis.
                      Each agent is specialized for a specific task and communicates through a central orchestrator.
                    </Text>

                    {/* Visual Diagram */}
                    <Box 
                      p={6} 
                      bg={useColorModeValue('gray.50', 'gray.900')} 
                      borderRadius="xl"
                      borderWidth="2px"
                      borderColor={borderColor}
                    >
                      <VStack spacing={6}>
                        {/* User Request */}
                        <Box textAlign="center">
                          <Badge colorScheme="blue" fontSize="md" px={4} py={2}>
                            User Request
                          </Badge>
                        </Box>

                        <Icon as={FaArrowRight} transform="rotate(90deg)" color="blue.500" boxSize={6} />

                        {/* Orchestrator */}
                        <Box 
                          p={4} 
                          bg="purple.100" 
                          _dark={{ bg: 'purple.800' }}
                          borderRadius="xl"
                          borderWidth="3px"
                          borderColor="purple.500"
                          textAlign="center"
                          minW="200px"
                        >
                          <Icon as={FaBrain} boxSize={8} color="purple.600" mb={2} />
                          <Text fontWeight="bold" color="purple.700" _dark={{ color: 'purple.200' }}>
                            ORCHESTRATOR AGENT
                          </Text>
                          <Text fontSize="xs" color="purple.600" _dark={{ color: 'purple.300' }}>
                            Coordinates & Manages Flow
                          </Text>
                        </Box>

                        <Icon as={FaArrowRight} transform="rotate(90deg)" color="purple.500" boxSize={6} />

                        {/* Specialized Agents Row */}
                        <Grid templateColumns="repeat(5, 1fr)" gap={3} w="100%">
                          {[
                            { icon: FaSearch, name: 'Research', color: 'blue' },
                            { icon: FaPen, name: 'Writer', color: 'green' },
                            { icon: FaBalanceScale, name: 'Compliance', color: 'orange' },
                            { icon: FaGlobe, name: 'Cultural', color: 'teal' },
                            { icon: FaExclamationTriangle, name: 'Risk', color: 'red' },
                          ].map((agent, idx) => (
                            <Box
                              key={idx}
                              p={3}
                              bg={`${agent.color}.100`}
                              _dark={{ bg: `${agent.color}.800` }}
                              borderRadius="lg"
                              borderWidth="2px"
                              borderColor={`${agent.color}.400`}
                              textAlign="center"
                            >
                              <Icon as={agent.icon} boxSize={5} color={`${agent.color}.500`} mb={1} />
                              <Text fontSize="xs" fontWeight="600" color={`${agent.color}.700`} _dark={{ color: `${agent.color}.200` }}>
                                {agent.name}
                              </Text>
                            </Box>
                          ))}
                        </Grid>

                        <Icon as={FaArrowRight} transform="rotate(90deg)" color="green.500" boxSize={6} />

                        {/* Output */}
                        <Box textAlign="center">
                          <Badge colorScheme="green" fontSize="md" px={4} py={2}>
                            Quality-Checked Output
                          </Badge>
                        </Box>
                      </VStack>
                    </Box>

                    {/* Key Features */}
                    <Grid templateColumns={{ base: '1fr', md: 'repeat(3, 1fr)' }} gap={4} mt={4}>
                      <Box p={4} bg={accentBg} borderRadius="lg">
                        <HStack mb={2}>
                          <Icon as={FaCogs} color="blue.500" />
                          <Text fontWeight="600" color={textColor}>Custom Python</Text>
                        </HStack>
                        <Text fontSize="sm" color={mutedColor}>
                          Built entirely in Python using FastAPI, no external workflow tools required.
                        </Text>
                      </Box>
                      <Box p={4} bg={agentBg} borderRadius="lg">
                        <HStack mb={2}>
                          <Icon as={FaBrain} color="purple.500" />
                          <Text fontWeight="600" color={textColor}>LLM Powered</Text>
                        </HStack>
                        <Text fontSize="sm" color={mutedColor}>
                          Uses GPT-4o and GPT-4o-mini via Emergent LLM Key for agent reasoning.
                        </Text>
                      </Box>
                      <Box p={4} bg={flowBg} borderRadius="lg">
                        <HStack mb={2}>
                          <Icon as={FaChartLine} color="green.500" />
                          <Text fontWeight="600" color={textColor}>Quality Gates</Text>
                        </HStack>
                        <Text fontSize="sm" color={mutedColor}>
                          Automatic retry with cultural score ≥80 requirement and compliance checks.
                        </Text>
                      </Box>
                    </Grid>
                  </VStack>
                </CardBody>
              </Card>

              {/* File Structure */}
              <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
                <CardBody>
                  <Heading size="md" color={textColor} mb={4}>File Structure</Heading>
                  <Code display="block" whiteSpace="pre" p={4} borderRadius="md" fontSize="sm">
{`/app/backend/services/agents/
├── __init__.py
├── base_agent.py              # Base class for all agents
├── orchestrator_agent.py      # Content generation orchestrator
├── research_agent.py          # News & trends research
├── writer_agent.py            # Content writing
├── compliance_agent.py        # Legal/policy compliance
├── cultural_agent.py          # Cultural sensitivity
├── analysis_orchestrator.py   # Content analysis orchestrator
├── visual_agent.py            # Image/video analysis
├── text_agent.py              # Text analysis
└── risk_agent.py              # Risk assessment

/app/backend/services/
├── multi_agent_content_service.py   # Generation workflow
└── multi_agent_analysis_service.py  # Analysis workflow`}
                  </Code>
                </CardBody>
              </Card>
            </VStack>
          </TabPanel>

          {/* Content Generation Tab */}
          <TabPanel p={0} pt={6}>
            <VStack spacing={6} align="stretch">
              <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <HStack>
                      <Icon as={FaPen} boxSize={6} color="green.500" />
                      <Heading size="md" color={textColor}>Content Generation Multi-Agent System</Heading>
                    </HStack>
                    <Text color={mutedColor}>
                      The content generation system uses 5 specialized agents working together to create high-quality, 
                      compliant, and culturally appropriate social media content.
                    </Text>

                    {/* Flow Diagram */}
                    <Box p={4} bg={useColorModeValue('green.50', 'green.900')} borderRadius="lg">
                      <Text fontWeight="600" mb={3} color={textColor}>Generation Flow:</Text>
                      <HStack spacing={2} flexWrap="wrap" justify="center">
                        {['User Prompt', '→', 'Orchestrator', '→', 'Research', '→', 'Writer', '→', 'Compliance', '→', 'Cultural', '→', 'Output'].map((item, idx) => (
                          item === '→' ? (
                            <Icon key={idx} as={FaArrowRight} color="green.500" />
                          ) : (
                            <Badge key={idx} colorScheme={
                              item === 'Orchestrator' ? 'purple' :
                              item === 'Research' ? 'blue' :
                              item === 'Writer' ? 'green' :
                              item === 'Compliance' ? 'orange' :
                              item === 'Cultural' ? 'teal' : 'gray'
                            } px={2} py={1}>
                              {item}
                            </Badge>
                          )
                        ))}
                      </HStack>
                    </Box>

                    <Divider />

                    {/* Agent Details */}
                    <Accordion allowMultiple>
                      {contentGenerationAgents.map((agent, idx) => (
                        <AccordionItem key={idx} border="none" mb={2}>
                          <AccordionButton 
                            bg={`${agent.color}.50`} 
                            _dark={{ bg: `${agent.color}.900` }}
                            borderRadius="lg"
                            _hover={{ bg: `${agent.color}.100` }}
                          >
                            <HStack flex="1" textAlign="left">
                              <Icon as={agent.icon} color={`${agent.color}.500`} boxSize={5} />
                              <Text fontWeight="600">{agent.name}</Text>
                              <Badge colorScheme={agent.color} ml={2}>{agent.file}</Badge>
                            </HStack>
                            <AccordionIcon />
                          </AccordionButton>
                          <AccordionPanel pb={4}>
                            <VStack align="stretch" spacing={3}>
                              <Text color={mutedColor}>{agent.description}</Text>
                              <Box>
                                <Text fontWeight="600" fontSize="sm" mb={2}>Responsibilities:</Text>
                                <VStack align="stretch" spacing={1} pl={4}>
                                  {agent.responsibilities.map((resp, ridx) => (
                                    <HStack key={ridx}>
                                      <Box w="6px" h="6px" borderRadius="full" bg={`${agent.color}.500`} />
                                      <Text fontSize="sm" color={mutedColor}>{resp}</Text>
                                    </HStack>
                                  ))}
                                </VStack>
                              </Box>
                            </VStack>
                          </AccordionPanel>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  </VStack>
                </CardBody>
              </Card>

              {/* Quality Gates */}
              <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
                <CardBody>
                  <Heading size="md" color={textColor} mb={4}>Quality Gates</Heading>
                  <Table size="sm">
                    <Thead>
                      <Tr>
                        <Th>Gate</Th>
                        <Th>Threshold</Th>
                        <Th>Action on Failure</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      <Tr>
                        <Td>Cultural Score</Td>
                        <Td><Badge colorScheme="green">≥ 80</Badge></Td>
                        <Td>Regenerate with cultural feedback (max 3 attempts)</Td>
                      </Tr>
                      <Tr>
                        <Td>Compliance Check</Td>
                        <Td><Badge colorScheme="green">Pass</Badge></Td>
                        <Td>Flag for manual review or auto-fix disclosures</Td>
                      </Tr>
                      <Tr>
                        <Td>Hashtag Count</Td>
                        <Td><Badge colorScheme="blue">As specified</Badge></Td>
                        <Td>Writer agent adjusts until count matches</Td>
                      </Tr>
                    </Tbody>
                  </Table>
                </CardBody>
              </Card>
            </VStack>
          </TabPanel>

          {/* Content Analysis Tab */}
          <TabPanel p={0} pt={6}>
            <VStack spacing={6} align="stretch">
              <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <HStack>
                      <Icon as={FaEye} boxSize={6} color="blue.500" />
                      <Heading size="md" color={textColor}>Content Analysis Multi-Agent System</Heading>
                    </HStack>
                    <Text color={mutedColor}>
                      The analysis system evaluates existing content for compliance, accuracy, cultural sensitivity, 
                      and provides comprehensive risk assessment with actionable recommendations.
                    </Text>

                    {/* Flow Diagram */}
                    <Box p={4} bg={useColorModeValue('blue.50', 'blue.900')} borderRadius="lg">
                      <Text fontWeight="600" mb={3} color={textColor}>Analysis Flow:</Text>
                      <VStack spacing={3}>
                        <Badge colorScheme="gray" px={3} py={1}>Content Input (Text + Media)</Badge>
                        <Icon as={FaArrowRight} transform="rotate(90deg)" color="blue.500" />
                        <Badge colorScheme="purple" px={3} py={1}>Analysis Orchestrator</Badge>
                        <Icon as={FaArrowRight} transform="rotate(90deg)" color="purple.500" />
                        <HStack spacing={4}>
                          <Badge colorScheme="blue" px={2} py={1}>Visual</Badge>
                          <Badge colorScheme="green" px={2} py={1}>Text</Badge>
                          <Badge colorScheme="orange" px={2} py={1}>Compliance</Badge>
                        </HStack>
                        <Icon as={FaArrowRight} transform="rotate(90deg)" color="orange.500" />
                        <Badge colorScheme="red" px={3} py={1}>Risk Agent</Badge>
                        <Icon as={FaArrowRight} transform="rotate(90deg)" color="red.500" />
                        <Badge colorScheme="green" px={3} py={1}>Analysis Report</Badge>
                      </VStack>
                    </Box>

                    <Divider />

                    {/* Agent Details */}
                    <Accordion allowMultiple>
                      {contentAnalysisAgents.map((agent, idx) => (
                        <AccordionItem key={idx} border="none" mb={2}>
                          <AccordionButton 
                            bg={`${agent.color}.50`} 
                            _dark={{ bg: `${agent.color}.900` }}
                            borderRadius="lg"
                            _hover={{ bg: `${agent.color}.100` }}
                          >
                            <HStack flex="1" textAlign="left">
                              <Icon as={agent.icon} color={`${agent.color}.500`} boxSize={5} />
                              <Text fontWeight="600">{agent.name}</Text>
                              <Badge colorScheme={agent.color} ml={2}>{agent.file}</Badge>
                            </HStack>
                            <AccordionIcon />
                          </AccordionButton>
                          <AccordionPanel pb={4}>
                            <VStack align="stretch" spacing={3}>
                              <Text color={mutedColor}>{agent.description}</Text>
                              <Box>
                                <Text fontWeight="600" fontSize="sm" mb={2}>Responsibilities:</Text>
                                <VStack align="stretch" spacing={1} pl={4}>
                                  {agent.responsibilities.map((resp, ridx) => (
                                    <HStack key={ridx}>
                                      <Box w="6px" h="6px" borderRadius="full" bg={`${agent.color}.500`} />
                                      <Text fontSize="sm" color={mutedColor}>{resp}</Text>
                                    </HStack>
                                  ))}
                                </VStack>
                              </Box>
                            </VStack>
                          </AccordionPanel>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  </VStack>
                </CardBody>
              </Card>

              {/* Score Thresholds */}
              <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
                <CardBody>
                  <Heading size="md" color={textColor} mb={4}>Score Thresholds</Heading>
                  <Table size="sm">
                    <Thead>
                      <Tr>
                        <Th>Score Type</Th>
                        <Th>Pass</Th>
                        <Th>Warning</Th>
                        <Th>Fail</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      <Tr>
                        <Td>Overall Score</Td>
                        <Td><Badge colorScheme="green">≥ 80</Badge></Td>
                        <Td><Badge colorScheme="yellow">60-79</Badge></Td>
                        <Td><Badge colorScheme="red">&lt; 60</Badge></Td>
                      </Tr>
                      <Tr>
                        <Td>Compliance Score</Td>
                        <Td><Badge colorScheme="green">≥ 80</Badge></Td>
                        <Td><Badge colorScheme="yellow">60-79</Badge></Td>
                        <Td><Badge colorScheme="red">&lt; 60</Badge></Td>
                      </Tr>
                      <Tr>
                        <Td>Accuracy Score</Td>
                        <Td><Badge colorScheme="green">≥ 80</Badge></Td>
                        <Td><Badge colorScheme="yellow">60-79</Badge></Td>
                        <Td><Badge colorScheme="red">&lt; 60</Badge></Td>
                      </Tr>
                      <Tr>
                        <Td>Cultural Score</Td>
                        <Td><Badge colorScheme="green">≥ 80</Badge></Td>
                        <Td><Badge colorScheme="yellow">60-79</Badge></Td>
                        <Td><Badge colorScheme="red">&lt; 60</Badge></Td>
                      </Tr>
                    </Tbody>
                  </Table>
                </CardBody>
              </Card>
            </VStack>
          </TabPanel>

          {/* Data Flow Tab */}
          <TabPanel p={0} pt={6}>
            <VStack spacing={6} align="stretch">
              <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
                <CardBody>
                  <Heading size="md" color={textColor} mb={4}>API Endpoints</Heading>
                  <Table size="sm">
                    <Thead>
                      <Tr>
                        <Th>Endpoint</Th>
                        <Th>Method</Th>
                        <Th>Description</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      <Tr>
                        <Td><Code>/api/v1/content/generate/async</Code></Td>
                        <Td><Badge colorScheme="green">POST</Badge></Td>
                        <Td>Start content generation (multi-agent)</Td>
                      </Tr>
                      <Tr>
                        <Td><Code>/api/v1/content/analyze</Code></Td>
                        <Td><Badge colorScheme="green">POST</Badge></Td>
                        <Td>Analyze content (multi-agent)</Td>
                      </Tr>
                      <Tr>
                        <Td><Code>/api/v1/video/analyze</Code></Td>
                        <Td><Badge colorScheme="green">POST</Badge></Td>
                        <Td>Analyze video/media content</Td>
                      </Tr>
                      <Tr>
                        <Td><Code>/api/v1/content/agents</Code></Td>
                        <Td><Badge colorScheme="blue">GET</Badge></Td>
                        <Td>Get generation agent capabilities</Td>
                      </Tr>
                      <Tr>
                        <Td><Code>/api/v1/video/agents</Code></Td>
                        <Td><Badge colorScheme="blue">GET</Badge></Td>
                        <Td>Get analysis agent capabilities</Td>
                      </Tr>
                    </Tbody>
                  </Table>
                </CardBody>
              </Card>

              <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
                <CardBody>
                  <Heading size="md" color={textColor} mb={4}>External Integrations</Heading>
                  <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)' }} gap={4}>
                    <Box p={4} bg={accentBg} borderRadius="lg">
                      <HStack mb={2}>
                        <Icon as={FaBrain} color="blue.500" />
                        <Text fontWeight="600">OpenAI (via Emergent)</Text>
                      </HStack>
                      <Text fontSize="sm" color={mutedColor}>
                        GPT-4o and GPT-4o-mini for agent reasoning and content generation.
                      </Text>
                    </Box>
                    <Box p={4} bg={accentBg} borderRadius="lg">
                      <HStack mb={2}>
                        <Icon as={FaSearch} color="blue.500" />
                        <Text fontWeight="600">NewsAPI</Text>
                      </HStack>
                      <Text fontSize="sm" color={mutedColor}>
                        Current news and trending topics for content relevance.
                      </Text>
                    </Box>
                    <Box p={4} bg={accentBg} borderRadius="lg">
                      <HStack mb={2}>
                        <Icon as={FaEye} color="blue.500" />
                        <Text fontWeight="600">Google Vision API</Text>
                      </HStack>
                      <Text fontSize="sm" color={mutedColor}>
                        Image and video safety analysis for media content.
                      </Text>
                    </Box>
                    <Box p={4} bg={accentBg} borderRadius="lg">
                      <HStack mb={2}>
                        <Icon as={FaDatabase} color="blue.500" />
                        <Text fontWeight="600">MongoDB</Text>
                      </HStack>
                      <Text fontSize="sm" color={mutedColor}>
                        Storage for analysis results, content history, and user data.
                      </Text>
                    </Box>
                  </Grid>
                </CardBody>
              </Card>
            </VStack>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
}
