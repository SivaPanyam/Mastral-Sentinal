import { Workflow, Step } from '@mastra/core';
import { z } from 'zod';
import { triageAgent, diagnosisAgent, recommendationAgent, reportAgent, knowledgeAgent } from '../agents';
import axios from 'axios';
import * as dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../../../.env') });
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000/api/v1';

// Helper to push SSE events to FastAPI
async function publishSse(incidentId: string, stepName: string, status: string, data: any) {
  try {
    await axios.post(`${FASTAPI_URL}/incidents/${incidentId}/mastra-webhook`, {
      event: 'step_completed',
      incident_id: incidentId,
      step: stepName,
      status,
      data
    });
  } catch (err: any) {
    console.error(`Failed to push SSE for ${stepName}:`, err.message);
  }
}

export const triageStep = new Step({
  id: 'triage',
  execute: async ({ context, suspend }) => {
    const { incidentId, title, service, severity, logs } = context.triggerData;
    const prompt = `Title: ${title}\nService: ${service}\nSeverity: ${severity}\nLogs:\n${logs}`;
    
    // We can define structured output schemas if needed using Zod.
    const res = await triageAgent.generate(prompt);
    
    await publishSse(incidentId, 'TRIAGE', 'COMPLETED', { result: res.text });
    return { ...context.triggerData, triageResult: res.text };
  }
});

export const diagnosisStep = new Step({
  id: 'diagnosis',
  execute: async ({ context }) => {
    const { incidentId, title, service, logs, triageResult } = context.triage;
    const prompt = `Service: ${service}\nDescription: ${title}\nLogs: ${logs}\nTriage: ${triageResult}`;
    
    const res = await diagnosisAgent.generate(prompt);
    
    await publishSse(incidentId, 'DIAGNOSIS', 'COMPLETED', { result: res.text });
    return { ...context.triage, diagnosisResult: res.text };
  }
});

export const recommendationStep = new Step({
  id: 'recommendation',
  execute: async ({ context }) => {
    const { incidentId, diagnosisResult } = context.diagnosis;
    const prompt = `Diagnosis: ${diagnosisResult}\nRecommend a safe mitigation step.`;
    
    const res = await recommendationAgent.generate(prompt);
    
    await publishSse(incidentId, 'RECOMMENDATION', 'COMPLETED', { result: res.text });
    return { ...context.diagnosis, recommendationResult: res.text };
  }
});

export const reportStep = new Step({
  id: 'report',
  execute: async ({ context }) => {
    const { incidentId, triageResult, diagnosisResult, recommendationResult } = context.recommendation;
    const prompt = `Write an RCA report.\nTriage: ${triageResult}\nDiagnosis: ${diagnosisResult}\nRecommendation: ${recommendationResult}`;
    
    const res = await reportAgent.generate(prompt);
    
    await publishSse(incidentId, 'REPORT', 'COMPLETED', { result: res.text });
    return { ...context.recommendation, reportResult: res.text };
  }
});

export const knowledgeStep = new Step({
  id: 'knowledge',
  execute: async ({ context }) => {
    const { incidentId, reportResult } = context.report;
    const prompt = `Convert this RCA report into a runbook:\n${reportResult}`;
    
    const res = await knowledgeAgent.generate(prompt);
    
    await publishSse(incidentId, 'KNOWLEDGE_INDEX', 'COMPLETED', { result: res.text });
    
    // Signal pipeline completion
    try {
      await axios.post(`${FASTAPI_URL}/incidents/${incidentId}/mastra-webhook`, {
        event: 'pipeline_completed',
        incident_id: incidentId
      });
    } catch (err: any) {}
    
    return { ...context.report, knowledgeResult: res.text };
  }
});

export const incidentResponseWorkflow = new Workflow({
  name: 'IncidentResponseWorkflow',
  triggerSchema: z.object({
    incidentId: z.string(),
    title: z.string(),
    service: z.string(),
    severity: z.string(),
    logs: z.string()
  })
});

incidentResponseWorkflow
  .step(triageStep)
  .then(diagnosisStep)
  .then(recommendationStep)
  .then(reportStep)
  .then(knowledgeStep)
  .commit();
