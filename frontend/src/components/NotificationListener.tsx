import { useEffect } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { store } from "@/lib/store";

const NotificationListener = () => {
  const queryClient = useQueryClient();
  const isAdmin = store.isAdmin();
  const token = localStorage.getItem("safina_token");

  useEffect(() => {
    if (!token) return;

    const apiBaseUrl = import.meta.env.VITE_APP_API_URL || "/api";
    const sseUrl = `${apiBaseUrl}/notifications/stream?token=${token}`;
    
    console.log("Connecting to SSE:", sseUrl);
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("SSE Message received:", data);
        
        // Show toast
        toast(data.title || "Уведомление", {
          description: data.message,
          duration: 5000,
        });

        // Invalidate relevant queries
        queryClient.invalidateQueries({ queryKey: ["admin-expenses-approvals"] });
        queryClient.invalidateQueries({ queryKey: ["expenses"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
        
      } catch (err) {
        console.error("Error parsing SSE data:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Connection error:", err);
      // EventSource automatically retries
    };

    return () => {
      eventSource.close();
    };
  }, [token, queryClient]);

  return null;
};

export default NotificationListener;
