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
            
            // Task 2: Token is now handled via Cookies (Task 2 backend)
            // We removed url.searchParams.append('token', token)
            const url = new URL(`${import.meta.env.VITE_API_BASE_URL || ''}/api/notifications/stream`);
            
            // Note: Even if we use cookies, we might want withCredentials if on different subdomains
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

                    // Task 6: Invalidate queries on any notification to keep data fresh
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

                // Task 1: Exponential backoff
                const delay = Math.min(Math.pow(2, reconnectCount) * 1000, 30000);
                console.log(`Reconnecting in ${delay}ms...`);
                
                if (reconnectCount < 10) {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        setReconnectCount(prev => prev + 1);
                        connect();
                    }, delay);
                } else {
                    toast.error('Не удалось восстановить связь с сервером. Пожалуйста, обновите страницу.');
                }
            };
        };

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
