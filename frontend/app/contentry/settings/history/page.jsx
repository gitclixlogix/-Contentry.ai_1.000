'use client';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Input,
  Button,
  Flex,
  Text,
  useColorModeValue,
  Card,
  CardBody,
  InputGroup,
  InputLeftElement,
  Icon,
} from '@chakra-ui/react';
import { FaSearch } from 'react-icons/fa';
import { createAuthenticatedAxios } from '@/lib/api';

export default function History() {
  const { t } = useTranslation();
  const [history, setHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [user, setUser] = useState(null);

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const loadHistory = async () => {
    try {
      const axiosInstance = createAuthenticatedAxios();
      const response = await axiosInstance.get('/history');
      setHistory(response.data.history || []);
    } catch (error) {
      console.error('Failed to load history:', error);
      // Mock data for demo
      setHistory([
        {
          id: '1',
          action: 'Content Analysis',
          details: 'Analyzed social media post for compliance',
          timestamp: new Date().toISOString(),
          status: 'completed',
        },
        {
          id: '2',
          action: 'Post Generation',
          details: 'Generated LinkedIn post with professional tone',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          status: 'completed',
        },
        {
          id: '3',
          action: 'Risk Assessment',
          details: 'Performed risk assessment on employee profile',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          status: 'completed',
        },
      ]);
    }
  };

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    loadHistory();
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  const filteredHistory = history.filter(
    (item) =>
      item.action?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.details?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'pending':
        return 'yellow';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <Box px={{ base: 2, md: 4 }} pt={{ base: '80px', md: '80px' }}>
      <Heading size={{ base: 'md', md: 'lg' }} mb={{ base: 4, md: 6 }}>
        {t('settings.activityHistory')}
      </Heading>

      <Card bg={cardBg} mb={6}>
        <CardBody>
          <Flex justify="space-between" align="center" mb={6} gap={4} direction={{ base: 'column', md: 'row' }}>
            <InputGroup maxW={{ base: '100%', md: '400px' }}>
              <InputLeftElement pointerEvents="none">
                <Icon as={FaSearch} color="gray.400" />
              </InputLeftElement>
              <Input
                placeholder={t('settings.searchHistory')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
            <Button colorScheme="brand" size="sm" onClick={loadHistory}>
              {t('common.refresh')}
            </Button>
          </Flex>

          <Box overflowX="auto">
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>{t('settings.action')}</Th>
                  <Th>{t('settings.details')}</Th>
                  <Th>{t('settings.dateTime')}</Th>
                  <Th>{t('common.status')}</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredHistory.length > 0 ? (
                  filteredHistory.map((item) => (
                    <Tr key={item.id}>
                      <Td fontWeight="600" color={textColor}>
                        {item.action}
                      </Td>
                      <Td color={textColorSecondary}>{item.details}</Td>
                      <Td color={textColorSecondary}>
                        {new Date(item.timestamp).toLocaleString()}
                      </Td>
                      <Td>
                        <Badge colorScheme={getStatusColor(item.status)}>
                          {item.status}
                        </Badge>
                      </Td>
                    </Tr>
                  ))
                ) : (
                  <Tr>
                    <Td colSpan={4} textAlign="center" py={10}>
                      <Text color={textColorSecondary}>
                        {t('settings.noHistoryFound')}
                      </Text>
                    </Td>
                  </Tr>
                )}
              </Tbody>
            </Table>
          </Box>
        </CardBody>
      </Card>
    </Box>
  );
}