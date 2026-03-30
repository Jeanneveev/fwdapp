// webrtc/scripts/config.js
// Override WS_URL for production deployment.
export const WS_URL = 'ws://localhost:8765';

export const ICE_SERVERS = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
];
