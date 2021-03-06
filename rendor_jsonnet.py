# export GRAFANA_SERVER="http://admin:admin@ppatel4-640:3001"
# set -xe
# for file in $(ls $CURRENT_PATH); do
#   jsonnet $CURRENT_PATH/$file > rendor/"${file%.jsonnet}".json
#   payload="{\"dashboard\": $(jq .  rendor/"${file%.jsonnet}".json), \"overwrite\": true}"
#   curl -X POST \
#     -H 'Content-Type: application/json' \
#     -d "${payload}" \
#     "${GRAFANA_SERVER}/api/dashboards/"
# done
import argparse
import json
import logging
import os
import subprocess
import requests


def render_file(file, dashboard_name, jsonnet_lib_path='vendor', output_dir='render'):
    if subprocess.run('jsonnet -J {} -e \'(import "{}").grafanaDashboards.{}\' --output-file {}'
                              .format(jsonnet_lib_path, file, dashboard_name,
                                      '{}/{}.json'.format(output_dir, dashboard_name)),
                      shell=True).returncode == 0:
        return '{}/{}.json'.format(output_dir, dashboard_name)
    else:
        return -1


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Validate Grafana Dashboards.')
    parser.add_argument('--dir', '-d', help="Directory Path for dashboards jsonnet")
    parser.add_argument('--grafana-url', '-u', help="Grafana URL")
    parser.add_argument('--user', help='Grafana user', default="admin")
    parser.add_argument('--password', '-p', help="Grafana password")
    parser.add_argument('--api-token', help="Grafana API Token")

    args = parser.parse_args()
    if args.user and args.password:
        auth = requests.auth.HTTPBasicAuth(args.user, args.password)
    else:
        auth = args.api_token
    for file in os.listdir(args.dir):
        output_jsonnet = os.path.abspath(os.path.join(args.dir, file))
        dashboard_json = render_file(output_jsonnet, file.split('.')[0].title().replace('-', ''))
        if dashboard_json == -1: raise Exception("Jsonnet Render Failed.")
        r = requests.post("{}/api/dashboards/db".format(args.grafana_url), json={
            "Dashboard": json.load(open(dashboard_json, 'r')),
            "overwrite": True
        }, auth=auth)
        if not r.ok:
            print(r.status_code, r.text)
        else:
            logging.info(dashboard_json + " applied successfully.")
