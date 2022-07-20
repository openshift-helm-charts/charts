
import json
import requests
import yaml

def _make_http_request(method, url, body=None, params={}, headers={}, verbose=False):
    method_map = {"get": requests.get,
                  "post": requests.post,
                  "put": requests.put,
                  "delete": requests.delete,
                  "patch": requests.patch}
    request_method = method_map[method]
    response = request_method(url, params=params, headers=headers, json=body)
    if verbose:
        print(json.dumps(headers, indent=4, sort_keys=True))
        print(json.dumps(body, indent=4, sort_keys=True))
        print(json.dumps(params, indent=4, sort_keys=True))
        print(response.text)
    return response.text

def _load_index_yaml(url):

    yaml_text = _make_http_request('get', url)
    dct = yaml.safe_load(yaml_text)
    return dct

def get_chart_info(tar_name):
    index_dct = _load_index_yaml("https://charts.openshift.io/index.yaml")
    for entry, charts in index_dct["entries"].items():
        if tar_name.startswith(entry):
            for chart in charts:
                index_tar_name = f"{entry}-{chart['version']}"
                if tar_name == index_tar_name :
                    print(f"[INFO] match found: {tar_name}")
                    providerType = chart["annotations"]["charts.openshift.io/providerType"]
                    provider = chart["annotations"]["charts.openshift.io/provider"]
                    return providerType, provider, chart["name"], chart["version"]
    print(f"[INFO] match not found: {tar_name}")
    return "","","",""

if __name__ == "__main__":
    get_chart_info("redhat-dotnet-0.0.1")