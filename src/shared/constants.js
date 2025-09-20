module.exports = {
    APP_NAME: 'Clarity',

    IPC_CHANNELS: {
        APP_CLOSE: 'app:close',
        VOICE_START: 'voice:start',
        VOICE_STOP: 'voice:stop',
        VOICE_STATUS: 'voice:status',
        VOICE_ERROR: 'voice:error',
        AUDIO_LEVEL: 'audio:level',
        SETTINGS_GET: 'settings:get',
        SETTINGS_SET: 'settings:set'
    },

    LIVEKIT: {
        DEFAULT_ROOM_PREFIX: 'clarity',
        TOKEN_TTL: '10h',
        RECONNECT_ATTEMPTS: 3,
        RECONNECT_DELAY: 1000
    },

    WINDOW: {
        DEFAULT_WIDTH: 240,
        DEFAULT_HEIGHT: 60,
        DEFAULT_X: 20,
        DEFAULT_Y: 20
    },

    AUDIO: {
        SAMPLE_RATE: 48000,
        CHANNELS: 1,
        FRAME_SIZE: 960
    }
};