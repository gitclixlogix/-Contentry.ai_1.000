'use client';

import React from 'react';
import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Button,
  HStack,
  VStack,
  Text,
  Icon,
  Box,
  useColorModeValue,
  Badge,
  Divider,
} from '@chakra-ui/react';
import { ChevronDown, User, Building2, Check } from 'lucide-react';
import { useWorkspace, WORKSPACE_TYPES } from '@/context/WorkspaceContext';

export default function WorkspaceSwitcher() {
  const {
    currentWorkspace,
    switchWorkspace,
    availableWorkspaces,
    hasEnterpriseAccess,
    isLoading,
  } = useWorkspace();

  // OKLCH-Based Blue Design System Colors
  const bgColor = useColorModeValue('white', 'rgba(23, 37, 84, 0.6)'); // Card with glassmorphism
  const borderColor = useColorModeValue('#e2e8f0', '#334155');
  const hoverBg = useColorModeValue('#f8fafc', 'rgba(255,255,255,0.05)');
  const activeBg = useColorModeValue('#eff6ff', 'rgba(59, 130, 246, 0.15)'); // Light blue tint
  const textColor = useColorModeValue('#172554', '#f0f9ff'); // Deep Navy / Off-White
  const secondaryText = useColorModeValue('#475569', '#94a3b8');
  const inactiveIconBg = useColorModeValue('#f1f5f9', '#334155');
  const loadingBg = useColorModeValue('#f1f5f9', '#1e293b');
  const brandPrimary = useColorModeValue('#1e40af', '#3b82f6'); // Royal Blue / Bright Blue
  const brandAccent = useColorModeValue('#0284c7', '#38bdf8'); // Electric Blue / Vibrant Blue

  // Get current workspace info
  const currentWorkspaceInfo = availableWorkspaces.find(
    (w) => w.id === currentWorkspace
  ) || availableWorkspaces[0];

  // Don't show switcher if user only has personal workspace
  if (!hasEnterpriseAccess) {
    return null;
  }

  if (isLoading) {
    return (
      <Box
        px={3}
        py={2}
        borderRadius="lg"
        bg={loadingBg}
        w="140px"
        h="36px"
      />
    );
  }

  return (
    <Menu placement="bottom-end">
      <MenuButton
        as={Button}
        variant="ghost"
        size="sm"
        rightIcon={<ChevronDown size={16} />}
        px={3}
        py={2}
        h="auto"
        borderRadius="lg"
        border="1px solid"
        borderColor={borderColor}
        bg={bgColor}
        _hover={{ bg: hoverBg, borderColor: brandPrimary }}
        _active={{ bg: activeBg }}
      >
        <HStack spacing={2}>
          <Icon
            as={currentWorkspace === WORKSPACE_TYPES.ENTERPRISE ? Building2 : User}
            boxSize={4}
            color={brandPrimary}
          />
          <Text
            fontSize="sm"
            fontWeight="500"
            color={textColor}
            maxW="120px"
            isTruncated
          >
            {currentWorkspaceInfo?.name || 'Workspace'}
          </Text>
        </HStack>
      </MenuButton>

      <MenuList
        bg={bgColor}
        borderColor={borderColor}
        shadow="lg"
        py={2}
        minW="260px"
        zIndex={2000}
        backdropFilter="blur(10px)"
      >
        <Box px={3} py={2}>
          <Text fontSize="xs" fontWeight="600" color={secondaryText} textTransform="uppercase" letterSpacing="wide">
            Switch Workspace
          </Text>
        </Box>
        <Divider my={1} borderColor={borderColor} />

        {availableWorkspaces.map((workspace) => {
          const isActive = workspace.id === currentWorkspace;
          const IconComponent = workspace.id === WORKSPACE_TYPES.ENTERPRISE ? Building2 : User;

          return (
            <MenuItem
              key={workspace.id}
              onClick={() => switchWorkspace(workspace.id)}
              bg={isActive ? activeBg : 'transparent'}
              _hover={{ bg: isActive ? activeBg : hoverBg }}
              py={3}
              px={3}
            >
              <HStack spacing={3} w="full" justify="space-between">
                <HStack spacing={3}>
                  <Box
                    p={2}
                    borderRadius="md"
                    bg={isActive ? brandPrimary : inactiveIconBg}
                  >
                    <Icon
                      as={IconComponent}
                      boxSize={4}
                      color={isActive ? 'white' : secondaryText}
                    />
                  </Box>
                  <VStack align="start" spacing={0}>
                    <HStack spacing={2}>
                      <Text fontSize="sm" fontWeight="500" color={textColor}>
                        {workspace.name}
                      </Text>
                      {workspace.role && (
                        <Badge
                          size="sm"
                          bg={activeBg}
                          color={brandPrimary}
                          fontSize="10px"
                          textTransform="capitalize"
                          fontWeight="600"
                        >
                          {workspace.role.replace('enterprise_', '')}
                        </Badge>
                      )}
                    </HStack>
                    <Text fontSize="xs" color={secondaryText}>
                      {workspace.description}
                    </Text>
                  </VStack>
                </HStack>

                {isActive && (
                  <Icon as={Check} boxSize={4} color={brandPrimary} />
                )}
              </HStack>
            </MenuItem>
          );
        })}
      </MenuList>
    </Menu>
  );
}
