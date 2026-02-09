/**
 * Export utilities for content analysis results
 */

// Export analysis as JSON
export function exportToJSON(analysis, content, filename = 'content-analysis') {
  const exportData = {
    exported_at: new Date().toISOString(),
    content: {
      text: content,
      length: content?.length || 0,
    },
    analysis: {
      overall_score: calculateOverallScore(analysis),
      compliance: {
        severity: analysis?.compliance_analysis?.severity || 'unknown',
        issues: analysis?.compliance_analysis?.issues || [],
        recommendations: analysis?.compliance_analysis?.recommendations || [],
      },
      accuracy: {
        score: analysis?.accuracy_analysis?.accuracy_score || 0,
        issues: analysis?.accuracy_analysis?.issues || [],
        claims: analysis?.accuracy_analysis?.claims || [],
      },
      cultural_sensitivity: {
        overall_score: analysis?.cultural_analysis?.overall_score || 0,
        dimensions: analysis?.cultural_analysis?.dimensions || [],
        recommendations: analysis?.cultural_analysis?.recommendations || [],
      },
    },
    flagged_status: analysis?.flagged_status || 'pending',
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  downloadBlob(blob, `${filename}-${Date.now()}.json`);
}

// Export analysis as PDF-ready HTML (opens print dialog)
export function exportToPDF(analysis, content) {
  const overallScore = calculateOverallScore(analysis);
  const complianceScore = getComplianceScore(analysis?.compliance_analysis?.severity);
  const accuracyScore = analysis?.accuracy_analysis?.accuracy_score || 0;
  const culturalScore = analysis?.cultural_analysis?.overall_score || 0;

  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Content Analysis Report</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; color: #333; }
        h1 { color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px; }
        h2 { color: #1e40af; margin-top: 30px; }
        .score-box { display: inline-block; padding: 15px 25px; border-radius: 10px; text-align: center; margin: 10px; }
        .score-excellent { background: #E8FFF3; border: 2px solid #00C853; }
        .score-good { background: #FFF8E1; border: 2px solid #FFB300; }
        .score-poor { background: #FFEBEE; border: 2px solid #F44336; }
        .score-number { font-size: 32px; font-weight: bold; }
        .score-label { font-size: 12px; color: #666; }
        .content-box { background: #F5F5F5; padding: 20px; border-radius: 8px; margin: 20px 0; white-space: pre-wrap; }
        .issue-item { padding: 10px; margin: 5px 0; background: #FFF3E0; border-left: 3px solid #FF9800; }
        .recommendation { padding: 10px; margin: 5px 0; background: #E8F5E9; border-left: 3px solid #4CAF50; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #E0E0E0; border-radius: 8px; }
        .timestamp { color: #999; font-size: 12px; }
        @media print { body { padding: 20px; } }
      </style>
    </head>
    <body>
      <h1>📊 Content Analysis Report</h1>
      <p class="timestamp">Generated: ${new Date().toLocaleString()}</p>
      
      <h2>Overall Score</h2>
      <div style="text-align: center; margin: 30px 0;">
        <div class="score-box ${overallScore >= 75 ? 'score-excellent' : overallScore >= 50 ? 'score-good' : 'score-poor'}">
          <div class="score-number">${overallScore}</div>
          <div class="score-label">OVERALL</div>
        </div>
        <div class="score-box ${complianceScore >= 75 ? 'score-excellent' : complianceScore >= 50 ? 'score-good' : 'score-poor'}">
          <div class="score-number">${complianceScore}</div>
          <div class="score-label">COMPLIANCE</div>
        </div>
        <div class="score-box ${accuracyScore >= 75 ? 'score-excellent' : accuracyScore >= 50 ? 'score-good' : 'score-poor'}">
          <div class="score-number">${accuracyScore}</div>
          <div class="score-label">ACCURACY</div>
        </div>
        <div class="score-box ${culturalScore >= 75 ? 'score-excellent' : culturalScore >= 50 ? 'score-good' : 'score-poor'}">
          <div class="score-number">${culturalScore}</div>
          <div class="score-label">CULTURAL</div>
        </div>
      </div>

      <h2>Analyzed Content</h2>
      <div class="content-box">${escapeHtml(content || 'No content provided')}</div>

      <h2>Compliance Analysis</h2>
      <div class="section">
        <p><strong>Severity:</strong> ${analysis?.compliance_analysis?.severity || 'Unknown'}</p>
        ${(analysis?.compliance_analysis?.issues?.length > 0) ? `
          <p><strong>Issues Found:</strong></p>
          ${analysis.compliance_analysis.issues.map(issue => `<div class="issue-item">${escapeHtml(typeof issue === 'string' ? issue : issue.description || JSON.stringify(issue))}</div>`).join('')}
        ` : '<p>No compliance issues detected.</p>'}
        ${(analysis?.compliance_analysis?.recommendations?.length > 0) ? `
          <p><strong>Recommendations:</strong></p>
          ${analysis.compliance_analysis.recommendations.map(rec => `<div class="recommendation">${escapeHtml(typeof rec === 'string' ? rec : rec.recommendation || JSON.stringify(rec))}</div>`).join('')}
        ` : ''}
      </div>

      <h2>Accuracy Analysis</h2>
      <div class="section">
        <p><strong>Accuracy Score:</strong> ${accuracyScore}/100</p>
        ${(analysis?.accuracy_analysis?.issues?.length > 0) ? `
          <p><strong>Issues Found:</strong></p>
          ${analysis.accuracy_analysis.issues.map(issue => `<div class="issue-item">${escapeHtml(typeof issue === 'string' ? issue : issue.description || JSON.stringify(issue))}</div>`).join('')}
        ` : '<p>No accuracy issues detected.</p>'}
      </div>

      <h2>Cultural Sensitivity Analysis</h2>
      <div class="section">
        <p><strong>Cultural Score:</strong> ${culturalScore}/100</p>
        ${(analysis?.cultural_analysis?.dimensions?.length > 0) ? `
          <p><strong>Dimensions Analyzed:</strong></p>
          ${analysis.cultural_analysis.dimensions.map(dim => `
            <div class="issue-item">
              <strong>${escapeHtml(dim.dimension || 'Unknown')}:</strong> Score ${dim.score || 0}/100
              ${dim.cultures_affected?.length > 0 ? `<br><small>Cultures: ${dim.cultures_affected.join(', ')}</small>` : ''}
            </div>
          `).join('')}
        ` : '<p>No cultural sensitivity concerns detected.</p>'}
        ${(analysis?.cultural_analysis?.recommendations?.length > 0) ? `
          <p><strong>Recommendations:</strong></p>
          ${analysis.cultural_analysis.recommendations.map(rec => `<div class="recommendation">${escapeHtml(typeof rec === 'string' ? rec : JSON.stringify(rec))}</div>`).join('')}
        ` : ''}
      </div>

      <hr style="margin-top: 40px;">
      <p style="text-align: center; color: #999; font-size: 11px;">
        Generated by Contentry Content Intelligence Platform
      </p>
    </body>
    </html>
  `;

  const printWindow = window.open('', '_blank');
  printWindow.document.write(htmlContent);
  printWindow.document.close();
  printWindow.onload = () => {
    printWindow.print();
  };
}

// Helper functions
function calculateOverallScore(analysis) {
  const complianceScore = getComplianceScore(analysis?.compliance_analysis?.severity);
  const accuracyScore = analysis?.accuracy_analysis?.accuracy_score || 85;
  const culturalScore = analysis?.cultural_analysis?.overall_score || 75;
  return Math.round((complianceScore + accuracyScore + culturalScore) / 3);
}

function getComplianceScore(severity) {
  switch (severity) {
    case 'none': return 100;
    case 'low': return 70;
    case 'medium': return 50;
    case 'high': return 30;
    default: return 75;
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
