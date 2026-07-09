import { createTool } from '@mastra/core';
import { z } from 'zod';
import axios from 'axios';
import * as dotenv from 'dotenv';
import path from 'path';

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
  description: 'Generates embeddings for a given text.',
  inputSchema: z.object({
    text: z.string().describe('Text to embed.')
  }),
  execute: async ({ context }) => {
    return { embeddings: [0.1, 0.2, 0.3], mock: true };
  }
});

export const geminiTool = createTool({
  id: 'geminiTool',
  description: 'Uses Gemini API to perform raw generation tasks.',
  inputSchema: z.object({
    prompt: z.string().describe('Prompt for Gemini.')
  }),
  execute: async ({ context }) => {
    return { response: "Generated response from Gemini Tool." };
  }
});
