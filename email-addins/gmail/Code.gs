/**
 * Gmail Add-on using Google Apps Script
 * This serves as a wrapper that loads our React app in an iframe
 */

// Configuration
const CONTENTRY_APP_URL = 'https://gmail-addin.contentry.ai'; // Will be your deployed URL

/**
 * Homepage trigger - shown when add-on is opened from sidebar
 */
function onHomepage(e) {
  return createMainCard();
}

/**
 * Compose trigger - shown when composing an email
 */
function onCompose(e) {
  return createMainCard(e.draftMetadata);
}

/**
 * Creates the main card with embedded iframe
 */
function createMainCard(draftMetadata) {
  // Get current message info if available
  let messageId = '';
  if (draftMetadata && draftMetadata.messageId) {
    messageId = draftMetadata.messageId;
  }
  
  // Build the iframe URL with message context
  const iframeUrl = `${CONTENTRY_APP_URL}?messageId=${encodeURIComponent(messageId)}`;
  
  const card = CardService.newCardBuilder()
    .setHeader(
      CardService.newCardHeader()
        .setTitle('Contentry.ai')
        .setSubtitle('Content Analysis')
        .setImageUrl('https://contentry.ai/icon-48.png')
        .setImageStyle(CardService.ImageStyle.CIRCLE)
    )
    .addSection(
      CardService.newCardSection()
        .addWidget(
          CardService.newTextParagraph()
            .setText('Analyze your email content for compliance, cultural sensitivity, and accuracy.')
        )
        .addWidget(
          CardService.newTextButton()
            .setText('Open Analysis Panel')
            .setOpenLink(
              CardService.newOpenLink()
                .setUrl(iframeUrl)
                .setOpenAs(CardService.OpenAs.OVERLAY)
                .setOnClose(CardService.OnClose.NOTHING)
            )
        )
    );
  
  return card.build();
}

/**
 * Alternative: Create a sidebar card with native UI
 * This can be used if iframe approach has issues
 */
function createNativeCard(subject, body) {
  const card = CardService.newCardBuilder()
    .setHeader(
      CardService.newCardHeader()
        .setTitle('Contentry.ai')
        .setSubtitle('Email Analysis')
        .setImageUrl('https://contentry.ai/icon-48.png')
    );
  
  // Add content preview section
  const previewSection = CardService.newCardSection()
    .setHeader('Email Preview')
    .addWidget(
      CardService.newTextParagraph()
        .setText(`<b>Subject:</b> ${subject || '(no subject)'}`)
    )
    .addWidget(
      CardService.newTextParagraph()
        .setText(truncateText(body || '(empty)', 200))
    );
  
  card.addSection(previewSection);
  
  // Add analyze button
  const actionSection = CardService.newCardSection()
    .addWidget(
      CardService.newTextButton()
        .setText('Analyze Content')
        .setBackgroundColor('#6941C6')
        .setOnClickAction(
          CardService.newAction()
            .setFunctionName('analyzeContent')
            .setParameters({ subject: subject || '', body: body || '' })
        )
    );
  
  card.addSection(actionSection);
  
  return card.build();
}

/**
 * Analyze content via Contentry.ai API
 */
function analyzeContent(e) {
  const subject = e.parameters.subject || '';
  const body = e.parameters.body || '';
  const content = `Subject: ${subject}\n\n${body}`;
  
  try {
    // Call Contentry.ai API
    const response = UrlFetchApp.fetch('https://api.contentry.ai/api/content/analyze', {
      method: 'POST',
      contentType: 'application/json',
      payload: JSON.stringify({
        content: content,
        source: 'gmail',
        language: 'en'
      }),
      headers: {
        'X-API-Key': PropertiesService.getUserProperties().getProperty('CONTENTRY_API_KEY')
      }
    });
    
    const result = JSON.parse(response.getContentText());
    return createResultsCard(result);
    
  } catch (error) {
    return createErrorCard(error.message);
  }
}

/**
 * Create results card showing analysis
 */
function createResultsCard(result) {
  const card = CardService.newCardBuilder()
    .setHeader(
      CardService.newCardHeader()
        .setTitle('Analysis Results')
        .setImageUrl('https://contentry.ai/icon-48.png')
    );
  
  // Scores section
  const scoresSection = CardService.newCardSection()
    .setHeader('3-Pillar Scores')
    .addWidget(
      CardService.newDecoratedText()
        .setText(`Compliance: ${result.compliance_score || 0}`)
        .setStartIcon(
          CardService.newIconImage().setIcon(CardService.Icon.STAR)
        )
    )
    .addWidget(
      CardService.newDecoratedText()
        .setText(`Cultural: ${result.cultural_sensitivity_score || 0}`)
        .setStartIcon(
          CardService.newIconImage().setIcon(CardService.Icon.PERSON)
        )
    )
    .addWidget(
      CardService.newDecoratedText()
        .setText(`Accuracy: ${result.accuracy_score || 0}`)
        .setStartIcon(
          CardService.newIconImage().setIcon(CardService.Icon.BOOKMARK)
        )
    )
    .addWidget(
      CardService.newDecoratedText()
        .setText(`Overall: ${result.overall_score || 0}`)
        .setStartIcon(
          CardService.newIconImage().setIcon(CardService.Icon.STAR)
        )
        .setBottomLabel('out of 100')
    );
  
  card.addSection(scoresSection);
  
  // Analysis section
  if (result.detailed_analysis) {
    const analysisSection = CardService.newCardSection()
      .setHeader('Analysis')
      .addWidget(
        CardService.newTextParagraph()
          .setText(truncateText(result.detailed_analysis, 500))
      );
    card.addSection(analysisSection);
  }
  
  return card.build();
}

/**
 * Create error card
 */
function createErrorCard(message) {
  return CardService.newCardBuilder()
    .setHeader(
      CardService.newCardHeader()
        .setTitle('Error')
        .setImageUrl('https://contentry.ai/icon-48.png')
    )
    .addSection(
      CardService.newCardSection()
        .addWidget(
          CardService.newTextParagraph()
            .setText(`An error occurred: ${message}`)
        )
        .addWidget(
          CardService.newTextButton()
            .setText('Try Again')
            .setOnClickAction(
              CardService.newAction().setFunctionName('onHomepage')
            )
        )
    )
    .build();
}

/**
 * Helper to truncate text
 */
function truncateText(text, maxLength) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}
