# Mastra Sentinel Testing Strategies

This document defines testing guidelines for both backend python and frontend React modules to maintain absolute stability under pressure.

## 1. Backend API & Agent Testing

The Python backend is tested using **pytest** and **httpx** for API clients.

### Unit Testing Runbook Matches
Under `/backend/tests/test_agents.py`, SRE engineers can test individual model responses:

```python
import pytest
from app.mastra.agents import triage_agent

def test_triage_classification():
    prompt = "Triage this checkout timeout with latency exceeding 12000ms."
    result = triage_agent.run(prompt)
    assert "classification" in result
    assert result["confidence"] > 0.80
```

### Mocking External Connections
We implement robust mocking wrappers for the Google Gemini and Qdrant APIs to support offline CI pipelines:

* **Gemini Mocking**: Simulated outputs based on prompt keywords (located in `MastraAgent._fallback_run`).
* **Qdrant Mocking**: Lightweight in-memory caches which store similarity vectors and search using exact numpy operations (located in `QdrantRagManager.local_cache`).

---

## 2. Frontend React Component Testing

The React client is tested using **Vitest** and **React Testing Library**.

### Component Unit Testing Example
Testing dashboard status gauges:

```typescript
import { render, screen } from '@testing-library/react';
import { AgentStatusCard } from '../components/AgentStatusCard';

test('renders agent cards correctly', () => {
  render(<AgentStatusCard runs={[]} isRunningAgent={false} />);
  expect(screen.getByText('Triage Agent')).toBeInTheDocument();
});
```
