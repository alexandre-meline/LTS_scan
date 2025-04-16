import asyncio
import aiohttp
import sys
import logging
import csv

API = 'https://api.ssllabs.com/api/v2/'

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


async def requestAPI(session, path, payload={}, retries=3, delay=10):
    '''Request data/server test from Qualys SSL Labs. 
    Returns JSON formatted data'''
    url = API + path
    attempt = 0

    while attempt < retries:
        try:
            async with session.get(url,
                                   params=payload, timeout=30) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientResponseError as e:
            logging.exception(f'HTTP Error: {e}. Retrying...')
            attempt += 1
            await asyncio.sleep(delay)
        except aiohttp.ClientError as e:
            logging.exception(f'Request failed with error: {e}. Retrying...')
            attempt += 1
            await asyncio.sleep(delay)
        except Exception as e:
            logging.exception(f'Unexpected error: {e}. Exiting...')
            sys.exit(1)

    logging.error('Max retries reached. Exiting...')
    sys.exit(1)


async def newScan(session, host, filename, publish='off', startNew='on', all='done', ignoreMismatch='on'):
    await asyncio.sleep(10)

    path = 'analyze'
    payload = {
        'host': host,
        'publish': publish,
        'startNew': startNew,
        'all': all,
        'ignoreMismatch': ignoreMismatch
    }

    results = await requestAPI(session, path, payload)
    print(f'Scanning {host} in new scan')

    # Subset of payload for subsequent requests
    refresh_payload = {key: payload[key] for key in payload if key not in [
        'startNew', 'ignoreMismatch']}

    while 'status' not in results or (results['status'] != 'READY' and results['status'] != 'ERROR'):
        if 'status' not in results:
            logging.error('No status in the response')
            sys.exit(1)
        await asyncio.sleep(90)
        results = await requestAPI(session, path, refresh_payload)
        print(f'Scanning {host} {results["status"]}')

    append_to_csv([results], filename)
    return results


def append_to_csv(data, filename):
    fieldnames = ['host', 'status', 'startTime', 
                  'testTime', 'ipAddress', 'grade']
    with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Check if file is empty to write headers
        csvfile.seek(0, 2)
        if csvfile.tell() == 0:
            writer.writeheader()

        for entry in data:
            if 'endpoints' in entry:
                for endpoint in entry.get('endpoints', []):
                    row = {
                        'host': entry.get('host', ''),
                        'status': entry.get('status', ''),
                        'startTime': entry.get('startTime', ''),
                        'testTime': entry.get('testTime', ''),
                        'ipAddress': endpoint.get('ipAddress', ''),
                        'grade': endpoint.get('grade', '')
                    }
                    writer.writerow(row)


async def processHosts(hosts, filename):
    async with aiohttp.ClientSession() as session:
        for host in hosts:
            try:
                await newScan(session, host, filename)
            except Exception as e:
                logging.exception(f'Error with {host}: {e}')
            await asyncio.sleep(15)


def initialize_csv(filename):
    # Create empty CSV or clear the existing one
    with open(filename, 
              mode='w', newline='', encoding='utf-8') as csvfile:
        pass


async def main():
    filename = 'results.csv'
    initialize_csv(filename)
    with open('hosts.txt') as f:
        hosts = f.read().splitlines()
        print(hosts)
    await processHosts(hosts, filename)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
