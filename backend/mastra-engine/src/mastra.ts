import { generateText, tool } from 'ai';

export class WorkflowContext {
  sharedMemory: Record<string, any> = {};
  reasoningHistory: string[] = [];
  traceData: Array<{
    step: string;
    durationMs: number;
    inputs: any;
    outputs: any;
    toolCalls: any[];
    errors: string | null;
  }> = [];

  appendReasoning(agentName: string, text: string) {
    this.reasoningHistory.push(`[${agentName}]: ${text}`);
  }
}

export class Agent {
  config: any;
  constructor(config: any) {
    this.config = config;
  }

  async generate(prompt: string, contextObj: any = {}) {
    const aiTools: Record<string, any> = {};
    if (this.config.tools) {
      for (const [key, t] of Object.entries(this.config.tools)) {
        const anyTool: any = t;
         aiTools[key] = tool({
           description: anyTool.description,
           parameters: anyTool.inputSchema,
           execute: async (args) => await anyTool.execute({ context: { ...args, ...contextObj } })
         });
      }
    }
    
    let systemInstruction = this.config.instructions;
    
    if (contextObj.workflowContext && contextObj.workflowContext.reasoningHistory.length > 0) {
       systemInstruction += "\n\n### Shared Reasoning History ###\n" + contextObj.workflowContext.reasoningHistory.join("\n");
    }

    const startTime = Date.now();
    try {
      const response = await generateText({
        model: this.config.model,
        system: systemInstruction,
        prompt: prompt,
        tools: aiTools,
        maxSteps: 5
      });

      const durationMs = Date.now() - startTime;
      const allToolCalls = response.steps?.flatMap(s => s.toolCalls) || [];

      // Append to shared reasoning
      if (contextObj.workflowContext) {
         contextObj.workflowContext.appendReasoning(this.config.name, response.text);
      }

      return { 
        text: response.text, 
        toolCalls: allToolCalls,
        durationMs,
        error: null
      };
    } catch (e: any) {
      const durationMs = Date.now() - startTime;
      return {
        text: "",
        toolCalls: [],
        durationMs,
        error: e.message
      }
    }
  }
}

export function createTool(config: any) {
  return config;
}

export class Step {
  id: string;
  executeFn: any;
  constructor(config: any) {
    this.id = config.id;
    this.executeFn = config.execute;
  }
  async execute(params: any) {
    return this.executeFn(params);
  }
}

export class Workflow {
  name: string;
  steps: Step[] = [];
  triggerSchema: any;
  
  constructor(config: any) {
    this.name = config.name;
    this.triggerSchema = config.triggerSchema;
  }
  
  step(s: Step) {
    this.steps.push(s);
    return this;
  }
  
  then(s: Step) {
    this.steps.push(s);
    return this;
  }
  
  commit() {}
  
  async execute(initialContext: any) {
    const workflowContext = new WorkflowContext();
    let currentContext = { ...initialContext, workflowContext };
    
    for (const s of this.steps) {
        const startTime = Date.now();
        let error: string | null = null;
        let outputs: any = null;
        
        try {
           const result = await s.execute({ context: currentContext });
           outputs = result;
           if (s.id === 'triage') {
                currentContext = { triage: result, workflowContext };
           } else if (s.id === 'diagnosis') {
                currentContext = { diagnosis: result, workflowContext };
           } else if (s.id === 'knowledgeRetrieval') {
                currentContext = { knowledgeRetrieval: result, workflowContext };
           } else if (s.id === 'recommendation') {
                currentContext = { recommendation: result, workflowContext };
           } else if (s.id === 'report') {
                currentContext = { report: result, workflowContext };
           } else if (s.id === 'knowledge') {
                currentContext = { knowledge: result, workflowContext };
           }
        } catch (e: any) {
           error = e.message;
           throw e;
        } finally {
           const durationMs = Date.now() - startTime;
           workflowContext.traceData.push({
             step: s.id,
             durationMs,
             inputs: currentContext,
             outputs,
             toolCalls: outputs?.toolCalls || [],
             errors: error
           });
        }
    }
  }
}
