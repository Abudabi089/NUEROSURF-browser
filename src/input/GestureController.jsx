import React, { useEffect, useRef, useCallback, useState } from 'react';
import socketManager from '../services/socketManager';
import useStore from '../store/useStore';

/**
 * Gesture types recognized
 */
const GESTURES = {
    PINCH: 'pinch',
    PALM: 'palm',
    POINT: 'point',
    FIST: 'fist',
    THUMBS_UP: 'thumbs_up',
    NONE: 'none'
};

/**
 * GestureController Component
 * MediaPipe hand tracking with visible webcam feed
 */
function GestureController({ enabled = true, onGesture }) {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isActive, setIsActive] = useState(false);
    const [currentGesture, setCurrentGesture] = useState(GESTURES.NONE);
    const [error, setError] = useState(null);
    const gestureHoldCount = useRef(0);
    const lastGesture = useRef(GESTURES.NONE);

    const setGesture = useStore((state) => state.setGesture);
    const addThought = useStore((state) => state.addThought);

    // Execute gesture action
    const executeGestureAction = useCallback((gesture) => {
        console.log('[Gesture] Executing:', gesture);

        switch (gesture) {
            case GESTURES.PALM:
                // HALT - Stop all agent actions
                socketManager.haltAgent();
                addThought({ text: '✋ HALT - Agent stopped', type: 'action' });
                break;

            case GESTURES.PINCH:
                // Zoom or grab action
                addThought({ text: '🤏 Pinch detected - Zoom mode', type: 'action' });
                break;

            case GESTURES.POINT:
                // Point to highlight
                addThought({ text: '☝️ Point detected - Highlight mode', type: 'action' });
                break;

            case GESTURES.FIST:
                // Grab/scroll action
                addThought({ text: '✊ Fist detected - Scroll mode', type: 'action' });
                break;

            case GESTURES.THUMBS_UP:
                // Confirm/accept action
                addThought({ text: '👍 Thumbs up - Confirmed!', type: 'action' });
                break;
        }

        // Send to backend
        socketManager.sendGesture({ type: gesture });

        // Callback
        if (onGesture) {
            onGesture({ type: gesture });
        }
    }, [addThought, onGesture]);

    // Initialize camera and hand tracking
    useEffect(() => {
        if (!enabled) return;

        let animationId = null;
        let hands = null;
        let mounted = true;

        const initGestures = async () => {
            try {
                // Get video element
                const video = videoRef.current;
                const canvas = canvasRef.current;
                if (!video || !canvas) return;

                // Request camera
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 320, height: 240, facingMode: 'user' }
                });
                video.srcObject = stream;
                await video.play();

                // Import MediaPipe dynamically
                const { Hands, HAND_CONNECTIONS } = await import('@mediapipe/hands');

                if (!mounted) return;

                // Create Hands detector
                hands = new Hands({
                    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
                });

                hands.setOptions({
                    maxNumHands: 1,
                    modelComplexity: 0, // Faster
                    minDetectionConfidence: 0.6,
                    minTrackingConfidence: 0.5
                });

                hands.onResults((results) => {
                    if (!mounted) return;

                    const ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, canvas.width, canvas.height);

                    // Draw video frame (mirrored)
                    ctx.save();
                    ctx.scale(-1, 1);
                    ctx.drawImage(video, -canvas.width, 0, canvas.width, canvas.height);
                    ctx.restore();

                    // Draw hand landmarks
                    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
                        const landmarks = results.multiHandLandmarks[0];

                        // Draw connections
                        ctx.strokeStyle = '#00d4ff';
                        ctx.lineWidth = 2;

                        const connections = [
                            [0, 1], [1, 2], [2, 3], [3, 4], // Thumb
                            [0, 5], [5, 6], [6, 7], [7, 8], // Index
                            [0, 9], [9, 10], [10, 11], [11, 12], // Middle
                            [0, 13], [13, 14], [14, 15], [15, 16], // Ring
                            [0, 17], [17, 18], [18, 19], [19, 20], // Pinky
                            [5, 9], [9, 13], [13, 17] // Palm
                        ];

                        for (const [start, end] of connections) {
                            const p1 = landmarks[start];
                            const p2 = landmarks[end];
                            ctx.beginPath();
                            ctx.moveTo((1 - p1.x) * canvas.width, p1.y * canvas.height);
                            ctx.lineTo((1 - p2.x) * canvas.width, p2.y * canvas.height);
                            ctx.stroke();
                        }

                        // Draw points
                        ctx.fillStyle = '#ff3366';
                        for (const point of landmarks) {
                            ctx.beginPath();
                            ctx.arc((1 - point.x) * canvas.width, point.y * canvas.height, 3, 0, Math.PI * 2);
                            ctx.fill();
                        }

                        // Detect gesture
                        const gesture = detectGesture(landmarks);
                        setCurrentGesture(gesture);

                        // Require holding gesture for 15 frames
                        if (gesture === lastGesture.current && gesture !== GESTURES.NONE) {
                            gestureHoldCount.current++;
                            if (gestureHoldCount.current === 15) {
                                setGesture({ type: gesture });
                                executeGestureAction(gesture);
                            }
                        } else {
                            lastGesture.current = gesture;
                            gestureHoldCount.current = 0;
                        }
                    } else {
                        setCurrentGesture(GESTURES.NONE);
                    }
                });

                // Process frames
                const processFrame = async () => {
                    if (!mounted || !hands) return;
                    await hands.send({ image: video });
                    animationId = requestAnimationFrame(processFrame);
                };

                setIsActive(true);
                setError(null);
                processFrame();

            } catch (err) {
                console.error('[Gesture] Error:', err);
                setError(err.message);
                setIsActive(false);
            }
        };

        // Detect gesture from landmarks
        const detectGesture = (landmarks) => {
            const tips = [4, 8, 12, 16, 20]; // Finger tips
            const pips = [3, 6, 10, 14, 18]; // Finger PIPs
            const mcps = [2, 5, 9, 13, 17];  // Finger MCPs

            // Check each finger extended
            const extended = [];

            // Thumb (special case - check x distance)
            const thumbExtended = landmarks[4].x < landmarks[3].x;
            extended.push(thumbExtended);

            // Other fingers (check y position)
            for (let i = 1; i < 5; i++) {
                const tip = landmarks[tips[i]];
                const pip = landmarks[pips[i]];
                extended.push(tip.y < pip.y);
            }

            // Count extended fingers
            const extendedCount = extended.filter(Boolean).length;

            // Pinch: thumb and index tips close
            const pinchDist = Math.hypot(
                landmarks[4].x - landmarks[8].x,
                landmarks[4].y - landmarks[8].y
            );
            if (pinchDist < 0.05) return GESTURES.PINCH;

            // Palm: all 5 fingers extended
            if (extendedCount === 5) return GESTURES.PALM;

            // Point: only index extended
            if (extended[1] && !extended[2] && !extended[3] && !extended[4]) {
                return GESTURES.POINT;
            }

            // Fist: no fingers extended
            if (extendedCount === 0) return GESTURES.FIST;

            // Thumbs up: only thumb extended
            if (extended[0] && !extended[1] && !extended[2] && !extended[3] && !extended[4]) {
                return GESTURES.THUMBS_UP;
            }

            return GESTURES.NONE;
        };

        initGestures();

        return () => {
            mounted = false;
            if (animationId) cancelAnimationFrame(animationId);
            if (videoRef.current?.srcObject) {
                videoRef.current.srcObject.getTracks().forEach(t => t.stop());
            }
        };
    }, [enabled, executeGestureAction, setGesture]);

    if (!enabled) return null;

    return (
        <>
            {/* Hidden video source */}
            <video ref={videoRef} style={{ display: 'none' }} playsInline muted />

            {/* Visible webcam canvas - Bottom Left */}
            <div style={{
                position: 'fixed',
                bottom: 40,
                left: 20,
                width: 200,
                height: 150,
                borderRadius: 12,
                overflow: 'hidden',
                border: `2px solid ${isActive ? 'var(--neural-blue)' : 'var(--neural-red)'}`,
                boxShadow: isActive ? '0 0 20px rgba(0, 212, 255, 0.3)' : 'none',
                zIndex: 9000,
                background: '#000'
            }}>
                <canvas
                    ref={canvasRef}
                    width={200}
                    height={150}
                    style={{ width: '100%', height: '100%' }}
                />

                {/* Gesture label */}
                <div style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    padding: '4px 8px',
                    background: 'rgba(0, 0, 0, 0.7)',
                    color: currentGesture !== GESTURES.NONE ? 'var(--neural-gold)' : 'var(--text-muted)',
                    fontSize: 11,
                    fontFamily: 'var(--font-display)',
                    textAlign: 'center',
                    textTransform: 'uppercase'
                }}>
                    {currentGesture !== GESTURES.NONE ? `👋 ${currentGesture}` : (isActive ? '👋 Ready' : '⏳ Loading...')}
                </div>

                {/* Error overlay */}
                {error && (
                    <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(255, 51, 102, 0.9)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: 9,
                        padding: 8,
                        textAlign: 'center',
                        flexDirection: 'column'
                    }}>
                        <div>📷 {error}</div>
                        <div style={{ marginTop: 4, fontSize: 8, opacity: 0.8 }}>
                            Check camera permissions
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}

export default GestureController;
export { GESTURES };
