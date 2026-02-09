'use client';
import React, { useState } from 'react';

// chakra imports
import {
  Box,
  Flex,
  Drawer,
  DrawerBody,
  Icon,
  useColorModeValue,
  DrawerOverlay,
  useDisclosure,
  DrawerContent,
  DrawerCloseButton,
  IconButton,
  Tooltip,
} from '@chakra-ui/react';
import Content from '@/components/sidebar/components/Content';
import {
  renderThumb,
  renderTrack,
  renderView,
} from '@/components/scrollbar/Scrollbar';
import { Scrollbars } from 'react-custom-scrollbars-2';

// Updated to Lucide icons
import { Menu, ChevronLeft, ChevronRight } from 'lucide-react';
import { isWindowAvailable } from '@/utils/navigation';

function Sidebar(props) {
  const { routes, setApiKey, isCollapsed, onToggleCollapse } = props;
  // this is for the rest of the collapses
  let variantChange = '0.2s linear';
  let shadow = useColorModeValue(
    '14px 17px 40px 4px rgba(112, 144, 176, 0.08)',
    'unset',
  );
  // Chakra Color Mode
  let sidebarBg = useColorModeValue('white', 'navy.800');
  let sidebarRadius = '14px';
  let sidebarMargins = '0px';
  let toggleBg = useColorModeValue('white', 'navy.700');
  let toggleHoverBg = useColorModeValue('gray.100', 'navy.600');
  
  // Header height offset
  const headerHeight = '72px';
  
  // SIDEBAR
  return (
    <>
      {/* Toggle Button - Always visible, positioned fixed */}
      <Box display={{ base: 'none', xl: 'block' }}>
        <Tooltip label={isCollapsed ? 'Show Menu' : 'Hide Menu'} placement="right">
          <IconButton
            icon={isCollapsed ? <ChevronRight size={16} strokeWidth={2} /> : <ChevronLeft size={16} strokeWidth={2} />}
            onClick={onToggleCollapse}
            position="fixed"
            top={`calc(${headerHeight} + 50%)`}
            left={isCollapsed ? '10px' : '273px'}
            transform="translateY(-50%)"
            size="sm"
            borderRadius="full"
            bg={toggleBg}
            _hover={{ bg: toggleHoverBg }}
            boxShadow="md"
            zIndex={1001}
            transition="left 0.3s ease"
            aria-label={isCollapsed ? 'Show menu' : 'Hide menu'}
          />
        </Tooltip>
      </Box>

      {/* Sidebar Container - Now starts below the header */}
      <Box 
        display={{ base: 'none', xl: 'block' }} 
        position="fixed"
        top={headerHeight}
        left="0"
        minH={`calc(100vh - ${headerHeight})`}
        transition="all 0.3s ease"
        w={isCollapsed ? '0px' : '285px'}
        overflow="hidden"
        zIndex={1000}
      >
        <Box
          bg={sidebarBg}
          w="285px"
          ms={{
            sm: '16px',
          }}
          my={{
            sm: '16px',
          }}
          h={`calc(100vh - 72px - 32px)`}
          m={sidebarMargins}
          borderRadius={sidebarRadius}
          minH="100%"
          overflowX="hidden"
          boxShadow={shadow}
          transform={isCollapsed ? 'translateX(-300px)' : 'translateX(0)'}
          transition="transform 0.3s ease"
        >
          <Scrollbars
            autoHide
            renderTrackVertical={renderTrack}
            renderThumbVertical={renderThumb}
            renderView={renderView}
            universal={true}
          >
            <Content setApiKey={setApiKey} routes={routes} />
          </Scrollbars>
        </Box>
      </Box>
    </>
  );
}

// FUNCTIONS
export function SidebarResponsive(props) {
  let sidebarBackgroundColor = useColorModeValue('white', 'navy.800');
  let menuColor = useColorModeValue('gray.400', 'white');
  // // SIDEBAR
  const { isOpen, onOpen, onClose } = useDisclosure();

  const { routes } = props;
  return (
    <Flex display={{ sm: 'flex', xl: 'none' }} alignItems="center">
      <Flex w="max-content" h="max-content" onClick={onOpen}>
        <Icon
          as={Menu}
          color={menuColor}
          my="auto"
          w="20px"
          h="20px"
          me="10px"
          _hover={{ cursor: 'pointer' }}
        />
      </Flex>
      <Drawer
        isOpen={isOpen}
        onClose={onClose}
        placement={
          isWindowAvailable() && document.documentElement.dir === 'rtl'
            ? 'right'
            : 'left'
        }
      >
        <DrawerOverlay />
        <DrawerContent
          w="285px"
          maxW="285px"
          ms={{
            sm: '16px',
          }}
          my={{
            sm: '16px',
          }}
          borderRadius="16px"
          bg={sidebarBackgroundColor}
        >
          <DrawerCloseButton
            zIndex="3"
            onClick={onClose}
            _focus={{ boxShadow: 'none' }}
            _hover={{ boxShadow: 'none' }}
          />
          <DrawerBody maxW="285px" px="0rem" pb="0">
            <Scrollbars
              universal={true}
              autoHide
              renderTrackVertical={renderTrack}
              renderThumbVertical={renderThumb}
              renderView={renderView}
            >
              <Content routes={routes} />
            </Scrollbars>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Flex>
  );
}
// PROPS

export default Sidebar;
