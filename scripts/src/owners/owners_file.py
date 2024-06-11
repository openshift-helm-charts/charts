import contextlib
import os

import yaml

try:
    from yaml import CSafeoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


class OwnersFileError(Exception):
    pass


class ConfigKeyMissing(Exception):
    pass


def get_owner_data(category, organization, chart):
    path = os.path.join("charts", category, organization, chart, "OWNERS")
    success = False

    try:
        owner_content = get_owner_data_from_file(path)
        success = True
    except OwnersFileError as e:
        print(f"Error getting OWNERS file data: {e}")

    return success, owner_content


def get_owner_data_from_file(owner_path):
    try:
        with open(owner_path) as owner_data:
            owner_content = yaml.load(owner_data, Loader=SafeLoader)
    except yaml.YAMLError as e:
        print(f"Exception loading OWNERS file: {e}")
        raise OwnersFileError from e
    except OSError as e:
        print(f"Error opening OWNERS file: {e}")
        raise OwnersFileError from e

    return owner_content


def get_vendor(owner_data):
    vendor_name = ""
    with contextlib.suppress(KeyError):
        vendor_name = owner_data["vendor"]["name"]
    return vendor_name


def get_vendor_label(owner_data):
    vendor_label = ""
    with contextlib.suppress(KeyError):
        vendor_label = owner_data["vendor"]["label"]
    return vendor_label


def get_chart(owner_data):
    chart = ""
    with contextlib.suppress(KeyError):
        chart = owner_data["chart"]["name"]
    return chart


def get_web_catalog_only(owner_data, raise_if_missing=False):
    """Check the delivery method set in the OWNERS file data

    Args:
        owner_data (dict): Content of the OWNERS file. Typically this is the return value of the
            get_owner_data or get_owner_data_from_file function.
        raise_if_missing (bool, optional): Whether to raise an Exception if the delivery method is
            not set in the OWNERS data. If set to False, the function returns False.

    Raises:
        ConfigKeyMissing: if the key is not found in OWNERS and raise_if_missing is set to True

    """
    if (
        "web_catalog_only" not in owner_data
        and "providerDelivery" not in owner_data
        and raise_if_missing
    ):
        raise ConfigKeyMissing(
            "Neither web_catalog_only nor providerDelivery keys were set"
        )

    return owner_data.get("web_catalog_only", False) or owner_data.get(
        "providerDelivery", False
    )


def get_users_included(owner_data):
    users = owner_data.get("users", list())
    return len(users) != 0


def get_pgp_public_key(owner_data):
    return owner_data.get("publicPgpKey", "")
