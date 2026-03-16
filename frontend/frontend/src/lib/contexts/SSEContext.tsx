import React, { createContext, useContext, useEffect, useState } from 'react';
import { toast } from 'sonner';

interface SSEContextType {
    isConnected: boolean;
}

const SSEContext = createContext<SSEContextType>({ isConnected: false });

export const useSSE = () => useContext(SSEContext);

export const SSEProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        // We only connect if we have a token (user is logged in)
        const token = localStorage.getItem('safina_token');
        if (!token) return;

        // Use EventSource to connect to our new backend endpoint
        // Add token to URL query param or rely on cookie if set
        // Here we'll pass it in URL since EventSource doesn't support custom headers easily natively
        // We assume backend auth middleware can check query params if needed, or we adapt as needed.
        const baseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
        const url = new URL('/api/notifications/stream', baseUrl);
        url.searchParams.append('token', token);

        const eventSource = new EventSource(url.toString());

        eventSource.onopen = () => {
            console.log('SSE connection opened.');
            setIsConnected(true);
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('SSE message received:', data);

                // Show a UI toast map
                if (data.title && data.message) {
                    toast(data.title, { description: data.message });
                } else {
                    toast('Новое уведомление', { description: JSON.stringify(data) });
                }
            } catch (err) {
                console.error('Error parsing SSE message:', err);
            }
        };

        eventSource.onerror = (err) => {
            console.error('SSE connection error:', err);
            setIsConnected(false);
            eventSource.close();

            // Attempt to reconnect after a delay
            setTimeout(() => {
                // Simple reconnect logic, in production you'd want exponential backoff
            }, 5000);
        };

        return () => {
            eventSource.close();
            setIsConnected(false);
        };
    }, []);

    return (
        <SSEContext.Provider value={{ isConnected }}>
            {children}
        </SSEContext.Provider>
    );
};
