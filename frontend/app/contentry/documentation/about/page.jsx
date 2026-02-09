'use client';
import { useTranslation } from 'react-i18next';
import { FaLightbulb } from 'react-icons/fa';
import DocumentationLayout, {
  DocSection,
  DocSubsection,
  DocParagraph,
  DocFeatureList,
  DocTip,
  DocImage,
} from '../DocumentationLayout';

export default function AboutBestPractices() {
  const { t } = useTranslation();

  const sections = [
    { id: 'what-is-contentry', title: t('documentation.about.sections.whatIsContentry') },
    { id: 'key-features', title: t('documentation.about.sections.keyFeatures') },
    { id: 'best-practices', title: t('documentation.about.sections.bestPractices') },
    { id: 'optimize-content', title: t('documentation.about.sections.optimizeContent') },
    { id: 'brand-deals', title: t('documentation.about.sections.brandDeals') },
    { id: 'influencer-profiles', title: t('documentation.about.sections.influencerProfiles') },
  ];

  return (
    <DocumentationLayout
      title={t('documentation.aboutGuide.title')}
      description={t('documentation.aboutGuide.description')}
      icon={FaLightbulb}
      iconColor="orange"
      sections={sections}
    >
      {/* What is Contentry */}
      <DocSection id="what-is-contentry" title={t('documentation.about.sections.whatIsContentry')}>
        <DocParagraph>
          {t('documentation.about.whatIsContentry.intro')}
        </DocParagraph>
        
        <DocSubsection title={t('documentation.about.whatIsContentry.missionTitle')}>
          <DocParagraph>
            {t('documentation.about.whatIsContentry.missionDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.whatIsContentry.benefit1'),
              t('documentation.about.whatIsContentry.benefit2'),
              t('documentation.about.whatIsContentry.benefit3'),
              t('documentation.about.whatIsContentry.benefit4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          {t('documentation.about.whatIsContentry.tip')}
        </DocTip>
      </DocSection>

      {/* Key Features */}
      <DocSection id="key-features" title={t('documentation.about.sections.keyFeatures')}>
        <DocParagraph>
          {t('documentation.about.keyFeatures.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.about.keyFeatures.aiContentTitle')}>
          <DocParagraph>
            {t('documentation.about.keyFeatures.aiContentDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.keyFeatures.aiFeature1'),
              t('documentation.about.keyFeatures.aiFeature2'),
              t('documentation.about.keyFeatures.aiFeature3'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.about.keyFeatures.complianceTitle')}>
          <DocParagraph>
            {t('documentation.about.keyFeatures.complianceDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.keyFeatures.complianceFeature1'),
              t('documentation.about.keyFeatures.complianceFeature2'),
              t('documentation.about.keyFeatures.complianceFeature3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.about.keyFeatures.tip')}
        </DocTip>
      </DocSection>

      {/* Best Practices */}
      <DocSection id="best-practices" title={t('documentation.about.sections.bestPractices')}>
        <DocParagraph>
          {t('documentation.about.bestPractices.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.about.bestPractices.workflowTitle')}>
          <DocParagraph>
            {t('documentation.about.bestPractices.workflowDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.bestPractices.workflow1'),
              t('documentation.about.bestPractices.workflow2'),
              t('documentation.about.bestPractices.workflow3'),
              t('documentation.about.bestPractices.workflow4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.about.bestPractices.consistencyTitle')}>
          <DocParagraph>
            {t('documentation.about.bestPractices.consistencyDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.bestPractices.consistency1'),
              t('documentation.about.bestPractices.consistency2'),
              t('documentation.about.bestPractices.consistency3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="warning">
          {t('documentation.about.bestPractices.warning')}
        </DocTip>
      </DocSection>

      {/* Optimize Content */}
      <DocSection id="optimize-content" title={t('documentation.about.sections.optimizeContent')}>
        <DocParagraph>
          {t('documentation.about.optimizeContent.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.about.optimizeContent.platformTitle')}>
          <DocParagraph>
            {t('documentation.about.optimizeContent.platformDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.optimizeContent.platform1'),
              t('documentation.about.optimizeContent.platform2'),
              t('documentation.about.optimizeContent.platform3'),
              t('documentation.about.optimizeContent.platform4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.about.optimizeContent.engagementTitle')}>
          <DocFeatureList
            items={[
              t('documentation.about.optimizeContent.engagement1'),
              t('documentation.about.optimizeContent.engagement2'),
              t('documentation.about.optimizeContent.engagement3'),
              t('documentation.about.optimizeContent.engagement4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.about.optimizeContent.tip')}
        </DocTip>
      </DocSection>

      {/* Brand Deals */}
      <DocSection id="brand-deals" title={t('documentation.about.sections.brandDeals')}>
        <DocParagraph>
          {t('documentation.about.brandDeals.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.about.brandDeals.preparationTitle')}>
          <DocParagraph>
            {t('documentation.about.brandDeals.preparationDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.brandDeals.prep1'),
              t('documentation.about.brandDeals.prep2'),
              t('documentation.about.brandDeals.prep3'),
              t('documentation.about.brandDeals.prep4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.about.brandDeals.pitchingTitle')}>
          <DocParagraph>
            {t('documentation.about.brandDeals.pitchingDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.brandDeals.pitch1'),
              t('documentation.about.brandDeals.pitch2'),
              t('documentation.about.brandDeals.pitch3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          {t('documentation.about.brandDeals.tip')}
        </DocTip>
      </DocSection>

      {/* Influencer Profiles */}
      <DocSection id="influencer-profiles" title={t('documentation.about.sections.influencerProfiles')}>
        <DocParagraph>
          {t('documentation.about.influencerProfiles.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.about.influencerProfiles.setupTitle')}>
          <DocParagraph>
            {t('documentation.about.influencerProfiles.setupDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.influencerProfiles.setup1'),
              t('documentation.about.influencerProfiles.setup2'),
              t('documentation.about.influencerProfiles.setup3'),
              t('documentation.about.influencerProfiles.setup4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.about.influencerProfiles.optimizeTitle')}>
          <DocParagraph>
            {t('documentation.about.influencerProfiles.optimizeDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.about.influencerProfiles.optimize1'),
              t('documentation.about.influencerProfiles.optimize2'),
              t('documentation.about.influencerProfiles.optimize3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.about.influencerProfiles.tip')}
        </DocTip>
      </DocSection>
    </DocumentationLayout>
  );
}
