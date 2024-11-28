import asyncio
from light_controller import LightController

async def main():
    controller = LightController()
    
    # Configure your sequences here
    # Each sequence is (sequence_id, [room_ids], pattern_id, brightness, force_on)
    sequences = [
        ("porch_christmas_lights", ["front_porch"], "80s_christmas", 100, True),
        # ("kitchen_christmas_lights", ["kitchen_full"], "80s_christmas", 10, False),
    ]
    
    try:
        await controller.initialize()
        
        for sequence_id, room_ids, pattern_id, brightness, force_on in sequences:
            await controller.start_sequence(sequence_id, room_ids, pattern_id, brightness, force_on)
        
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all sequences...")
        for sequence_id in list(controller.active_sequences.keys()):
            await controller.stop_sequence(sequence_id)

if __name__ == "__main__":
    print("Starting light sequences. Press Ctrl+C to stop.")
    asyncio.run(main()) 