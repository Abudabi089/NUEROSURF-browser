import { useState, useCallback, useEffect } from 'react';

const useDraggable = (initialPos = { x: 0, y: 0 }, storageKey = null) => {
    const [position, setPosition] = useState(() => {
        if (storageKey) {
            const saved = localStorage.getItem(storageKey);
            if (saved) return JSON.parse(saved);
        }
        return initialPos;
    });

    const [isDragging, setIsDragging] = useState(false);
    const [rel, setRel] = useState(null); // relative mouse position inside the element

    const onMouseDown = useCallback((e) => {
        if (e.button !== 0) return;
        setIsDragging(true);
        const rect = e.currentTarget.getBoundingClientRect();
        setRel({
            x: e.pageX - rect.left,
            y: e.pageY - rect.top
        });
        e.stopPropagation();
    }, []);

    const onMouseMove = useCallback((e) => {
        if (!isDragging) return;
        const newX = e.pageX - rel.x;
        const newY = e.pageY - rel.y;
        setPosition({ x: newX, y: newY });
        e.preventDefault();
    }, [isDragging, rel]);

    const onMouseUp = useCallback(() => {
        setIsDragging(false);
        if (storageKey) {
            localStorage.setItem(storageKey, JSON.stringify(position));
        }
    }, [position, storageKey]);

    useEffect(() => {
        if (isDragging) {
            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', onMouseUp);
        } else {
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
        }
        return () => {
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
        };
    }, [isDragging, onMouseMove, onMouseUp]);

    return {
        position,
        onMouseDown,
        isDragging
    };
};

export default useDraggable;
