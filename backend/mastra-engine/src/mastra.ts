import { GoogleGenAI } from '@google/genai';

export class Agent {
  config: any;
  constructor(config: any) {
    this.config = config;
  }
  async generate(prompt: string) {
    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
      config: { systemInstruction: this.config.instructions }
    });
    return { text: response.text };
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
  steps: Step[] = [];
  constructor(config: any) {}
  
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
    let currentContext = { ...initialContext };
    for (const s of this.steps) {
        const result = await s.execute({ context: currentContext });
        if (s.id === 'triage') {
             currentContext = { triage: result };
        } else if (s.id === 'diagnosis') {
             currentContext = { diagnosis: result };
        } else if (s.id === 'recommendation') {
             currentContext = { recommendation: result };
        } else if (s.id === 'report') {
             currentContext = { report: result };
        } else if (s.id === 'knowledge') {
             currentContext = { knowledge: result };
        }
    }
  }
}
