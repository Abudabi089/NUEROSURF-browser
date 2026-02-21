import React, { useState, useCallback } from 'react';

function CommandInput({ value, onChange, onSubmit }) {
    const [isFocused, setIsFocused] = useState(false);

    const handleKeyDown = useCallback((e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSubmit(value);
        }
    }, [value, onSubmit]);

    return (
        <div style={{
            position: 'fixed',
            bottom: 40,
            left: 240, // After webcam
            right: 360, // Before ThoughtStream
            padding: '0 20px',
            zIndex: 200
        }}>
            <div style={{
                padding: '12px 20px',
                background: 'rgba(10, 10, 20, 0.95)',
                border: `1px solid ${isFocused ? 'var(--neural-gold)' : 'var(--neural-blue)'}`,
                borderRadius: 30,
                boxShadow: isFocused ? '0 0 20px rgba(255, 215, 0, 0.3)' : '0 0 15px rgba(0, 212, 255, 0.2)'
            }}>
                <input
                    type="text"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    placeholder="Ask Neuro anything... (/research <topic> for 3D cards)"
                    style={{
                        width: '100%',
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        fontSize: 15,
                        color: 'white',
                        fontFamily: 'var(--font-body)'
                    }}
                />
            </div>
        </div>
    );
}

export default CommandInput;
