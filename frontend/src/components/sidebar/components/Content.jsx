'use client';
// chakra imports
import {
  Box,
  Flex,
  Stack,
  useColorModeValue,
} from '@chakra-ui/react';
import APIModal from '@/components/apiModal';
import Links from '@/components/sidebar/components/Links';
import SidebarCard from '@/components/sidebar/components/SidebarCard';
import { useEffect, useState } from 'react';

// FUNCTIONS

function SidebarContent(props) {
  const { routes, setApiKey } = props;
  const [user, setUser] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);
  // SIDEBAR - Logo removed, now in AppHeader
  // Manus-style layout: Menu items from top, Credits/Settings at bottom
  return (
    <Flex
      direction="column"
      height="100%"
      pt="12px"
      pb="16px"
      borderRadius="30px"
      maxW="285px"
      px="16px"
      justify="space-between"
    >
      {/* Top Section - Navigation Links */}
      <Box flex="1" overflowY="auto">
        <Stack direction="column" spacing={0}>
          <Box ps="0px" pe={{ md: '0px', '2xl': '0px' }}>
            <Links routes={routes} />
          </Box>
        </Stack>
      </Box>

      {/* Bottom Section - Credits Card */}
      <Box width={'100%'} display={'flex'} flexDirection="column" alignItems="center" pt={4}>
        <SidebarCard />
        {/* API Key Modal removed - not needed for regular users */}
      </Box>
    </Flex>
  );
}

export default SidebarContent;
