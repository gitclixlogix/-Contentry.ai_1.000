'use client';
import { useTranslation } from 'react-i18next';
import { FaBuilding } from 'react-icons/fa';
import DocumentationLayout, {
  DocSection,
  DocSubsection,
  DocParagraph,
  DocFeatureList,
  DocTip,
  DocImage,
  DocScreenshot,
  WorkflowGif,
} from '../DocumentationLayout';

export default function EnterpriseGuide() {
  const { t } = useTranslation();

  const sections = [
    { id: 'getting-started', title: t('documentation.enterprise.sections.gettingStarted') },
    { id: 'team-management', title: t('documentation.enterprise.sections.teamManagement') },
    { id: 'knowledge-base', title: t('documentation.enterprise.sections.knowledgeBase') },
    { id: 'approval-workflow', title: t('documentation.enterprise.sections.approvalWorkflow') },
    { id: 'billing', title: t('documentation.enterprise.sections.billing') },
  ];

  return (
    <DocumentationLayout
      title={t('documentation.enterpriseGuide.title')}
      description={t('documentation.enterpriseGuide.description')}
      icon={FaBuilding}
      iconColor="blue"
      sections={sections}
    >
      {/* Getting Started */}
      <DocSection id="getting-started" title={t('documentation.enterprise.sections.gettingStarted')}>
        <DocParagraph>
          {t('documentation.enterprise.gettingStarted.intro')}
        </DocParagraph>
        
        <DocSubsection title={t('documentation.enterprise.gettingStarted.setupTitle')}>
          <DocParagraph>
            {t('documentation.enterprise.gettingStarted.setupDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="enterprise-dashboard" caption="Enterprise Dashboard with team analytics and performance metrics" />
          
          <DocFeatureList
            items={[
              t('documentation.enterprise.gettingStarted.step1'),
              t('documentation.enterprise.gettingStarted.step2'),
              t('documentation.enterprise.gettingStarted.step3'),
              t('documentation.enterprise.gettingStarted.step4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.enterprise.gettingStarted.tip')}
        </DocTip>
      </DocSection>

      {/* Team Management */}
      <DocSection id="team-management" title={t('documentation.enterprise.sections.teamManagement')}>
        <DocParagraph>
          {t('documentation.enterprise.teamManagement.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.enterprise.teamManagement.inviteTitle')}>
          <DocParagraph>
            {t('documentation.enterprise.teamManagement.inviteDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="enterprise-team" caption="Team Management interface for inviting and managing team members" />
          
          <DocFeatureList
            items={[
              t('documentation.enterprise.teamManagement.feature1'),
              t('documentation.enterprise.teamManagement.feature2'),
              t('documentation.enterprise.teamManagement.feature3'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.enterprise.teamManagement.rolesTitle')}>
          <DocParagraph>
            {t('documentation.enterprise.teamManagement.rolesDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.enterprise.teamManagement.role1'),
              t('documentation.enterprise.teamManagement.role2'),
              t('documentation.enterprise.teamManagement.role3'),
            ]}
          />
          
          {/* Workflow GIF: Assigning a Role */}
          <WorkflowGif 
            workflowId="role-assignment" 
            caption="How to change a team member's role from Creator to Manager"
          />
        </DocSubsection>

        <DocTip type="info">
          {t('documentation.enterprise.teamManagement.tip')}
        </DocTip>
      </DocSection>

      {/* Knowledge Base */}
      <DocSection id="knowledge-base" title={t('documentation.enterprise.sections.knowledgeBase')}>
        <DocParagraph>
          {t('documentation.enterprise.knowledgeBase.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.enterprise.knowledgeBase.uploadTitle')}>
          <DocParagraph>
            {t('documentation.enterprise.knowledgeBase.uploadDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="knowledge-base" caption="Knowledge Base for uploading company documents and brand guidelines" />
          
          <DocFeatureList
            items={[
              t('documentation.enterprise.knowledgeBase.docType1'),
              t('documentation.enterprise.knowledgeBase.docType2'),
              t('documentation.enterprise.knowledgeBase.docType3'),
              t('documentation.enterprise.knowledgeBase.docType4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.enterprise.knowledgeBase.tip')}
        </DocTip>
      </DocSection>

      {/* Approval Workflow */}
      <DocSection id="approval-workflow" title={t('documentation.enterprise.sections.approvalWorkflow')}>
        <DocParagraph>
          {t('documentation.enterprise.approvalWorkflow.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.enterprise.approvalWorkflow.processTitle')}>
          <DocParagraph>
            {t('documentation.enterprise.approvalWorkflow.processDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.enterprise.approvalWorkflow.step1'),
              t('documentation.enterprise.approvalWorkflow.step2'),
              t('documentation.enterprise.approvalWorkflow.step3'),
              t('documentation.enterprise.approvalWorkflow.step4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="warning">
          {t('documentation.enterprise.approvalWorkflow.warning')}
        </DocTip>
      </DocSection>

      {/* Billing */}
      <DocSection id="billing" title={t('documentation.enterprise.sections.billing')}>
        <DocParagraph>
          {t('documentation.enterprise.billing.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.enterprise.billing.subscriptionTitle')}>
          <DocParagraph>
            {t('documentation.enterprise.billing.subscriptionDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.enterprise.billing.feature1'),
              t('documentation.enterprise.billing.feature2'),
              t('documentation.enterprise.billing.feature3'),
            ]}
          />
        </DocSubsection>
      </DocSection>
    </DocumentationLayout>
  );
}
