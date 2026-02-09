/**
 * articleGenerator Stream Utility
 * 
 * SECURITY UPDATE: This utility now proxies AI calls through the backend
 * instead of making direct OpenAI API calls with exposed keys.
 * 
 * The API key is securely stored in the backend environment.
 */

import endent from 'endent';

const getApiUrl = () => {
  return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
};

const createPrompt = (topic, title, language, words) => {
  
    return endent`
      You are an expert at generating compelling, high converting and SEO-Friendly articles.
      You know very well how to generate compelling, high converting and SEO-Friendly articles. Generate an article with the ${title} title and about the following topic: ${topic}.
      The article should contain AT LEAST ${words} words.
      The article should be written in ${language}.
      The content must be in markdown format but not rendered, it must include all markdown characteristics. The title must be bold, and there should be a &nbsp; between every paragraph.
      Do not include informations about console logs or print messages.
    `;

};
export const OpenAIStream = async (
  topic,
  title,
  language,
  words,
  model,
  key,
) => {
  const prompt = createPrompt(topic, title, language);

  // SECURITY: Use backend AI proxy instead of direct OpenAI calls
  // The API key is stored securely in the backend
  const res = await fetch(`${getApiUrl()}/api/ai/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': 'anonymous'
    },
    body: JSON.stringify({
      prompt: prompt,
      model: model || 'gpt-4o-mini',
      temperature: 0,
      operation_type: 'articlegenerator'
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(
      `AI API returned an error: ${errorData.detail || res.statusText}`
    );
  }

  const data = await res.json();
  const encoder = new TextEncoder();
  
  const stream = new ReadableStream({
    start(controller) {
      const text = data.content || '';
      const queue = encoder.encode(text);
      controller.enqueue(queue);
      controller.close();
    },
  });

  return stream;
};
