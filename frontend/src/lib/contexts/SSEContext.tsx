import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { toast } from 'sonner';
import { useQueryClient } from '@tanstack/react-query';

interface SSEContextType {
    isConnected: boolean;
    reconnectCount: number;
}

const SSEContext = createContext<SSEContextType>({ isConnected: false, reconnectCount: 0 });

export const useSSE = () => useContext(SSEContext);

export const SSEProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [reconnectCount, setReconnectCount] = useState(0);
    const queryClient = useQueryClient();
    const eventSourceRef = useRef<EventSource | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    
    // We track the token to handle login/logout
    const [token, setToken] = useState<string | null>(localStorage.getItem('safina_token'));

    // Listen for storage changes (logout in other tabs)
    useEffect(() => {
        const handleStorage = () => {
            const currentToken = localStorage.getItem('safina_token');
            if (currentToken !== token) {
                setToken(currentToken);
            }
        };
        window.addEventListener('storage', handleStorage);
        
        // Also check periodically or via custom event if needed
        const interval = setInterval(handleStorage, 2000);
        
        return () => {
            window.removeEventListener('storage', handleStorage);
            clearInterval(interval);
        };
    }, [token]);

    useEffect(() => {
        if (!token) {
            if (eventSourceRef.current) {
                console.log('Closing SSE due to logout');
                eventSourceRef.current.close();
                eventSourceRef.current = null;
                setIsConnected(false);
            }
            return;
        }

        const connect = () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }

            console.log(`Connecting to SSE (Attempt ${reconnectCount + 1})...`);
            
            try {
                // Determing base URL safely
                const origin = window.location.origin;
                const apiBase = import.meta.env.VITE_APP_API_URL || "";
                
                // If apiBase is absolute, use it. Otherwise, use origin.
                const baseUrl = apiBase.startsWith("http") ? apiBase : origin;
                
                // Construct the URL safely
                const url = new URL('/api/notifications/stream', baseUrl);
                
                // Add token safely
                if (token) {
                    url.searchParams.append('token', token);
                }
                
                const es = new EventSource(url.toString(), { withCredentials: true });
                eventSourceRef.current = es;

                es.onopen = () => {
                    console.log('SSE connection established');
                    setIsConnected(true);
                    setReconnectCount(0);
                };

                es.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('SSE message received:', data);

                        // Invalidate queries to keep data fresh
                        queryClient.invalidateQueries();

                        if (data.title && data.message) {
                            toast(data.title, { description: data.message });
                        }
                    } catch (err) {
                        console.error('Error parsing SSE message:', err);
                    }
                };

                es.onerror = (err) => {
                    console.error('SSE connection error:', err);
                    setIsConnected(false);
                    es.close();
                    eventSourceRef.current = null;

                    // Exponential backoff
                    const delay = Math.min(Math.pow(2, reconnectCount) * 1000, 30000);
                    console.log(`Reconnecting in ${delay}ms...`);
                    
                    if (reconnectCount < 5) {
                        reconnectTimeoutRef.current = setTimeout(() => {
                            setReconnectCount(prev => prev + 1);
                            connect();
                        }, delay);
                    }
                };
            } catch (err) {
                console.error('Critical failure constructing SSE URL:', err);
            }
        };

        if (!token) return;
        connect();

        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [token, queryClient]); // Re-connect if token changes

    return (
        <SSEContext.Provider value={{ isConnected, reconnectCount }}>
            {children}
        </SSEContext.Provider>
    );
};
