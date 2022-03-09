import os
import re
import requests
import logging
import sys
import itertools

logging.basicConfig(level=logging.INFO)


def parse_response(response):
    result = []
    for obj in response:
        if 'name' in obj and len(obj.get('assets', [])) > 0:
            release = {
                'name': obj['name'],
                'assets': list(map(lambda asset: (asset.get('name', 'unknown'), asset.get('download_count', 0)), obj['assets']))
            }
            result.append(release)
    return result


def get_metrics():
    result = []
    for i in itertools.count(start=1):
        response = requests.get(
            f'https://api.github.com/repos/openshift-helm-charts/charts/releases?per_page=100&page={i}')
        if not 200 <= response.status_code < 300:
            logging.error(f"unexpected response getting release data : {response.status_code} : {response.reason}")
            sys.exit(1)
        response_json = response.json()
        if len(response_json) == 0:
            break
        result.extend(response_json)
    return parse_response(result)


def send_metrics(metrics: dict):
    for release in metrics:
        headers = {
            'Authorization': os.getenv('SEGMENT_WRITE_KEY')}
        json = {
            "userId": release['name'],
            "event": "Chart Certification Metrics",
            "properties": dict(release['assets']),
        }
        response = requests.post(
            url='https://api.segment.io/v1/track', headers=headers, json=json)
        if not 200 <= response.status_code < 300:
            logging.error(f"unexpected response sending data to segment : {response.status_code} : {response.reason}")
            sys.exit(1)
        logging.info(f'POST {json["userId"]}\nRESPONSE {response}')


def main():
    send_metrics(get_metrics())


if __name__ == '__main__':
    main()
