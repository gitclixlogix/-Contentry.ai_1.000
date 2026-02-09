'use client';
import { Box, Portal, useDisclosure, Flex } from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';
import Sidebar, { SidebarResponsive } from '@/components/sidebar/Sidebar';
import AppHeader from '@/components/header/AppHeader';
import { SidebarContext } from '@/contexts/SidebarContext';
import { usePathname } from 'next/navigation';
import { useEffect, useState, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import { WorkspaceProvider, useWorkspace, WORKSPACE_TYPES } from '@/context/WorkspaceContext';
import OnboardingGuard from '@/components/onboarding/OnboardingGuard';
import Script from 'next/script';
// Updated to Lucide icons for modern outline style
import { 
  Home, 
  CheckCircle, 
  Bell, 
  CreditCard, 
  Settings, 
  BarChart3, 
  Sparkles, 
  BookOpen, 
  Building2, 
  Users, 
  UserCircle, 
  Clock, 
  Search, 
  Calendar, 
  FileText, 
  HelpCircle,
  FolderKanban,
  MessageCircle
} from 'lucide-react';

// Inner layout component that uses workspace context
function ContentryLayoutInner({ children }) {
  const { t, i18n } = useTranslation();
  const pathname = usePathname();
  const { onOpen } = useDisclosure();
  const { user } = useAuth();
  const { currentWorkspace, isEnterpriseWorkspace, hasEnterpriseAccess } = useWorkspace();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('contentry_sidebar_collapsed') === 'true';
    }
    return false;
  });
  
  // Force re-render when language changes
  const [, forceUpdate] = useState(0);
  
  useEffect(() => {
    const handleLanguageChange = () => {
      forceUpdate(n => n + 1);
    };
    
    window.addEventListener('languageChanged', handleLanguageChange);
    // Also listen for i18n language change events
    i18n.on('languageChanged', handleLanguageChange);
    
    return () => {
      window.removeEventListener('languageChanged', handleLanguageChange);
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, [i18n]);

  const toggleSidebarCollapse = () => {
    const newState = !isSidebarCollapsed;
    setIsSidebarCollapsed(newState);
    localStorage.setItem('contentry_sidebar_collapsed', String(newState));
  };

  // =================================================================
  // UNIFIED NAVIGATION - Routes are now workspace-context-aware
  // All users see the same core navigation, with enterprise features
  // appearing based on workspace context and access level
  // =================================================================
  // Check if user is an admin (company admin) or super_admin (platform admin)
  // For enterprise users, enterprise_role of 'admin' or 'enterprise_admin' also grants admin access
  const isAdmin = user?.role === 'admin' || 
                  user?.role === 'super_admin' || 
                  user?.enterprise_role === 'admin' || 
                  user?.enterprise_role === 'enterprise_admin' ||
                  user?.is_enterprise_admin === true;
  // Check if user is a platform super-admin (manages entire platform)
  const isPlatformAdmin = user?.role === 'super_admin' || (user?.role === 'admin' && user?.is_platform_admin === true);
  
  const routes = useMemo(() => {

    // ============================================================
    // UNIFIED ROUTES - Workspace and Role aware
    // ============================================================
    const unifiedRoutes = [];

    // ============================================================
    // CONTENT INTELLIGENCE - Available to all users in all workspaces
    // ============================================================
    unifiedRoutes.push({
      name: t('navigation.contentIntelligence'),
      layout: '/contentry',
      path: '/content-moderation',
      icon: <Sparkles size={18} strokeWidth={1.75} />,
      collapse: true,
      defaultOpen: true,
      items: [
        {
          name: t('navigation.analyzeContent'),
          layout: '/contentry',
          path: '/content-moderation?tab=analyze',
          icon: <Search size={18} strokeWidth={1.75} />,
        },
        {
          name: t('navigation.contentGeneration'),
          layout: '/contentry',
          path: '/content-moderation?tab=generate',
          icon: <Sparkles size={18} strokeWidth={1.75} />,
        },
        {
          name: t('navigation.scheduled'),
          layout: '/contentry',
          path: '/content-moderation?tab=scheduled',
          icon: <Calendar size={18} strokeWidth={1.75} />,
        },
        {
          name: t('navigation.allPosts'),
          layout: '/contentry',
          path: '/content-moderation?tab=posts',
          icon: <FileText size={18} strokeWidth={1.75} />,
        },
        {
          name: t('navigation.projects', 'Projects'),
          layout: '/contentry',
          path: '/projects',
          icon: <FolderKanban size={18} strokeWidth={1.75} />,
        },
      ],
    });

    // ============================================================
    // DASHBOARDS & ANALYTICS
    // ============================================================
    const dashboardItems = [
      // Dashboard item - name changes based on workspace
      {
        name: isEnterpriseWorkspace 
          ? t('navigation.companyDashboard', 'Company Dashboard') 
          : t('navigation.myDashboard'),
        layout: '/contentry',
        path: isEnterpriseWorkspace ? '/enterprise/dashboard' : '/dashboard',
      },
    ];

    // Admin-only analytics items
    if (isAdmin) {
      dashboardItems.push(
        {
          name: t('navigation.analyticsOverview', 'Analytics Overview'),
          layout: '/contentry',
          path: '/admin',
        },
        {
          name: t('navigation.advancedAnalytics', 'Advanced Analytics'),
          layout: '/contentry',
          path: '/analytics',
        }
      );
      
      // Enterprise Analytics - Only in Company Workspace
      if (isEnterpriseWorkspace && hasEnterpriseAccess) {
        dashboardItems.push({
          name: t('navigation.enterpriseAnalytics', 'Enterprise Analytics'),
          layout: '/contentry',
          path: '/enterprise/candidate-analysis',
        });
      }
    }

    unifiedRoutes.push({
      name: t('navigation.dashboardsAnalytics', 'Dashboards & Analytics'),
      layout: '/contentry',
      path: isEnterpriseWorkspace ? '/enterprise/dashboard' : '/dashboard',
      icon: <BarChart3 size={18} strokeWidth={1.75} />,
      collapse: true,
      items: dashboardItems,
    });

    // ============================================================
    // SENTIMENT ANALYSIS - Top-level menu item for Enterprise Admins
    // ============================================================
    if (isEnterpriseWorkspace && hasEnterpriseAccess && isAdmin) {
      unifiedRoutes.push({
        name: t('navigation.sentimentAnalysis', 'Sentiment Analysis'),
        layout: '/contentry',
        path: '/enterprise/sentiment-analysis',
        icon: <MessageCircle size={18} strokeWidth={1.75} />,
      });
    }

    // ============================================================
    // NOTIFICATIONS - Available to all users
    // ============================================================
    unifiedRoutes.push({
      name: t('navigation.notifications'),
      layout: '/contentry',
      path: '/notifications',
      icon: <Bell size={18} strokeWidth={1.75} />,
    });

    // ============================================================
    // COMPANY SETTINGS - Only visible in Enterprise Workspace AND only for Admins
    // ============================================================
    if (isEnterpriseWorkspace && hasEnterpriseAccess && isAdmin) {
      unifiedRoutes.push({
        name: 'separator',
        separator: true,
      });

      unifiedRoutes.push({
        name: t('navigation.companySettings', 'Company Settings'),
        layout: '/contentry',
        path: '/enterprise/settings/company',
        icon: <Building2 size={18} strokeWidth={1.75} />,
        collapse: true,
        items: [
          {
            name: t('navigation.companyProfile', 'Company Profile'),
            layout: '/contentry',
            path: '/enterprise/settings/company',
          },
          {
            name: t('navigation.companyKnowledge', 'Company Knowledge'),
            layout: '/contentry',
            path: '/enterprise/settings/knowledge',
          },
          {
            name: t('navigation.strategicProfiles', 'Strategic Profiles'),
            layout: '/contentry',
            path: '/enterprise/settings/social',
          },
          {
            name: t('navigation.teamManagement', 'Team Management'),
            layout: '/contentry',
            path: '/enterprise/settings/team',
          },
          {
            name: t('navigation.billingUsage', 'Billing & Usage'),
            layout: '/contentry',
            path: '/enterprise/settings/billing',
          },
        ],
      });
    }

    // ============================================================
    // PERSONAL SETTINGS - Only visible in Personal Workspace
    // ============================================================
    if (!isEnterpriseWorkspace) {
      unifiedRoutes.push({
        name: t('navigation.settings'),
        layout: '/contentry',
        path: '/settings',
        icon: <Settings size={18} strokeWidth={1.75} />,
        collapse: true,
        items: [
          {
            name: t('navigation.profile'),
            layout: '/contentry',
            path: '/settings',
          },
          {
            name: t('navigation.socialAccounts'),
            layout: '/contentry',
            path: '/settings/social',
          },
          {
            name: t('navigation.knowledgeBase', 'Knowledge Base'),
            layout: '/contentry',
            path: '/settings/knowledge',
          },
          {
            name: t('navigation.history'),
            layout: '/contentry',
            path: '/settings/history',
          },
          {
            name: t('navigation.usageCredits'),
            layout: '/contentry',
            path: '/settings/usage',
          },
          {
            name: t('navigation.billingInvoicing'),
            layout: '/contentry',
            path: '/settings/billing',
          },
        ],
      });
    }

    // ============================================================
    // HELP & DOCUMENTATION - Always available
    // ============================================================
    unifiedRoutes.push({
      name: t('navigation.helpDocumentation'),
      layout: '/contentry',
      path: '/documentation',
      icon: <HelpCircle size={18} strokeWidth={1.75} />,
    });

    // ============================================================
    // PLATFORM ADMINISTRATION - Only for super_admin
    // ============================================================
    if (isPlatformAdmin) {
      unifiedRoutes.push({
        name: 'separator',
        separator: true,
      });

      unifiedRoutes.push({
        name: t('navigation.administration', 'Administration'),
        layout: '/contentry',
        path: '/admin/users',
        icon: <Settings size={18} strokeWidth={1.75} />,
        collapse: true,
        items: [
          {
            name: t('navigation.allPlatformUsers', 'All Platform Users'),
            layout: '/contentry',
            path: '/admin/users',
          },
          {
            name: t('navigation.documentation', 'Documentation Admin'),
            layout: '/contentry',
            path: '/admin/documentation',
          },
        ],
      });
    }

    return unifiedRoutes;
  }, [user?.role, isAdmin, isPlatformAdmin, currentWorkspace, isEnterpriseWorkspace, hasEnterpriseAccess, t, i18n.language]);

  // Don't show sidebar on auth pages, terms, or privacy pages (public legal pages)
  const isPublicPage = pathname?.includes('/auth/') || 
                       pathname?.includes('/terms') || 
                       pathname?.includes('/privacy');
  
  if (isPublicPage) {
    return <>{children}</>;
  }

  // Force sidebar to re-render when language changes
  const sidebarKey = `sidebar-${i18n.language}`;

  return (
    <Box>
      <SidebarContext.Provider value={{ toggleSidebar: onOpen, isSidebarCollapsed, toggleSidebarCollapse }}>
        {/* Fixed Full-Width App Header with Workspace Switcher */}
        <AppHeader 
          routes={routes} 
          user={user}
        />
        
        {/* Sidebar - Below Header - Key forces re-render on language change */}
        <Sidebar key={sidebarKey} routes={routes} isCollapsed={isSidebarCollapsed} onToggleCollapse={toggleSidebarCollapse} />
        
        <Box
          float="right"
          minHeight="100vh"
          height="100%"
          overflow="auto"
          position="relative"
          maxHeight="100%"
          w={{ base: '100%', xl: isSidebarCollapsed ? '100%' : 'calc( 100% - 290px )' }}
          maxWidth={{ base: '100%', xl: isSidebarCollapsed ? '100%' : 'calc( 100% - 290px )' }}
          transition="all 0.33s cubic-bezier(0.685, 0.0473, 0.346, 1)"
          transitionDuration=".2s, .2s, .35s"
          transitionProperty="top, bottom, width"
          transitionTimingFunction="linear, linear, ease"
        >
          {/* Main Content Area - with top padding for fixed header */}
          <Box mx="auto" p={{ base: '20px', md: '30px' }} pe="20px" minH="100vh" pt={{ base: '90px', md: '100px' }}>
            {children}
          </Box>
        </Box>
      </SidebarContext.Provider>
    </Box>
  );
}

// Main layout component that wraps with providers
export default function ContentryLayout({ children }) {
  return (
    <OnboardingGuard>
      <WorkspaceProvider>
        <ContentryLayoutInner>
          {children}
        </ContentryLayoutInner>
        {/* ElevenLabs Voice Widget - Floating widget */}
        <Script
          src="https://unpkg.com/@elevenlabs/convai-widget-embed"
          strategy="afterInteractive"
        />
        <Box 
          id="elevenlabs-floating-widget"
          position="fixed" 
          bottom="20px" 
          right="20px" 
          zIndex="999"
        >
          <elevenlabs-convai agent-id="agent_2101k2bjmvmnee9r91bsv9cnh9gg" />
        </Box>
      </WorkspaceProvider>
    </OnboardingGuard>
  );
}