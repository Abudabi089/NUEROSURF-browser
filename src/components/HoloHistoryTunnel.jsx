import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Image, Float } from '@react-three/drei';
import * as THREE from 'three';
import useStore from '../store/useStore';

/**
 * HoloHistoryTunnel
 * Renders visited sites/screenshots in a spiral time-tunnel.
 */
const HoloHistoryTunnel = () => {
    const history = useStore((state) => state.history);
    const groupRef = useRef();

    // If history is empty, show a placeholder
    const displayItems = history.length > 0 ? history : [{ id: 'placeholder', title: 'History Empty - Start Browsing', url: '', position: [0, 0, 0], rotation: [0, 0, 0] }];

    // Create a spiral layout
    const items = useMemo(() => {
        return displayItems.map((item, index) => {
            const angle = index * 0.5; // Spiral angle spacing
            const radius = 3 + index * 0.2; // Widen spiral
            const z = -index * 1.5; // Depth

            return {
                ...item,
                position: [
                    Math.cos(angle) * radius,
                    Math.sin(angle) * radius,
                    z
                ],
                rotation: [0, 0, angle] // Face inward
            };
        });
    }, [displayItems]);

    useFrame((state) => {
        if (!groupRef.current) return;
        // Slowly rotate the entire tunnel
        groupRef.current.rotation.z += 0.001;
        // Float effect (breathing)
        groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.5;
    });

    // if (history.length === 0) return null; // Removed to show placeholder

    return (
        <group ref={groupRef}>
            {items.map((item, i) => (
                <Float key={item.id} speed={2} rotationIntensity={0.2} floatIntensity={0.5}>
                    <group position={item.position} rotation={item.rotation}>
                        {/* Frame */}
                        <mesh position={[0, 0, -0.05]}>
                            <planeGeometry args={[3.2, 2.2]} />
                            <meshStandardMaterial
                                color="#00fff2"
                                transparent
                                opacity={0.3}
                                side={THREE.DoubleSide}
                                emissive="#00fff2"
                                emissiveIntensity={0.5}
                            />
                        </mesh>

                        {/* Content Placeholder (or Image if available) */}
                        <mesh>
                            <planeGeometry args={[3, 2]} />
                            <meshStandardMaterial color="#111" />
                        </mesh>

                        {/* Title Text */}
                        <Text
                            position={[0, -1.2, 0]}
                            fontSize={0.2}
                            color="#00fff2"
                            anchorX="center"
                            anchorY="middle"
                            maxWidth={2.8}
                        >
                            {item.title || item.url || 'Unknown Page'}
                        </Text>
                    </group>
                </Float>
            ))}
        </group>
    );
};

export default HoloHistoryTunnel;
