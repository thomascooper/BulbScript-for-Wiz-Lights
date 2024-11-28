import asyncio
from typing import Dict, List
from pywizlight import wizlight, PilotBuilder
from light_patterns import PATTERNS
from rooms import ROOMS
from discovery import BulbDiscovery
from dataclasses import dataclass

@dataclass
class Color:
    r: int
    g: int
    b: int

    @classmethod
    def from_tuple(cls, color_tuple: tuple[int, int, int]) -> 'Color':
        return cls(r=color_tuple[0], g=color_tuple[1], b=color_tuple[2])

class LightController:
    def __init__(self):
        self.active_sequences: Dict[str, asyncio.Task] = {}
        self.mac_to_ip: Dict[str, str] = {}

    async def initialize(self):
        """Discover bulbs and create MAC to IP mapping."""
        required_macs = BulbDiscovery.get_all_macs_from_rooms()
        self.mac_to_ip = await BulbDiscovery.discover_bulbs(required_macs=required_macs, retry_missing=True)
        
        found_macs = set(self.mac_to_ip.keys())
        missing_macs = required_macs - found_macs
        
        print(f"Discovered {len(self.mac_to_ip)} bulbs")
        if missing_macs:
            print("Warning: Could not find the following bulbs:")
            for mac in missing_macs:
                for room in ROOMS.values():
                    for bulb_name, bulb_mac in room["lights"].items():
                        if bulb_mac == mac:
                            print(f"  - {bulb_name} (MAC: {mac})")

    async def initialize_rooms(self, room_ids: List[str]) -> Dict[str, List[wizlight]]:
        room_bulbs = {}
        for room_id in room_ids:
            room = ROOMS.get(room_id)
            if not room:
                print(f"Room {room_id} not found!")
                continue

            bulbs = []
            for bulb_name, mac in room["lights"].items():
                ip = self.mac_to_ip.get(mac)
                if not ip:
                    print(f"No IP found for bulb {bulb_name} (MAC: {mac})")
                    continue
                
                try:
                    bulb = wizlight(ip)
                    await bulb.updateState()
                    bulbs.append(bulb)
                    print(f"Connected to {bulb_name} at {ip} (MAC: {mac})")
                except Exception as e:
                    print(f"Failed to connect to {bulb_name} at {ip}: {e}")
            room_bulbs[room_id] = bulbs
        return room_bulbs

    async def cleanup_rooms(self, room_bulbs: Dict[str, List[wizlight]]):
        for bulbs in room_bulbs.values():
            for bulb in bulbs:
                try:
                    await bulb.async_close()
                except Exception:
                    pass

    async def set_bulb_color(self, bulb: wizlight, color_tuple: tuple[int, int, int], brightness: int, force_on: bool = False):
        """Set bulb color with brightness."""
        try:
            # Convert tuple to Color object
            color = Color.from_tuple(color_tuple)
            
            # Clamp brightness between 1 and 100
            brightness = max(1, min(100, brightness))
            
            if force_on:
                await bulb.turn_on(PilotBuilder(
                    rgb=(color.r, color.g, color.b),
                    brightness=brightness
                ))
            else:
                state = await bulb.updateState()
                if state and state.get_state():
                    await bulb.turn_on(PilotBuilder(
                        rgb=(color.r, color.g, color.b),
                        brightness=brightness
                    ))
        except Exception as e:
            print(f"Error setting color for bulb {bulb.ip}: {e}")

    async def run_pattern_on_rooms(self, sequence_id: str, room_ids: List[str], pattern_id: str, brightness: int = 100, force_on: bool = False):
        pattern = PATTERNS.get(pattern_id)
        if not pattern:
            print(f"Pattern {pattern_id} not found!")
            return

        room_bulbs = await self.initialize_rooms(room_ids)
        if not room_bulbs:
            return

        try:
            color_index = 0
            count = 0
            while True:
                all_bulbs = []
                for room_id in room_ids:
                    room = ROOMS.get(room_id)
                    if not room:
                        continue
                    for mac in room["lights"].values():
                        ip = self.mac_to_ip.get(mac)
                        if ip:
                            for bulb in room_bulbs[room_id]:
                                if bulb.ip == ip:
                                    all_bulbs.append(bulb)
                                    break
                if count == 0:  
                    print(f"Cycling {len(all_bulbs)} bulbs in {sequence_id} with {pattern.name}")
                count += 1
                
                for i, bulb in enumerate(all_bulbs):
                    current_color = pattern.colors[(color_index + i) % len(pattern.colors)]
                    await self.set_bulb_color(bulb, current_color, brightness, force_on)
                
                await asyncio.sleep(pattern.interval)
                color_index = (color_index + 1) % len(pattern.colors)
                
        except asyncio.CancelledError:
            room_names = [ROOMS[room_id]['name'] for room_id in room_ids]
            print(f"Stopping sequence {sequence_id} for rooms: {', '.join(room_names)}")
        finally:
            await self.cleanup_rooms(room_bulbs)

    async def start_sequence(self, sequence_id: str, room_ids: List[str], pattern_id: str, brightness: int = 100, force_on: bool = False):
        if sequence_id in self.active_sequences:
            print(f"Sequence {sequence_id} already running")
            return

        task = asyncio.create_task(self.run_pattern_on_rooms(sequence_id, room_ids, pattern_id, brightness, force_on))
        self.active_sequences[sequence_id] = task
        room_names = [ROOMS[room_id]['name'] for room_id in room_ids]
        print(f"Started {PATTERNS[pattern_id].name} on rooms: {', '.join(room_names)} at {brightness}% brightness")

    async def stop_sequence(self, sequence_id: str):
        if sequence_id in self.active_sequences:
            self.active_sequences[sequence_id].cancel()
            await self.active_sequences[sequence_id]
            del self.active_sequences[sequence_id]
