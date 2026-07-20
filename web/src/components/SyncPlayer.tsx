import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, IconButton, Dialog, DialogContent, DialogTitle } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

export const SyncPlayer: React.FC = () => {
    const [open, setOpen] = useState(false);
    const [mediaUrl, setMediaUrl] = useState<string>('');
    const [isPlaying, setIsPlaying] = useState(false); // keep it for potential future use, or let's use it or remove it
    
    const wsRef = useRef<WebSocket | null>(null);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

    const connectWebSocket = () => {
        // Build WS URL based on current host
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Assume API is on same host or fallback to 8000
        const host = import.meta.env.DEV ? '127.0.0.1:8000' : window.location.host;
        const deviceName = "Web-Device-" + Math.floor(Math.random() * 10000);
        
        const wsUrl = `${protocol}//${host}/api/sync/ws?device_name=${deviceName}`;
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('[SyncPlay] Connected to server.');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('[SyncPlay] Command received:', data);
                
                if (data.type === 'LOAD' && data.url) {
                    // API url might need base URL if running in dev
                    const baseUrl = import.meta.env.DEV ? 'http://127.0.0.1:8000' : '';
                    setMediaUrl(baseUrl + data.url);
                    setOpen(true);
                    setIsPlaying(true);
                } 
                else if (data.type === 'PLAY') {
                    setIsPlaying(true);
                    videoRef.current?.play().catch(e => console.error("Play error", e));
                }
                else if (data.type === 'PAUSE') {
                    setIsPlaying(false);
                    videoRef.current?.pause();
                }
                else if (data.type === 'TOGGLE_PLAY') {
                    setIsPlaying(prev => {
                        if (prev) videoRef.current?.pause();
                        else videoRef.current?.play().catch(e => console.error("Play error", e));
                        return !prev;
                    });
                }
                else if (data.type === 'SEEK' && data.time !== undefined) {
                    if (videoRef.current) {
                        videoRef.current.currentTime = data.time;
                    }
                }
            } catch (err) {
                console.error("Error parsing WS message", err);
            }
        };

        ws.onclose = () => {
            console.log('[SyncPlay] Disconnected. Reconnecting in 3s...');
            reconnectTimeout.current = setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (err) => {
            console.error('[SyncPlay] WebSocket error:', err);
            ws.close();
        };
        
        wsRef.current = ws;
    };

    useEffect(() => {
        connectWebSocket();
        return () => {
            if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    const handleClose = () => {
        setOpen(false);
        setMediaUrl('');
        if (videoRef.current) {
            videoRef.current.pause();
        }
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
            <DialogTitle>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="h6">Sync Play (Watch Party) - Beta</Typography>
                    <IconButton onClick={handleClose}>
                        <CloseIcon />
                    </IconButton>
                </Box>
            </DialogTitle>
            <DialogContent sx={{ p: 0, bgcolor: 'black', display: 'flex', justifyContent: 'center' }}>
                {mediaUrl && (
                    <Box width="100%" display="flex" flexDirection="column" alignItems="center">
                        <video
                            ref={videoRef}
                            src={mediaUrl}
                            controls
                            autoPlay
                            style={{ width: '100%', maxHeight: '80vh' }}
                            onPlay={() => setIsPlaying(true)}
                            onPause={() => setIsPlaying(false)}
                        />
                        <Typography variant="caption" sx={{ color: 'white', mt: 1 }}>
                            Status: {isPlaying ? 'Playing' : 'Paused'}
                        </Typography>
                    </Box>
                )}
            </DialogContent>
        </Dialog>
    );
};
