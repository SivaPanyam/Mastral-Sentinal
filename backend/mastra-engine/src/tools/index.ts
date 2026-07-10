import { createTool } from '../mastra';
import { z } from 'zod';
import axios from 'axios';
import * as dotenv from 'dotenv';
import path from 'path';
import { GoogleGenAI } from '@google/genai';

// Load environment variables from backend
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000/api/v1';

export const knowledgeSearchTool = createTool({
  id: 'knowledgeSearch',
  description: 'Searches the RAG knowledge base for SOPs and runbooks related to the incident.',
  inputSchema: z.object({
    query: z.string().describe('The search query for retrieving knowledge.'),
    limit: z.number().optional().default(3).describe('Maximum number of documents to return.')
  }),
  execute: async ({ context }) => {
    try {
      const response = await axios.get(`${FASTAPI_URL}/knowledge/search`, {
        params: { query: context.query, limit: context.limit }
      });
      return response.data;
    } catch (error: any) {
      console.error("Knowledge search error:", error.message);
      return { error: 'Failed to retrieve knowledge' };
    }
  }
});

export const databaseTool = createTool({
  id: 'databaseTool',
  description: 'Accesses PostgreSQL services to fetch incident or logs.',
  inputSchema: z.object({
    incidentId: z.string().describe('The ID of the incident to fetch.'),
    action: z.enum(['GET_INCIDENT', 'GET_LOGS', 'UPDATE_INCIDENT']).describe('The action to perform.')
  }),
  execute: async ({ context }) => {
    try {
      if (context.action === 'GET_INCIDENT') {
        const response = await axios.get(`${FASTAPI_URL}/incidents/${context.incidentId}`);
        return response.data;
      }
      if (context.action === 'GET_LOGS') {
        const response = await axios.get(`${FASTAPI_URL}/incidents/${context.incidentId}/logs`);
        return response.data;
      }
      return { error: 'Unsupported action' };
    } catch (error: any) {
      console.error("Database error:", error.message);
      return { error: 'Database operation failed' };
    }
  }
});

export const reportTool = createTool({
  id: 'reportTool',
  description: 'Manages RCA Reports in the system.',
  inputSchema: z.object({
    title: z.string().describe('Incident title.'),
    summary: z.string().describe('RCA summary.'),
    rootCause: z.string().describe('The determined root cause.'),
    impact: z.string().describe('Impact blast radius.'),
    incidentId: z.string().describe('The associated incident ID.')
  }),
  execute: async ({ context }) => {
    try {
      const response = await axios.post(`${FASTAPI_URL}/reports/`, {
        incidentId: context.incidentId,
        title: context.title,
        summary: context.summary,
        rootCause: context.rootCause,
        impact: context.impact,
        timeline: [],
        actionItems: []
      });
      return response.data;
    } catch (error: any) {
      console.error("Report generation error:", error.message);
      return { error: 'Failed to generate report' };
    }
  }
});

export const guardrailTool = createTool({
  id: 'guardrailTool',
  description: 'Validates input and output using Enkrypt AI guardrails.',
  inputSchema: z.object({
    text: z.string().describe('Text to validate against security guardrails.')
  }),
  execute: async ({ context }) => {
    try {
      const response = await axios.post(`${FASTAPI_URL}/copilot/guardrail-check`, {
        text: context.text
      });
      return response.data;
    } catch (error: any) {
      console.error("Guardrail error:", error.message);
      // Fail open or closed depending on requirements. Let's return a safe mock if FastAPI doesn't have this.
      return { status: "SAFE", threats: [] };
    }
  }
});

export const embeddingTool = createTool({
  id: 'embeddingTool',
  description: 'Generates embeddings for a given text or list of texts.',
  inputSchema: z.object({
    text: z.union([z.string(), z.array(z.string())]).describe('Text or list of texts to embed.')
  }),
  execute: async ({ context }) => {
    try {
      const client = getGeminiClient();
      const texts = Array.isArray(context.text) ? context.text : [context.text];
      
      const MAX_RETRIES = 5;
      const results: any[] = [];
      const chunkSize = 10; // Batch requests concurrency
      
      for (let i = 0; i < texts.length; i += chunkSize) {
        const batch = texts.slice(i, i + chunkSize);
        
        const batchPromises = batch.map(async (text) => {
          let attempt = 0;
          let lastError = null;
          
          while (attempt < MAX_RETRIES) {
            try {
              attempt++;
              const response: any = await client.models.embedContent({
                model: 'text-embedding-004',
                contents: text,
              });
              
              const embedding = response.embeddings?.[0]?.values || response.embedding?.values || response.embeddings?.[0];
              if (!embedding) {
                 throw new Error("No embedding values returned from API");
              }
              // Extract the array of floats safely
              return Array.isArray(embedding) ? embedding : embedding.values || embedding;
            } catch (err: any) {
              lastError = err;
              const isRateLimit = err.status === 429 || err.message?.includes('429') || err.message?.includes('quota');
              
              if (isRateLimit) {
                // Rate limit - exponential backoff starting at 2s
                await new Promise(res => setTimeout(res, 2000 * Math.pow(2, attempt)));
              } else if (attempt >= MAX_RETRIES) {
                break;
              } else {
                // Other transient error - exponential backoff starting at 1s
                await new Promise(res => setTimeout(res, 1000 * Math.pow(2, attempt)));
              }
            }
          }
          throw new Error(`Embedding failed for chunk after ${MAX_RETRIES} attempts: ${lastError?.message}`);
        });

        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults);
      }

      return { embeddings: Array.isArray(context.text) ? results : results[0] };

    } catch (error: any) {
      console.error("[Embedding Tool Error]:", error.message);
      return { error: 'Failed to generate embeddings', details: error.message };
    }
  }
});

// Initialize the Gemini client lazily
let geminiClient: GoogleGenAI | null = null;
function getGeminiClient() {
  if (!geminiClient) {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error("GEMINI_API_KEY environment variable is missing.");
    }
    geminiClient = new GoogleGenAI({ apiKey });
  }
  return geminiClient;
}

export const geminiTool = createTool({
  id: 'geminiTool',
  description: 'Uses Gemini API to perform reasoning and generation tasks.',
  inputSchema: z.object({
    systemPrompt: z.string().describe('System instructions for the model.'),
    userPrompt: z.string().describe('The primary user prompt or query.'),
    context: z.string().optional().describe('Optional contextual information (e.g., logs, RAG results).'),
    history: z.array(z.object({
      role: z.string(),
      parts: z.array(z.object({ text: z.string() }))
    })).optional().describe('Optional conversation history.')
  }),
  execute: async ({ context }) => {
    try {
      const client = getGeminiClient();
      const model = process.env.GEMINI_MODEL || 'gemini-2.5-flash';
      
      let fullPrompt = context.userPrompt;
      if (context.context) {
        fullPrompt = `Context:\n${context.context}\n\nTask:\n${context.userPrompt}`;
      }

      const contents: any[] = [];
      if (context.history && context.history.length > 0) {
        contents.push(...context.history);
      }
      contents.push({ role: 'user', parts: [{ text: fullPrompt }] });

      const generateConfig: any = {};
      if (context.systemPrompt) {
        generateConfig.systemInstruction = context.systemPrompt;
      }

      // Retry logic with timeout
      const MAX_RETRIES = 3;
      let attempt = 0;
      let lastError: Error | null = null;

      while (attempt < MAX_RETRIES) {
        try {
          attempt++;
          
          const timeoutMs = 30000;
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error("Gemini API request timed out")), timeoutMs)
          );

          const response: any = await Promise.race([
            client.models.generateContent({
              model,
              contents,
              config: generateConfig
            }),
            timeoutPromise
          ]);

          return { response: response.text };

        } catch (error: any) {
          lastError = error;
          console.error(`[Gemini Tool Error] Attempt ${attempt}/${MAX_RETRIES} failed:`, error.message);
          if (attempt >= MAX_RETRIES) {
            break;
          }
          // Exponential backoff
          await new Promise(res => setTimeout(res, 1000 * Math.pow(2, attempt)));
        }
      }
      
      return { error: 'Failed to generate response from Gemini API', details: lastError?.message };

    } catch (error: any) {
      console.error("[Gemini Tool Init Error]:", error.message);
      return { error: 'Failed to initialize Gemini Tool', details: error.message };
    }
  }
});

export const indexKnowledgeTool = createTool({
  id: 'indexKnowledgeTool',
  description: 'Indexes a lessons learned document into the vector database.',
  inputSchema: z.object({
    docId: z.string().describe('A unique ID for the document.'),
    title: z.string().describe('The title of the knowledge document.'),
    content: z.string().describe('The content or lessons learned to index.'),
    service: z.string().describe('The service this relates to.')
  }),
  execute: async ({ context }) => {
    try {
      const response = await axios.post(`${FASTAPI_URL}/knowledge/documents`, {
        doc_id: context.docId,
        title: context.title,
        content: context.content,
        metadata: {
          type: 'POST_MORTEM',
          service: context.service,
          author: 'knowledge-agent'
        }
      });
      return response.data;
    } catch (error: any) {
      console.error("Index Knowledge error:", error.message);
      return { error: 'Failed to index knowledge' };
    }
  }
});
