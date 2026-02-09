'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from './AuthContext';

// Workspace types
export const WORKSPACE_TYPES = {
  PERSONAL: 'personal',
  ENTERPRISE: 'enterprise',
};

// Pages that are only accessible in specific workspaces
const ENTERPRISE_ONLY_PAGES = [
  '/contentry/enterprise',
  '/contentry/enterprise/settings',
  '/contentry/enterprise/dashboard',
];

const PERSONAL_ONLY_PAGES = [
  '/contentry/settings',
  '/contentry/settings/social',
  '/contentry/settings/history',
  '/contentry/settings/usage',
  '/contentry/settings/billing',
];

// Default pages for each workspace
const DEFAULT_PAGES = {
  [WORKSPACE_TYPES.PERSONAL]: '/contentry/dashboard',
  [WORKSPACE_TYPES.ENTERPRISE]: '/contentry/content-moderation',
};

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  const { user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [currentWorkspace, setCurrentWorkspace] = useState(WORKSPACE_TYPES.PERSONAL);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user has access to enterprise/company workspace
  // This includes Enterprise, Team, and Business subscription plans
  const hasEnterpriseAccess = useCallback(() => {
    if (!user) return false;
    
    // Check if user has enterprise/company association
    const hasCompanyAssociation = !!(
      user.enterprise_id ||
      user.enterprise_role === 'enterprise_admin' ||
      user.enterprise_role === 'admin' ||
      user.enterprise_role === 'manager' ||
      user.enterprise_role === 'creator' ||
      user.enterprise_role === 'reviewer' ||
      user.enterprise_role === 'enterprise_member' ||
      user.is_enterprise_admin === true
    );
    
    // Also check if user has Team, Business, or Enterprise subscription
    // These plans include team/company workspace features
    const subscriptionPlan = user.subscription_plan || user.plan_tier || '';
    const hasTeamPlan = ['team', 'business', 'enterprise'].includes(subscriptionPlan.toLowerCase());
    
    return hasCompanyAssociation || hasTeamPlan;
  }, [user]);

  // Get enterprise/company info
  const getEnterpriseInfo = useCallback(() => {
    if (!user || !hasEnterpriseAccess()) return null;
    
    // For Team/Business users without explicit enterprise_id, 
    // create a virtual "company" based on their account
    const subscriptionPlan = user.subscription_plan || user.plan_tier || '';
    const planName = subscriptionPlan.charAt(0).toUpperCase() + subscriptionPlan.slice(1);
    
    return {
      id: user.enterprise_id || `${user.id}-workspace`,
      name: user.enterprise_name || user.company_name || `${planName} Workspace`,
      role: user.enterprise_role || (user.is_enterprise_admin ? 'admin' : 'member'),
    };
  }, [user, hasEnterpriseAccess]);

  // Check if current page is accessible in the given workspace
  const isPageAccessibleInWorkspace = useCallback((page, workspace) => {
    if (workspace === WORKSPACE_TYPES.ENTERPRISE) {
      // In enterprise workspace, personal-only pages are not accessible
      return !PERSONAL_ONLY_PAGES.some(p => page.startsWith(p));
    } else {
      // In personal workspace, enterprise-only pages are not accessible
      return !ENTERPRISE_ONLY_PAGES.some(p => page.startsWith(p));
    }
  }, []);

  // Load saved workspace preference
  useEffect(() => {
    if (!user) {
      setIsLoading(false);
      return;
    }

    const savedWorkspace = localStorage.getItem(`contentry_workspace_${user.id}`);
    
    if (savedWorkspace && savedWorkspace === WORKSPACE_TYPES.ENTERPRISE && hasEnterpriseAccess()) {
      setCurrentWorkspace(WORKSPACE_TYPES.ENTERPRISE);
    } else if (hasEnterpriseAccess() && !savedWorkspace) {
      // Default to enterprise for first-time enterprise users
      setCurrentWorkspace(WORKSPACE_TYPES.ENTERPRISE);
      localStorage.setItem(`contentry_workspace_${user.id}`, WORKSPACE_TYPES.ENTERPRISE);
    } else {
      setCurrentWorkspace(WORKSPACE_TYPES.PERSONAL);
    }
    
    setIsLoading(false);
  }, [user, hasEnterpriseAccess]);

  // Switch workspace with automatic navigation
  const switchWorkspace = useCallback((workspace) => {
    if (workspace === WORKSPACE_TYPES.ENTERPRISE && !hasEnterpriseAccess()) {
      console.warn('User does not have enterprise access');
      return;
    }

    // Don't do anything if switching to the same workspace
    if (workspace === currentWorkspace) {
      return;
    }

    setCurrentWorkspace(workspace);
    if (user?.id) {
      localStorage.setItem(`contentry_workspace_${user.id}`, workspace);
    }

    // Always navigate to default page when switching workspaces
    const defaultPage = DEFAULT_PAGES[workspace];
    if (pathname !== defaultPage) {
      router.push(defaultPage);
    }
  }, [user, hasEnterpriseAccess, currentWorkspace, pathname, router]);

  // Available workspaces for the user
  const availableWorkspaces = useCallback(() => {
    const workspaces = [
      {
        id: WORKSPACE_TYPES.PERSONAL,
        name: 'Personal Workspace',
        icon: 'user',
        description: 'Your personal content and settings',
      },
    ];

    if (hasEnterpriseAccess()) {
      const enterprise = getEnterpriseInfo();
      workspaces.push({
        id: WORKSPACE_TYPES.ENTERPRISE,
        name: enterprise?.name || 'Company Workspace',
        icon: 'building',
        description: 'Team content and enterprise settings',
        role: enterprise?.role,
      });
    }

    return workspaces;
  }, [hasEnterpriseAccess, getEnterpriseInfo]);

  // Check if currently in enterprise workspace
  const isEnterpriseWorkspace = currentWorkspace === WORKSPACE_TYPES.ENTERPRISE;
  const isPersonalWorkspace = currentWorkspace === WORKSPACE_TYPES.PERSONAL;

  const value = {
    currentWorkspace,
    switchWorkspace,
    isEnterpriseWorkspace,
    isPersonalWorkspace,
    hasEnterpriseAccess: hasEnterpriseAccess(),
    availableWorkspaces: availableWorkspaces(),
    enterpriseInfo: getEnterpriseInfo(),
    isLoading,
    isPageAccessibleInWorkspace,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}

export default WorkspaceContext;
