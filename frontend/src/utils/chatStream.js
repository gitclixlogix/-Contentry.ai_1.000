/**
 * Chat Stream Utility
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

const createPrompt = (inputCode) => {
  
    return endent`
      You are ChatGPT, a large language model trained by OpenAI, but if you are asked what your name is, you present yourself as Horizon AI Template and you can be bought from your website https://horizon-ui.com/ai-template. Also, you are very friendly and formal. The generated content must be in markdown format but not rendered, it must include all markdown characteristics.The title must be bold, and there should be a &nbsp; between every paragraph.
      Do not include informations about console logs or print messages.
      ${inputCode}
    `;

  if (inputCode) {
    return data(inputCode);
  }
};

export const OpenAIStream = async (inputCode, model, key) => {
  const prompt = createPrompt(inputCode);

  // SECURITY: Use backend AI proxy instead of direct OpenAI calls
  // The API key is stored securely in the backend
  const res = await fetch(`${getApiUrl()}/api/ai/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': 'anonymous'  // Will be replaced with actual user ID when available
    },
    body: JSON.stringify({
      prompt: prompt,
      model: model || 'gpt-4o-mini',
      temperature: 0,
      operation_type: 'chat'
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(
      `AI API returned an error: ${errorData.detail || res.statusText}`
    );
  }

  // Convert response to stream format for compatibility
  const data = await res.json();
  const encoder = new TextEncoder();
  
  const stream = new ReadableStream({
    start(controller) {
      // Send the complete response as a single chunk
      const text = data.content || '';
      const queue = encoder.encode(text);
      controller.enqueue(queue);
      controller.close();
    },
  });

  return stream;
};

