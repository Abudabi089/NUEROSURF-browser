import React, { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import useStore from '../store/useStore';

function AmbientParticles({ count = 400 }) { // Increased count
    const pointsRef = useRef();
    const { pointer, camera } = useThree();
    const isListening = useStore((state) => state.isListening);

    // Generate particle positions
    const [positions, colors, initialPositions] = useMemo(() => {
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);
        const initialPositions = new Float32Array(count * 3); // Store initial pos for return force

        const colorPalette = [
            new THREE.Color('#00d4ff'),
            new THREE.Color('#9d4edd'),
            new THREE.Color('#ffd700'),
            new THREE.Color('#00ff88'),
            new THREE.Color('#00fff2') // Cyan for Phase 12 feel
        ];

        for (let i = 0; i < count; i++) {
            // Random position in a larger sphere
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            const radius = 10 + Math.random() * 30;

            const x = radius * Math.sin(phi) * Math.cos(theta);
            const y = radius * Math.sin(phi) * Math.sin(theta);
            const z = radius * Math.cos(phi);

            positions[i * 3] = x;
            positions[i * 3 + 1] = y;
            positions[i * 3 + 2] = z;

            initialPositions[i * 3] = x;
            initialPositions[i * 3 + 1] = y;
            initialPositions[i * 3 + 2] = z;

            // Random color from palette
            const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }

        return [positions, colors, initialPositions];
    }, [count]);

    // Animate particles
    useFrame((state, delta) => {
        if (!pointsRef.current) return;

        // Mouse interaction vector (projected to 3D roughly)
        // We use a simplified interaction: raycasting is expensive for 400 particles every frame in JS,
        // so we projected pointer to a plane at z=0 for interaction feel.
        const vector = new THREE.Vector3(pointer.x, pointer.y, 0.5);
        vector.unproject(camera);
        const dir = vector.sub(camera.position).normalize();
        const distance = -camera.position.z / dir.z;
        const target = camera.position.clone().add(dir.multiplyScalar(distance));

        const attributes = pointsRef.current.geometry.attributes;
        const currentPositions = attributes.position.array;

        // Voice reactivity pulse
        const pulse = isListening ? 1.5 + Math.sin(state.clock.elapsedTime * 20) * 0.5 : 1;

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            let x = currentPositions[i3];
            let y = currentPositions[i3 + 1];
            let z = currentPositions[i3 + 2];

            const ix = initialPositions[i3];
            const iy = initialPositions[i3 + 1];
            const iz = initialPositions[i3 + 2];

            // 1. Gentle drift (organic movement)
            const time = state.clock.elapsedTime;
            const driftX = Math.sin(time * 0.3 + i) * 0.02;
            const driftY = Math.cos(time * 0.2 + i * 0.5) * 0.02;

            // 2. Interaction: Repulsion from mouse "ray"
            // Simple distance check from particle to mouse target point (approximate)
            const dx = x - target.x * 10; // Scale up pointer effect
            const dy = y - target.y * 10;
            const dz = z - target.z; // Less Z effect
            const distSq = dx * dx + dy * dy + dz * dz;

            if (distSq < 25) { // Interaction radius
                const force = (25 - distSq) * 0.01;
                x += dx * force;
                y += dy * force;
                z += dz * force;
            }

            // 3. Spring back to initial position (elasticity)
            x += (ix + driftX - x) * 0.05;
            y += (iy + driftY - y) * 0.05;
            z += (iz - z) * 0.05;

            currentPositions[i3] = x;
            currentPositions[i3 + 1] = y;
            currentPositions[i3 + 2] = z;
        }

        attributes.position.needsUpdate = true;

        // Rotate entire field slowly
        pointsRef.current.rotation.y += delta * 0.02;

        // Pulse size on voice
        pointsRef.current.material.size = 0.15 * pulse;
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
                blending={THREE.AdditiveBlending}
                depthWrite={false}
            />
        </points>
    );
}

export default AmbientParticles;
