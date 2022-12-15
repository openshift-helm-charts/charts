import os

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def get_owner_data(category, organization, chart):
    path=os.path.join("charts", category, organization, chart, "OWNERS")
    status,owner_content=get_owner_data_from_file(path)
    return status,owner_content

def get_owner_data_from_file(owner_path):
    try:
        with open(owner_path) as owner_data:
            owner_content = yaml.load(owner_data,Loader=Loader)
        return True,owner_content
    except Exception as err:
        print(f"Exception loading OWNERS file: {err}")
        return False,""

def get_vendor(owner_data):
    vendor=""
    try:
        vendor = owner_data['vendor']['name']
    except Exception:
        pass
    return vendor

def get_chart(owner_data):
    chart=""
    try:
        chart = owner_data['chart']['name']
    except Exception:
        pass
    return chart

def get_provider_delivery(owner_data):
    provider_delivery = False
    try:
        provider_delivery = owner_data['providerDelivery']
    except Exception:
        pass
    return provider_delivery

def get_users_included(owner_data):
    users_included="No"
    try:
        users = owner_data['users']
        if len(users)!=0:
            return "Yes"
    except Exception:
        pass
    return users_included

def get_pgp_public_key(owner_data):
    pgp_public_key = "null"
    try:
        pgp_public_key = owner_data["publicPgpKey"]
    except Exception:
        pass
    return pgp_public_key


