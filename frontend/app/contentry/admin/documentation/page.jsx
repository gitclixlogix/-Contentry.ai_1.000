'use client';
import { useTranslation } from 'react-i18next';
/* eslint-disable react/no-unstable-nested-components */
import { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Heading,
  Button,
  HStack,
  VStack,
  Card,
  CardBody,
  useColorModeValue,
  Text,
  Spinner,
  Center,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Code,
  Divider
} from '@chakra-ui/react';
import { FaDownload, FaFilePdf, FaFileCode, FaCopy } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getApiUrl } from '@/lib/api';

export default function AdminDocumentation() {
  const [docContent, setDocContent] = useState('');
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const codeBg = useColorModeValue('gray.100', 'gray.900');
  const blockquoteBg = useColorModeValue('gray.50', 'gray.900');
  const tableTh = useColorModeValue('gray.100', 'gray.700');

  // Memoize markdown components to prevent recreation on every render
  const markdownComponents = useMemo(() => ({
    h1: ({ node, ...props }) => (
      <Heading as="h1" size="xl" mt={8} mb={4} color={textColor} {...props} />
    ),
    h2: ({ node, ...props }) => (
      <Heading as="h2" size="lg" mt={6} mb={3} color={textColor} {...props} />
    ),
    h3: ({ node, ...props }) => (
      <Heading as="h3" size="md" mt={4} mb={2} color={textColor} {...props} />
    ),
    h4: ({ node, ...props }) => (
      <Heading as="h4" size="sm" mt={3} mb={2} color={textColor} {...props} />
    ),
    p: ({ node, ...props }) => (
      <Text mb={3} color={textColor} lineHeight="1.8" {...props} />
    ),
    code: ({ node, inline, ...props }) =>
      inline ? (
        <Code
          bg={codeBg}
          px={2}
          py={1}
          borderRadius="md"
          fontSize="sm"
          {...props}
        />
      ) : (
        <Code
          display="block"
          bg={codeBg}
          p={4}
          borderRadius="md"
          fontSize="sm"
          overflowX="auto"
          whiteSpace="pre"
          {...props}
        />
      ),
    ul: ({ node, ...props }) => (
      <Box as="ul" pl={6} mb={3} {...props} />
    ),
    ol: ({ node, ...props }) => (
      <Box as="ol" pl={6} mb={3} {...props} />
    ),
    li: ({ node, ...props }) => (
      <Box as="li" mb={1} color={textColor} {...props} />
    ),
    blockquote: ({ node, ...props }) => (
      <Box
        as="blockquote"
        borderLeftWidth="4px"
        borderLeftColor="brand.500"
        pl={4}
        py={2}
        my={4}
        fontStyle="italic"
        bg={blockquoteBg}
        {...props}
      />
    ),
    hr: ({ node, ...props }) => <Divider my={6} {...props} />,
    table: ({ node, ...props }) => (
      <Box overflowX="auto" mb={4}>
        <Box
          as="table"
          width="100%"
          borderWidth="1px"
          borderColor="gray.200"
          {...props}
        />
      </Box>
    ),
    th: ({ node, ...props }) => (
      <Box
        as="th"
        bg={tableTh}
        p={2}
        textAlign="left"
        borderWidth="1px"
        fontWeight="bold"
        {...props}
      />
    ),
    td: ({ node, ...props }) => (
      <Box
        as="td"
        p={2}
        borderWidth="1px"
        borderColor="gray.200"
        {...props}
      />
    ),
  }), [textColor, codeBg, blockquoteBg, tableTh]);

  useEffect(() => {
    fetchDocumentation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchDocumentation = async () => {
    try {
      const API = getApiUrl();
      const response = await fetch(`${API}/admin/documentation`);
      const data = await response.json();
      setDocContent(data.content);
    } catch (error) {
      console.error('Error fetching documentation:', error);
      toast({
        title: 'Error Loading Documentation',
        description: 'Could not load documentation content',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const downloadMarkdown = () => {
    const blob = new Blob([docContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Contentry_Platform_Documentation.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Download Started',
      description: 'Markdown file is being downloaded',
      status: 'success',
      duration: 2000,
    });
  };

  const downloadPDF = async () => {
    try {
      toast({
        title: 'Opening Print Dialog',
        description: 'Use "Save as PDF" in print options',
        status: 'info',
        duration: 3000,
      });

      const API = getApiUrl();
      // Open the PDF endpoint in a new window - it returns printable HTML
      window.open(`${API}/admin/documentation/pdf`, '_blank');

    } catch (error) {
      toast({
        title: 'PDF Generation Failed',
        description: error.message,
        status: 'error',
        duration: 3000,
      });
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(docContent);
    toast({
      title: 'Copied!',
      description: 'Documentation copied to clipboard',
      status: 'success',
      duration: 2000,
    });
  };

  if (loading) {
    return (
      <Center h="80vh">
        <VStack spacing={4}>
          <Spinner size="xl" color="brand.500" thickness="4px" />
          <Text>Loading Documentation...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box pt={{ base: '80px', md: '80px' }} px={{ base: 2, md: 4 }}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Card bg={cardBg} borderWidth="2px" borderColor="brand.500">
          <CardBody>
            <HStack justify="space-between" flexWrap="wrap" gap={4}>
              <VStack align="start" spacing={1}>
                <Heading size={{ base: "md", md: "lg" }} color={textColor}>
                  📚 Platform Documentation
                </Heading>
                <Text fontSize={{ base: "sm", md: "md" }} color="gray.600">
                  Comprehensive Contentry AI Platform Reference
                </Text>
                <Text fontSize="xs" color="gray.500">
                  Version 1.0.0 | Last Updated: November 26, 2024
                </Text>
              </VStack>

              <HStack spacing={2} flexWrap="wrap">
                <Button
                  leftIcon={<FaCopy />}
                  colorScheme="blue"
                  size="sm"
                  onClick={copyToClipboard}
                >
                  Copy
                </Button>
                <Button
                  leftIcon={<FaFileCode />}
                  colorScheme="green"
                  size="sm"
                  onClick={downloadMarkdown}
                >
                  Download MD
                </Button>
                <Button
                  leftIcon={<FaFilePdf />}
                  colorScheme="red"
                  size="sm"
                  onClick={downloadPDF}
                >
                  Download PDF
                </Button>
              </HStack>
            </HStack>
          </CardBody>
        </Card>

        {/* Content */}
        <Card bg={cardBg}>
          <CardBody>
            <Tabs variant="enclosed" colorScheme="brand">
              <TabList>
                <Tab fontSize={{ base: "sm", md: "md" }}>📖 Formatted View</Tab>
                <Tab fontSize={{ base: "sm", md: "md" }}>💻 Raw Markdown</Tab>
              </TabList>

              <TabPanels>
                {/* Formatted View */}
                <TabPanel>
                  <Box
                    maxH="70vh"
                    overflowY="auto"
                    p={4}
                    css={{
                      '&::-webkit-scrollbar': {
                        width: '8px',
                      },
                      '&::-webkit-scrollbar-track': {
                        background: '#f1f1f1',
                      },
                      '&::-webkit-scrollbar-thumb': {
                        background: '#888',
                        borderRadius: '4px',
                      },
                      '&::-webkit-scrollbar-thumb:hover': {
                        background: '#555',
                      },
                    }}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={markdownComponents}
                    >
                      {docContent}
                    </ReactMarkdown>
                  </Box>
                </TabPanel>

                {/* Raw Markdown */}
                <TabPanel>
                  <Box
                    as="pre"
                    maxH="70vh"
                    overflowY="auto"
                    bg={codeBg}
                    p={4}
                    borderRadius="md"
                    fontSize="sm"
                    fontFamily="monospace"
                    whiteSpace="pre-wrap"
                    wordBreak="break-word"
                    css={{
                      '&::-webkit-scrollbar': {
                        width: '8px',
                      },
                      '&::-webkit-scrollbar-track': {
                        background: '#f1f1f1',
                      },
                      '&::-webkit-scrollbar-thumb': {
                        background: '#888',
                        borderRadius: '4px',
                      },
                    }}
                  >
                    {docContent}
                  </Box>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
}
