import React, { createContext, useContext, useEffect, useState } from 'react';
import { toast } from 'sonner';

interface SSEContextType {
    isConnected: boolean;
}

const SSEContext = createContext<SSEContextType>({ isConnected: false });

export const useSSE = () => useContext(SSEContext);

export const SSEProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isConnected, setIsConnected] = useState(false);

    const [token, setToken] = useState<string | null>(localStorage.getItem("safina_token"));

    useEffect(() => {
        const handleStorageChange = () => {
            setToken(localStorage.getItem("safina_token"));
        };

        window.addEventListener("storage", handleStorageChange);
        // Also check periodically or on focus as 'storage' event only fires from other tabs
        const interval = setInterval(handleStorageChange, 2000);

        return () => {
            window.removeEventListener("storage", handleStorageChange);
            clearInterval(interval);
        };
    }, []);

    useEffect(() => {
        if (!token) {
            setIsConnected(false);
            return;
        }

        const baseUrl = import.meta.env.VITE_APP_API_URL || 
                        import.meta.env.VITE_API_URL || 
                        import.meta.env.VITE_API_BASE_URL || 
                        window.location.origin;
        // Ensure baseUrl is a valid URL string
        let validBaseUrl = baseUrl;
        if (!baseUrl.startsWith('http')) {
            validBaseUrl = window.location.origin;
        }
        
        try {
            const url = new URL('/api/notifications/stream', validBaseUrl);
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
        } catch (err) {
            console.error('Failed to create EventSource:', err);
        }
    }, [token]);

    return (
        <SSEContext.Provider value={{ isConnected }}>
            {children}
        </SSEContext.Provider>
    );
};
