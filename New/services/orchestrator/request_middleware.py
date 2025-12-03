"""
Request/Response Logging Middleware for FastAPI
Add this to app.py after CORS middleware
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import uuid

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Log incoming request
        logger.info("HTTP Request", extra={
            'event': 'http_request',
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'query': str(request.url.query) if request.url.query else None,
            'client_ip': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent')
        })
        
        try:
            # Process request
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.info("HTTP Response", extra={
                'event': 'http_response',
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms
            })
            
            # Add request ID to response headers for tracing
            response.headers['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error("HTTP Request Failed", extra={
                'event': 'http_error',
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'error': str(e),
                'error_type': type(e).__name__,
                'duration_ms': duration_ms
            })
            
            raise


# To add to app.py, insert after CORS middleware:
# app.add_middleware(RequestLoggingMiddleware)
