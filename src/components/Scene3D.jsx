/**
 * Scene3D - Rebuilt 3D Scene Component
 * 
 * A simplified, robust 3D scene with:
 * - Central neural halo (pulsing ring)
 * - Orbiting tab spheres
 * - Floating particles
 * - Stars background
 */

import React, { useRef, useMemo, Suspense } from 'react';
import { useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Html } from '@react-three/drei';
import * as THREE from 'three';
import useStore, { STATE_COLORS, AGENT_STATES } from '../store/useStore';
import SpatialTabs from './SpatialTabs';
import ThoughtAgent3D from './ThoughtAgent3D';

// ========== Central Neural Halo ==========
function NeuralHalo({ state = 'idle' }) {
    const ringRef = useRef();
    const coreRef = useRef();
    const glowRef = useRef();
    const timeRef = useRef(0);

    const color = STATE_COLORS[state] || STATE_COLORS[AGENT_STATES.IDLE];
    const threeColor = useMemo(() => new THREE.Color(color), [color]);

    useFrame((_, delta) => {
        timeRef.current += delta;
        const t = timeRef.current;

        // Rotate the ring
        if (ringRef.current) {
            ringRef.current.rotation.z += delta * 0.3;
        }

        // Pulse the core
        if (coreRef.current) {
            const pulse = 1 + Math.sin(t * 2) * 0.1;
            coreRef.current.scale.setScalar(pulse);
        }

        // Animate glow opacity
        if (glowRef.current) {
            glowRef.current.material.opacity = 0.3 + Math.sin(t * 3) * 0.1;
        }
    });

    return (
        <group>
            {/* Main Ring */}
            <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
                <torusGeometry args={[3, 0.15, 16, 100]} />
                <meshBasicMaterial
                    color={threeColor}
                    transparent
                    opacity={0.9}
                />
            </mesh>

            {/* Inner Ring */}
            <mesh rotation={[Math.PI / 2, 0, 0]}>
                <torusGeometry args={[2.5, 0.08, 16, 100]} />
                <meshBasicMaterial
                    color={threeColor}
                    transparent
                    opacity={0.5}
                />
            </mesh>

            {/* Outer Glow Ring */}
            <mesh ref={glowRef} rotation={[Math.PI / 2, 0, 0]}>
                <torusGeometry args={[3.5, 0.3, 16, 100]} />
                <meshBasicMaterial
                    color={threeColor}
                    transparent
                    opacity={0.2}
                    side={THREE.DoubleSide}
                />
            </mesh>

            {/* Center Core Sphere */}
            <mesh ref={coreRef}>
                <sphereGeometry args={[0.5, 32, 32]} />
                <meshBasicMaterial color={threeColor} />
            </mesh>

            {/* Inner Energy Core */}
            <mesh>
                <icosahedronGeometry args={[0.25, 1]} />
                <meshBasicMaterial color="#ffffff" />
            </mesh>
        </group>
    );
}

// ========== Floating Particles ==========
function FloatingParticles({ count = 200 }) {
    const pointsRef = useRef();

    const [positions, colors] = useMemo(() => {
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);

        const colorPalette = [
            new THREE.Color('#00d4ff'),
            new THREE.Color('#9d4edd'),
            new THREE.Color('#ffd700'),
            new THREE.Color('#00ff88')
        ];

        for (let i = 0; i < count; i++) {
            // Distribute in a sphere
            const radius = 8 + Math.random() * 20;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);

            positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = radius * Math.cos(phi);

            const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }

        return [positions, colors];
    }, [count]);

    useFrame((_, delta) => {
        if (pointsRef.current) {
            pointsRef.current.rotation.y += delta * 0.02;
            pointsRef.current.rotation.x += delta * 0.005;
        }
    });

    return (
        <points ref={pointsRef}>
            <bufferGeometry>
                <bufferAttribute
                    attach="attributes-position"
                    count={count}
                    array={positions}
                    itemSize={3}
                />
                <bufferAttribute
                    attach="attributes-color"
                    count={count}
                    array={colors}
                    itemSize={3}
                />
            </bufferGeometry>
            <pointsMaterial
                size={0.15}
                vertexColors
                transparent
                opacity={0.8}
                sizeAttenuation
            />
        </points>
    );
}

// ========== Orbiting Tab Spheres ==========
function OrbitingTabs() {
    const groupRef = useRef();
    const tabs = useStore((state) => state.tabs);
    const setActiveTab = useStore((state) => state.setActiveTab);

    useFrame((_, delta) => {
        if (groupRef.current) {
            groupRef.current.rotation.y += delta * 0.1;
        }
    });

    const orbitRadius = 5;

    return (
        <group ref={groupRef}>
            {tabs.map((tab, index) => {
                const angle = (index / Math.max(tabs.length, 1)) * Math.PI * 2;
                const x = Math.cos(angle) * orbitRadius;
                const z = Math.sin(angle) * orbitRadius;
                const isActive = tab.active;

                return (
                    <group key={tab.id} position={[x, 0, z]}>
                        {/* Tab Sphere */}
                        <mesh onClick={() => setActiveTab(tab.id)}>
                            <sphereGeometry args={[isActive ? 0.5 : 0.35, 32, 32]} />
                            <meshStandardMaterial
                                color={isActive ? '#00d4ff' : '#555555'}
                                emissive={isActive ? '#00d4ff' : '#222222'}
                                emissiveIntensity={isActive ? 0.5 : 0.1}
                            />
                        </mesh>

                        {/* Orbit Ring */}
                        {isActive && (
                            <mesh rotation={[Math.PI / 2, 0, 0]}>
                                <torusGeometry args={[0.7, 0.02, 16, 32]} />
                                <meshBasicMaterial color="#00d4ff" transparent opacity={0.6} />
                            </mesh>
                        )}

                        {/* Label */}
                        <Html
                            position={[0, 0.8, 0]}
                            center
                            distanceFactor={8}
                            style={{ pointerEvents: 'none' }}
                        >
                            <div style={{
                                color: isActive ? '#00d4ff' : '#888888',
                                fontSize: 11,
                                fontFamily: 'Orbitron, monospace',
                                textShadow: '0 0 10px rgba(0, 212, 255, 0.5)',
                                whiteSpace: 'nowrap',
                                background: 'rgba(0, 0, 0, 0.6)',
                                padding: '3px 8px',
                                borderRadius: 4,
                                border: isActive ? '1px solid #00d4ff' : '1px solid transparent'
                            }}>
                                {tab.title || 'Tab'}
                            </div>
                        </Html>
                    </group>
                );
            })}
        </group>
    );
}


// ========== Main Scene3D Component ==========
function Scene3D() {
    const zenMode = useStore((state) => state.zenMode);
    const agentState = useStore((state) => state.agentState);

    return (
        <>
            {/* Lighting */}
            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} intensity={1} color="#00d4ff" />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color="#9d4edd" />
            <pointLight position={[0, 5, 0]} intensity={0.3} color="#ffd700" />

            {/* Background Stars */}
            <Stars
                radius={100}
                depth={50}
                count={2000}
                factor={4}
                saturation={0}
                fade
                speed={0.3}
            />

            {/* Central Neural Halo */}
            <NeuralHalo state={zenMode ? 'zen' : agentState} />

            {/* Interactive Spatial Tabs (with webview) or Simple Orbiting Spheres */}
            <Suspense fallback={<OrbitingTabs />}>
                <SpatialTabs />
            </Suspense>


            {/* Neural Thought Beam */}
            <ThoughtAgent3D />

            {/* Floating Particles */}
            <FloatingParticles count={200} />

            {/* Grid Helper */}
            <gridHelper args={[20, 20, '#333333', '#222222']} position={[0, -4, 0]} />

            {/* Camera Controls */}
            <OrbitControls
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                minDistance={3}
                maxDistance={30}
                autoRotate={!zenMode}
                autoRotateSpeed={0.3}
            />
        </>
    );
}

export default Scene3D;
