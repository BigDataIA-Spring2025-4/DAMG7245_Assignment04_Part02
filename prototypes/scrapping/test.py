import requests
from itertools import cycle
import random

# List of user agents to rotate through
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Add more user agents here
]

# List of proxies to rotate through
proxies = [
    {"http": "http://proxy1.example.com:8080", "https": "http://proxy1.example.com:8080"},
    {"http": "http://proxy2.example.com:8080", "https": "http://proxy2.example.com:8080"},
    # Add more proxies here
]

# Function to get a random user agent
def get_random_user_agent():
    return random.choice(user_agents)

# Function to get a random proxy
def get_random_proxy():
    return random.choice(proxies)

# Function to make a request with optimized headers and rotating user agents and proxies
def make_request(url):
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
        # Add more headers here if needed
    }
    
    proxy = get_random_proxy()
    
    try:
        response = requests.get(url, headers=headers, proxies=proxy, timeout=10)
        response.raise_for_status()  # Raise error for HTTP errors (403, 404, etc.)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Failed: {e}")
        return None

# Usage example
url = "https://investor.nvidia.com/financial-info/quarterly-results/default.aspx"
content = make_request(url)

if content:
    print("Successfully scraped the content.")
    # Process the content here
else:
    print("Failed to scrape the content.")
