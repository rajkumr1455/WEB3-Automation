"""
Circuit Breaker Implementation for Agent Calls
Prevents cascading failures when agents fail repeatedly
"""
from pybreaker import CircuitBreaker, CircuitBreakerError
import logging
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Prometheus metrics for circuit breakers
CIRCUIT_BREAKER_OPENS = Counter('circuit_breaker_opens_total', 'Circuit breaker opens', ['agent'])
CIRCUIT_BREAKER_FAILURES = Counter('circuit_breaker_failures_total', 'Circuit breaker failures', ['agent'])


def create_agent_circuit_breaker(agent_name: str) -> CircuitBreaker:
    """
    Create a circuit breaker for an agent
    
    Args:
        agent_name: Name of the agent (recon, static, fuzzing, etc.)
        
    Returns:
        Configured CircuitBreaker instance
    """
    
    def on_open(breaker, _):
        """Called when circuit breaker opens"""
        logger.warning(f"Circuit breaker OPENED for {agent_name} agent", extra={
            'event': 'circuit_breaker_open',
            'agent': agent_name,
            'fail_count': breaker.fail_counter
        })
        CIRCUIT_BREAKER_OPENS.labels(agent=agent_name).inc()
    
    def on_close(breaker):
        """Called when circuit breaker closes"""
        logger.info(f"Circuit breaker CLOSED for {agent_name} agent", extra={
            'event': 'circuit_breaker_close',
            'agent': agent_name
        })
    
    def on_half_open(breaker):
        """Called when circuit breaker enters half-open state"""
        logger.info(f"Circuit breaker HALF-OPEN for {agent_name} agent (testing recovery)", extra={
            'event': 'circuit_breaker_half_open',
            'agent': agent_name
        })
    
    breaker = CircuitBreaker(
        fail_max=5,  # Open after 5 failures
        timeout_duration=60,  # Try to close after 60 seconds
        expected_exception=(Exception,),  # Catch all exceptions
        name=f"{agent_name}_circuit_breaker",
        listeners=[
            (on_open, CircuitBreaker.STATE_OPEN),
            (on_close, CircuitBreaker.STATE_CLOSED),
            (on_half_open, CircuitBreaker.STATE_HALF_OPEN)
        ]
    )
    
    return breaker


# Global circuit breakers for each agent
AGENT_CIRCUIT_BREAKERS = {}


def get_circuit_breaker(agent_name: str) -> CircuitBreaker:
    """
    Get or create circuit breaker for an agent
    
    Args:
        agent_name: Agent name
        
    Returns:
        CircuitBreaker instance
    """
    if agent_name not in AGENT_CIRCUIT_BREAKERS:
        AGENT_CIRCUIT_BREAKERS[agent_name] = create_agent_circuit_breaker(agent_name)
    
    return AGENT_CIRCUIT_BREAKERS[agent_name]


def call_with_circuit_breaker(agent_name: str, func, *args, **kwargs):
    """
    Call a function with circuit breaker protection
    
    Args:
        agent_name: Agent name for circuit breaker
        func: Function to call
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        Function result
        
    Raises:
        CircuitBreakerError: If circuit is open
        Exception: Original exception from function
    """
    breaker = get_circuit_breaker(agent_name)
    
    try:
        return breaker.call(func, *args, **kwargs)
    except CircuitBreakerError:
        # Circuit is open
        logger.error(f"Circuit breaker OPEN for {agent_name} - request rejected", extra={
            'event': 'circuit_breaker_rejection',
            'agent': agent_name
        })
        raise Exception(f"Agent {agent_name} is temporarily unavailable (circuit breaker open)")
    except Exception as e:
        # Track failures
        CIRCUIT_BREAKER_FAILURES.labels(agent=agent_name).inc()
        logger.error(f"Agent {agent_name} call failed", extra={
            'event': 'agent_call_failed',
            'agent': agent_name,
            'error': str(e)
        })
        raise


def reset_all_circuit_breakers():
    """Reset all circuit breakers (for testing or recovery)"""
    for agent_name, breaker in AGENT_CIRCUIT_BREAKERS.items():
        breaker.close()
        logger.info(f"Circuit breaker reset for {agent_name}", extra={
            'event': 'circuit_breaker_reset',
            'agent': agent_name
        })


def get_circuit_breaker_status() -> dict:
    """
    Get status of all circuit breakers
    
    Returns:
        Dict mapping agent names to their breaker status
    """
    return {
        agent_name: {
            'state': breaker.current_state,
            'fail_count': breaker.fail_counter,
            'last_failure': str(breaker.last_failure_time) if breaker.last_failure_time else None
        }
        for agent_name, breaker in AGENT_CIRCUIT_BREAKERS.items()
    }
