/**
 * useOpalAgent - React Hook for Google Opal Research Agent
 * 
 * Sends research queries to Google Opal webhook, which:
 * 1. Uses @search to find relevant information
 * 2. Forwards to local Ollama (via Ngrok) for summarization
 * 3. Returns structured JSON for 3D card generation
 */

import { useState, useCallback } from 'react';
import useStore from '../store/useStore';
import socketManager from '../services/socketManager';

// Fallback: Direct Ollama call (for testing without backend)
const OLLAMA_DIRECT_URL = 'http://localhost:11434/api/generate';

/**
 * Research result from Opal/Ollama
 * @typedef {Object} ResearchResult
 * @property {string} title - Short descriptive title
 * @property {string} summary - Research summary
 * @property {number} complexity_score - 0-100 complexity rating
 */

/**
 * Hook state
 * @typedef {Object} UseOpalAgentState
 * @property {boolean} loading - Query in progress
 * @property {string|null} error - Error message if any
 * @property {ResearchResult|null} result - Latest research result
 * @property {ResearchResult[]} history - All research results
 */

export function useOpalAgent() {
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const addThought = useStore((state) => state.addThought);
    const researchLoading = useStore((state) => state.researchLoading);
    const setResearchLoading = useStore((state) => state.setResearchLoading);

    /**
     * Send a research query to Google Opal
     * @param {string} query - The research question
     * @returns {Promise<ResearchResult|null>}
     */
    const sendQuery = useCallback(async (query) => {
        if (!query?.trim()) {
            setError('Query cannot be empty');
            return null;
        }

        setResearchLoading(true);
        setError(null);
        addThought({ text: `🔍 Researching: ${query}`, type: 'action' });

        try {
            const instruction = `RESEARCH TASK: Research "${query}". 1. Use web_search to find information. 2. Use web_scrape on the best results to get detailed content. 3. Use write_research_document to create a formatted document with all findings organized into sections with headings, including source URLs.`;

            socketManager.sendCommand(instruction, true);

            // Research doc will auto-open in browser when tool executes
            setTimeout(() => setResearchLoading(false), 30000); // timeout fallback
            return { success: true };

        } catch (err) {
            const errorMsg = err.message || 'Research query failed';
            setError(errorMsg);
            setResearchLoading(false);
            addThought({ text: `❌ Research startup error: ${errorMsg}`, type: 'error' });
            return null;
        }
    }, [addThought, setResearchLoading]);

    /**
     * Clear the current result and error
     */
    const clearResult = useCallback(() => {
        setResult(null);
        setError(null);
    }, []);

    return {
        // State
        loading: researchLoading,
        error,
        result,

        // Actions
        sendQuery,
        clearResult,

        // Computed
        isHighComplexity: result?.complexity_score > 80,
    };
}

export default useOpalAgent;
