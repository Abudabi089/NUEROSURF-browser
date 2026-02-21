import React, { Suspense } from 'react';
import { OrbitControls, Stars } from '@react-three/drei';
import NeuralHalo from './NeuralHalo';
import SpatialTabs from './SpatialTabs';
import AmbientParticles from './AmbientParticles';
import { EffectComposer, Bloom, Glitch } from '@react-three/postprocessing';
import { GlitchMode } from 'postprocessing';
import useStore from '../store/useStore';
import HoloHistoryTunnel from './HoloHistoryTunnel';
import ThoughtAgent3D from './ThoughtAgent3D';
import ErrorBoundary from './ErrorBoundary';

function Scene({ showBrowserTab = true }) {
    const zenMode = useStore((state) => state.zenMode);
    const phase12 = useStore((state) => state.phase12);
    const agentState = useStore((state) => state.agentState);
    const glitchActive = useStore((state) => state.glitchActive);

    return (
        <>
            {/* Lighting */}
            <ambientLight intensity={0.3} />
            <pointLight position={[10, 10, 10]} intensity={1} color="#00d4ff" />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color="#9d4edd" />

            {/* Background stars */}
            <Stars radius={100} depth={50} count={3000} factor={4} saturation={0} fade speed={0.5} />

            {/* Neural Halo - centered at origin
            <ErrorBoundary>
                <NeuralHalo state={zenMode ? 'zen' : agentState} />
            </ErrorBoundary>
            */}

            {/* ERROR DEBUG BOX - Massive Glowing Sphere */}
            <mesh position={[0, 0, -5]}>
                <sphereGeometry args={[2, 32, 32]} />
                <meshBasicMaterial color="#00ff00" wireframe />
            </mesh>

            {/* Restored visuals */}

            {/* Phase 12: Holo-History Tunnel */}
            {phase12 && <HoloHistoryTunnel />}
            {phase12 && <ThoughtAgent3D />}

            {/* Browser Tabs - Disabled to prevent Black Screen Crash
            {showBrowserTab && !phase12 && (
                <ErrorBoundary>
                    <Suspense fallback={null}>
                        <SpatialTabs />
                    </Suspense>
                </ErrorBoundary>
            )}
            */}

            {/* Ambient particles
            <ErrorBoundary>
                <AmbientParticles />
            </ErrorBoundary>
            */}

            {/* OrbitControls - allows mouse/gesture control */}
            <OrbitControls
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                minDistance={3}
                maxDistance={20}
                autoRotate={false}
            />

            {/* Post-processing */}
            {/* Post-processing - Disabled for debugging/stability
            <EffectComposer>
                <Bloom luminanceThreshold={0.2} luminanceSmoothing={0.9} intensity={0.5} />
                <Glitch
                    active={glitchActive}
                    delay={[0, 0]}
                    duration={[0.1, 0.3]}
                    strength={[0.3, 1.0]}
                    mode={GlitchMode.CONSTANT_MILD}
                />
            </EffectComposer>
            */}
        </>
    );
}

export default Scene;
