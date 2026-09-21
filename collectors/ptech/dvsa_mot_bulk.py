"""DVSA MOT bulk/delta download scaffold.
Requires registered credentials. Endpoint returns URLs for latest weekly bulk + deltas.
See official authentication docs before enabling."""
import os, requests
DOWNLOAD_ENDPOINT='https://history.mot.api.gov.uk/v1/trade/vehicles/bulk-download'

def download_manifest(access_token):
    headers={'Authorization':f'Bearer {access_token}','X-API-Key':os.environ['DVSA_API_KEY']}
    r=requests.get(DOWNLOAD_ENDPOINT,headers=headers,timeout=60);r.raise_for_status();return r.json()
