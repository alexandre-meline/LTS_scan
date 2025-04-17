import asyncio
import aiohttp
import sys
import logging
import csv

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class SSLScanner:
    API = 'https://api.ssllabs.com/api/v2/'

    def __init__(self, hosts_file='hosts.txt', output_file='results.csv'):
        self.hosts_file = hosts_file
        self.output_file = output_file
        self.session = None

    async def request_api(self, path, payload={}, retries=3, delay=10):
        url = self.API + path
        attempt = 0

        while attempt < retries:
            try:
                async with self.session.get(url, params=payload, timeout=30) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data
            except aiohttp.ClientResponseError as e:
                logging.warning(f'HTTP Error: {e}. Retrying...')
            except aiohttp.ClientError as e:
                logging.warning(f'Request failed with error: {e}. Retrying...')
            except Exception as e:
                logging.warning(f'Unexpected error: {e}. Retrying...')
            attempt += 1
            await asyncio.sleep(delay)

        logging.error(f'Max retries reached for path {path} with payload {payload}')
        return None

    async def new_scan(self, host, publish='off', startNew='on', all='done', ignoreMismatch='on'):
        await asyncio.sleep(10)

        path = 'analyze'
        payload = {
            'host': host,
            'publish': publish,
            'startNew': startNew,
            'all': all,
            'ignoreMismatch': ignoreMismatch
        }

        results = await self.request_api(path, payload)

        if results is None:
            logging.warning(f'Initial scan request failed for host: {host}')
            self.append_to_csv([{
                'host': host,
                'status': 'FAILED',
                'startTime': '',
                'testTime': '',
                'ipAddress': '',
                'grade': 'TIMEOUT'
            }])
            return

        logging.info(f'Scanning {host} in new scan')

        refresh_payload = {key: payload[key] for key in payload if key not in ['startNew', 'ignoreMismatch']}

        while 'status' not in results or results['status'] not in ['READY', 'ERROR']:
            await asyncio.sleep(90)
            results = await self.request_api(path, refresh_payload)

            if results is None:
                logging.warning(f'Follow-up scan request failed for host: {host}')
                self.append_to_csv([{
                    'host': host,
                    'status': 'FAILED',
                    'startTime': '',
                    'testTime': '',
                    'ipAddress': '',
                    'grade': 'TIMEOUT'
                }])
                return

            logging.info(f'Scanning {host} {results["status"]}')

        self.append_to_csv([results])

    def append_to_csv(self, data):
        fieldnames = [
            'host',
            'status',
            'startTime',
            'testTime',
            'ipAddress',
            'grade'
            ]
        with open(self.output_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            f.seek(0, 2)
            if f.tell() == 0:
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

    async def process_hosts(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            hosts = self.load_hosts()
            for host in hosts:
                try:
                    await self.new_scan(host)
                except Exception as e:
                    logging.exception(f'Error with {host}: {e}')
                await asyncio.sleep(15)

    def initialize_csv(self):
        with open(self.output_file, mode='w', newline='', encoding='utf-8') as f:
            pass

    def load_hosts(self):
        try:
            with open(self.hosts_file) as f:
                hosts = f.read().splitlines()
                logging.info(f'Found {len(hosts)} hosts to scan')
                if not hosts:
                    logging.error('No hosts found in hosts.txt')
                    sys.exit(1)
                return hosts
        except FileNotFoundError:
            logging.error(f'{self.hosts_file} not found.')
            sys.exit(1)

    async def run(self):
        self.initialize_csv()
        await self.process_hosts()


if __name__ == '__main__':
    scanner = SSLScanner()
    asyncio.run(scanner.run())
