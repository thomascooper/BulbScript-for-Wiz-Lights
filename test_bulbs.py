import asyncio
import socket
import sys
from pywizlight import discovery

async def test_network():
    print("Network Test Results:")
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"Local IP: {local_ip}")
        
        # Test UDP broadcast capability
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((local_ip, 0))
        print("UDP broadcast capability: OK")
        sock.close()
        
    except Exception as e:
        print(f"Network test failed: {e}")
        return False
    return True

async def find_bulbs():
    print("\nStarting bulb discovery...")
    print("Using broadcast address: 192.168.1.255")
    print("Timeout set to 10 seconds...")
    
    try:
        bulbs = await asyncio.wait_for(
            discovery.discover_lights(
                broadcast_space="192.168.1.255",
                wait_time=5
            ),
            timeout=10
        )
        
        if not bulbs:
            print("\nNo bulbs found!")
        else:
            print(f"\nFound {len(bulbs)} bulbs:")
            for bulb in bulbs:
                print(f"Bulb IP: {bulb.ip}")
                
    except asyncio.TimeoutError:
        print("Discovery timed out - no bulbs responded")
    except Exception as e:
        print(f"Error during discovery: {e}")

async def main():
    if await test_network():
        await find_bulbs()
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript terminated by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
