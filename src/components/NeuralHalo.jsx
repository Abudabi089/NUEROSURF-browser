import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { STATE_COLORS, AGENT_STATES } from '../store/useStore';

// GLSL Vertex Shader
const vertexShader = `
  varying vec2 vUv;
  varying vec3 vPosition;
  
  void main() {
    vUv = uv;
    vPosition = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// GLSL Fragment Shader
const fragmentShader = `
  uniform float uTime;
  uniform vec3 uColor;
  uniform float uIntensity;
  uniform float uPulseSpeed;
  
  varying vec2 vUv;
  varying vec3 vPosition;
  
  void main() {
    // Calculate distance from center of UV for radial gradient
    vec2 center = vec2(0.5, 0.5);
    float dist = distance(vUv, center);
    
    // Create ring effect
    float ringWidth = 0.15;
    float ringCenter = 0.4;
    float ring = smoothstep(ringCenter - ringWidth, ringCenter, dist) * 
                 (1.0 - smoothstep(ringCenter, ringCenter + ringWidth, dist));
    
    // Animated pulse
    float pulse = sin(uTime * uPulseSpeed) * 0.3 + 0.7;
    
    // Energy flow effect
    float angle = atan(vUv.y - 0.5, vUv.x - 0.5);
    float flow = sin(angle * 8.0 + uTime * 2.0) * 0.5 + 0.5;
    
    // Combine effects
    float finalIntensity = ring * pulse * uIntensity;
    finalIntensity += ring * flow * 0.3;
    
    // Glow falloff
    float glow = exp(-dist * 3.0) * 0.5;
    
    // Final color
    vec3 finalColor = uColor * (finalIntensity + glow);
    float alpha = finalIntensity + glow * 0.5;
    
    gl_FragColor = vec4(finalColor, alpha);
  }
`;

function NeuralHalo({ state = AGENT_STATES.IDLE }) {
    const meshRef = useRef();
    const materialRef = useRef();

    // Get target color based on state
    const targetColor = useMemo(() => {
        const hexColor = STATE_COLORS[state] || STATE_COLORS[AGENT_STATES.IDLE];
        return new THREE.Color(hexColor);
    }, [state]);

    // Create shader material
    const uniforms = useMemo(() => ({
        uTime: { value: 0 },
        uColor: { value: targetColor },
        uIntensity: { value: 1.0 },
        uPulseSpeed: { value: 2.0 }
    }), []);

    // Animation loop
    useFrame((state, delta) => {
        if (materialRef.current) {
            // Update time uniform
            materialRef.current.uniforms.uTime.value += delta;

            // Smoothly interpolate color
            materialRef.current.uniforms.uColor.value.lerp(targetColor, delta * 3);

            // Adjust pulse speed based on state
            const pulseSpeed =
                state === 'zen' ? 0.5 : // Zen Mode: Very Slow
                    state === 'acting' ? 5.0 :
                        state === 'planning' ? 3.0 :
                            state === 'listening' ? 4.0 : 2.0;

            materialRef.current.uniforms.uPulseSpeed.value = THREE.MathUtils.lerp(
                materialRef.current.uniforms.uPulseSpeed.value,
                pulseSpeed,
                delta * 0.5 // Slower transition
            );
        }

        // Rotate the halo
        if (meshRef.current) {
            // Zen Mode: Slower rotation
            const rotSpeed = state === 'zen' ? 0.05 : 0.2;
            meshRef.current.rotation.z += delta * rotSpeed;
        }
    });

    return (
        <group>
            {/* Main Halo Ring */}
            <mesh ref={meshRef} rotation={[Math.PI / 2, 0, 0]}>
                <ringGeometry args={[2.5, 3.5, 128]} />
                <shaderMaterial
                    ref={materialRef}
                    vertexShader={vertexShader}
                    fragmentShader={fragmentShader}
                    uniforms={uniforms}
                    transparent
                    side={THREE.DoubleSide}
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </mesh>

            {/* Inner Glow Ring */}
            <mesh rotation={[Math.PI / 2, 0, 0]}>
                <ringGeometry args={[2.0, 2.5, 64]} />
                <meshBasicMaterial
                    color={targetColor}
                    transparent
                    opacity={0.2}
                    side={THREE.DoubleSide}
                    blending={THREE.AdditiveBlending}
                />
            </mesh>

            {/* Outer Glow Ring */}
            <mesh rotation={[Math.PI / 2, 0, 0]}>
                <ringGeometry args={[3.5, 4.0, 64]} />
                <meshBasicMaterial
                    color={targetColor}
                    transparent
                    opacity={0.1}
                    side={THREE.DoubleSide}
                    blending={THREE.AdditiveBlending}
                />
            </mesh>

            {/* Center Orb */}
            <mesh>
                <sphereGeometry args={[0.5, 32, 32]} />
                <meshBasicMaterial
                    color={targetColor}
                    transparent
                    opacity={0.8}
                />
            </mesh>

            {/* Energy Core */}
            <mesh>
                <icosahedronGeometry args={[0.3, 1]} />
                <meshBasicMaterial
                    color="#ffffff"
                    transparent
                    opacity={0.9}
                />
            </mesh>
        </group>
    );
}

export default NeuralHalo;
