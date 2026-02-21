import React, { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, Text } from '@react-three/drei';
import * as THREE from 'three';
import useStore from '../store/useStore';
import socketManager from '../services/socketManager';

/**
 * SpatialTabs - Planetary System
 * Renders multiple tabs orbiting the Neural Halo.
 * - Active Tab: Interactive <Html><webview>
 * - Inactive Tabs: Suspended "Holographic Cards" (Mesh + Text)
 */
function SpatialTabs() {
    const groupRef = useRef();
    const webviewRef = useRef();

    // Store State
    const tabs = useStore((state) => state.tabs);
    const activeTabId = useStore((state) => state.activeTabId);
    const setActiveTab = useStore((state) => state.setActiveTab);
    const browserUrl = useStore((state) => state.browserUrl);
    const setBrowserUrl = useStore((state) => state.setBrowserUrl);

    // Rotation & Animation
    const systemRotation = useStore((state) => state.systemRotation);
    const setSystemRotation = useStore((state) => state.setSystemRotation);
    const orbitEnabled = useStore((state) => state.orbitEnabled);
    const targetRotation = useRef(0);

    // Orbit parameters
    const RADIUS = 5.5;

    // Calculate target rotation to center the active tab
    // We want the active tab tuple be at angle 0 (front, positive X or Z depending on camera)
    // Actually, let's say angle 0 is "Right" (Positive X).
    // If active tab is index i, its base angle is (i / total) * 2PI.
    // We want (baseAngle + systemRotation) = 0.
    // So systemRotation = -baseAngle.
    useEffect(() => {
        if (!orbitEnabled) {
            targetRotation.current = 0;
            return;
        }

        const index = tabs.findIndex(t => t.id === activeTabId);
        if (index !== -1) {
            const angleStep = tabs.length > 0 ? (Math.PI * 2) / tabs.length : 0;
            const baseAngle = index * angleStep;
            targetRotation.current = -baseAngle;
        }
    }, [activeTabId, tabs.length, orbitEnabled]);

    // Animation Loop
    useFrame((state, delta) => {
        if (groupRef.current) {
            // Smoothly interpolate rotation
            // Lerp factor
            const step = delta * 5;

            // Shortest path interpolation for circle
            let current = groupRef.current.rotation.y;
            let target = targetRotation.current;

            // Normalize angles
            while (target - current > Math.PI) target -= Math.PI * 2;
            while (target - current < -Math.PI) target += Math.PI * 2;

            groupRef.current.rotation.y += (target - current) * step;

            // Update store for other components if needed (throttled)
            // setSystemRotation(groupRef.current.rotation.y); 
        }
    });

    return (
        <group ref={groupRef} position={[0, 0, 0]}>
            {tabs.map((tab, index) => {
                const angleStep = tabs.length > 0 ? (Math.PI * 2) / tabs.length : 0;
                const angle = index * angleStep;
                const x = Math.cos(angle) * RADIUS;
                const z = Math.sin(angle) * RADIUS;
                const isActive = tab.id === activeTabId;

                return (
                    <group
                        key={tab.id}
                        position={[x, 0, z]}
                        rotation={[0, -angle + Math.PI / 2, 0]} // Face outward? Or inward?
                    // If we want it to face center: rotation.y = -angle
                    // If we want it to face outward: rotation.y = -angle + Math.PI
                    >
                        {/* If Active: Render Webview */}
                        {isActive ? (
                            <InteractiveTab
                                url={browserUrl}
                                setUrl={setBrowserUrl}
                            />
                        ) : (
                            /* If Inactive: Render Holographic Card */
                            <SuspendedTab
                                title={tab.title}
                                onClick={() => setActiveTab(tab.id)}
                            />
                        )}
                    </group>
                );
            })}
        </group>
    );
}

// --- Sub-Components ---

function InteractiveTab({ url, setUrl }) {
    const webviewRef = useRef();
    const [inputUrl, setInputUrl] = useState(url);
    const [isLoading, setIsLoading] = useState(true);

    // Sync inputUrl when url prop changes (e.g. from navigation)
    useEffect(() => {
        setInputUrl(url);
    }, [url]);

    useEffect(() => {
        const wb = webviewRef.current;
        if (!wb) return;

        const onStartLoading = () => setIsLoading(true);
        const onStopLoading = () => setIsLoading(false);

        const onFinishLoad = async () => {
            setIsLoading(false);
            try {
                // Active Intelligence: Extract text
                const text = await wb.executeJavaScript(`
                    document.body.innerText.substring(0, 5000)
                `);

                if (text && text.length > 50) {
                    // Check socket connection before analyzing
                    if (socketManager.socket?.connected) {
                        socketManager.analyzePage(text);
                    }
                }
            } catch (err) {
                console.error("3D Webview script error:", err);
            }
        };

        const onNewWindow = (e) => {
            e.preventDefault();
            const newUrl = e.url;
            if (newUrl) {
                // Add new tab to the store (Orbiting Tab)
                useStore.getState().addTab(newUrl);
            }
        };

        const onNavigate = (e) => {
            // Update input URL when webview navigates internally
            if (e.url) {
                setInputUrl(e.url);
            }
        };

        wb.addEventListener('did-start-loading', onStartLoading);
        wb.addEventListener('did-stop-loading', onStopLoading);
        wb.addEventListener('did-finish-load', onFinishLoad);
        wb.addEventListener('new-window', onNewWindow);
        wb.addEventListener('did-navigate', onNavigate);
        wb.addEventListener('did-navigate-in-page', onNavigate);

        return () => {
            wb.removeEventListener('did-start-loading', onStartLoading);
            wb.removeEventListener('did-stop-loading', onStopLoading);
            wb.removeEventListener('did-finish-load', onFinishLoad);
            wb.removeEventListener('new-window', onNewWindow);
            wb.removeEventListener('did-navigate', onNavigate);
            wb.removeEventListener('did-navigate-in-page', onNavigate);
        };
    }, []);

    // Handle URL navigation on form submit
    const handleNavigate = (e) => {
        e?.preventDefault();
        let targetUrl = inputUrl.trim();
        if (!targetUrl) return;

        // Add https:// if needed
        if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
            if (targetUrl.includes('.') && !targetUrl.includes(' ')) {
                targetUrl = 'https://' + targetUrl;
            } else {
                targetUrl = `https://www.google.com/search?q=${encodeURIComponent(targetUrl)}`;
            }
        }

        setInputUrl(targetUrl);
        setUrl(targetUrl); // Update global state
    };

    return (
        <group>
            {/* Glow Frame */}
            <mesh position={[0, 0, -0.05]}>
                <planeGeometry args={[3.3, 2.3]} />
                <meshBasicMaterial color="#00ff88" transparent opacity={0.2} />
            </mesh>


            <Html
                transform
                occlude="blending"
                position={[0, 0, 0]}
                scale={0.2}
                style={{ width: '1280px', height: '800px', pointerEvents: 'auto' }}
            >
                <div style={{
                    width: '100%', height: '100%',
                    background: '#000', borderRadius: '16px',
                    border: '4px solid #00ff88', overflow: 'hidden',
                    display: 'flex', flexDirection: 'column'
                }}>
                    <form onSubmit={handleNavigate} style={{
                        height: '50px', background: '#1a1a2e',
                        display: 'flex', alignItems: 'center', padding: '0 20px'
                    }}>
                        <input
                            type="text"
                            value={inputUrl}
                            onChange={e => setInputUrl(e.target.value)}
                            onKeyDown={e => { if (e.key === 'Enter') handleNavigate(e); }}
                            placeholder="Enter URL..."
                            style={{
                                flex: 1, background: 'rgba(255,255,255,0.1)',
                                border: 'none', color: 'white', padding: '8px 15px', borderRadius: 20,
                                fontSize: 14, outline: 'none'
                            }}
                        />
                        <button type="submit" style={{
                            marginLeft: 8, padding: '8px 16px',
                            background: '#00ff88', border: 'none',
                            borderRadius: 10, color: '#000',
                            cursor: 'pointer', fontWeight: 'bold'
                        }}>
                            Go
                        </button>
                        {isLoading && (
                            <div style={{
                                marginLeft: 8, width: 16, height: 16,
                                border: '2px solid #00ff88', borderTopColor: 'transparent',
                                borderRadius: '50%', animation: 'spin 1s linear infinite'
                            }} />
                        )}
                    </form>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <webview
                            ref={webviewRef}
                            src={url}
                            style={{ width: '100%', height: '100%' }}
                            allowpopups="true"
                        />
                    </div>
                </div>
            </Html>
        </group>
    );
}

function SuspendedTab({ title, onClick }) {
    const [hover, setHover] = useState(false);

    return (
        <group
            onClick={onClick}
            onPointerOver={() => setHover(true)}
            onPointerOut={() => setHover(false)}
        >
            <mesh>
                <planeGeometry args={[3, 2]} />
                <meshBasicMaterial
                    color={hover ? "#ff0088" : "#00d4ff"}
                    transparent
                    opacity={0.3}
                    side={THREE.DoubleSide}
                />
            </mesh>
            <Text
                position={[0, 0, 0.1]}
                fontSize={0.3}
                color="white"
                anchorX="center"
                anchorY="middle"
            >
                {title}
            </Text>
            <Text
                position={[0, -0.5, 0.1]}
                fontSize={0.15}
                color="#aaaaaa"
            >
                {hover ? "Click to Activate" : "Suspended"}
            </Text>
        </group>
    );
}

export default SpatialTabs;
