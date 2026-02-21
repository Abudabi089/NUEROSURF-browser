import { create } from 'zustand';

export const AGENT_STATES = {
    IDLE: 'idle',
    PLANNING: 'planning',
    ACTING: 'acting',
    LISTENING: 'listening',
    ERROR: 'error'
};

export const STATE_COLORS = {
    [AGENT_STATES.IDLE]: '#00d4ff',      // Blue
    [AGENT_STATES.PLANNING]: '#ffd700',   // Gold
    [AGENT_STATES.ACTING]: '#ff3366',     // Red
    [AGENT_STATES.LISTENING]: '#9d4edd',  // Purple
    [AGENT_STATES.ERROR]: '#ff0000'       // Bright Red
};

const useStore = create((set, get) => ({
    isConnected: false,
    setConnected: (connected) => set({ isConnected: connected }),

    agentState: AGENT_STATES.IDLE,
    setAgentState: (state) => set({ agentState: state }),

    // View Mode (Browser vs 3D)
    viewMode: 'browser',
    setViewMode: (mode) => set((state) => ({
        viewMode: typeof mode === 'function' ? mode(state.viewMode) : mode
    })),

    // Multi-Threading Support
    activeThreadId: 'main',
    threads: [{ id: 'main', name: 'Main Neural Thread' }],
    thoughts: { 'main': [] },

    addThread: (name) => set((state) => {
        const id = `thread-${Date.now()}`;
        return {
            threads: [...state.threads, { id, name: name || `Thread ${state.threads.length + 1}` }],
            thoughts: { ...state.thoughts, [id]: [] },
            activeThreadId: id
        };
    }),

    switchThread: (id) => set({ activeThreadId: id }),

    removeThread: (id) => set((state) => {
        if (id === 'main') return state; // Can't remove main
        const newThreads = state.threads.filter(t => t.id !== id);
        const newActiveId = state.activeThreadId === id ? 'main' : state.activeThreadId;
        const newThoughts = { ...state.thoughts };
        delete newThoughts[id];
        return {
            threads: newThreads,
            activeThreadId: newActiveId,
            thoughts: newThoughts
        };
    }),

    addThought: (thought) => set((state) => {
        const threadId = thought.thread_id || state.activeThreadId;
        const threadThoughts = state.thoughts[threadId] || [];
        return {
            thoughts: {
                ...state.thoughts,
                [threadId]: [
                    { id: thought.id || Date.now(), text: thought.text, type: thought.type, timestamp: new Date() },
                    ...threadThoughts
                ].slice(0, 50)
            }
        };
    }),

    updateThought: (id, text, threadId) => set((state) => {
        const tid = threadId || state.activeThreadId;
        const threadThoughts = state.thoughts[tid] || [];
        return {
            thoughts: {
                ...state.thoughts,
                [tid]: threadThoughts.map(t =>
                    t.id === id ? { ...t, text: text } : t
                )
            }
        };
    }),

    // --- Multi-Tab Planetary System State ---

    // Active URL (Synced with Neuro)
    browserUrl: 'https://www.google.com',
    setBrowserUrl: (url) => set((state) => ({
        browserUrl: url,
        tabs: state.tabs.map(t => t.id === state.activeTabId ? { ...t, url } : t)
    })),

    // Tabs List
    tabs: [
        { id: 1, title: 'Google', url: 'https://www.google.com', active: true },
        { id: 2, title: 'YouTube', url: 'https://www.youtube.com', active: false },
        { id: 3, title: 'GitHub', url: 'https://github.com', active: false }
    ],
    activeTabId: 1,

    // Orbital Rotation (0 to 2PI)
    systemRotation: 0,
    setSystemRotation: (rad) => set({ systemRotation: rad }),
    orbitEnabled: true,
    setOrbitEnabled: (enabled) => set({ orbitEnabled: enabled }),

    // Tab Actions
    addTab: (url = 'https://www.google.com') => set((state) => {
        const newId = Date.now();
        const newTabs = [...state.tabs, { id: newId, title: 'New Tab', url, active: true }];
        return {
            tabs: newTabs.map(t => ({ ...t, active: t.id === newId })),
            activeTabId: newId,
            browserUrl: url
        };
    }),

    removeTab: (id) => set((state) => {
        if (state.tabs.length <= 1) return state;
        const newTabs = state.tabs.filter(t => t.id !== id);
        const newActiveId = state.activeTabId === id ? newTabs[0].id : state.activeTabId;
        const newUrl = newTabs.find(t => t.id === newActiveId)?.url || state.browserUrl;
        return {
            tabs: newTabs.map(t => ({ ...t, active: t.id === newActiveId })),
            activeTabId: newActiveId,
            browserUrl: newUrl
        };
    }),

    setActiveTab: (id) => set((state) => {
        const tab = state.tabs.find(t => t.id === id);
        return {
            tabs: state.tabs.map(t => ({ ...t, active: t.id === id })),
            activeTabId: id,
            browserUrl: tab?.url || state.browserUrl
        };
    }),

    nextTab: () => set((state) => {
        const currentIndex = state.tabs.findIndex(t => t.id === state.activeTabId);
        const nextIndex = (currentIndex + 1) % state.tabs.length;
        const nextTab = state.tabs[nextIndex];
        return {
            tabs: state.tabs.map(t => ({ ...t, active: t.id === nextTab.id })),
            activeTabId: nextTab.id,
            browserUrl: nextTab.url
        };
    }),

    prevTab: () => set((state) => {
        const currentIndex = state.tabs.findIndex(t => t.id === state.activeTabId);
        const prevIndex = (currentIndex - 1 + state.tabs.length) % state.tabs.length;
        const prevTab = state.tabs[prevIndex];
        return {
            tabs: state.tabs.map(t => ({ ...t, active: t.id === prevTab.id })),
            activeTabId: prevTab.id,
            browserUrl: prevTab.url
        };
    }),

    updateTab: (id, updates) => set((state) => ({
        tabs: state.tabs.map(t => t.id === id ? { ...t, ...updates } : t)
    })),

    // Zen Mode State
    zenMode: false,
    zenPlaylist: [
        'PLjWdd7e2d72xmxPzWwjDwuLUYtomaQsyf' // Updated playlist
    ],
    currentTrackIndex: 0,
    setZenMode: (isZen) => {
        set({ zenMode: isZen, agentState: isZen ? AGENT_STATES.IDLE : AGENT_STATES.IDLE });
        get().triggerGlitch(300); // Longer glitch for Zen Mode
    },
    setZenPlaylist: (playlist) => set({ zenPlaylist: playlist }),
    setCurrentTrackIndex: (index) => set({ currentTrackIndex: index }),

    // Phase 12: Advanced Features
    phase12: false,
    setPhase12: (active) => {
        set({ phase12: active });
        get().triggerGlitch();
    },

    // Glitch Effect
    glitchActive: false,
    triggerGlitch: (duration = 200) => {
        set({ glitchActive: true });
        setTimeout(() => set({ glitchActive: false }), duration);
    },

    // History Tunnel
    history: [],
    addToHistory: (item) => set((state) => ({
        history: [{ ...item, id: Date.now(), timestamp: new Date() }, ...state.history].slice(0, 50)
    })),


    // Voice/Gesture/Task State
    isListening: false,
    setListening: (listening) => set({
        isListening: listening,
        agentState: listening ? AGENT_STATES.LISTENING : AGENT_STATES.IDLE
    }),

    currentGesture: null,
    setGesture: (gesture) => set({ currentGesture: gesture }),

    commandInput: '',
    setCommandInput: (input) => set({ commandInput: input }),

    activeModels: {},
    setActiveModels: (models) => set({ activeModels: models }),

    lastError: null,
    setError: (error) => set({ lastError: error, agentState: AGENT_STATES.ERROR }),
    clearError: () => set({ lastError: null }),

    // Agent Actions (from autonomous agent tool calls)
    agentActions: [],
    setAgentActions: (actions) => set({ agentActions: actions }),
    clearAgentActions: () => set({ agentActions: [] }),

    // Terminal Output
    terminalOutput: [],
    addTerminalOutput: (output) => set((state) => ({
        terminalOutput: [...state.terminalOutput, { text: output, timestamp: new Date() }].slice(-100)
    })),
    clearTerminalOutput: () => set({ terminalOutput: [] }),

    // File Manager State
    fileList: { path: '', items: [] },
    setFileList: (data) => set({ fileList: data }),

    fileContent: { path: '', content: '' },
    setFileContent: (data) => set({ fileContent: data }),


    // Voice Enabled State
    voiceEnabled: true,
    setVoiceEnabled: (enabled) => set({ voiceEnabled: enabled }),

    webcamEnabled: false,
    setWebcamEnabled: (enabled) => set({ webcamEnabled: enabled }),

    gesturesEnabled: true,
    setGesturesEnabled: (enabled) => set({ gesturesEnabled: enabled }),

    // Research Agent Loading State
    researchLoading: false,
    setResearchLoading: (loading) => set({ researchLoading: loading })
}));

export default useStore;
