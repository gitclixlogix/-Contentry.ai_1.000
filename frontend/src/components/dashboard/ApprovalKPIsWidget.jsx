'use client';

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  Flex,
  VStack,
  HStack,
  useColorModeValue,
  Spinner,
  Icon,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Tooltip,
} from '@chakra-ui/react';
import { FaClipboardCheck, FaClock, FaTimesCircle, FaCheckCircle, FaExternalLinkAlt } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import { createAuthenticatedAxios } from '@/lib/api';
import ExportButton from './ExportButton';

export default function ApprovalKPIsWidget({ userId, dateRange, customStart, customEnd }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const brandColor = useColorModeValue('brand.500', 'brand.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  useEffect(() => {
    fetchApprovalKPIs();
  }, [userId, dateRange, customStart, customEnd]);

  const fetchApprovalKPIs = async () => {
    setLoading(true);
    try {
      // Use authenticated axios with HttpOnly cookie (ARCH-022)
      const api = createAuthenticatedAxios();
      let url = `/dashboard/approval-kpis?date_range=${dateRange || 'last_30_days'}`;
      
      if (customStart && customEnd) {
        url += `&custom_start=${customStart}&custom_end=${customEnd}`;
      }

      const response = await api.get(url, {
        headers: {
          'x-user-id': userId,
        },
      });

      setData(response.data);
    } catch (err) {
      console.error('Approval KPIs error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKPIClick = (drillDownUrl) => {
    if (drillDownUrl) {
      router.push(drillDownUrl);
    }
  };

  const kpis = data?.kpis || {};

  return (
    <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
      <CardHeader pb={2}>
        <Flex justify="space-between" align="center">
          <HStack spacing={3}>
            <Icon as={FaClipboardCheck} boxSize={5} color={brandColor} />
            <Box>
              <Heading size="md" color={textColor}>
                {t('dashboard.approvalKpis.title', 'Approval Workflow KPIs')}
              </Heading>
              <Text fontSize="sm" color={textColorSecondary}>
                {t('dashboard.approvalKpis.description', 'Key metrics for content approval process')}
              </Text>
            </Box>
          </HStack>
          <ExportButton 
            widgetType="approval-kpis" 
            dateRange={dateRange}
            customStart={customStart}
            customEnd={customEnd}
          />
        </Flex>
      </CardHeader>
      <CardBody>
        {loading ? (
          <Flex justify="center" py={10}>
            <Spinner size="lg" color="brand.500" />
          </Flex>
        ) : error ? (
          <Text color="red.500" textAlign="center" py={4}>{error}</Text>
        ) : (
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            {/* Average Time to Approval */}
            <Tooltip label={t('dashboard.approvalKpis.clickToViewApproved', 'Click to view approved content')} hasArrow>
              <Box
                p={4}
                borderRadius="lg"
                bg={useColorModeValue('blue.50', 'blue.900')}
                cursor="pointer"
                _hover={{ bg: hoverBg, transform: 'translateY(-2px)' }}
                transition="all 0.2s"
                onClick={() => handleKPIClick(kpis.avg_time_to_approval?.drill_down_url)}
              >
                <Stat>
                  <StatLabel color={textColorSecondary} fontSize="xs">
                    <HStack>
                      <Icon as={FaClock} />
                      <Text>{t('dashboard.approvalKpis.avgTimeToApproval', 'Avg Time to Approval')}</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber color="blue.500" fontSize="2xl">
                    {kpis.avg_time_to_approval?.formatted || '0'}
                  </StatNumber>
                  <StatHelpText fontSize="xs">
                    <HStack>
                      <Text>{t('dashboard.approvalKpis.viewDetails', 'View details')}</Text>
                      <Icon as={FaExternalLinkAlt} boxSize={2} />
                    </HStack>
                  </StatHelpText>
                </Stat>
              </Box>
            </Tooltip>

            {/* Rejection Rate */}
            <Tooltip label={t('dashboard.approvalKpis.clickToViewRejected', 'Click to view rejected content')} hasArrow>
              <Box
                p={4}
                borderRadius="lg"
                bg={useColorModeValue(
                  kpis.rejection_rate?.value > 20 ? 'red.50' : 'green.50',
                  kpis.rejection_rate?.value > 20 ? 'red.900' : 'green.900'
                )}
                cursor="pointer"
                _hover={{ bg: hoverBg, transform: 'translateY(-2px)' }}
                transition="all 0.2s"
                onClick={() => handleKPIClick(kpis.rejection_rate?.drill_down_url)}
              >
                <Stat>
                  <StatLabel color={textColorSecondary} fontSize="xs">
                    <HStack>
                      <Icon as={FaTimesCircle} />
                      <Text>{t('dashboard.approvalKpis.rejectionRate', 'Rejection Rate')}</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber 
                    color={kpis.rejection_rate?.value > 20 ? 'red.500' : 'green.500'} 
                    fontSize="2xl"
                  >
                    {kpis.rejection_rate?.formatted || '0%'}
                  </StatNumber>
                  <StatHelpText fontSize="xs">
                    {kpis.rejection_rate?.value > 20 ? (
                      <StatArrow type="increase" />
                    ) : (
                      <StatArrow type="decrease" />
                    )}
                    {kpis.rejection_rate?.value > 20 ? t('dashboard.approvalKpis.high', 'High') : t('dashboard.approvalKpis.good', 'Good')}
                  </StatHelpText>
                </Stat>
              </Box>
            </Tooltip>

            {/* Total Approved */}
            <Tooltip label={t('dashboard.approvalKpis.clickToViewApproved', 'Click to view approved content')} hasArrow>
              <Box
                p={4}
                borderRadius="lg"
                bg={useColorModeValue('green.50', 'green.900')}
                cursor="pointer"
                _hover={{ bg: hoverBg, transform: 'translateY(-2px)' }}
                transition="all 0.2s"
                onClick={() => handleKPIClick(kpis.total_approved?.drill_down_url)}
              >
                <Stat>
                  <StatLabel color={textColorSecondary} fontSize="xs">
                    <HStack>
                      <Icon as={FaCheckCircle} />
                      <Text>{t('dashboard.approvalKpis.totalApproved', 'Total Approved')}</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber color="green.500" fontSize="2xl">
                    {kpis.total_approved?.value || 0}
                  </StatNumber>
                  <StatHelpText fontSize="xs">
                    <HStack>
                      <Text>{t('dashboard.approvalKpis.viewAll', 'View all')}</Text>
                      <Icon as={FaExternalLinkAlt} boxSize={2} />
                    </HStack>
                  </StatHelpText>
                </Stat>
              </Box>
            </Tooltip>

            {/* Total Rejected */}
            <Tooltip label={t('dashboard.approvalKpis.clickToViewRejected', 'Click to view rejected content')} hasArrow>
              <Box
                p={4}
                borderRadius="lg"
                bg={useColorModeValue('orange.50', 'orange.900')}
                cursor="pointer"
                _hover={{ bg: hoverBg, transform: 'translateY(-2px)' }}
                transition="all 0.2s"
                onClick={() => handleKPIClick(kpis.total_rejected?.drill_down_url)}
              >
                <Stat>
                  <StatLabel color={textColorSecondary} fontSize="xs">
                    <HStack>
                      <Icon as={FaTimesCircle} />
                      <Text>{t('dashboard.approvalKpis.totalRejected', 'Total Rejected')}</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber color="orange.500" fontSize="2xl">
                    {kpis.total_rejected?.value || 0}
                  </StatNumber>
                  <StatHelpText fontSize="xs">
                    <HStack>
                      <Text>{t('dashboard.approvalKpis.viewAll', 'View all')}</Text>
                      <Icon as={FaExternalLinkAlt} boxSize={2} />
                    </HStack>
                  </StatHelpText>
                </Stat>
              </Box>
            </Tooltip>
          </SimpleGrid>
        )}
      </CardBody>
    </Card>
  );
}
