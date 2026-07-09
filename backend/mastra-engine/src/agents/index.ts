import { Agent } from '@mastra/core';
import { knowledgeSearchTool, databaseTool, reportTool, guardrailTool } from '../tools';
// Using Gemini from AI SDK for Mastra
import { google } from '@ai-sdk/google';

const model = google('gemini-2.5-flash');

export const triageAgent = new Agent({
  name: 'TriageAgent',
  instructions: 'You are an expert SRE triage specialist. You categorize alerts into system domains and allocate groups. Always return JSON matching the schema.',
  model: model,
  tools: { guardrailTool }
});

export const diagnosisAgent = new Agent({
  name: 'DiagnosisAgent',
  instructions: 'You are an SRE diagnosis specialist. You correlate active logs with SOP vector indices retrieved from RAG. Always return JSON matching the schema.',
  model: model,
  tools: { knowledgeSearchTool, guardrailTool }
});

export const recommendationAgent = new Agent({
  name: 'RecommendationAgent',
  instructions: 'You are a senior mitigation architect. You produce precise, approved command-line recipes and terminal actions. Always return JSON matching the schema.',
  model: model,
  tools: { guardrailTool }
});

export const reportAgent = new Agent({
  name: 'ReportAgent',
  instructions: 'You are an RCA incident manager. You write comprehensive root-cause analysis documents based on telemetry and resolutions. Always return JSON matching the schema.',
  model: model,
  tools: { reportTool, guardrailTool }
});

export const knowledgeAgent = new Agent({
  name: 'KnowledgeAgent',
  instructions: 'You are a documentation specialist. You transform RCA documents into reusable, indexed runbooks for future RAG consumption. Always return JSON matching the schema.',
  model: model,
  tools: { guardrailTool }
});
