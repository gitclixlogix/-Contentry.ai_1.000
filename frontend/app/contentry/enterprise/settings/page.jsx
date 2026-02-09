'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import {
  Box, Card, CardBody, Flex, Icon, Text, VStack, useColorModeValue, Heading, Badge
} from '@chakra-ui/react';
import { FaBuilding, FaUsers, FaCreditCard, FaFileAlt, FaChevronRight } from 'react-icons/fa';
import { useRouter, usePathname } from 'next/navigation';

export default function CompanySettings() {
  const [user, setUser] = useState(null);
  const router = useRouter();
  const pathname = usePathname();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');

  useEffect(() => {
    const storedUser = localStorage.getItem('contentry_user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUser(userData);
      
      // Check if user is enterprise admin (accept both 'admin' and 'enterprise_admin' roles)
      const isEnterpriseAdmin = userData.enterprise_role === 'enterprise_admin' || 
                                 userData.enterprise_role === 'admin' ||
                                 userData.is_enterprise_admin === true;
      
      if (!isEnterpriseAdmin || !userData.enterprise_id) {
        router.push('/contentry/dashboard');
      }
    } else {
      router.push('/contentry/auth/login');
    }
  }, [router]);

  const settingsMenu = [
    {
      id: 'company',
      icon: FaBuilding,
      label: 'Company Profile',
      description: 'Manage company information, logo, and documents',
      path: '/contentry/enterprise/settings/company'
    },
    {
      id: 'users',
      icon: FaUsers,
      label: 'Users',
      description: 'View and manage company users',
      path: '/contentry/enterprise/settings/users'
    },
    {
      id: 'billing',
      icon: FaCreditCard,
      label: 'Billing & Usage',
      description: 'Subscription and usage analytics',
      path: '/contentry/enterprise/settings/billing'
    }
  ];

  const handleNavigate = (path) => {
    router.push(path);
  };

  if (!user) {
    return null;
  }

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      <Card bg={bgColor} boxShadow="lg" mb={6}>
        <CardBody p={{ base: 4, md: 6 }}>
          <Flex align="center" gap={3} mb={2}>
            <Icon as={FaBuilding} boxSize={8} color="brand.500" />
            <Heading size="lg" color={textColor}>Company Settings</Heading>
            <Badge colorScheme="blue" fontSize="sm" px={3} py={1}>
              ENTERPRISE ADMIN
            </Badge>
          </Flex>
          <Text color={textColorSecondary} fontSize="md">
            Manage your company profile, users, and billing settings
          </Text>
        </CardBody>
      </Card>

      <VStack spacing={4} align="stretch">
        {settingsMenu.map((item) => (
          <Card
            key={item.id}
            bg={bgColor}
            borderWidth="1px"
            borderColor={borderColor}
            cursor="pointer"
            transition="all 0.2s"
            _hover={{
              bg: hoverBg,
              borderColor: 'brand.500',
              transform: 'translateY(-2px)',
              boxShadow: 'lg'
            }}
            onClick={() => handleNavigate(item.path)}
          >
            <CardBody p={{ base: 4, md: 6 }}>
              <Flex align="center" justify="space-between">
                <Flex align="center" gap={4}>
                  <Icon
                    as={item.icon}
                    boxSize={{ base: 6, md: 8 }}
                    color="brand.500"
                  />
                  <Box>
                    <Text
                      fontSize={{ base: 'md', md: 'lg' }}
                      fontWeight="600"
                      color={textColor}
                      mb={1}
                    >
                      {item.label}
                    </Text>
                    <Text fontSize="sm" color={textColorSecondary}>
                      {item.description}
                    </Text>
                  </Box>
                </Flex>
                <Icon as={FaChevronRight} color={textColorSecondary} />
              </Flex>
            </CardBody>
          </Card>
        ))}
      </VStack>
    </Box>
  );
}
