'use client';
import { useTranslation } from 'react-i18next';
import { FaClipboardList } from 'react-icons/fa';
import DocumentationLayout, {
  DocSection,
  DocSubsection,
  DocParagraph,
  DocFeatureList,
  DocTip,
  DocScreenshot,
  WorkflowGif,
} from '../DocumentationLayout';

export default function WorkflowsGuide() {
  const { t } = useTranslation();

  const sections = [
    { id: 'scoring-system', title: t('documentation.workflows.sections.scoringSystem') },
    { id: 'analyze-content', title: t('documentation.workflows.sections.analyzeContent') },
    { id: 'generate-content', title: t('documentation.workflows.sections.generateContent') },
    { id: 'schedule-prompt', title: t('documentation.workflows.sections.schedulePrompt') },
    { id: 'schedule-post', title: t('documentation.workflows.sections.schedulePost') },
    { id: 'approval-workflow', title: t('documentation.workflows.sections.approvalWorkflow') },
  ];

  return (
    <DocumentationLayout
      title={t('documentation.workflowsGuide.title')}
      description={t('documentation.workflowsGuide.description')}
      icon={FaClipboardList}
      iconColor="teal"
      sections={sections}
    >
      {/* Scoring System */}
      <DocSection id="scoring-system" title={t('documentation.workflows.sections.scoringSystem')}>
        <DocParagraph>
          {t('documentation.workflows.scoring.intro')}
        </DocParagraph>
        
        <DocSubsection title={t('documentation.workflows.scoring.overallScoreTitle')}>
          <DocParagraph>
            {t('documentation.workflows.scoring.overallScoreDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.scoring.scoreRange1'),
              t('documentation.workflows.scoring.scoreRange2'),
              t('documentation.workflows.scoring.scoreRange3'),
              t('documentation.workflows.scoring.scoreRange4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.scoring.overallCalcTitle')}>
          <DocParagraph>
            {t('documentation.workflows.scoring.overallCalcDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.scoring.overallCalc1'),
              t('documentation.workflows.scoring.overallCalc2'),
              t('documentation.workflows.scoring.overallCalc3'),
              t('documentation.workflows.scoring.overallCalc4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.scoring.componentsTitle')}>
          <DocParagraph>
            {t('documentation.workflows.scoring.componentsDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.scoring.component1'),
              t('documentation.workflows.scoring.component2'),
              t('documentation.workflows.scoring.component3'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.scoring.complianceDetailTitle')}>
          <DocParagraph>
            {t('documentation.workflows.scoring.complianceDetailDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.scoring.complianceSeverity1'),
              t('documentation.workflows.scoring.complianceSeverity2'),
              t('documentation.workflows.scoring.complianceSeverity3'),
              t('documentation.workflows.scoring.complianceSeverity4'),
              t('documentation.workflows.scoring.complianceSeverity5'),
            ]}
          />
          <DocParagraph>
            {t('documentation.workflows.scoring.complianceAdjustment')}
          </DocParagraph>
          <DocParagraph>
            {t('documentation.workflows.scoring.complianceViolationTypes')}
          </DocParagraph>
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.scoring.culturalDetailTitle')}>
          <DocParagraph>
            {t('documentation.workflows.scoring.culturalDetailDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.scoring.culturalDim1'),
              t('documentation.workflows.scoring.culturalDim2'),
              t('documentation.workflows.scoring.culturalDim3'),
              t('documentation.workflows.scoring.culturalDim4'),
              t('documentation.workflows.scoring.culturalDim5'),
              t('documentation.workflows.scoring.culturalDim6'),
            ]}
          />
          <DocParagraph>
            {t('documentation.workflows.scoring.culturalCalc')}
          </DocParagraph>
          <DocTip type="info">
            {t('documentation.workflows.scoring.culturalRisk')}
          </DocTip>
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.scoring.accuracyDetailTitle')}>
          <DocParagraph>
            {t('documentation.workflows.scoring.accuracyDetailDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.scoring.accuracyCheck1'),
              t('documentation.workflows.scoring.accuracyCheck2'),
              t('documentation.workflows.scoring.accuracyCheck3'),
              t('documentation.workflows.scoring.accuracyCheck4'),
            ]}
          />
          <DocParagraph>
            {t('documentation.workflows.scoring.accuracyCalc')}
          </DocParagraph>
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.scoring.flagStatusTitle')}>
          <DocParagraph>
            {t('documentation.workflows.scoring.flagStatusDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.scoring.flag1'),
              t('documentation.workflows.scoring.flag2'),
              t('documentation.workflows.scoring.flag3'),
              t('documentation.workflows.scoring.flag4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.scoring.disclosureTitle')}>
          <DocParagraph>
            {t('documentation.workflows.scoring.disclosureDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.scoring.disclosure1'),
              t('documentation.workflows.scoring.disclosure2'),
              t('documentation.workflows.scoring.disclosure3'),
              t('documentation.workflows.scoring.disclosure4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.workflows.scoring.tip')}
        </DocTip>
      </DocSection>

      {/* Analyze Content */}
      <DocSection id="analyze-content" title={t('documentation.workflows.sections.analyzeContent')}>
        <DocParagraph>
          {t('documentation.workflows.analyze.intro')}
        </DocParagraph>

        <DocScreenshot pageId="content-analyze" caption="The Analyze Content interface" />

        <DocSubsection title={t('documentation.workflows.analyze.stepsTitle')}>
          <DocParagraph>
            {t('documentation.workflows.analyze.stepsDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.analyze.step1'),
              t('documentation.workflows.analyze.step2'),
              t('documentation.workflows.analyze.step3'),
              t('documentation.workflows.analyze.step4'),
              t('documentation.workflows.analyze.step5'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.analyze.analysisTypesTitle')}>
          <DocFeatureList
            items={[
              t('documentation.workflows.analyze.type1'),
              t('documentation.workflows.analyze.type2'),
              t('documentation.workflows.analyze.type3'),
              t('documentation.workflows.analyze.type4'),
            ]}
          />
        </DocSubsection>

        {/* Workflow GIF: Content Rewriting */}
        <WorkflowGif 
          workflowId="content-rewriting" 
          caption="How to analyze content and use AI to rewrite it"
        />

        <DocTip type="tip">
          {t('documentation.workflows.analyze.tip')}
        </DocTip>
      </DocSection>

      {/* Generate Content */}
      <DocSection id="generate-content" title={t('documentation.workflows.sections.generateContent')}>
        <DocParagraph>
          {t('documentation.workflows.generate.intro')}
        </DocParagraph>

        <DocScreenshot pageId="content-generate" caption="Content Generation interface with AI-powered creation tools" />

        <DocSubsection title={t('documentation.workflows.generate.stepsTitle')}>
          <DocFeatureList
            items={[
              t('documentation.workflows.generate.step1'),
              t('documentation.workflows.generate.step2'),
              t('documentation.workflows.generate.step3'),
              t('documentation.workflows.generate.step4'),
              t('documentation.workflows.generate.step5'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.generate.optionsTitle')}>
          <DocParagraph>
            {t('documentation.workflows.generate.optionsDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.generate.option1'),
              t('documentation.workflows.generate.option2'),
              t('documentation.workflows.generate.option3'),
              t('documentation.workflows.generate.option4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.workflows.generate.tip')}
        </DocTip>
      </DocSection>

      {/* Schedule Prompt */}
      <DocSection id="schedule-prompt" title={t('documentation.workflows.sections.schedulePrompt')}>
        <DocParagraph>
          {t('documentation.workflows.schedulePrompt.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.workflows.schedulePrompt.howToTitle')}>
          <DocParagraph>
            {t('documentation.workflows.schedulePrompt.howToDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.schedulePrompt.step1'),
              t('documentation.workflows.schedulePrompt.step2'),
              t('documentation.workflows.schedulePrompt.step3'),
              t('documentation.workflows.schedulePrompt.step4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.schedulePrompt.benefitsTitle')}>
          <DocFeatureList
            items={[
              t('documentation.workflows.schedulePrompt.benefit1'),
              t('documentation.workflows.schedulePrompt.benefit2'),
              t('documentation.workflows.schedulePrompt.benefit3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          {t('documentation.workflows.schedulePrompt.tip')}
        </DocTip>
      </DocSection>

      {/* Schedule Post */}
      <DocSection id="schedule-post" title={t('documentation.workflows.sections.schedulePost')}>
        <DocParagraph>
          {t('documentation.workflows.schedulePost.intro')}
        </DocParagraph>

        <DocScreenshot pageId="scheduled-posts" caption="Scheduled posts and approval queue" />

        <DocSubsection title={t('documentation.workflows.schedulePost.howToTitle')}>
          <DocFeatureList
            items={[
              t('documentation.workflows.schedulePost.step1'),
              t('documentation.workflows.schedulePost.step2'),
              t('documentation.workflows.schedulePost.step3'),
              t('documentation.workflows.schedulePost.step4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.schedulePost.optionsTitle')}>
          <DocParagraph>
            {t('documentation.workflows.schedulePost.optionsDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.schedulePost.option1'),
              t('documentation.workflows.schedulePost.option2'),
              t('documentation.workflows.schedulePost.option3'),
            ]}
          />
        </DocSubsection>

        <DocTip type="warning">
          {t('documentation.workflows.schedulePost.warning')}
        </DocTip>
      </DocSection>

      {/* Approval Workflow */}
      <DocSection id="approval-workflow" title={t('documentation.workflows.sections.approvalWorkflow')}>
        <DocParagraph>
          {t('documentation.workflows.approval.intro')}
        </DocParagraph>

        <DocSubsection title={t('documentation.workflows.approval.processTitle')}>
          <DocParagraph>
            {t('documentation.workflows.approval.processDesc')}
          </DocParagraph>
          <DocFeatureList
            items={[
              t('documentation.workflows.approval.step1'),
              t('documentation.workflows.approval.step2'),
              t('documentation.workflows.approval.step3'),
              t('documentation.workflows.approval.step4'),
            ]}
          />
        </DocSubsection>

        <DocSubsection title={t('documentation.workflows.approval.statusesTitle')}>
          <DocFeatureList
            items={[
              t('documentation.workflows.approval.status1'),
              t('documentation.workflows.approval.status2'),
              t('documentation.workflows.approval.status3'),
              t('documentation.workflows.approval.status4'),
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          {t('documentation.workflows.approval.tip')}
        </DocTip>
      </DocSection>
    </DocumentationLayout>
  );
}
