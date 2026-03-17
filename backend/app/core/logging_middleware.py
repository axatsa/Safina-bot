import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger
import traceback

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture basic request info
        request_info = {
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "query_params": str(request.query_params)
        }
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response info
            log_data = {
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
                **request_info
            }
            
            # Log 4xx and 5xx errors with higher priority
            if response.status_code >= 500:
                logger.error(f"Server Error: {request.method} {request.url.path}", extra={"extra_info": log_data})
            elif response.status_code >= 400:
                logger.warning(f"Client Error: {request.method} {request.url.path}", extra={"extra_info": log_data})
            else:
                logger.info(f"Request: {request.method} {request.url.path}", extra={"extra_info": log_data})
                
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            error_data = {
                "exception": str(e),
                "traceback": traceback.format_exc(),
                "process_time_ms": round(process_time * 1000, 2),
                **request_info
            }
            logger.error(f"Unhandled Exception: {request.method} {request.url.path}", extra={"extra_info": error_data})
            # Re-raise to let FastAPI handle it or return a generic error response
            raise e
