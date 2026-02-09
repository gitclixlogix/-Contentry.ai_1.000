'use client';
import { useTranslation } from 'react-i18next';
import { FaUser } from 'react-icons/fa';
import DocumentationLayout, {
  DocSection,
  DocSubsection,
  DocParagraph,
  DocFeatureList,
  DocTip,
  DocImage,
  DocScreenshot,
} from '../DocumentationLayout';

export default function UserGuide() {
  const { t } = useTranslation();

  const sections = [
    { id: 'getting-started', title: t('documentation.user.sections.gettingStarted') },
    { id: 'browser-extension', title: 'Browser Extension' },
    { id: 'email-addins', title: 'Email Add-ins' },
    { id: 'content-creation', title: t('documentation.user.sections.contentCreation') },
    { id: 'analyze-content', title: t('documentation.user.sections.analyzeContent') },
    { id: 'voice-assistant', title: 'Voice Assistant (Olivia AI)' },
    { id: 'content-refinement', title: 'Content Refinement Chat' },
    { id: 'strategic-profiles', title: t('documentation.user.sections.strategicProfiles') },
    { id: 'social-accounts', title: t('documentation.user.sections.socialAccounts') },
    { id: 'approval-process', title: t('documentation.user.sections.approvalProcess') },
  ];

  return (
    <DocumentationLayout
      title={t('documentation.userGuide.title')}
      description={t('documentation.userGuide.description')}
      icon={FaUser}
      iconColor="green"
      sections={sections}
    >
      {/* Getting Started */}
      <DocSection id="getting-started" title={t('documentation.user.sections.gettingStarted')}>
        <DocParagraph>
          {t('documentation.user.gettingStarted.intro')}
        </DocParagraph>
        
        <DocScreenshot pageId="login" caption="The login page with multiple authentication options" />
        
        <DocSubsection title={t('documentation.user.gettingStarted.firstStepsTitle')}>
          <DocParagraph>
            {t('documentation.user.gettingStarted.firstStepsDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.user.gettingStarted.step1'),
              t('documentation.user.gettingStarted.step2'),
              t('documentation.user.gettingStarted.step3'),
              t('documentation.user.gettingStarted.step4'),
            ]}
          />
        </DocSubsection>
        
        <DocScreenshot pageId="dashboard" caption="Your personal dashboard with content metrics and activity overview" />

        <DocTip type="tip">
          {t('documentation.user.gettingStarted.tip')}
        </DocTip>
      </DocSection>

      {/* Browser Extension */}
      <DocSection id="browser-extension" title="Browser Extension">
        <DocParagraph>
          The Contentry.ai Browser Extension brings real-time content analysis directly to your browser. 
          Analyze content on any website - LinkedIn, Twitter, email, CMS platforms - without leaving your current workflow.
        </DocParagraph>

        <DocSubsection title="Installation">
          <DocParagraph>
            Install the extension for Chrome or Edge:
          </DocParagraph>
          <DocFeatureList
            items={[
              'Open Chrome Web Store or Edge Add-ons',
              'Search for "Contentry.ai"',
              'Click "Add to Chrome" or "Get" for Edge',
              'The Contentry.ai icon will appear in your toolbar',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="How to Activate">
          <DocParagraph>
            There are two ways to activate the extension:
          </DocParagraph>
          <DocFeatureList
            items={[
              'Method 1: Click the Contentry.ai icon in your browser toolbar → Click "Open Analysis Panel" to open the side panel',
              'Method 2: Right-click the toolbar icon → Select "Open side panel" from the context menu',
            ]}
          />
          <DocTip type="tip">
            The side panel stays open while you type, providing continuous real-time analysis without interrupting your workflow.
          </DocTip>
        </DocSubsection>

        <DocSubsection title="Using the Extension">
          <DocParagraph>
            Once the side panel is open:
          </DocParagraph>
          <DocFeatureList
            items={[
              '1. Sign in with your Contentry.ai account (first time only)',
              '2. Select your Strategic Profile (Brand Brain) from the dropdown',
              '3. Start typing in any text field on the webpage',
              '4. See real-time 3-Pillar Scores: Compliance, Cultural Sensitivity, and Accuracy',
              '5. Review recommendations and fix any flagged issues',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Supported Platforms">
          <DocParagraph>
            The extension works on any website with text fields:
          </DocParagraph>
          <DocFeatureList
            items={[
              'LinkedIn - Post composer, comments, messages',
              'Twitter/X - Tweet composer, replies, DMs',
              'Gmail & Outlook - Email composition',
              'WordPress, Medium, and other CMS platforms',
              'Any website with text areas or rich text editors',
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          The extension automatically detects when you&apos;re typing and analyzes content with a 1.5-second delay to avoid excessive API calls while providing real-time feedback.
        </DocTip>
      </DocSection>

      {/* Email Add-ins */}
      <DocSection id="email-addins" title="Email Add-ins">
        <DocParagraph>
          Contentry.ai Email Add-ins bring real-time content analysis directly into Gmail and Outlook. 
          Analyze your emails for compliance, cultural sensitivity, and accuracy while you compose - no copy-pasting required.
        </DocParagraph>

        <DocSubsection title="Gmail Add-on">
          <DocParagraph>
            Install the Contentry.ai add-on from the Google Workspace Marketplace:
          </DocParagraph>
          <DocFeatureList
            items={[
              'Open Google Workspace Marketplace',
              'Search for "Contentry.ai"',
              'Click "Install" and grant permissions',
              'The add-on appears in your Gmail sidebar when composing'
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Outlook Add-in">
          <DocParagraph>
            Install the Contentry.ai add-in from Microsoft AppSource:
          </DocParagraph>
          <DocFeatureList
            items={[
              'Open Outlook (web or desktop)',
              'Go to "Get Add-ins" in the ribbon',
              'Search for "Contentry.ai"',
              'Click "Add" to install',
              'Click "Analyze Email" in the ribbon when composing'
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Using Email Add-ins">
          <DocParagraph>
            Both add-ins work the same way:
          </DocParagraph>
          <DocFeatureList
            items={[
              '1. Sign in with your Contentry.ai credentials',
              '2. Select a Strategic Profile from the dropdown',
              '3. Compose your email (subject line + body are analyzed together)',
              '4. View real-time 3-Pillar Scores in the side panel',
              '5. Review and fix any flagged issues before sending'
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          All email analyses are automatically logged to your Contentry.ai dashboard, so you can track your content quality over time.
        </DocTip>
      </DocSection>

      {/* Content Creation */}
      <DocSection id="content-creation" title={t('documentation.user.sections.contentCreation')}>
        <DocParagraph>
          {t('documentation.user.contentCreation.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.user.contentCreation.generateTitle')}>
          <DocParagraph>
            {t('documentation.user.contentCreation.generateDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="content-generate" caption="Content Generation interface with platform and tone options" />
          
          <DocFeatureList
            items={[
              t('documentation.user.contentCreation.feature1'),
              t('documentation.user.contentCreation.feature2'),
              t('documentation.user.contentCreation.feature3'),
              t('documentation.user.contentCreation.feature4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.user.contentCreation.schedulingTitle')}>
          <DocParagraph>
            {t('documentation.user.contentCreation.schedulingDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="scheduled-posts" caption="Scheduled posts and content approval queue" />
          
          <DocFeatureList
            items={[
              t('documentation.user.contentCreation.schedule1'),
              t('documentation.user.contentCreation.schedule2'),
              t('documentation.user.contentCreation.schedule3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          {t('documentation.user.contentCreation.tip')}
        </DocTip>
      </DocSection>

      {/* Analyze Content */}
      <DocSection id="analyze-content" title={t('documentation.user.sections.analyzeContent')}>
        <DocParagraph>
          {t('documentation.user.analyzeContent.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.user.analyzeContent.howToTitle')}>
          <DocParagraph>
            {t('documentation.user.analyzeContent.howToDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="content-analyze" caption="Analyze Content interface for compliance checking" />
          
          <DocFeatureList
            items={[
              t('documentation.user.analyzeContent.step1'),
              t('documentation.user.analyzeContent.step2'),
              t('documentation.user.analyzeContent.step3'),
              t('documentation.user.analyzeContent.step4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.user.analyzeContent.analysisTypesTitle')}>
          <DocFeatureList
            items={[
              t('documentation.user.analyzeContent.type1'),
              t('documentation.user.analyzeContent.type2'),
              t('documentation.user.analyzeContent.type3'),
              t('documentation.user.analyzeContent.type4'),
            ]}
          />
        </DocSubsection>

        {/* Platform-Aware Content Engine - New Feature */}
        <DocSubsection title="Platform-Aware Content Engine">
          <DocParagraph>
            Optimize your content for specific social media platforms with intelligent character limits and platform-specific analysis.
          </DocParagraph>
          
          <DocFeatureList
            items={[
              'Select target platforms (X/Twitter, LinkedIn, Instagram, Facebook, TikTok, etc.)',
              'Real-time character counter shows your progress against platform limits',
              'Platform-specific AI analysis adapts to each platform&apos;s culture and best practices',
              'Strictest character limit is automatically enforced when multiple platforms are selected',
            ]}
          />
          
          <DocTip type="info">
            When you select X (Twitter), the AI will prioritize brevity and strong hooks. For LinkedIn, it focuses on professional tone and value-driven insights.
          </DocTip>
          
          <DocParagraph fontWeight="600">Character Limits by Platform:</DocParagraph>
          <DocFeatureList
            items={[
              'X (Twitter): 280 characters',
              'Instagram: 2,200 characters',
              'LinkedIn: 3,000 characters',
              'Facebook: 2,000 characters',
              'Threads: 500 characters',
              'TikTok: 2,200 characters',
              'Pinterest: 500 characters',
              'YouTube: 5,000 characters',
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.user.analyzeContent.tip')}
        </DocTip>
      </DocSection>

      {/* Voice Assistant */}
      <DocSection id="voice-assistant" title="Voice Assistant (Olivia AI)">
        <DocParagraph>
          Contentry.ai features Olivia, an AI-powered voice assistant that helps you create and refine content using natural speech. 
          Olivia is available throughout the platform and can assist with content generation, analysis, and general questions about your account.
        </DocParagraph>

        <DocSubsection title="Accessing Olivia">
          <DocParagraph>
            You can access Olivia in several ways:
          </DocParagraph>
          <DocFeatureList
            items={[
              'Click the headphone icon (🎧) in the prompt toolbar next to the microphone',
              'The floating voice widget appears in the bottom-right corner of the screen',
              'Simply click and start speaking to interact with Olivia',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="What Olivia Can Help With">
          <DocFeatureList
            items={[
              'Generate content ideas and drafts using voice commands',
              'Refine and improve your existing content',
              'Answer questions about Contentry.ai features',
              'Guide you through the content analysis process',
              'Help troubleshoot common issues',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Voice Dictation">
          <DocParagraph>
            For quick text input, use the microphone icon (🎤) to dictate content directly into any text field. 
            This is separate from Olivia and simply converts your speech to text.
          </DocParagraph>
        </DocSubsection>

        <DocTip type="info">
          Olivia is powered by ElevenLabs conversational AI and supports natural language interactions. 
          Speak naturally and Olivia will understand your requests.
        </DocTip>
      </DocSection>

      {/* Content Refinement Chat */}
      <DocSection id="content-refinement" title="Content Refinement Chat">
        <DocParagraph>
          After analyzing or rewriting content, you can refine it further using the built-in chat interface. 
          This allows you to make iterative improvements through natural conversation.
        </DocParagraph>

        <DocSubsection title="Using the Refinement Chat">
          <DocParagraph>
            When you have rewritten content displayed in the Analyze Content tab:
          </DocParagraph>
          <DocFeatureList
            items={[
              '1. Look for the "Refine with AI" section below the rewritten content',
              '2. Type your refinement request in the chat input (e.g., "Make it shorter")',
              '3. Press Enter or click the send button to submit your request',
              '4. The AI will update the content based on your instruction',
              '5. Continue refining until you&apos;re satisfied with the result',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Example Refinement Requests">
          <DocFeatureList
            items={[
              '"Make it shorter" - Condenses the content while keeping key points',
              '"Add more enthusiasm" - Increases the emotional energy of the text',
              '"Make it more formal" - Adjusts tone for professional contexts',
              '"Add a call to action" - Includes a compelling CTA at the end',
              '"Remove hashtags" - Strips out any hashtags from the content',
              '"Translate to Spanish" - Converts the content to another language',
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          The chat maintains context from your previous requests, so you can build on refinements. 
          For example, first ask to &quot;make it shorter&quot; then &quot;add emojis&quot; to get progressively refined content.
        </DocTip>
      </DocSection>

      {/* Strategic Profiles */}
      <DocSection id="strategic-profiles" title={t('documentation.user.sections.strategicProfiles')}>
        <DocParagraph>
          {t('documentation.user.strategicProfiles.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.user.strategicProfiles.createTitle')}>
          <DocParagraph>
            {t('documentation.user.strategicProfiles.createDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="strategic-profiles" caption="Strategic Profiles page with knowledge base integration" />
          
          <DocFeatureList
            items={[
              t('documentation.user.strategicProfiles.feature1'),
              t('documentation.user.strategicProfiles.feature2'),
              t('documentation.user.strategicProfiles.feature3'),
              t('documentation.user.strategicProfiles.feature4'),
            ]}
          />
        </DocSubsection>

        {/* Default Platforms Feature - New */}
        <DocSubsection title="Default Target Platforms">
          <DocParagraph>
            Save time by setting default target platforms for each Strategic Profile. When you select a profile, the Platform Selector automatically populates with your preferred platforms.
          </DocParagraph>
          
          <DocFeatureList
            items={[
              'Set default platforms when creating or editing a profile',
              'Platforms auto-populate when selecting the profile',
              'Override defaults anytime in the content creation flow',
              'Perfect for profiles dedicated to specific platforms (e.g., "LinkedIn Thought Leader")',
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          {t('documentation.user.strategicProfiles.tip')}
        </DocTip>
      </DocSection>

      {/* Social Accounts */}
      <DocSection id="social-accounts" title={t('documentation.user.sections.socialAccounts')}>
        <DocParagraph>
          {t('documentation.user.socialAccounts.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.user.socialAccounts.connectTitle')}>
          <DocParagraph>
            {t('documentation.user.socialAccounts.connectDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.user.socialAccounts.platform1'),
              t('documentation.user.socialAccounts.platform2'),
              t('documentation.user.socialAccounts.platform3'),
              t('documentation.user.socialAccounts.platform4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="warning">
          {t('documentation.user.socialAccounts.warning')}
        </DocTip>
      </DocSection>

      {/* Approval Process */}
      <DocSection id="approval-process" title={t('documentation.user.sections.approvalProcess')}>
        <DocParagraph>
          {t('documentation.user.approvalProcess.intro')}
        </DocParagraph>

        <DocSubsection title="For Content Creators">
          <DocParagraph>
            If you have the Creator role in a Company Workspace, your content must be approved before publishing:
          </DocParagraph>
          <DocFeatureList
            items={[
              '1. Create your content using Generate or Analyze tabs',
              '2. Click "Submit for Approval" (orange button) instead of "Post to Social"',
              '3. Your content enters the approval queue and managers are notified',
              '4. Track your submission status in the "All Posts" tab under "Pending Approval"',
              '5. If rejected, you&apos;ll see feedback and can revise and resubmit',
            ]}
          />
          
          <DocParagraph fontWeight="600">Status Filters for Creators:</DocParagraph>
          <DocFeatureList
            items={[
              'All - View all your posts regardless of status',
              'Drafts - Posts saved but not submitted',
              'Pending Approval - Awaiting manager review',
              'Needs Revision - Rejected with feedback, edit and resubmit',
              'Approved - Ready to be scheduled or published',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="For Managers & Admins">
          <DocParagraph>
            Managers and Admins can review and approve content from team members:
          </DocParagraph>
          <DocFeatureList
            items={[
              '1. Go to the "All Posts" tab (not Scheduled)',
              '2. Use the "Pending Review" filter to see content awaiting approval',
              '3. Review content details, analysis scores, and author information',
              '4. Click "Approve" to allow publishing, or "Reject" to request changes',
              '5. When rejecting, provide feedback to help the creator improve',
              '6. Approved content appears in "Ready to Publish" and can be scheduled',
            ]}
          />
          
          <DocParagraph fontWeight="600">Status Filters for Managers:</DocParagraph>
          <DocFeatureList
            items={[
              'All - View all team posts',
              'Pending Review - Content awaiting your approval (action required)',
              'Ready to Publish - Approved content ready for scheduling',
              'Published - Content that has been posted',
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          The approval workflow only applies in Company Workspace mode. Personal workspace content can be published directly without approval.
        </DocTip>
      </DocSection>
    </DocumentationLayout>
  );
}
