import base64
import filecmp
import os
import re
import subprocess
import sys

sys.path.append("../")
from owners import owners_file
from pullrequest import prartifact
from reporegex import matchers
from report import verifier_report


def check_and_prepare_signed_chart(api_url, report_path, owner_path, key_file_path):
    signed_chart = is_chart_signed(api_url, report_path)
    key_in_owners = False
    keys_match = False
    if signed_chart:
        owners_pgp_key = get_pgp_key_from_owners(owner_path)
        if owners_pgp_key:
            key_in_owners = True
            if report_path:
                keys_match = check_pgp_public_key(owners_pgp_key, report_path)
            elif key_file_path:
                create_public_key_file(owners_pgp_key, key_file_path)

    return signed_chart, key_in_owners, keys_match


def get_verifier_flags(tar_file, owners_file, temp_dir):
    prov_file = f"{tar_file}.prov"
    if os.path.exists(prov_file):
        gpg_key = get_pgp_key_from_owners(owners_file)
        if gpg_key:
            key_file = os.path.join(temp_dir, "pgp", f"{tar_file}.key")
            create_public_key_file(gpg_key, key_file)
            return f"--pgp-public-key {key_file}"
    return ""


def is_chart_signed(api_url, report_path):
    if api_url:
        files = prartifact.get_modified_files(api_url)
        tgz_pattern = re.compile(
            matchers.submission_path_matcher(strict_categories=False) + r".*.tgz"
        )
        tgz_found = False
        prov_pattern = re.compile(
            matchers.submission_path_matcher(strict_categories=False) + r".*.tgz.prov"
        )
        prov_found = False

        for file_path in files:
            if tgz_pattern.match(file_path):
                tgz_found = True
            if prov_pattern.match(file_path):
                prov_found = True

        if tgz_found and prov_found:
            return True
    elif report_path:
        return check_report_for_signed_chart(report_path)

    return False


def get_pgp_key_from_owners(owner_path):
    try:
        owner_data = owners_file.get_owner_data_from_file(owner_path)
    except owners_file.OwnersFileError:
        return ""

    pgp_key = owners_file.get_pgp_public_key(owner_data)
    return pgp_key


def check_report_for_signed_chart(report_path):
    """Check that the report has passed the "signature-is-valid" test

    Args:
        report_path (str): Path to the report.yaml file

    Returns:
        bool: set to True if the report has passed the "signature-is-valid" test,
              False otherwise
    """
    found, report_data = verifier_report.get_report_data(report_path)
    if found:
        _, reason = verifier_report.get_signature_is_valid_result(report_data)
        if "Chart is signed" in reason:
            return True
    return False


def check_pgp_public_key(owner_pgp_key, report_path):
    """Check if the PGP key in the OWNERS file matches the one from report.yaml

    This checks passes if one of the following condition is met:
    - The PGP keys match.
    - The report is not for a signed chart
    - The report is not found

    Consequently, the check fails if the report is found and one the following is true:
    - The PGP keys do not match
    - The report is for a signed chart but no PGP key is provided in report.yaml

    Args:
        owner_pgp_key (str): The PGP key present in the OWNERS file.
        report_path (str): Path to the report.yaml file.

    Returns:
        bool: Set to True if the check passes, to False otherwise.
    """
    found, report_data = verifier_report.get_report_data(report_path)
    if found:
        pgp_public_key_digest_owners = subprocess.getoutput(
            f"echo {owner_pgp_key} | sha256sum"
        ).split(" ")[0]
        print(f"[INFO] digest of PGP key from OWNERS :{pgp_public_key_digest_owners}:")
        pgp_public_digest_report = verifier_report.get_public_key_digest(report_data)
        print(f"[INFO] PGP key digest in report :{pgp_public_digest_report}:")
        if pgp_public_digest_report:
            return pgp_public_key_digest_owners == pgp_public_digest_report
        else:
            return not check_report_for_signed_chart(report_path)
    return True


def create_public_key_file(pgp_public_key_from_owners, key_file_path):
    key_content = base64.b64decode(pgp_public_key_from_owners)

    key_file = open(key_file_path, "w")
    key_file.write(key_content.decode("utf-8"))
    key_file.close()


def main():
    if not is_chart_signed("", "./partner-report.yaml"):
        print("ERROR chart is signed")
    else:
        print("PASS chart is signed")

    if not check_report_for_signed_chart("./partner-report.yaml"):
        print("ERROR report indicates chart is signed")
    else:
        print("PASS report is signed")

    encoded_key_in_owners = get_pgp_key_from_owners("./OWNERS")
    if not check_pgp_public_key(encoded_key_in_owners, "./partner-report.yaml"):
        print("ERROR key digests do not match")
    else:
        print("PASS key digests match")

    signed, key_in_owners, keys_match = check_and_prepare_signed_chart(
        "", "./partner-report.yaml", "./OWNERS", "./pgp.key"
    )
    if signed and key_in_owners and keys_match:
        print("PASS all is good")
    else:
        print(
            f"ERROR, all true expected: signed = {signed}, key_in_owners = {key_in_owners}. keys_match = {keys_match}"
        )

    create_public_key_file(encoded_key_in_owners, "./pgp.key")
    if os.path.exists("./pgp.key"):
        if not filecmp.cmp("./psql-service-0.1.11.tgz.key", "./pgp.key"):
            print("ERROR public key files file do not match")
        else:
            print("PASS public key files do match")
        os.remove("./pgp.key")
    else:
        print("ERROR pgp key file was not created")


if __name__ == "__main__":
    main()
