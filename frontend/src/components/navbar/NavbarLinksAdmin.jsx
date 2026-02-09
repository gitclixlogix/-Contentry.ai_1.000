'use client';
// Chakra Imports
import {
  Avatar,
  Button,
  Flex,
  Icon,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
  useColorMode,
  useColorModeValue,
  Box,
} from '@chakra-ui/react';
import { useRouter } from 'next/navigation';
import { FaMoon, FaSun, FaSignOutAlt, FaCog, FaUser, FaGlobe } from 'react-icons/fa';
import { useEffect, useState } from 'react';
import LanguageSelector from '@/components/LanguageSelector';
import { getImageUrl } from '@/lib/api';
import NotificationBell from '@/components/notifications/NotificationBell';

export default function HeaderLinks(props) {
  const { secondary } = props;
  const { colorMode, toggleColorMode } = useColorMode();
  const router = useRouter();
  const [user, setUser] = useState(null);

  // Chakra Color Mode
  const navbarIcon = useColorModeValue('gray.500', 'gray.300');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    // Load user data initially
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }

    // Listen for storage changes (when Settings updates the profile picture)
    const handleStorageChange = (e) => {
      if (e.key === 'contentry_user' || e.key === null) {
        const updatedUser = localStorage.getItem('contentry_user');
        if (updatedUser) {
          setUser(JSON.parse(updatedUser));
        }
      }
    };

    // Listen for custom event when profile is updated
    const handleProfileUpdate = () => {
      const updatedUser = localStorage.getItem('contentry_user');
      if (updatedUser) {
        setUser(JSON.parse(updatedUser));
      }
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('profileUpdated', handleProfileUpdate);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('profileUpdated', handleProfileUpdate);
    };
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  const handleLogout = () => {
    localStorage.removeItem('contentry_user');
    router.push('/contentry/auth/login');
  };

  const getUserRole = () => {
    if (!user) return 'User';
    if (user.is_enterprise_admin) return 'Enterprise Admin';
    if (user.role === 'admin') return 'Administrator';
    return 'User';
  };

  return (
    <Flex
      w={{ sm: '100%', md: 'auto' }}
      alignItems="center"
      flexDirection="row"
      bg="transparent"
      flexWrap={secondary ? { base: 'wrap', md: 'nowrap' } : 'unset'}
      p="0px"
      gap="16px"
    >
      {/* Language Selector */}
      <Box display={{ base: 'none', md: 'flex' }} alignItems="center">
        <LanguageSelector />
      </Box>

      {/* Notifications Bell */}
      <NotificationBell />

      <Button
        variant="no-hover"
        bg="transparent"
        p="0px"
        minW="unset"
        minH="unset"
        h="22px"
        w="max-content"
        onClick={toggleColorMode}
      >
        <Icon
          h="20px"
          w="20px"
          color={navbarIcon}
          as={colorMode === 'light' ? FaMoon : FaSun}
        />
      </Button>

      {/* User Profile Menu with Dropdown */}
      <Menu>
        <MenuButton
          as={Button}
          variant="no-hover"
          bg="transparent"
          p="0px"
          minW="unset"
          h="auto"
          _hover={{ opacity: 0.8 }}
        >
          <Flex align="center" gap="10px">
            <Avatar
              size="sm"
              name={user?.full_name || 'User'}
              src={getImageUrl(user?.profile_picture)}
              cursor="pointer"
            />
            <Box display={{ base: 'none', md: 'block' }}>
              <Text fontSize="sm" fontWeight="600" color={textColor} lineHeight="1.2">
                {user?.full_name || 'User'}
              </Text>
              <Text fontSize="xs" color={textColorSecondary} lineHeight="1.2">
                {getUserRole()}
              </Text>
            </Box>
          </Flex>
        </MenuButton>
        <MenuList p="10px" borderRadius="10px" shadow="lg">
          <MenuItem 
            borderRadius="8px" 
            onClick={() => router.push('/contentry/settings')}
            icon={<Icon as={FaUser} color="gray.500" />}
          >
            <Text fontSize="sm">Profile Settings</Text>
          </MenuItem>
          <MenuItem 
            borderRadius="8px" 
            onClick={() => router.push('/contentry/settings/billing')}
            icon={<Icon as={FaCog} color="gray.500" />}
          >
            <Text fontSize="sm">Billing & Subscription</Text>
          </MenuItem>
          <MenuItem 
            borderRadius="8px" 
            onClick={handleLogout}
            icon={<Icon as={FaSignOutAlt} color="red.500" />}
            color="red.500"
          >
            <Text fontSize="sm" fontWeight="500">Sign Out</Text>
          </MenuItem>
        </MenuList>
      </Menu>

      {/* Logout Button - Always Visible as backup */}
      <Button
        variant="no-hover"
        bg="transparent"
        p="0px"
        minW="unset"
        minH="unset"
        h="22px"
        w="max-content"
        onClick={handleLogout}
        _hover={{ opacity: 0.7 }}
        title="Sign Out"
        display={{ base: 'flex', md: 'none' }}  // Only show on mobile as backup
      >
        <Icon
          h="20px"
          w="20px"
          color="red.500"
          as={FaSignOutAlt}
        />
      </Button>
    </Flex>
  );
}
