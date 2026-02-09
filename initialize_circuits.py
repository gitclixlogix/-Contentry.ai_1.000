#!/usr/bin/env python3
"""
Initialize circuit breakers for testing
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, '/app/backend')

async def initialize_circuits():
    """Initialize circuit breakers"""
    try:
        from services.circuit_breaker_service import get_or_create_circuit
        
        # Initialize common circuit breakers
        circuits = ['openai', 'gemini', 'claude', 'stripe', 'ayrshare', 'vision_api']
        
        print("Initializing circuit breakers...")
        for circuit_name in circuits:
            circuit = await get_or_create_circuit(circuit_name)
            print(f"✅ Initialized circuit: {circuit_name}")
        
        print(f"✅ Successfully initialized {len(circuits)} circuit breakers")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize circuits: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(initialize_circuits())
    sys.exit(0 if success else 1)