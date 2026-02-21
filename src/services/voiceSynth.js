
/**
 * Voice Synthesis Service for Neuro
 * Uses Browser Speech Synthesis API
 */

class VoiceSynth {
    constructor() {
        this.synth = window.speechSynthesis;
        this.voice = null;
        this.enabled = true;
        this.initialized = false;

        // Neuro's personality: Slightly robotic but friendly
        this.rate = 1.05;
        this.pitch = 0.9;
        this.volume = 0.8;
    }

    init() {
        if (this.initialized) return;

        const voices = this.synth.getVoices();
        // Try to find a futuristic/premium sounding voice
        this.voice = voices.find(v => v.name.includes('Google US English') || v.name.includes('Samantha')) || voices[0];

        // Listen for voice changes
        this.synth.onvoiceschanged = () => {
            const updatedVoices = this.synth.getVoices();
            this.voice = updatedVoices.find(v => v.name.includes('Google US English') || v.name.includes('Samantha')) || updatedVoices[0];
        };

        this.initialized = true;
    }

    speak(text) {
        if (!this.enabled || !text) return;

        // Stop any current speech
        this.synth.cancel();

        // Clean text (remove tool blocks, links, etc)
        const cleanText = text
            .replace(/https?:\/\/\S+/g, 'link')
            .replace(/\{"tool":.+?\}/g, '')
            .replace(/```.+?```/gs, 'code block')
            .trim();

        if (!cleanText) return;

        const utterance = new SpeechSynthesisUtterance(cleanText);
        if (this.voice) utterance.voice = this.voice;
        utterance.rate = this.rate;
        utterance.pitch = this.pitch;
        utterance.volume = this.volume;

        this.synth.speak(utterance);
    }

    stop() {
        this.synth.cancel();
    }

    setEnabled(val) {
        this.enabled = val;
        if (!val) this.stop();
    }
}

const voiceSynth = new VoiceSynth();
export default voiceSynth;
