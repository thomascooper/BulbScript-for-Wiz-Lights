import asyncio
import socket
import json
from typing import Dict, Set
from rooms import ROOMS

DISCOVERY_PORT = 38899
REGISTER_MESSAGE = b'{"method":"registration","params":{"phoneMac":"AAAAAAAAAAAA","register":false,"phoneIp":"1.2.3.4","id":"1"}}'

class BulbDiscovery:
    @staticmethod
    def get_all_macs_from_rooms() -> Set[str]:
        """Get all MAC addresses from room configurations."""
        macs = set()
        for room in ROOMS.values():
            macs.update(room["lights"].values())
        return macs

    @staticmethod
    async def discover_bulbs(required_macs: Set[str] = None, retry_missing: bool = True) -> Dict[str, str]:
        """Discover bulbs and return dict of MAC -> IP mappings."""
        if required_macs is None:
            required_macs = BulbDiscovery.get_all_macs_from_rooms()

        mac_to_ip = {}
        
        # Get broadcast IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
            broadcast_ip = f"{'.'.join(local_ip.split('.')[:3])}.255"
        finally:
            s.close()

        # First discovery attempt
        mac_to_ip = await BulbDiscovery._do_discovery(broadcast_ip)
        
        # Check if we need to retry for missing MACs
        if retry_missing:
            missing_macs = required_macs - set(mac_to_ip.keys())
            if missing_macs:
                print(f"Missing {len(missing_macs)} bulbs, retrying discovery...")
                retry_results = await BulbDiscovery._do_discovery(broadcast_ip)
                
                # Only add new MACs that weren't found in first attempt
                for mac, ip in retry_results.items():
                    if mac not in mac_to_ip:
                        mac_to_ip[mac] = ip

        return mac_to_ip

    @staticmethod
    async def _do_discovery(broadcast_ip: str, timeout: int = 2) -> Dict[str, str]:
        """Perform one discovery attempt."""
        mac_to_ip = {}
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', DISCOVERY_PORT))
        sock.settimeout(timeout)

        try:
            sock.sendto(REGISTER_MESSAGE, (broadcast_ip, DISCOVERY_PORT))
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    ip = addr[0]
                    try:
                        resp = json.loads(data.decode())
                        mac = resp.get("result", {}).get("mac")
                        if mac:
                            mac_to_ip[mac] = ip
                            print(f"Found bulb at {ip} (MAC: {mac})")
                    except json.JSONDecodeError:
                        print(f"Found bulb at {ip}")
                except socket.timeout:
                    await asyncio.sleep(0.1)
        finally:
            sock.close()

        return mac_to_ip