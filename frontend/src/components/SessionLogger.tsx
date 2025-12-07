import { useEffect } from 'react';

// Using a dedicated fetch to avoid circular dependencies with API clients
const LOG_ENDPOINT = '/api/v1/client-logs';

export const SessionLogger = () => {
    useEffect(() => {
        // Save original methods
        const originalLog = console.log;
        const originalInfo = console.info;
        const originalWarn = console.warn;
        const originalError = console.error;

        const sendLog = (level: string, ...args: any[]) => {
            try {
                const message = args.map(arg => {
                    if (typeof arg === 'object') {
                        try {
                            return JSON.stringify(arg);
                        } catch (e) {
                            return String(arg);
                        }
                    }
                    return String(arg);
                }).join(' ');

                const timestamp = new Date().toISOString();

                // Use keepalive to ensure logs are sent even during navigation
                fetch(LOG_ENDPOINT, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        level,
                        message,
                        timestamp
                    }),
                    keepalive: true
                }).catch(() => {
                    // Put a catch here to prevent infinite loop if logging fails
                });
            } catch (err) {
                // Fallback
            }
        };

        // Override
        console.log = (...args) => {
            originalLog(...args);
            sendLog('log', ...args);
        };

        console.info = (...args) => {
            originalInfo(...args);
            sendLog('info', ...args);
        };

        console.warn = (...args) => {
            originalWarn(...args);
            sendLog('warn', ...args);
        };

        console.error = (...args) => {
            originalError(...args);
            sendLog('error', ...args);
        };

        return () => {
            // Restore
            console.log = originalLog;
            console.info = originalInfo;
            console.warn = originalWarn;
            console.error = originalError;
        };
    }, []);

    return null;
};
