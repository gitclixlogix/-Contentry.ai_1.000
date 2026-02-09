/**
 * bootstrapToTailwindConverter Stream Utility
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

    You are an expert programmer in all programming languages. You know very well to refactor the code.
    Refactor the following code by changing all Bootstrap specific classes with the equivalent TailwindCSS classes.
    THE RESULT MUST BE THE CODE REFACTORED. DO NOT GIVE ANY OTHER EXPLAINING, JUST THE CODE, BUT WRITE IT AS NORMAL TEXT
    
    ${content}
     
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
      operation_type: 'bootstraptotailwindconverter'
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
