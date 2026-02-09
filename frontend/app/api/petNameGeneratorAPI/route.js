/**
 * petNameGenerator API API Route
 * 
 * SECURITY UPDATE: This route now proxies AI calls through the FastAPI backend
 * instead of making direct OpenAI API calls.
 * 
 * The API key is securely stored in the backend environment.
 */

import { OpenAIStream } from '@/utils/petNameGeneratorStream';

export const runtime = 'edge';

const getBackendUrl = () => {
  return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
};

export async function GET(req) {
  try {
    const { inputCode, model } = await req.json();
    
    // Use the updated stream utility which proxies through backend
    const stream = await OpenAIStream(inputCode, model);
    
    return new Response(stream);
  } catch (error) {
    console.error(error);
    return new Response(JSON.stringify({ error: error.message }), { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

export async function POST(req) {
  try {
    const { inputCode, model } = await req.json();
    
    // Use the updated stream utility which proxies through backend
    const stream = await OpenAIStream(inputCode, model);
    
    return new Response(stream);
  } catch (error) {
    console.error(error);
    return new Response(JSON.stringify({ error: error.message }), { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
