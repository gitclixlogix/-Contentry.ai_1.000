'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Icon,
  useColorModeValue,
  Spinner,
  Center,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react';
import { 
  FaChartLine, 
  FaUsers, 
  FaDollarSign, 
  FaCog,
  FaShieldAlt,
  FaHome,
  FaChartBar,
  FaBuilding,
  FaBook
} from 'react-icons/fa';
import { FaRobot } from 'react-icons/fa';
import Link from 'next/link';
import { getApiUrl } from '@/lib/api';

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/superadmin/dashboard', icon: FaChartLine, description: 'KPIs & Overview' },
  { label: 'Token Management', href: '/superadmin/token-management', icon: FaRobot, description: 'AI Token Usage' },
  { label: 'Users & Customers', href: '/superadmin/users', icon: FaUsers, description: 'Manage accounts' },
  { label: 'Analytics', href: '/superadmin/analytics', icon: FaChartBar, description: 'Deep insights' },
  { label: 'Technical Docs', href: '/superadmin/documentation', icon: FaBook, description: 'System architecture' },
];

export default function SuperAdminLayout({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthorized, setIsAuthorized] = useState(null);
  const [loading, setLoading] = useState(true);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const sidebarBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.700', 'white');
  const accentColor = useColorModeValue('red.600', 'red.400');
  const hoverBg = useColorModeValue('red.50', 'red.900');

  useEffect(() => {
    // Small delay to ensure localStorage is populated after redirect
    const timer = setTimeout(() => {
      verifySuperAdminAccess();
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  const verifySuperAdminAccess = async () => {
    try {
      // Get userId from either direct storage or from contentry_user object
      let userId = localStorage.getItem('userId');
      let userRole = null;
      
      // Always read user data from contentry_user for role info
      const userStr = localStorage.getItem('contentry_user');
      console.log('[SuperAdmin] Checking access - userId:', userId, 'userStr:', userStr ? 'exists' : 'null');
      
      if (userStr) {
        try {
          const userData = JSON.parse(userStr);
          // Use userId from contentry_user if not found directly
          if (!userId) {
            userId = userData.id;
          }
          userRole = userData.role;
          console.log('[SuperAdmin] Parsed user data - role:', userRole, 'id:', userData.id);
        } catch (e) {
          console.error('[SuperAdmin] Failed to parse user data:', e);
        }
      }

      // Quick check from localStorage before API call
      if (!userId) {
        console.log('[SuperAdmin] No userId found, denying access');
        setIsAuthorized(false);
        setLoading(false);
        return;
      }
      
      // Check role from localStorage first (fast path)
      console.log('[SuperAdmin] Role check - userRole:', userRole, 'isSuper:', userRole === 'super_admin');
      if (userRole === 'super_admin') {
        // Verify with backend using HttpOnly cookie auth
        console.log('[SuperAdmin] Making verify API call...');
        const response = await fetch(`${getApiUrl()}/superadmin/verify`, {
          method: 'GET',
          credentials: 'include',  // Include HttpOnly cookies
          headers: {
            'Content-Type': 'application/json',
            'x-user-id': userId,
          },
        });

        console.log('[SuperAdmin] Verify response:', response.status);
        if (response.ok) {
          setIsAuthorized(true);
        } else {
          setIsAuthorized(false);
        }
      } else {
        console.log('[SuperAdmin] Role is not super_admin, denying access');
        setIsAuthorized(false);
      }
    } catch (error) {
      console.error('[SuperAdmin] Verification failed:', error);
      setIsAuthorized(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Center h="100vh" bg={bgColor}>
        <VStack spacing={4}>
          <Spinner size="xl" color="red.500" thickness="4px" />
          <Text color={textColor}>Verifying access...</Text>
        </VStack>
      </Center>
    );
  }

  if (!isAuthorized) {
    return (
      <Center h="100vh" bg={bgColor}>
        <Alert
          status="error"
          variant="subtle"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          textAlign="center"
          borderRadius="xl"
          py={10}
          px={8}
          maxW="500px"
          boxShadow="xl"
        >
          <AlertIcon boxSize="50px" mr={0} mb={4} />
          <AlertTitle fontSize="xl" mb={2}>
            Access Denied
          </AlertTitle>
          <AlertDescription maxWidth="sm">
            You do not have permission to access the Super Admin dashboard.
            This area is restricted to users with the <strong>super_admin</strong> role.
          </AlertDescription>
          <Link href="/contentry/dashboard">
            <Text 
              color="red.500" 
              fontWeight="600" 
              mt={4} 
              cursor="pointer"
              _hover={{ textDecoration: 'underline' }}
            >
              ← Return to Dashboard
            </Text>
          </Link>
        </Alert>
      </Center>
    );
  }

  return (
    <Flex minH="100vh" bg={bgColor}>
      {/* Sidebar */}
      <Box
        w="250px"
        bg={sidebarBg}
        borderRight="1px"
        borderColor={useColorModeValue('gray.200', 'gray.700')}
        py={6}
        position="fixed"
        h="100vh"
        overflowY="auto"
      >
        {/* Logo/Title */}
        <VStack spacing={1} mb={8} px={6}>
          <HStack spacing={2}>
            <Icon as={FaShieldAlt} boxSize={6} color={accentColor} />
            <Text fontSize="lg" fontWeight="bold" color={accentColor}>
              Super Admin
            </Text>
          </HStack>
          <Text fontSize="xs" color="gray.500">
            Business Intelligence Portal
          </Text>
        </VStack>

        {/* Navigation */}
        <VStack spacing={1} align="stretch" px={3}>
          {NAV_ITEMS.map((item) => {
            // Check if current path starts with the nav item href (for nested routes)
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
            return (
              <Link key={item.href} href={item.href}>
                <VStack
                  align="stretch"
                  spacing={0}
                  px={4}
                  py={3}
                  borderRadius="lg"
                  bg={isActive ? hoverBg : 'transparent'}
                  _hover={{ bg: hoverBg }}
                  transition="all 0.2s"
                  cursor="pointer"
                >
                  <HStack>
                    <Icon as={item.icon} boxSize={5} color={isActive ? accentColor : textColor} />
                    <Text fontSize="sm" fontWeight={isActive ? '600' : '500'} color={isActive ? accentColor : textColor}>
                      {item.label}
                    </Text>
                  </HStack>
                  {item.description && (
                    <Text fontSize="xs" color="gray.500" ml={7}>
                      {item.description}
                    </Text>
                  )}
                </VStack>
              </Link>
            );
          })}
        </VStack>

        {/* Back to App */}
        <Box position="absolute" bottom={6} left={0} right={0} px={3}>
          <Link href="/contentry/dashboard">
            <HStack
              px={4}
              py={3}
              borderRadius="lg"
              color="gray.500"
              _hover={{ bg: hoverBg, color: textColor }}
              transition="all 0.2s"
              cursor="pointer"
            >
              <Icon as={FaHome} boxSize={5} />
              <Text fontSize="sm">Back to App</Text>
            </HStack>
          </Link>
        </Box>
      </Box>

      {/* Main Content */}
      <Box ml="250px" flex={1} p={8}>
        {children}
      </Box>
    </Flex>
  );
}
