'use client';
import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import dynamic from 'next/dynamic';
import {
  Box,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Icon,
  Badge,
  Flex,
  Button,
  Spinner,
  Center,
} from '@chakra-ui/react';
import { Search, Sparkles, FileText, Calendar } from 'lucide-react';
import useLanguage from '@/hooks/useLanguage';

// Loading fallback component
const TabLoadingFallback = () => (
  <Center py={10}>
    <Spinner size="lg" color="brand.500" thickness="3px" />
  </Center>
);

// Page loading fallback
const PageLoadingFallback = () => (
  <Center py={20}>
    <Spinner size="xl" color="brand.500" thickness="4px" />
  </Center>
);

// Dynamic imports for heavy tab components - loaded on demand
const AnalyzeContentTab = dynamic(() => import('./analyze/AnalyzeContentTab'), {
  loading: () => <TabLoadingFallback />,
  ssr: false,
});

const ContentGenerationTab = dynamic(() => import('./ContentGenerationTab'), {
  loading: () => <TabLoadingFallback />,
  ssr: false,
});

const AllPostsTab = dynamic(() => import('./posts/AllPostsTab'), {
  loading: () => <TabLoadingFallback />,
  ssr: false,
});

const ScheduledPostsTab = dynamic(() => import('./scheduled/ScheduledPostsTab'), {
  loading: () => <TabLoadingFallback />,
  ssr: false,
});

// Main content component that uses searchParams
function ContentModerationContent() {
  const { t } = useTranslation();
  const router = useRouter();
  const searchParams = useSearchParams();
  const language = useLanguage();
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [postCounts, setPostCounts] = useState({ all: 0, scheduled: 0 });
  const [analyzeContent, setAnalyzeContent] = useState(''); // Content to analyze from scheduled post

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const loadUserData = () => {
      const savedUser = localStorage.getItem('contentry_user');
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      }
    };
    loadUserData();
    
    // Check for tab parameter in URL - setting state based on URL params is a valid pattern
    const tab = searchParams.get('tab');
    if (tab === 'generate') setActiveTab(1);
    else if (tab === 'scheduled') setActiveTab(2);
    else if (tab === 'posts') setActiveTab(3);
    else setActiveTab(0);
  }, [searchParams]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const handleTabChange = (index) => {
    setActiveTab(index);
    // Update URL without page reload
    const tabs = ['analyze', 'generate', 'scheduled', 'posts'];
    router.push(`/contentry/content-moderation?tab=${tabs[index]}`, { scroll: false });
  };

  const updatePostCounts = (counts) => {
    setPostCounts(counts);
  };

  // Handle opening scheduled post in analyze tab
  const handleOpenInAnalyze = (content) => {
    setAnalyzeContent(content);
    setActiveTab(0); // Switch to Analyze Content tab
    router.push(`/contentry/content-moderation?tab=analyze`, { scroll: false });
  };

  return (
    <Box px={{ base: 2, md: 4 }} pt={{ base: '10px', md: '10px' }}>
      <Flex justify="flex-end" align="center" mb={{ base: 4, md: 6 }} flexWrap="wrap" gap={3}>
        <Button
          leftIcon={<Icon as={FileText} />}
          colorScheme="green"
          size="sm"
          onClick={() => {
            if (user?.id) {
              window.open(`/contentry/report?user_id=${user.id}`, '_blank');
            } else {
              window.open('/contentry/report', '_blank');
            }
          }}
        >
          {t('contentModeration.viewReport')}
        </Button>
      </Flex>

      <Tabs 
        index={activeTab} 
        onChange={handleTabChange} 
        variant="enclosed" 
        colorScheme="brand" 
        isLazy
      >
        <TabList flexWrap="wrap" gap={1}>
          <Tab fontSize={{ base: 'xs', md: 'sm' }}>
            <Icon as={Search} mr={2} />
            {t('contentModeration.analyzeContent')}
          </Tab>
          <Tab fontSize={{ base: 'xs', md: 'sm' }}>
            <Icon as={Sparkles} mr={2} />
            {t('navigation.contentGeneration')}
          </Tab>
          <Tab fontSize={{ base: 'xs', md: 'sm' }}>
            <Icon as={Calendar} mr={2} />
            {t('contentModeration.scheduled')}
            {postCounts.scheduled > 0 && (
              <Badge ml={2} colorScheme="blue" fontSize="xs">{postCounts.scheduled}</Badge>
            )}
          </Tab>
          <Tab fontSize={{ base: 'xs', md: 'sm' }}>
            <Icon as={FileText} mr={2} />
            {t('contentModeration.allPosts')}
            {postCounts.all > 0 && (
              <Badge ml={2} colorScheme="blue" fontSize="xs">{postCounts.all}</Badge>
            )}
          </Tab>
        </TabList>

        <TabPanels>
          <TabPanel px={0}>
            {user && <AnalyzeContentTab user={user} language={language} setActiveTab={setActiveTab} initialContent={analyzeContent} />}
          </TabPanel>
          <TabPanel px={0}>
            {user && <ContentGenerationTab user={user} language={language} setActiveTab={setActiveTab} />}
          </TabPanel>
          <TabPanel px={0}>
            {user && <ScheduledPostsTab user={user} updatePostCounts={updatePostCounts} onOpenInAnalyze={handleOpenInAnalyze} />}
          </TabPanel>
          <TabPanel px={0}>
            {user && <AllPostsTab user={user} updatePostCounts={updatePostCounts} />}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
}

// Export default with Suspense wrapper for useSearchParams
export default function ContentModeration() {
  return (
    <Suspense fallback={<PageLoadingFallback />}>
      <ContentModerationContent />
    </Suspense>
  );
}
