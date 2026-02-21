import React, { useEffect, useRef } from 'react';
import socketManager from '../services/socketManager';
import useDraggable from '../hooks/useDraggable';

const WebcamController = ({ enabled }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const intervalRef = useRef(null);

    const { position, onMouseDown } = useDraggable({ x: 10, y: window.innerHeight - 250 }, 'neuro_webcam_pos');

    useEffect(() => {
        if (!enabled) {
            stopWebcam();
            return;
        }

        startWebcam();

        return () => stopWebcam();
    }, [enabled]);

    const startWebcam = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 320, height: 240, frameRate: 5 }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }

            // Start sending frames periodically
            intervalRef.current = setInterval(captureAndSend, 1000); // 1 FPS for efficiency
        } catch (err) {
            console.error("Error accessing webcam:", err);
        }
    };

    const stopWebcam = () => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }
        if (videoRef.current && videoRef.current.srcObject) {
            videoRef.current.srcObject.getTracks().forEach(track => track.stop());
            videoRef.current.srcObject = null;
        }
    };

    const captureAndSend = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.5); // 0.5 quality for speed
            socketManager.sendWebcamFrame(dataUrl);
        }
    };

    if (!enabled) return null;

    return (
        <div
            onMouseDown={onMouseDown}
            style={{
                position: 'fixed',
                left: position.x,
                top: position.y,
                zIndex: 1000,
                cursor: 'move',
                padding: '4px',
                background: 'rgba(0,0,0,0.5)',
                borderRadius: '10px',
                border: '1px solid var(--neural-blue)',
                boxShadow: '0 0 15px rgba(0, 243, 255, 0.3)'
            }}
        >
            <video
                ref={videoRef}
                autoPlay
                playsInline
                style={{ width: 160, height: 120, borderRadius: 6, display: 'block' }}
            />
            <canvas ref={canvasRef} width="320" height="240" style={{ display: 'none' }} />
            <div style={{ fontSize: 9, color: 'var(--neural-blue)', textAlign: 'center', marginTop: 4, fontFamily: 'monospace', fontWeight: 'bold' }}>
                NEURAL_VISION_ACTIVE
            </div>
        </div>
    );
};

export default WebcamController;
