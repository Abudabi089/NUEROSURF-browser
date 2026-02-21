import React, { useEffect, useState } from 'react';

function GestureFeedback({ gesture }) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (gesture) {
            setVisible(true);
            const timer = setTimeout(() => setVisible(false), 1500);
            return () => clearTimeout(timer);
        }
    }, [gesture]);

    const getGestureLabel = () => {
        switch (gesture?.type) {
            case 'pinch': return '🤏 Rotate';
            case 'palm': return '✋ Halt';
            case 'point': return '👆 Point';
            case 'fist': return '✊ Grab';
            default: return gesture?.type || '';
        }
    };

    if (!gesture) return null;

    return (
        <div className={`gesture-feedback ${visible ? 'gesture-feedback--visible' : ''}`}>
            {getGestureLabel()}
        </div>
    );
}

export default GestureFeedback;
