import asyncio
from pywizlight import wizlight

async def test_direct_connection():
    bulb = None
    try:
        bulb = wizlight("192.168.1.53")  # Replace with actual bulb IP
        await bulb.turn_on()
        print("Successfully connected to bulb!")
        
        # Let's also try to get the bulb's state
        state = await bulb.updateState()
        print(f"Bulb state: {state}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        if bulb:
            await bulb.async_close()

if __name__ == "__main__":
    asyncio.run(test_direct_connection())
