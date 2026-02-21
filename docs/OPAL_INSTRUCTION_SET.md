# Google Opal Instruction Set for NeuroSurf Research Agent

## Overview
This document contains the natural language prompt to paste into Google Opal to create the Research Agent workflow.

---

## Opal App Creation Prompt

Copy and paste the following into Google Opal's creation interface:

```
Create a Research Agent app with these capabilities:

## Input
Accept a webhook POST request with JSON body: { "query": "user's research question" }

## Workflow Steps

1. **Search the Web**
   Use @search to find relevant information about the user's query. 
   Get the top 3-5 results with summaries.

2. **Prepare Context**
   Combine the search results into a context string for the LLM.

3. **Call Local Ollama**
   Send a POST request to my local Ollama instance:
   
   URL: [PASTE YOUR NGROK URL HERE]/api/generate
   
   Headers: { "Content-Type": "application/json" }
   
   Body:
   {
     "model": "llama3",
     "prompt": "You are a research analyst. Based on the following search results, provide a structured research summary.\n\nSearch Results:\n[INSERT SEARCH RESULTS HERE]\n\nUser Query: [INSERT ORIGINAL QUERY]\n\nRespond ONLY in this exact JSON format, nothing else:\n{\"title\": \"Short descriptive title (max 10 words)\", \"summary\": \"Comprehensive 2-3 sentence summary of findings\", \"complexity_score\": 0-100}\n\nThe complexity_score should be:\n- 0-30: Simple, well-established facts\n- 31-60: Moderate complexity, some nuance\n- 61-80: Complex topic with multiple perspectives\n- 81-100: Highly complex, controversial, or cutting-edge research",
     "stream": false,
     "options": {
       "temperature": 0.7,
       "num_predict": 500
     }
   }

4. **Parse Response**
   Extract the JSON from Ollama's response field and return it.

## Output
Return the parsed JSON to the webhook caller:
{
  "title": "string",
  "summary": "string", 
  "complexity_score": number
}

## Error Handling
If any step fails, return: { "error": "description of what failed" }
```

---

## Setup Steps

### 1. Get Your Ngrok URL
Run this in your NeuroSurf project:
```batch
setup-ngrok.bat
```
Copy the forwarding URL (e.g., `https://abc123.ngrok-free.app`)

### 2. Create the Opal App
1. Go to Google Opal (labs.google.com/opal or similar)
2. Create a new app
3. Paste the instruction set above
4. Replace `[PASTE YOUR NGROK URL HERE]` with your actual Ngrok URL
5. Deploy and get your Opal webhook URL

### 3. Configure NeuroSurf
Set your Opal webhook URL in the frontend:
```javascript
// In src/hooks/useOpalAgent.js
const OPAL_WEBHOOK_URL = 'https://your-opal-app.web.app/webhook';
```

---

## Testing the Workflow

### Test Ollama Directly (via Ngrok)
```bash
curl -X POST https://YOUR_NGROK_URL/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "Say hello in JSON format: {\"message\": \"...\"}",
    "stream": false
  }'
```

### Test Opal Webhook
```bash
curl -X POST https://YOUR_OPAL_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"query": "What is quantum computing?"}'
```

Expected response:
```json
{
  "title": "Quantum Computing Fundamentals",
  "summary": "Quantum computing uses quantum mechanical phenomena...",
  "complexity_score": 65
}
```

---

## JSON Schema Reference

### Request Schema (to Opal)
```json
{
  "query": "string (user's research question)"
}
```

### Response Schema (from Opal)
```json
{
  "title": "string (max 100 chars)",
  "summary": "string (max 500 chars)",
  "complexity_score": "number (0-100)"
}
```

### Complexity Score Interpretation
| Score | Visual Effect | Description |
|-------|---------------|-------------|
| 0-30  | Normal | Simple, factual information |
| 31-60 | Subtle glow | Moderate complexity |
| 61-80 | Pulsing | Complex topic |
| 81-100 | **Glitch/Shake** | High complexity, controversial |
