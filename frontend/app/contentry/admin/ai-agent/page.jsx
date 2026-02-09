'use client';
import { useTranslation } from 'react-i18next';

import { Box } from '@chakra-ui/react';
import AgentAnalyticsDashboard from '@/components/admin/AgentAnalyticsDashboard';

export default function AIAgentAdminPage() {
  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }} px={{ base: 4, md: 6 }}>
      <AgentAnalyticsDashboard />
    </Box>
  );
}
