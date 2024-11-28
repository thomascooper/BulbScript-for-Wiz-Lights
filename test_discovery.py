import asyncio
import socket
import json
from pywizlight import wizlight
from typing import Set

DISCOVERY_PORT = 38899
REGISTER_MESSAGE = b'{"method":"registration","params":{"phoneMac":"AAAAAAAAAAAA","register":false,"phoneIp":"1.2.3.4","id":"1"}}'

async def get_bulb_info(ip: str) -> dict:
    try:
        bulb = wizlight(ip)
        state = await bulb.updateState()
        
        info = {
            "ip": ip
        }
        
        if state:
            if state.get_state() is not None:
                info["state"] = "On" if state.get_state() else "Off"
            if state.get_brightness() is not None:
                info["brightness"] = state.get_brightness()
            if state.get_scene() is not None:
                info["scene"] = state.get_scene()
            if state.get_colortemp() is not None:
                info["colortemp"] = state.get_colortemp()
            if state.get_warm_white() is not None:
                info["warm_white"] = state.get_warm_white()
            if state.get_cold_white() is not None:
                info["cold_white"] = state.get_cold_white()
                
        return info
        
    except Exception as e:
        print(f"Error getting bulb info for {ip}: {str(e)}")
        return None

async def send_discovery_broadcast(broadcast_ip: str) -> Set[str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', DISCOVERY_PORT))
    sock.settimeout(2)
    
    found_ips = set()
    
    try:
        sock.sendto(REGISTER_MESSAGE, (broadcast_ip, DISCOVERY_PORT))
        
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < 2:
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                if ip not in found_ips:
                    found_ips.add(ip)
                    try:
                        resp = json.loads(data.decode())
                        mac = resp.get("result", {}).get("mac")
                        if mac:
                            print(f"Found bulb at {ip} (MAC: {mac})")
                        else:
                            print(f"Found bulb at {ip}")
                    except json.JSONDecodeError:
                        print(f"Found bulb at {ip}")
            except socket.timeout:
                await asyncio.sleep(0.1)
    finally:
        sock.close()
    
    return found_ips

async def discover_all_bulbs():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    
    broadcast_ip = f"{'.'.join(local_ip.split('.')[:3])}.255"
    print(f"Local IP: {local_ip}")
    print(f"Using broadcast address: {broadcast_ip}\n")
    
    found_devices = await send_discovery_broadcast(broadcast_ip)
    
    if not found_devices:
        print("\nNo bulbs found!")
        return
    
    print(f"\nFound {len(found_devices)} bulbs. Getting details...\n")
    
    for ip, mac in sorted(found_devices):
        info = await get_bulb_info(ip)
        if info:
            print(f"Bulb at {info['ip']}:")
            print(f"  MAC: {mac}")
            if 'state' in info:
                print(f"  State: {info['state']}")
            if 'brightness' in info:
                print(f"  Brightness: {info['brightness']}%")
            if 'scene' in info:
                print(f"  Scene: {info['scene']}")
            print()

if __name__ == "__main__":
    print("WiZ Light Discovery Tool")
    print("This will attempt to find all WiZ lights on your network")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(discover_all_bulbs())
    except KeyboardInterrupt:
        print("\nDiscovery stopped by user")