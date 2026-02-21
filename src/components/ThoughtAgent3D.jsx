import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line, Sphere } from '@react-three/drei';
import * as THREE from 'three';
import useStore from '../store/useStore';

/**
 * ThoughtAgent3D
 * Visualizes the connection between the Agent (Halo) and the Environment (Tabs/Actions).
 * "Thought-to-Action"
 */
const ThoughtAgent3D = () => {
    const agentState = useStore((state) => state.agentState);
    const thoughts = useStore((state) => state.thoughts);
    const tabs = useStore((state) => state.tabs);
    const activeTabId = useStore((state) => state.activeTabId);

    // Find active tab position
    const activeTab = tabs.find(t => t.id === activeTabId);
    const targetPos = useMemo(() => {
        if (!activeTab) return new THREE.Vector3(0, 0, -4);
        // Simple heuristic for orbit position (synced with SpatialTabs)
        const index = tabs.indexOf(activeTab);
        const orbitRadius = 5;
        const angle = (index / Math.max(tabs.length, 1)) * Math.PI * 2;
        // In SpatialTabs, they might rotate or have complex positioning
        // Let's assume a static but better target for now
        return new THREE.Vector3(Math.cos(angle) * orbitRadius, 0, Math.sin(angle) * orbitRadius);
    }, [activeTabId, tabs]);

    const isActive = agentState === 'acting' || agentState === 'planning';
    const color = agentState === 'acting' ? '#ff3366' : '#ffd700';

    const beamRef = useRef();
    const coreRef = useRef();

    useFrame((state) => {
        if (beamRef.current && isActive) {
            const t = state.clock.elapsedTime;
            beamRef.current.material.opacity = 0.6 + Math.sin(t * 12) * 0.3;
            beamRef.current.rotation.z += 0.1;
        }
        if (coreRef.current && isActive) {
            const pulse = 1 + Math.sin(state.clock.elapsedTime * 20) * 0.2;
            coreRef.current.scale.setScalar(pulse);
        }
    });

    if (!isActive) return null;

    return (
        <group>
            {/* Energy Beam Core */}
            <Line
                ref={beamRef}
                points={[[0, 0, 0], targetPos]}
                color={color}
                lineWidth={5}
                transparent
                opacity={0.9}
            />

            {/* Glowing Aura Beam */}
            <Line
                points={[[0, 0, 0], targetPos]}
                color={color}
                lineWidth={15}
                transparent
                opacity={0.2}
            />

            {/* Impact Point */}
            <Sphere ref={coreRef} position={targetPos} args={[0.3, 32, 32]}>
                <meshBasicMaterial color={color} transparent opacity={0.8} />
            </Sphere>

            {/* Particles along the beam */}
            {[...Array(5)].map((_, i) => (
                <ParticleAlongBeam
                    key={i}
                    start={[0, 0, 0]}
                    end={targetPos}
                    delay={i * 0.2}
                    color={color}
                />
            ))}
        </group>
    );
};

const ParticleAlongBeam = ({ start, end, delay, color }) => {
    const meshRef = useRef();
    const curve = useMemo(() => new THREE.LineCurve3(
        new THREE.Vector3(...start),
        new THREE.Vector3().copy(end)
    ), [start, end]);

    useFrame((state) => {
        const t = (state.clock.elapsedTime * 0.5 + delay) % 1;
        const pos = curve.getPoint(t);
        meshRef.current.position.copy(pos);
        meshRef.current.scale.setScalar(1 - t);
    });

    return (
        <mesh ref={meshRef}>
            <sphereGeometry args={[0.1, 8, 8]} />
            <meshBasicMaterial color={color} />
        </mesh>
    );
};

export default ThoughtAgent3D;
