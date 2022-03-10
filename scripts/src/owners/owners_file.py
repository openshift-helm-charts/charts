import os

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def get_owner_data(category, organization, chart):
    try:
        with open(os.path.join("charts", category, organization, chart, "OWNERS")) as owner_data:
            owner_content = yaml.load(owner_data,Loader=Loader)
        return True,owner_content
    except Exception as err:
        print(f"Exception loading OWNERS file: {err}")
        return False,""


def get_provider_delivery(owner_data):
    provider_delivery = False
    try:
        provider_delivery = owner_data["providerDelivery"]
    except Exception:
        pass
    return provider_delivery

