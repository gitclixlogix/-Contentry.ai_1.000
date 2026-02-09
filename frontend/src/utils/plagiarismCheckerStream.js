/**
 * plagiarismChecker Stream Utility
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

const createPrompt = (content) => {
  
    return endent`
    You are an expert content plagiarism checker in all languages.
    You know very well what plagiarism of a content is. You know very well if a content is plagiarism-free or not. You will check all sources to verify if the given sentence or content is plagiarized or plagiarism-free. Is the following content: ${content}, plagiarism-free? Reply with "Your content is plagiarized!" if the content is plagiarized, and explain why and from where. Reply with "Your content is plagiarism-free!" if the content is plagiarism-free, and explain why.
    The generated response must be in markdown format but not rendered, it must include all markdown characteristics. The title must be bold, and there should be a &nbsp; between every paragraph.
    Do not include informations about console logs or print messages.
    `;

};
export const OpenAIStream = async (content, model, key) => {
  const prompt = createPrompt(content);

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
      operation_type: 'plagiarismchecker'
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
