import { Agent } from '../mastra';
import { knowledgeSearchTool, databaseTool, reportTool, guardrailTool } from '../tools';
// Using Gemini from AI SDK for Mastra
import { google } from '@ai-sdk/google';
import {
  buildAgentInstructions,
  TriagePrompt,
  DiagnosisPrompt,
  RecommendationPrompt,
  ReportPrompt,
  KnowledgePrompt
} from '../prompts';

const model = google('gemini-2.5-flash');

export const triageAgent = new Agent({
  name: 'TriageAgent',
  instructions: buildAgentInstructions(TriagePrompt),
  model: model,
  tools: { guardrailTool }
});

export const diagnosisAgent = new Agent({
  name: 'DiagnosisAgent',
  instructions: buildAgentInstructions(DiagnosisPrompt),
  model: model,
  tools: { knowledgeSearchTool, guardrailTool }
});

export const recommendationAgent = new Agent({
  name: 'RecommendationAgent',
  instructions: buildAgentInstructions(RecommendationPrompt),
  model: model,
  tools: { guardrailTool }
});

export const reportAgent = new Agent({
  name: 'ReportAgent',
  instructions: buildAgentInstructions(ReportPrompt),
  model: model,
  tools: { reportTool, guardrailTool }
});

export const knowledgeAgent = new Agent({
  name: 'KnowledgeAgent',
  instructions: buildAgentInstructions(KnowledgePrompt),
  model: model,
  tools: { guardrailTool }
});
