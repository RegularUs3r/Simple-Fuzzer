#!/usr/bin/env python3

import argparse  # For parsing command-line arguments
import asyncio  # For asynchronous programming
import aiohttp  # For asynchronous HTTP requests
import time  # For time-related functions
import signal  # For handling signals
from urllib3 import disable_warnings  # For disabling warnings
from random import choice  # For random payload selection
import re
import sys

# Define a global variable for the event loop
loop = None

# Asynchronous function for making requests with fuzzing in the body
async def fuzz_request_body(session, method, host, path, headers, body, proxy, filter_size, filter_code, delay, counter, lock, semaphore, word1, word2, check_word):
    # Limit the number of concurrent tasks
    async with semaphore:
        # Replace placeholders with payloads in the body
        payload_data = body.replace("FUZZ", word1).replace("BLAH", word2)
        
        # Make the HTTP request
        async with session.request(method, host + path, data=payload_data, proxy=proxy, headers=headers) as response:
            await process_response(response, word1, word2, filter_size, filter_code, check_word)
        
        # Delay between requests
        await asyncio.sleep(delay)
        
        # Increment the counter
        async with lock:
            counter['count'] += 1

# Asynchronous function for making requests with fuzzing in the URL path
async def fuzz_request_path(session, method, host, path, headers, body, proxy, filter_size, filter_code, delay, counter, lock, semaphore, word1, word2, check_word):
    # Limit the number of concurrent tasks
    async with semaphore:
        # Replace placeholders with payloads in the URL path
        # Nested regex subtitution by ME :D 
        request_path = re.sub(r"\bFUZZ2\b", word2, re.sub(r"\bFUZZ\b", word1, path))
        
        # Make the HTTP request
        async with session.request(method, host + request_path, data=body, proxy=proxy, headers=headers) as response:
            await process_response(response, word1, word2, filter_size, filter_code, check_word)
        
        # Delay between requests
        await asyncio.sleep(delay)
        
        # Increment the counter
        async with lock:
            counter['count'] += 1

# Asynchronous function for processing the HTTP response
async def process_response(response, word1, word2, filter_size, filter_code, check_word):
    # Get the Content-Length header
    r_size = response.headers.get('Content-Length', None)
    # Get the status code
    r_code = response.status

    # If Content-Length is not present, read the entire content and determine the size
    if r_size is None:
        content = await response.read()
        r_size = len(content)
    else:
        content = await response.read()
    
    content_str = content.decode('utf-8', errors='ignore')  # Decode the content to a string

    # Create a string representation of the payloads
    payload_str = f"FUZZ - [{word1}] BLAH - [{word2}]"
    
    # Parse filter inputs
    sizes = filter_size.split(",") if filter_size else []
    codes = filter_code.split(",") if filter_code else []

    # Define the conditions
    size_condition = not sizes or str(r_size) not in sizes
    code_condition = not codes or str(r_code) not in codes
    word_condition = not check_word or check_word not in content_str

    # Print if all conditions are met
    if size_condition and code_condition and word_condition:
        print(f"\rStatus Code-[{r_code}] Response Size-[{r_size}] {payload_str} ", flush=True)


# Asynchronous function for updating the counter display
async def update_counter(counter, lock, start_time):
    while True:
        async with lock:
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            # Calculate requests per second
            rps = int(counter['count'] / elapsed_time) if elapsed_time > 0 else 0
            print(f"\rProcessed {counter['count']} payloads | {rps} requests/sec", end='', flush=True)
        await asyncio.sleep(0.1)  # Update every 0.1 seconds

# Main function for orchestrating the fuzzing tasks
async def main():
    disable_warnings()  # Disable warnings from urllib3
    parser = argparse.ArgumentParser()  # Create an ArgumentParser object
    
    # Add command-line arguments
    parser.add_argument("-f", "--request-file", dest="request_file", metavar="", required=True, help="File containing the request template")
    parser.add_argument("-w", "--wordlist", metavar="", required=True, help="File containing the wordlist for FUZZ")
    parser.add_argument("-w+", "--wordlist+", dest="wordlist_plus", metavar="", help="Additional wordlist for BLAH")
    parser.add_argument("-x", "--proxy", metavar="", help="Proxy to use for requests")
    parser.add_argument("-fs", "--filter-size", dest="filter_size", metavar="", help="Filter responses by size")
    parser.add_argument("-fc", "--filter-code", dest="filter_code", metavar="", help="Filter responses by status code")
    parser.add_argument("-d", "--delay", metavar="", type=int, default=0, help="Delay between requests in seconds")
    parser.add_argument("-t", "--threads", metavar="", type=int, default=10, help="Number of concurrent threads/tasks")
    parser.add_argument("--random", action="store_true", help="Enable random payload selection")
    parser.add_argument("--iterations", metavar="", type=int, default=100, help="Number of iterations to run in cluster chaos mode")
    parser.add_argument("--check-word", metavar="", help="Filter responses by given word")
    
    args = parser.parse_args()  # Parse command-line arguments

    # Get command-line arguments
    request_file = args.request_file
    proxy = args.proxy if args.proxy else None
    wordlist_path = args.wordlist
    wordlist_plus = args.wordlist_plus
    filter_size = args.filter_size
    filter_code = args.filter_code
    delay = args.delay
    threads = args.threads
    random_selection = args.random
    num_iterations = args.iterations  # Get the number of iterations
    check_word = args.check_word  # Get the word to check in the response

    headers = {}
    body = ""

    # Read the request file and extract method, path, headers, and body
    with open(request_file, "r") as file:
        first_line = file.readline().strip().split(" ")
        method = first_line[0]
        path = first_line[1]
        for line in file:
            line = line.strip()
            if line.startswith("Host"):
                host = "https://" + line.split(" ")[1]
            elif ": " in line:
                param_name, param_value = line.split(": ", 1)
                headers[param_name] = param_value
            else:
                body += line

    tasks = []  # List to hold all the tasks
    counter = {'count': 0}  # Dictionary to keep track of the counter
    lock = asyncio.Lock()  # Lock for synchronizing access to the counter
    semaphore = asyncio.Semaphore(threads)  # Semaphore to limit the number of concurrent tasks
    start_time = time.time()  # Record the start time

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        if wordlist_plus:
            wordlist_one = []
            wordlist_two = []

            # Read both wordlists for dual placeholder mode
            with open(wordlist_path) as wl_one, open(wordlist_plus) as wl_two:
                wordlist_one = wl_one.read().splitlines()
                wordlist_two = wl_two.read().splitlines()

            # Limit the number of iterations
            for _ in range(num_iterations):
                word1 = choice(wordlist_one)
                word2 = choice(wordlist_two)
                if "FUZZ" in body or "FUZZ2" in body:
                    tasks.append(asyncio.create_task(fuzz_request_body(session, method, host, path, headers, body, proxy, filter_size, filter_code, delay, counter, lock, semaphore, word1, word2, check_word)))
                if "FUZZ" in path or "FUZZ2" in path:
                    tasks.append(asyncio.create_task(fuzz_request_path(session, method, host, path, headers, body, proxy, filter_size, filter_code, delay, counter, lock, semaphore, word1, word2, check_word)))
                else:
                    print("Missing additional keyword `FUZZ2`")
                    break
                if not random_selection:
                    break
        else:
            # Read the wordlist and create tasks
            with open(wordlist_path, "r") as wordlist:
                wordlist_content = wordlist.read().splitlines()
                for word in wordlist_content:
                    if "FUZZ" in body:
                        tasks.append(asyncio.create_task(fuzz_request_body(session, method, host, path, headers, body, proxy, filter_size, filter_code, delay, counter, lock, semaphore, word, "", check_word)))
                    elif "FUZZ" in path:
                        tasks.append(asyncio.create_task(fuzz_request_path(session, method, host, path, headers, body, proxy, filter_size, filter_code, delay, counter, lock, semaphore, word, "", check_word)))

        counter_task = asyncio.create_task(update_counter(counter, lock, start_time))  # Create a task to update the counter
        await asyncio.gather(*tasks)  # Run all the tasks concurrently
        counter_task.cancel()  # Cancel the counter update task

    # Print final count and RPS
    elapsed_time = time.time() - start_time  # Calculate elapsed time
    rps = int(counter['count'] / elapsed_time) if elapsed_time > 0 else 0  # Calculate requests per second
    print(f"\rProcessed {counter['count']} payloads | {rps} requests/sec", flush=True)

# Function to handle shutdown
def shutdown():
    print("\nShutdown initiated...")
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    loop.stop()
    print("Shutdown complete.")

# Entry point of the script
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
