import argparse
import sys

import analytics

sys.path.append("../")
from owners import owners_file


def bool_to_yes_no(my_bool):
    return "Yes" if my_bool else "No"


def getVendorType(changed_file):
    path_as_list = changed_file.split("/")
    for i in range(len(path_as_list) - 1):
        if path_as_list[i] == "charts":
            vendor_type = path_as_list[i + 1]
            return vendor_type


def getFileContent(changed_file):
    try:
        owner_data = owners_file.get_owner_data_from_file(changed_file)
    except owners_file.OwnersFileError as e:
        print("Exception loading OWNERS file: {e}")
        return "", "", "", "", ""

    users_included = owners_file.get_users_included(owner_data)
    web_catalog_only = owners_file.get_web_catalog_only(owner_data)
    vendor_name = owners_file.get_vendor(owner_data)
    chart_name = owners_file.get_chart(owner_data)
    vendor_type = getVendorType(changed_file)
    return (
        bool_to_yes_no(users_included),
        bool_to_yes_no(web_catalog_only),
        vendor_name,
        chart_name,
        vendor_type,
    )


def process_pr(added_file, modified_file):
    if modified_file != "":
        action = "update"
        update = "existing-vendor"
        (
            users_included,
            web_catalog_only,
            vendor_name,
            chart_name,
            vendor_type,
        ) = getFileContent(modified_file)
        return (
            users_included,
            web_catalog_only,
            vendor_name,
            chart_name,
            vendor_type,
            action,
            update,
        )
    elif added_file != "":
        action = "create"
        update = "new-vendor"
        (
            users_included,
            web_catalog_only,
            vendor_name,
            chart_name,
            vendor_type,
        ) = getFileContent(added_file)
        return (
            users_included,
            web_catalog_only,
            vendor_name,
            chart_name,
            vendor_type,
            action,
            update,
        )


def send_owner_metric(
    write_key,
    prefix,
    users_included,
    web_catalog_only,
    partner,
    chart_name,
    type,
    action,
    update,
):
    if chart_name != "" and partner != "":
        id = f"{prefix}-{type}-{chart_name}"
        properties = {
            "type": type,
            "vendor": partner,
            "chart": chart_name,
            "users_included": users_included,
            "provider_delivery": web_catalog_only,
            "action": action,
            "update": update,
        }
        send_metric(write_key, id, "owners v1.0", properties)


def on_error(error, items):
    print("An error occurred creating metrics:", error)
    print("error with items:", items)
    sys.exit(1)


def send_metric(write_key, id, event, properties):
    analytics.write_key = write_key
    analytics.on_error = on_error

    print(f"[INFO] Add track:  id: {id},  event:{event},  properties:{properties}")

    analytics.track(id, event, properties)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-k",
        "--write-key",
        dest="write_key",
        type=str,
        required=True,
        help="segment write key",
    )
    parser.add_argument(
        "-t",
        "--metric-type",
        dest="type",
        type=str,
        required=True,
        help="metric type, releases or pull_request",
    )
    parser.add_argument(
        "-n", "--added", dest="added", nargs="*", required=False, help="files added"
    )
    parser.add_argument(
        "-a",
        "--modified",
        dest="modified",
        nargs="*",
        required=False,
        help="files modified",
    )
    parser.add_argument(
        "-r",
        "--repository",
        dest="repository",
        type=str,
        required=False,
        help="The repository of the pr",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        dest="prefix",
        type=str,
        required=False,
        help="The prefix of the id in segment",
    )

    args = parser.parse_args()
    print("Input arguments:")
    print(f"   --write-key length : {len(args.write_key)}")
    print(f"   --metric-type : {args.type}")
    print(f"   --added : {args.added}")
    print(f"   --modified : {args.modified}")
    print(f"   --repository : {args.repository}")
    print(f"   --prefix : {args.prefix}")

    if not args.write_key:
        print("Error: Segment write key not set")
        sys.exit(1)

    (
        users_included,
        web_catalog_only,
        vendor_name,
        chart_name,
        vendor_type,
        action,
        update,
    ) = process_pr(args.added[0], args.modified[0])
    send_owner_metric(
        args.write_key,
        args.prefix,
        users_included,
        web_catalog_only,
        vendor_name,
        chart_name,
        vendor_type,
        action,
        update,
    )


if __name__ == "__main__":
    main()
