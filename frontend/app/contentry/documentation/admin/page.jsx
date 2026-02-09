'use client';
import { useTranslation } from 'react-i18next';
import { FaUserShield } from 'react-icons/fa';
import DocumentationLayout, {
  DocSection,
  DocSubsection,
  DocParagraph,
  DocFeatureList,
  DocTip,
  DocImage,
  DocScreenshot,
} from '../DocumentationLayout';

export default function AdminGuide() {
  const { t } = useTranslation();

  const sections = [
    { id: 'overview', title: t('documentation.admin.sections.overview') },
    { id: 'user-management', title: t('documentation.admin.sections.userManagement') },
    { id: 'analytics', title: t('documentation.admin.sections.analytics') },
    { id: 'financials', title: t('documentation.admin.sections.financials') },
    { id: 'system-config', title: t('documentation.admin.sections.systemConfig') },
  ];

  return (
    <DocumentationLayout
      title={t('documentation.adminGuide.title')}
      description={t('documentation.adminGuide.description')}
      icon={FaUserShield}
      iconColor="blue"
      sections={sections}
    >
      {/* Platform Overview */}
      <DocSection id="overview" title={t('documentation.admin.sections.overview')}>
        <DocParagraph>
          {t('documentation.admin.overview.intro')}
        </DocParagraph>
        
        <DocSubsection title={t('documentation.admin.overview.dashboardTitle')}>
          <DocParagraph>
            {t('documentation.admin.overview.dashboardDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="admin-analytics" caption="Admin Analytics Dashboard with platform-wide metrics" />
          
          <DocFeatureList
            items={[
              t('documentation.admin.overview.feature1'),
              t('documentation.admin.overview.feature2'),
              t('documentation.admin.overview.feature3'),
              t('documentation.admin.overview.feature4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          {t('documentation.admin.overview.tip')}
        </DocTip>
      </DocSection>

      {/* User Management */}
      <DocSection id="user-management" title={t('documentation.admin.sections.userManagement')}>
        <DocParagraph>
          {t('documentation.admin.userManagement.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.admin.userManagement.viewUsersTitle')}>
          <DocParagraph>
            {t('documentation.admin.userManagement.viewUsersDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="user-management" caption="User Management interface for managing platform users" />
          
          <DocFeatureList
            items={[
              t('documentation.admin.userManagement.feature1'),
              t('documentation.admin.userManagement.feature2'),
              t('documentation.admin.userManagement.feature3'),
              t('documentation.admin.userManagement.feature4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.admin.userManagement.rolesTitle')}>
          <DocParagraph>
            {t('documentation.admin.userManagement.rolesDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.admin.userManagement.role1'),
              t('documentation.admin.userManagement.role2'),
              t('documentation.admin.userManagement.role3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="warning">
          {t('documentation.admin.userManagement.warning')}
        </DocTip>
      </DocSection>

      {/* Analytics */}
      <DocSection id="analytics" title={t('documentation.admin.sections.analytics')}>
        <DocParagraph>
          {t('documentation.admin.analytics.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.admin.analytics.metricsTitle')}>
          <DocScreenshot pageId="advanced-analytics" caption="Advanced Analytics with detailed metrics and drill-down capabilities" />
          
          <DocFeatureList
            items={[
              t('documentation.admin.analytics.metric1'),
              t('documentation.admin.analytics.metric2'),
              t('documentation.admin.analytics.metric3'),
              t('documentation.admin.analytics.metric4'),
              t('documentation.admin.analytics.metric5'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.admin.analytics.tip')}
        </DocTip>
      </DocSection>

      {/* Financials */}
      <DocSection id="financials" title={t('documentation.admin.sections.financials')}>
        <DocParagraph>
          {t('documentation.admin.financials.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.admin.financials.revenueTitle')}>
          <DocParagraph>
            {t('documentation.admin.financials.revenueDesc')}
          </DocParagraph>
          
          <DocScreenshot pageId="financial-analytics" caption="Financial Analytics with revenue tracking and subscription metrics" />
          
          <DocFeatureList
            items={[
              t('documentation.admin.financials.feature1'),
              t('documentation.admin.financials.feature2'),
              t('documentation.admin.financials.feature3'),
            ]}
          />
        </DocSubsection>
      </DocSection>

      {/* System Configuration */}
      <DocSection id="system-config" title={t('documentation.admin.sections.systemConfig')}>
        <DocParagraph>
          {t('documentation.admin.systemConfig.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.admin.systemConfig.integrationsTitle')}>
          <DocParagraph>
            {t('documentation.admin.systemConfig.integrationsDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.admin.systemConfig.integration1'),
              t('documentation.admin.systemConfig.integration2'),
              t('documentation.admin.systemConfig.integration3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          {t('documentation.admin.systemConfig.tip')}
        </DocTip>
      </DocSection>
    </DocumentationLayout>
  );
}
