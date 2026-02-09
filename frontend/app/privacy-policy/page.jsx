'use client';

import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  useColorModeValue,
  Skeleton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  UnorderedList,
  ListItem,
  Divider,
} from '@chakra-ui/react';
import ReactMarkdown from 'react-markdown';

export default function PrivacyPolicyPage() {
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.700', 'gray.200');

  useEffect(() => {
    fetch('/legal/privacy-policy.md')
      .then((res) => res.text())
      .then((text) => {
        setContent(text);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, []);

  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')} py={12}>
      <Container maxW="4xl">
        <Box bg={bgColor} borderRadius="xl" shadow="sm" p={8}>
          {isLoading ? (
            <VStack spacing={4} align="stretch">
              <Skeleton height="40px" width="60%" />
              <Skeleton height="20px" />
              <Skeleton height="20px" />
              <Skeleton height="20px" width="80%" />
            </VStack>
          ) : (
            <Box
              className="prose prose-lg max-w-none"
              color={textColor}
              sx={{
                h1: { fontSize: '2xl', fontWeight: 'bold', mb: 4 },
                h2: { fontSize: 'xl', fontWeight: 'semibold', mt: 8, mb: 4 },
                h3: { fontSize: 'lg', fontWeight: 'semibold', mt: 6, mb: 3 },
                p: { mb: 4, lineHeight: 'tall' },
                ul: { pl: 6, mb: 4 },
                li: { mb: 2 },
                table: { width: '100%', mb: 4 },
                th: { textAlign: 'left', p: 2, borderBottom: '2px solid', borderColor: 'gray.200' },
                td: { p: 2, borderBottom: '1px solid', borderColor: 'gray.100' },
                a: { color: 'brand.500', textDecoration: 'underline' },
                hr: { my: 8 },
              }}
            >
              <ReactMarkdown
                components={{
                  h1: ({ children }) => <Heading as="h1" size="xl" mb={4}>{children}</Heading>,
                  h2: ({ children }) => <Heading as="h2" size="lg" mt={8} mb={4}>{children}</Heading>,
                  h3: ({ children }) => <Heading as="h3" size="md" mt={6} mb={3}>{children}</Heading>,
                  p: ({ children }) => <Text mb={4} lineHeight="tall">{children}</Text>,
                  ul: ({ children }) => <UnorderedList pl={6} mb={4}>{children}</UnorderedList>,
                  li: ({ children }) => <ListItem mb={2}>{children}</ListItem>,
                  hr: () => <Divider my={8} />,
                  table: ({ children }) => <Table variant="simple" mb={4}>{children}</Table>,
                  thead: ({ children }) => <Thead>{children}</Thead>,
                  tbody: ({ children }) => <Tbody>{children}</Tbody>,
                  tr: ({ children }) => <Tr>{children}</Tr>,
                  th: ({ children }) => <Th>{children}</Th>,
                  td: ({ children }) => <Td>{children}</Td>,
                }}
              >
                {content}
              </ReactMarkdown>
            </Box>
          )}
        </Box>
      </Container>
    </Box>
  );
}
