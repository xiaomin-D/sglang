import asyncio
import aiohttp
import json
import random

prompt_collection = [
    "The ancient ruins stood silently under the starlit sky, their weathered stones holding secrets of civilizations long forgotten. Archaeological teams had spent decades",
    "Deep in the quantum physics laboratory, scientists observed an unprecedented phenomenon. The particles were behaving in ways that defied our current understanding",
    "The artificial intelligence system displayed unexpected behavior during the routine maintenance check. Engineers noticed patterns emerging in the neural networks that",
    "Climate researchers in Antarctica made a startling discovery beneath the ice sheets. Their advanced scanning equipment revealed a network of underground chambers",
    "The genetic modification breakthrough promised to revolutionize modern medicine. Clinical trials showed remarkable success in treating previously incurable diseases",
    "Space telescopes captured an anomalous signal from a distant galaxy cluster. Astronomers worldwide began analyzing the mysterious electromagnetic frequencies that",
    "In the depths of the Amazon rainforest, botanists identified a new species of plant with extraordinary properties. Initial tests suggested it could synthesize",
    "The cybersecurity team detected an unusual pattern in the global network traffic. The sophisticated algorithm they developed highlighted potential vulnerabilities",
    "Marine biologists studying deep-sea ecosystems found evidence of previously unknown life forms. The hydrothermal vents harbored organisms that could survive in",
    "The experimental quantum computer achieved a breakthrough in processing capability. Its novel architecture allowed for simultaneous calculations that traditional"
]

async def send_request(session, delay):
    # Wait for the specified delay
    await asyncio.sleep(delay)
    
    url = "http://127.0.0.1:30001/generate"
    headers = {"Content-Type": "application/json"}
    payload = {
        "text": prompt_collection[random.randint(0, len(prompt_collection) - 1)],
        "sampling_params": {
            "temperature": 0,
        },
        "is_prefill": "true"
    }
    
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            print(f"Response after {delay}s delay:", result)
            return result
    except Exception as e:
        print(f"Error after {delay}s delay:", str(e))
        return None

async def main():
    # Create delays for multiple requests (in seconds)
    delays = [i * 0.001 for i in range(20)]
    
    async with aiohttp.ClientSession() as session:
        # Create tasks for each request with different delays
        tasks = [send_request(session, delay) for delay in delays]
        # Wait for all requests to complete
        results = await asyncio.gather(*tasks)
        
        # Print final results
        for delay, result in zip(delays, results):
            if result:
                print(f"\nFinal result for {delay}s delay:", result)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
