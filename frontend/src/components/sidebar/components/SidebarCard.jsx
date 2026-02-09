'use client';
import { Box, Flex, Text, Progress, Skeleton } from '@chakra-ui/react';
import BarChart from '@/components/charts/BarChart';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { createAuthenticatedAxios } from '@/lib/api';

export default function SidebarDocs() {
  const bgColor = 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)';
  const router = useRouter();
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  
  // Credit data state
  const [creditData, setCreditData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState([]);
  
  // Fetch credit balance from API
  const fetchCreditBalance = useCallback(async () => {
    if (!isAuthenticated || !user?.id) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const api = createAuthenticatedAxios();
      
      // Fetch both balance and usage in parallel
      const [balanceResponse, usageResponse] = await Promise.all([
        api.get('/credits/balance'),
        api.get('/credits/usage?days=7').catch(() => ({ data: { success: false } }))
      ]);
      
      if (balanceResponse.data?.success && balanceResponse.data?.data) {
        setCreditData(balanceResponse.data.data);
        
        // Generate chart data based on daily usage (last 7 days)
        let chartValues = [0, 0, 0, 0, 0, 0, 0]; // Default empty data
        
        if (usageResponse.data?.success && usageResponse.data?.data?.daily_usage) {
          const dailyUsage = usageResponse.data.data.daily_usage;
          // Get last 7 days, pad with zeros if needed
          chartValues = dailyUsage.slice(-7).map(u => u.credits || 0);
          while (chartValues.length < 7) {
            chartValues.unshift(0);
          }
        }
        
        setChartData([{
          name: 'Credits Used',
          data: chartValues,
        }]);
      }
    } catch (err) {
      console.error('Error fetching credit balance:', err);
      // Set default values on error
      setCreditData({
        credits_balance: 0,
        credits_used_this_month: 0,
        monthly_allowance: 25,
        plan: 'free',
      });
      setChartData([{ name: 'Credits Used', data: [0, 0, 0, 0, 0, 0, 0] }]);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user?.id]);
  
  // Fetch on mount and when user changes
  useEffect(() => {
    fetchCreditBalance();
    
    // Refresh every 60 seconds
    const interval = setInterval(fetchCreditBalance, 60000);
    
    // Listen for credit updates from other parts of the app
    const handleCreditUpdate = () => fetchCreditBalance();
    window.addEventListener('creditsUpdated', handleCreditUpdate);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('creditsUpdated', handleCreditUpdate);
    };
  }, [fetchCreditBalance]);

  const handleClick = () => {
    router.push('/contentry/settings/usage');
  };
  
  // Calculate usage percentage
  const creditsUsed = creditData?.credits_used_this_month || 0;
  const monthlyAllowance = creditData?.monthly_allowance || 25;
  const creditsRemaining = creditData?.credits_balance || 0;
  const usagePercentage = monthlyAllowance > 0 
    ? Math.min(100, Math.round((creditsUsed / monthlyAllowance) * 100))
    : 0;
  
  // Format numbers for display
  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };
  
  // Chart options (adapted for sidebar)
  const barChartOptions = {
    chart: {
      toolbar: { show: false },
      background: 'transparent',
      sparkline: { enabled: true },
    },
    tooltip: {
      theme: 'dark',
      y: {
        formatter: (value) => `${value} credits`,
      },
    },
    plotOptions: {
      bar: {
        borderRadius: 3,
        columnWidth: '60%',
      },
    },
    colors: ['rgba(255, 255, 255, 0.7)'],
    grid: { show: false },
    dataLabels: { enabled: false },
    xaxis: {
      labels: { show: false },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: { show: false },
  };

  return (
    <Flex
      justify="center"
      direction="column"
      align="center"
      bg={bgColor}
      borderRadius={{ base: '12px', md: '16px' }}
      position="relative"
      w="100%"
      pb={{ base: '6px', md: '10px' }}
      cursor="pointer"
      onClick={handleClick}
      transition="all 0.2s"
      _hover={{
        transform: 'translateY(-2px)',
        boxShadow: '0 4px 12px rgba(30, 64, 175, 0.4)',
      }}
      _active={{
        transform: 'translateY(0px)',
      }}
      minH={{ base: '100px', sm: '120px', md: '180px' }}
    >
      <Flex direction="column" mb={{ base: '6px', md: '12px' }} w="100%" px={{ base: '12px', md: '20px' }} pt={{ base: '12px', md: '20px' }}>
        <Flex justify="space-between" align="center" mb={{ base: '6px', md: '10px' }} flexWrap="wrap" gap={1}>
          <Text fontSize={{ base: 'xs', md: 'sm' }} fontWeight={'600'} color="white">
            {t('subscription.credits', 'Credits')}
          </Text>
          {creditData?.plan && (
            <Text 
              fontSize={{ base: '2xs', md: 'xs' }}
              fontWeight="500" 
              color="whiteAlpha.800"
              textTransform="capitalize"
              bg="whiteAlpha.200"
              px={{ base: '6px', md: '8px' }}
              py={{ base: '1px', md: '2px' }}
              borderRadius="full"
            >
              {creditData.plan}
            </Text>
          )}
        </Flex>
        
        {loading ? (
          <>
            <Skeleton height="6px" mb="6px" startColor="whiteAlpha.300" endColor="whiteAlpha.500" />
            <Skeleton height="14px" width="60%" startColor="whiteAlpha.300" endColor="whiteAlpha.500" />
          </>
        ) : (
          <>
            <Progress
              mb={{ base: '4px', md: '6px' }}
              value={usagePercentage}
              colorScheme={usagePercentage > 80 ? 'red' : 'whiteAlpha'}
              style={{
                background: 'rgba(255, 255, 255, 0.3)',
                width: '100%',
                height: '6px',
              }}
              borderRadius="full"
            />
            <Flex 
              justify="space-between" 
              align="center" 
              mb={{ base: '8px', md: '14px' }}
              flexWrap="wrap"
              gap={{ base: 1, md: 2 }}
            >
              <Text fontWeight={'500'} fontSize={{ base: 'xs', md: 'sm' }} color="white">
                {formatNumber(creditsUsed)}/{formatNumber(monthlyAllowance)} {t('subscription.creditsUsed', 'used')}
              </Text>
              <Text fontWeight={'600'} fontSize={{ base: '2xs', md: 'xs' }} color="whiteAlpha.800">
                {formatNumber(creditsRemaining)} {t('subscription.remaining', 'left')}
              </Text>
            </Flex>
          </>
        )}
      </Flex>
      
      {/* Usage Chart - Hidden on very small screens */}
      <Box 
        h={{ base: '80px', sm: '100px', md: '160px' }}
        w="100%" 
        mt={{ base: '-24px', md: '-46px' }}
        pointerEvents="none"
        display={{ base: 'none', sm: 'block' }}
      >
        {!loading && chartData.length > 0 && (
          <BarChart
            chartData={chartData}
            chartOptions={barChartOptions}
          />
        )}
      </Box>
    </Flex>
  );
}
