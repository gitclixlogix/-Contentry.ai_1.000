/**
 * AI Service Client
 * =================
 * Secure client for AI operations through the backend API.
 * 
 * SECURITY: This replaces all direct OpenAI API calls that exposed the API key.
 * All AI operations now go through the backend which holds the API key securely.
 * 
 * Usage:
 *   import { aiService } from '@/lib/aiService';
 *   const result = await aiService.complete({ prompt: 'Hello', operation_type: 'chat' });
 */

const getApiUrl = () => {
  return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
};

/**
 * Generic AI completion
 */
export const aiComplete = async (prompt, options = {}) => {
  const {
    systemPrompt = null,
    model = 'gpt-4o-mini',
    temperature = 0.7,
    maxTokens = null,
    operationType = 'general',
    userId = null
  } = options;

  const response = await fetch(`${getApiUrl()}/api/ai/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId || 'anonymous'
    },
    body: JSON.stringify({
      prompt,
      system_prompt: systemPrompt,
      model,
      temperature,
      max_tokens: maxTokens,
      operation_type: operationType
    })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'AI service error' }));
    throw new Error(error.detail || 'AI service error');
  }

  return response.json();
};

/**
 * Chat completion with message history
 */
export const aiChat = async (messages, options = {}) => {
  const {
    model = 'gpt-4o-mini',
    temperature = 0.7,
    maxTokens = null,
    operationType = 'chat',
    userId = null
  } = options;

  const response = await fetch(`${getApiUrl()}/api/ai/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId || 'anonymous'
    },
    body: JSON.stringify({
      messages,
      model,
      temperature,
      max_tokens: maxTokens,
      operation_type: operationType
    })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Chat service error' }));
    throw new Error(error.detail || 'Chat service error');
  }

  return response.json();
};

/**
 * Translation
 */
export const aiTranslate = async (text, targetLanguage, options = {}) => {
  const {
    sourceLanguage = 'auto',
    userId = null
  } = options;

  const response = await fetch(`${getApiUrl()}/api/ai/translate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId || 'anonymous'
    },
    body: JSON.stringify({
      text,
      source_language: sourceLanguage,
      target_language: targetLanguage
    })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Translation error' }));
    throw new Error(error.detail || 'Translation error');
  }

  return response.json();
};

/**
 * Content rewriting
 */
export const aiRewrite = async (content, options = {}) => {
  const {
    style = 'professional',
    instructions = null,
    userId = null
  } = options;

  const response = await fetch(`${getApiUrl()}/api/ai/rewrite`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId || 'anonymous'
    },
    body: JSON.stringify({
      content,
      style,
      instructions
    })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Rewrite error' }));
    throw new Error(error.detail || 'Rewrite error');
  }

  return response.json();
};

/**
 * Content generation
 */
export const aiGenerate = async (topic, options = {}) => {
  const {
    contentType = 'article',
    tone = 'professional',
    length = 'medium',
    additionalContext = null,
    userId = null
  } = options;

  const response = await fetch(`${getApiUrl()}/api/ai/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId || 'anonymous'
    },
    body: JSON.stringify({
      topic,
      content_type: contentType,
      tone,
      length,
      additional_context: additionalContext
    })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Generation error' }));
    throw new Error(error.detail || 'Generation error');
  }

  return response.json();
};

/**
 * Text summarization
 */
export const aiSummarize = async (text, options = {}) => {
  const {
    maxLength = 200,
    style = 'concise',
    userId = null
  } = options;

  const response = await fetch(`${getApiUrl()}/api/ai/summarize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId || 'anonymous'
    },
    body: JSON.stringify({
      text,
      max_length: maxLength,
      style
    })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Summarization error' }));
    throw new Error(error.detail || 'Summarization error');
  }

  return response.json();
};

/**
 * Hashtag generation
 */
export const aiGenerateHashtags = async (topic, options = {}) => {
  const {
    count = 10,
    userId = null
  } = options;

  const response = await fetch(`${getApiUrl()}/api/ai/hashtags?topic=${encodeURIComponent(topic)}&count=${count}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId || 'anonymous'
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Hashtag generation error' }));
    throw new Error(error.detail || 'Hashtag generation error');
  }

  return response.json();
};

/**
 * SEO keyword generation
 */
export const aiGenerateSeoKeywords = async (topic, options = {}) => {
  const {
    count = 15,
    userId = null
  } = options;

  const response = await fetch(`${getApiUrl()}/api/ai/seo-keywords?topic=${encodeURIComponent(topic)}&count=${count}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId || 'anonymous'
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'SEO keyword generation error' }));
    throw new Error(error.detail || 'SEO keyword generation error');
  }

  return response.json();
};

/**
 * Streaming AI completion (for real-time responses)
 * Returns a ReadableStream for progressive content display
 */
export const aiCompleteStream = async (prompt, options = {}) => {
  const {
    systemPrompt = null,
    model = 'gpt-4o-mini',
    temperature = 0.7,
    operationType = 'general',
    userId = null,
    onChunk = null  // Callback for each chunk
  } = options;

  // For now, use non-streaming endpoint and simulate streaming
  // TODO: Implement proper streaming when backend supports it
  const result = await aiComplete(prompt, {
    systemPrompt,
    model,
    temperature,
    operationType,
    userId
  });

  // Simulate streaming by returning chunks
  if (onChunk && result.content) {
    const words = result.content.split(' ');
    for (let i = 0; i < words.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 50));
      onChunk(words.slice(0, i + 1).join(' '));
    }
  }

  return result;
};

// Export as a service object for convenience
export const aiService = {
  complete: aiComplete,
  chat: aiChat,
  translate: aiTranslate,
  rewrite: aiRewrite,
  generate: aiGenerate,
  summarize: aiSummarize,
  generateHashtags: aiGenerateHashtags,
  generateSeoKeywords: aiGenerateSeoKeywords,
  completeStream: aiCompleteStream
};

export default aiService;
