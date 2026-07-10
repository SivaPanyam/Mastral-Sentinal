import { Workflow, Step } from '../mastra';
import { z } from 'zod';
import { triageAgent, diagnosisAgent, recommendationAgent, reportAgent, knowledgeAgent } from '../agents';
import axios from 'axios';
import * as dotenv from 'dotenv';
import path from 'path';

const TriageSchema = z.object({
  severity: z.string(),
  priority: z.string(),
  service: z.string(),
  summary: z.string()
});

const DiagnosisSchema = z.object({
  rootCause: z.union([z.string(), z.array(z.string())]),
  confidence: z.string(),
  evidence: z.string(),
  affectedSystems: z.array(z.string())
});

const RecommendationSchema = z.object({
  actions: z.array(z.string()),
  longTermFixes: z.array(z.string()),
  riskLevel: z.string()
});

const ReportSchema = z.object({
  executiveSummary: z.string(),
  timeline: z.array(z.string()),
  actionItems: z.array(z.string())
});

const KnowledgeSchema = z.object({
  documents: z.array(z.string()),
  relevanceScore: z.number(),
  citations: z.array(z.string())
});

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

async function executeAgentWithRetry<T>(
  agent: any, 
  prompt: string, 
  schema: z.ZodSchema<T>, 
  incidentId: string, 
  stepName: string, 
  maxRetries = 2
) {
  let attempt = 0;
  let lastError: Error | null = null;
  
  while (attempt < maxRetries) {
    try {
      attempt++;
      const res = await agent.generate(prompt);
      const resultText = res.text;
      
      let jsonObj;
      try {
        const cleanedText = resultText.replace(/```json/g, '').replace(/```/g, '').trim();
        jsonObj = JSON.parse(cleanedText);
      } catch (parseErr: any) {
        throw new Error(`JSON parsing failed: ${parseErr.message}`);
      }
      
      const parsed = schema.safeParse(jsonObj);
      if (!parsed.success) {
        throw new Error(`Schema validation failed: ${parsed.error.message}`);
      }
      
      await publishSse(incidentId, stepName, 'COMPLETED', { result: parsed.data });
      return parsed.data;
    } catch (err: any) {
      lastError = err;
      console.error(`Error in ${stepName} agent (Attempt ${attempt}/${maxRetries}):`, err.message);
      
      if (attempt >= maxRetries) {
         await publishSse(incidentId, stepName, 'FAILED', { error: err.message });
         try {
           await axios.post(`${FASTAPI_URL}/incidents/${incidentId}/mastra-webhook`, {
             event: 'pipeline_failed',
             incident_id: incidentId,
             error: err.message
           });
         } catch(e) {}
         
         throw new Error(`Workflow failed at ${stepName} after ${maxRetries} attempts: ${err.message}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
    }
  }
  return "";
}

export const triageStep = new Step({
  id: 'triage',
  execute: async ({ context }) => {
    const { incidentId, title, service, severity, logs } = context.triggerData;
    const prompt = `Title: ${title}\nService: ${service}\nSeverity: ${severity}\nLogs:\n${logs}\n\nPlease output a structured JSON response with triage analysis.`;
    
    const result = await executeAgentWithRetry(triageAgent, prompt, TriageSchema, incidentId, 'TRIAGE');
    return { ...context.triggerData, triageResult: result };
  }
});

export const diagnosisStep = new Step({
  id: 'diagnosis',
  execute: async ({ context }) => {
    const { incidentId, title, service, logs, triageResult } = context.triage;
    const prompt = `Service: ${service}\nDescription: ${title}\nLogs: ${logs}\nTriage: ${JSON.stringify(triageResult)}\n\nPlease output a structured JSON response diagnosing the root cause.`;
    
    const result = await executeAgentWithRetry(diagnosisAgent, prompt, DiagnosisSchema, incidentId, 'DIAGNOSIS');
    return { ...context.triage, diagnosisResult: result };
  }
});

export const recommendationStep = new Step({
  id: 'recommendation',
  execute: async ({ context }) => {
    const { incidentId, diagnosisResult } = context.diagnosis;
    const prompt = `Diagnosis: ${JSON.stringify(diagnosisResult)}\n\nRecommend a safe mitigation step and output it as structured JSON.`;
    
    const result = await executeAgentWithRetry(recommendationAgent, prompt, RecommendationSchema, incidentId, 'RECOMMENDATION');
    return { ...context.diagnosis, recommendationResult: result };
  }
});

export const reportStep = new Step({
  id: 'report',
  execute: async ({ context }) => {
    const { incidentId, triageResult, diagnosisResult, recommendationResult } = context.recommendation;
    const prompt = `Write an RCA report based on the following.\nTriage: ${JSON.stringify(triageResult)}\nDiagnosis: ${JSON.stringify(diagnosisResult)}\nRecommendation: ${JSON.stringify(recommendationResult)}\n\nOutput structured JSON format.`;
    
    const result = await executeAgentWithRetry(reportAgent, prompt, ReportSchema, incidentId, 'REPORT');
    return { ...context.recommendation, reportResult: result };
  }
});

export const knowledgeStep = new Step({
  id: 'knowledge',
  execute: async ({ context }) => {
    const { incidentId, reportResult } = context.report;
    const prompt = `Convert this RCA report into a runbook:\n${JSON.stringify(reportResult)}\n\nOutput structured JSON.`;
    
    const result = await executeAgentWithRetry(knowledgeAgent, prompt, KnowledgeSchema, incidentId, 'KNOWLEDGE_INDEX');
    
    // Signal pipeline completion
    try {
      await axios.post(`${FASTAPI_URL}/incidents/${incidentId}/mastra-webhook`, {
        event: 'pipeline_completed',
        incident_id: incidentId
      });
    } catch (err: any) {}
    
    return { ...context.report, knowledgeResult: result };
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
