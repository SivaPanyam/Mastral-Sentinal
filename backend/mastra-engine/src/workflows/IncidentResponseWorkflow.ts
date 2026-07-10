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
  riskLevel: z.string(),
  rank: z.number().optional(),
  rollbackPlans: z.array(z.string()).optional(),
  preventiveActions: z.array(z.string()).optional()
});

const ReportSchema = z.object({
  executiveSummary: z.string(),
  timeline: z.array(z.string()),
  actionItems: z.array(z.string())
});

const KnowledgeSchema = z.object({
  documents: z.array(z.string()),
  lessonsLearned: z.string().optional(),
  relevanceScore: z.number(),
  citations: z.array(z.string())
});

const KnowledgeRetrievalSchema = z.object({
  retrievedRunbooks: z.array(z.string()),
  qdrantContext: z.string()
});

dotenv.config({ path: path.resolve(__dirname, '../../../../.env') });
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000/api/v1';

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
  contextObj: any,
  maxRetries = 2
) {
  let attempt = 0;
  
  while (attempt < maxRetries) {
    try {
      attempt++;
      const res = await agent.generate(prompt, contextObj);
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
      
      const dataWithTrace = { ...parsed.data, _durationMs: res.durationMs, _toolCalls: res.toolCalls };
      await publishSse(incidentId, stepName, 'COMPLETED', { result: dataWithTrace });
      
      // Update shared memory
      if (contextObj.workflowContext) {
          contextObj.workflowContext.sharedMemory[stepName] = parsed.data;
      }

      return parsed.data;
    } catch (err: any) {
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
    const { incidentId, title, service, severity, logs, metadata, historical_incidents } = context.triggerData;
    const prompt = `Title: ${title}\nService: ${service}\nSeverity: ${severity}\nLogs:\n${logs}\nMetadata:\n${JSON.stringify(metadata)}\nHistorical Incidents:\n${JSON.stringify(historical_incidents)}\n\nPlease output a structured JSON response with triage analysis.`;
    
    const result = await executeAgentWithRetry(triageAgent, prompt, TriageSchema, incidentId, 'TRIAGE', context);
    return { ...context.triggerData, triageResult: result };
  }
});

export const diagnosisStep = new Step({
  id: 'diagnosis',
  execute: async ({ context }) => {
    const { incidentId, title, service, logs, metadata, historical_incidents, triageResult } = context.triage;
    
    // REQUIREMENT: Diagnosis Agent should retrieve: Logs, Metrics, Historical incidents, Similar incidents, Runbooks, SOPs, Policies, Knowledge Base BEFORE asking the LLM.
    let preRetrievedKnowledge = "";
    try {
        const query = `${service} ${title} ${triageResult?.summary || ""}`;
        const response = await axios.get(`${FASTAPI_URL}/knowledge/search`, {
          params: { query, limit: 3 }
        });
        preRetrievedKnowledge = JSON.stringify(response.data);
    } catch(e) {
        preRetrievedKnowledge = "Failed to retrieve from Qdrant.";
    }

    const prompt = `Service: ${service}\nDescription: ${title}\nLogs: ${logs}\nMetadata: ${JSON.stringify(metadata)}\nHistorical Incidents: ${JSON.stringify(historical_incidents)}\nTriage: ${JSON.stringify(triageResult)}\n\nPRE-RETRIEVED KNOWLEDGE (SOPs, Policies, Similar Incidents):\n${preRetrievedKnowledge}\n\nPlease output a structured JSON response diagnosing the root cause.`;
    
    const result = await executeAgentWithRetry(diagnosisAgent, prompt, DiagnosisSchema, incidentId, 'DIAGNOSIS', context);
    return { ...context.triage, diagnosisResult: result };
  }
});

export const knowledgeRetrievalStep = new Step({
  id: 'knowledgeRetrieval',
  execute: async ({ context }) => {
    const { incidentId, title, service, logs, metadata, historical_incidents, triageResult, diagnosisResult } = context.diagnosis;
    const query = `Service: ${service}, Root Cause: ${diagnosisResult.rootCause}`;
    
    try {
      const response = await axios.get(`${FASTAPI_URL}/knowledge/search`, {
        params: { query, limit: 3 }
      });
      const qdrantContext = JSON.stringify(response.data);
      const retrievedRunbooks = Array.isArray(response.data) ? response.data.map((d: any) => d.title || d.id) : [];
      
      const result = { retrievedRunbooks, qdrantContext };
      await publishSse(incidentId, 'KNOWLEDGE_RETRIEVAL', 'COMPLETED', { result });
      return { ...context.diagnosis, knowledgeRetrievalResult: result };
    } catch (err: any) {
      const result = { retrievedRunbooks: [], qdrantContext: "" };
      await publishSse(incidentId, 'KNOWLEDGE_RETRIEVAL', 'FAILED', { error: err.message });
      return { ...context.diagnosis, knowledgeRetrievalResult: result };
    }
  }
});

export const recommendationStep = new Step({
  id: 'recommendation',
  execute: async ({ context }) => {
    const { incidentId, title, service, logs, metadata, historical_incidents, triageResult, diagnosisResult, knowledgeRetrievalResult } = context.knowledgeRetrieval;
    const prompt = `Diagnosis: ${JSON.stringify(diagnosisResult)}\nRetrieved Runbooks: ${JSON.stringify(knowledgeRetrievalResult)}\nHistorical Incidents: ${JSON.stringify(historical_incidents)}\n\nRecommend a safe mitigation step and output it as structured JSON including rank, confidence, riskLevel, rollbackPlans, and preventiveActions.`;
    
    const result = await executeAgentWithRetry(recommendationAgent, prompt, RecommendationSchema, incidentId, 'RECOMMENDATION', context);
    return { ...context.knowledgeRetrieval, recommendationResult: result };
  }
});

export const reportStep = new Step({
  id: 'report',
  execute: async ({ context }) => {
    const { incidentId, triageResult, diagnosisResult, recommendationResult, knowledgeRetrievalResult } = context.recommendation;
    const prompt = `Write an RCA report based on the following.\nTriage: ${JSON.stringify(triageResult)}\nDiagnosis: ${JSON.stringify(diagnosisResult)}\nRunbooks Referenced: ${JSON.stringify(knowledgeRetrievalResult.retrievedRunbooks)}\nRecommendation: ${JSON.stringify(recommendationResult)}\n\nOutput structured JSON format.`;
    
    const result = await executeAgentWithRetry(reportAgent, prompt, ReportSchema, incidentId, 'REPORT', context);
    return { ...context.recommendation, reportResult: result };
  }
});

export const knowledgeStep = new Step({
  id: 'knowledge',
  execute: async ({ context }) => {
    const { incidentId, triageResult, diagnosisResult, recommendationResult, knowledgeRetrievalResult, reportResult } = context.report;
    const prompt = `Extract lessons learned and create a knowledge document from this incident.\n\nFull Context:\nTriage: ${JSON.stringify(triageResult)}\nDiagnosis: ${JSON.stringify(diagnosisResult)}\nRecommendation: ${JSON.stringify(recommendationResult)}\nRCA Report: ${JSON.stringify(reportResult)}\n\nOutput structured JSON containing 'documents', 'lessonsLearned', 'relevanceScore', and 'citations'.`;
    
    const result = await executeAgentWithRetry(knowledgeAgent, prompt, KnowledgeSchema, incidentId, 'KNOWLEDGE_INDEX', context);
    
    // Signal pipeline completion and push trace data
    try {
      await axios.post(`${FASTAPI_URL}/incidents/${incidentId}/mastra-webhook`, {
        event: 'pipeline_completed',
        incident_id: incidentId,
        data: {
          traceData: context.workflowContext?.traceData || []
        }
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
    logs: z.string(),
    metadata: z.record(z.any()).optional(),
    historical_incidents: z.array(z.any()).optional()
  })
});

incidentResponseWorkflow
  .step(triageStep)
  .then(diagnosisStep)
  .then(knowledgeRetrievalStep)
  .then(recommendationStep)
  .then(reportStep)
  .then(knowledgeStep)
  .commit();
