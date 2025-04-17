import argparse
import asyncio
import aiohttp
import sys
import logging
import csv
import json
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class SSLScanner:
    API = 'https://api.ssllabs.com/api/v2/'

    def __init__(
            self,
            hosts_file='hosts.txt',
            output_file='results.csv',
            output_format='csv',
            retries=3,
            delay=10
            ):
        self.hosts_file = hosts_file
        self.output_file = output_file
        self.output_format = output_format
        self.retries = retries
        self.delay = delay
        self.session = None

    async def request_api(self, path, payload={}):
        url = self.API + path
        attempt = 0

        while attempt < self.retries:
            try:
                async with self.session.get(
                    url,
                    params=payload,
                    timeout=30
                ) as response:
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
            await asyncio.sleep(self.delay)

        logging.error(f'''
                      Max retries reached for path {path}
                      with payload {payload}
                      URL: {url}
                      ''')
        return None

    async def new_scan(
            self,
            host,
            publish='off',
            startNew='on',
            all='done',
            ignoreMismatch='on'
            ):
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

        refresh_payload = {key: payload[key]
                           for key in payload
                           if key not in ['startNew', 'ignoreMismatch']}

        while 'status' not in results or results['status'] not in ['READY', 'ERROR']:
            await asyncio.sleep(90)
            results = await self.request_api(path, refresh_payload)

            if results is None:
                logging.warning(f'''
                                Follow-up scan request 
                                failed for host: {host}
                                with payload {refresh_payload}
                                ''')
                self.append_to_file([{
                    'host': host,
                    'status': 'FAILED',
                    'startTime': '',
                    'testTime': '',
                    'ipAddress': '',
                    'grade': 'TIMEOUT'
                }])
                return

            logging.info(f'Scanning {host} {results["status"]}')

        self.append_to_file([results])

    def append_to_file(self, data):
        if self.output_format == 'json':
            self.append_to_json(data)
        else:
            self.append_to_csv(data)

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

    def append_to_json(self, data):
        try:
            # Lire le contenu existant
            existing = []
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    try:
                        existing = json.load(f)
                    except json.JSONDecodeError:
                        pass

            # Ajouter les nouvelles données
            existing.extend(data)

            # Réécrire le fichier complet
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            logging.exception(f"Erreur lors de l'écriture JSON : {e}")

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


def print_banner():
    banner = r"""
     ___   _________  ________           ________  ________  ________  ________      
|\  \ |\___   ___\\   ____\         |\   ____\|\   ____\|\   __  \|\   ___  \    
\ \  \\|___ \  \_\ \  \___|_        \ \  \___|\ \  \___|\ \  \|\  \ \  \\ \  \   
 \ \  \    \ \  \ \ \_____  \        \ \_____  \ \  \    \ \   __  \ \  \\ \  \  
  \ \  \____\ \  \ \|____|\  \        \|____|\  \ \  \____\ \  \ \  \ \  \\ \  \ 
   \ \_______\ \__\  ____\_\  \         ____\_\  \ \_______\ \__\ \__\ \__\\ \__\
    \|_______|\|__| |\_________\       |\_________\|_______|\|__|\|__|\|__| \|__|
                    \|_________|       \|_________|                              
    """
    print(banner)


def parse_args():
    parser = argparse.ArgumentParser(
        description='SSL Labs Scanner to test hosts.')
    parser.add_argument('-i', '--input', default='hosts.txt',
                        help='File containing the hosts to be scanned')
    parser.add_argument('-o', '--output', default='results.csv',
                        help='CSV output file')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                        help='Output format (csv or json), default: csv')
    parser.add_argument('--retries', type=int, default=3,
                        help='Number of attempts in case of failure')
    parser.add_argument('--delay', type=int, default=10,
                        help='Delay between attempts (seconds)')
    return parser.parse_args()


def main():
    print_banner()
    args = parse_args()
    scanner = SSLScanner(
        hosts_file=args.input,
        output_file=args.output,
        output_format=args.format,
        retries=args.retries,
        delay=args.delay
    )
    asyncio.run(scanner.run())


if __name__ == "__main__":
    main()
