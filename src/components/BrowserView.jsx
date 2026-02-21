import React, { useState, useRef, useCallback, useEffect } from 'react';
import useStore from '../store/useStore';
import socketManager from '../services/socketManager';

/**
 * BrowserView Component
 * Uses Electron webview (bypasses CORS/iframe blocking)
 */
function BrowserView() {
    // Local state for UI inputs (to allow typing before committing)
    const [inputUrl, setInputUrl] = useState('https://www.google.com');
    const [isLoading, setIsLoading] = useState(true);
    const [canGoBack, setCanGoBack] = useState(false);
    const [canGoForward, setCanGoForward] = useState(false);
    const webviewRef = useRef(null);

    const addThought = useStore((state) => state.addThought);

    // Neuro/Store controlled URL
    const browserUrl = useStore((state) => state.browserUrl);
    const setBrowserUrl = useStore((state) => state.setBrowserUrl);
    const addTab = useStore((state) => state.addTab);
    const setViewMode = useStore((state) => state.setViewMode);
    const activeTabId = useStore((state) => state.activeTabId);
    const tabs = useStore((state) => state.tabs);

    // Sync input when Neuro changes URL
    useEffect(() => {
        if (browserUrl && browserUrl !== inputUrl) {
            setInputUrl(browserUrl);
        }
    }, [browserUrl]);

    const addToHistory = useStore((state) => state.addToHistory);

    // Setup webview events
    useEffect(() => {
        const webview = webviewRef.current;
        if (!webview) return;

        const handleStartLoading = () => setIsLoading(true);
        const handleStopLoading = () => setIsLoading(false);

        const handleNavigate = (e) => {
            const url = e.url;
            setInputUrl(url);

            // Phase 12: Record History
            addToHistory({ url: url, title: `Visisted ${new URL(url).hostname}` });
            addThought({ text: `🌐 ${new URL(url).hostname}`, type: 'action' });

            // Core Feature: "Search opens in Halo Orbit"
            // Logic: If on Main Tab (1) and URL is NOT a generic Google Homepage (handling localization like .co.in, .fr, etc)
            const isMainTab = activeTabId === 1;
            if (isMainTab) {
                try {
                    const newUrlObj = new URL(url);
                    const isGoogle = newUrlObj.hostname.includes('google.');
                    const isHomePage = isGoogle && (newUrlObj.pathname === '/' || newUrlObj.pathname === '/webhp');

                    // If it is NOT the homepage (e.g. it is /search, /maps, or a different domain entirely)
                    if (!isHomePage) {
                        console.log("Main Tab Action detected (Search or Nav). Spawning Halo Tab...");

                        // 1. Open New Tab
                        addTab(url);

                        // 2. Switch to 3D
                        setViewMode('3d');

                        // 3. Reset Main Tab back to Google (so it acts as a launcher)
                        useStore.getState().updateTab(1, { url: 'https://www.google.com' });
                    }
                } catch (err) {
                    console.error("URL Parse error:", err);
                }
            }
        };

        const handlePageTitle = (e) => {
            document.title = `${e.title} - NeuroSurf`;
            // Optional: Update history title here if we had ID
        };

        const handleDomReady = async () => {
            try {
                // Active Intelligence: Extract text
                const text = await webview.executeJavaScript(`
                    document.body.innerText.substring(0, 5000)
                `);

                if (text && text.length > 50) {
                    console.log("Analyzing page content...");
                    // Check if socket is connected, retry with delay if not
                    const tryAnalyze = () => {
                        if (socketManager.socket?.connected) {
                            socketManager.analyzePage(text);
                        } else {
                            console.log("Socket not connected, retrying in 500ms...");
                            setTimeout(tryAnalyze, 500);
                        }
                    };
                    tryAnalyze();
                }
            } catch (err) {
                console.error("Failed to extract text:", err);
            }
        };

        webview.addEventListener('did-start-loading', handleStartLoading);
        webview.addEventListener('did-stop-loading', handleStopLoading);
        // Removed handleDomReady trigger to prevent automatic analysis
        webview.addEventListener('did-navigate', handleNavigate);
        webview.addEventListener('did-navigate-in-page', handleNavigate);
        webview.addEventListener('page-title-updated', handlePageTitle);

        const checkNav = () => {
            if (webview.canGoBack) setCanGoBack(webview.canGoBack());
            if (webview.canGoForward) setCanGoForward(webview.canGoForward());
        };
        webview.addEventListener('did-stop-loading', checkNav);

        // Manual Analyze Trigger
        const handleManualAnalyze = async () => {
            console.log("Manual analysis triggered...");
            await handleDomReady();
        };
        window.addEventListener('neuro:analyze_page', handleManualAnalyze);

        return () => {
            webview.removeEventListener('did-start-loading', handleStartLoading);
            webview.removeEventListener('did-stop-loading', handleStopLoading);
            // Removed handleDomReady trigger from here as well
            webview.removeEventListener('did-navigate', handleNavigate);
            webview.removeEventListener('did-navigate-in-page', handleNavigate);
            webview.removeEventListener('page-title-updated', handlePageTitle);
            window.removeEventListener('neuro:analyze_page', handleManualAnalyze);
        };
    }, [addThought, browserUrl, activeTabId, addTab, setViewMode, addToHistory]);

    // Manual navigation
    const handleNavigate = useCallback((e) => {
        e?.preventDefault();
        let targetUrl = inputUrl.trim();
        if (!targetUrl) return;

        if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
            if (targetUrl.includes('.') && !targetUrl.includes(' ')) {
                targetUrl = 'https://' + targetUrl;
            } else {
                targetUrl = `https://www.google.com/search?q=${encodeURIComponent(targetUrl)}`;
            }
        }

        // Logic: If we are on the "Main" Google tab (id=1 usually), open in new tab & switch to 3D
        // Otherwise, just navigate normally
        const isMainTab = activeTabId === 1; // Assuming ID 1 is always the main/first tab

        if (isMainTab) {
            addTab(targetUrl);
            setViewMode('3d');
            addThought({ text: `🚀 Opening ${new URL(targetUrl).hostname} in Halo`, type: 'action' });
        } else {
            setBrowserUrl(targetUrl); // Update store -> Syncs to Neuro, Tabs, SpatialTabs
        }
    }, [inputUrl, setBrowserUrl, activeTabId, addTab, setViewMode, addThought]);

    const goBack = () => webviewRef.current?.goBack();
    const goForward = () => webviewRef.current?.goForward();
    const refresh = () => webviewRef.current?.reload();

    return (
        <div style={{
            position: 'fixed',
            top: 32,
            left: 0,
            right: 350,
            bottom: 80,
            display: 'flex',
            flexDirection: 'column',
            background: '#1a1a25',
            zIndex: 50,
            borderRight: '1px solid rgba(0, 212, 255, 0.2)'
        }}>
            {/* URL Bar */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 12px',
                background: 'rgba(10, 10, 15, 0.95)',
                borderBottom: '1px solid rgba(0, 212, 255, 0.2)'
            }}>
                <button onClick={goBack} disabled={!canGoBack} style={{ ...navBtnStyle, opacity: canGoBack ? 1 : 0.4 }}>←</button>
                <button onClick={goForward} disabled={!canGoForward} style={{ ...navBtnStyle, opacity: canGoForward ? 1 : 0.4 }}>→</button>
                <button onClick={refresh} style={navBtnStyle}>⟳</button>

                <form onSubmit={handleNavigate} style={{ flex: 1 }}>
                    <input
                        type="text"
                        value={inputUrl}
                        onChange={(e) => setInputUrl(e.target.value)}
                        placeholder="Enter URL or search Google..."
                        style={{
                            width: '100%',
                            padding: '10px 16px',
                            background: 'rgba(0, 0, 0, 0.5)',
                            border: '1px solid rgba(0, 212, 255, 0.4)',
                            borderRadius: 25,
                            color: 'white',
                            fontSize: 14,
                            outline: 'none',
                            fontFamily: 'var(--font-body)'
                        }}
                    />
                </form>

                {isLoading && (
                    <div style={{
                        width: 20, height: 20,
                        border: '2px solid var(--neural-blue)',
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} />
                )}
            </div>

            {/* Webview - Electron's embedded browser */}
            <div style={{ flex: 1, position: 'relative' }}>
                <webview
                    ref={webviewRef}
                    src={browserUrl} // Sync with Store
                    style={{ width: '100%', height: '100%' }}
                    allowpopups="true"
                    webpreferences="contextIsolation=yes"
                />

                {isLoading && (
                    <div style={{
                        position: 'absolute',
                        top: '50%', left: '50%',
                        transform: 'translate(-50%, -50%)',
                        color: 'var(--neural-blue)',
                        fontSize: 14,
                        fontFamily: 'var(--font-display)',
                        background: 'rgba(0,0,0,0.8)',
                        padding: '12px 24px',
                        borderRadius: 8
                    }}>
                        Loading...
                    </div>
                )}
            </div>
        </div>
    );
}

const navBtnStyle = {
    width: 32, height: 32,
    border: '1px solid rgba(0, 212, 255, 0.3)',
    background: 'rgba(0, 0, 0, 0.4)',
    color: 'var(--neural-blue)',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 14,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
};

export default BrowserView;
