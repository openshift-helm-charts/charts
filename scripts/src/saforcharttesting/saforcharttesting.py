import os
import base64
import json
import argparse
import subprocess
import tempfile
from string import Template

namespace_template = """\
apiVersion: v1
kind: Namespace
metadata:
  name: ${name}
"""

serviceaccount_template = """\
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${name}
  namespace: ${name}
"""

role_template = """
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: ${name}
  namespace: ${name}
rules:
  - apiGroups:
      - "*"
    resources:
      - '*'
    verbs:
      - '*'
"""

rolebinding_template = """
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ${name}
  namespace: ${name}
subjects:
- kind: ServiceAccount
  name: ${name}
  namespace: ${name}
roleRef:
  kind: Role
  name: ${name}
"""

def apply_config(tmpl, **values):
    with tempfile.TemporaryDirectory(prefix="sa-for-chart-testing-") as tmpdir:
        content = Template(tmpl).substitute(values)
        config_path = os.path.join(tmpdir, "config.yaml")
        with open(config_path, "w") as fd:
            fd.write(content)
        out = subprocess.run(["./oc", "apply", "-f", config_path], capture_output=True)
        stdout = out.stdout.decode("utf-8")
        if out.returncode != 0:
            stderr = out.stderr.decode("utf-8")
        else:
            stderr = ""

    return stdout, stderr

def delete_config(tmpl, **values):
    with tempfile.TemporaryDirectory(prefix="sa-for-chart-testing-") as tmpdir:
        content = Template(tmpl).substitute(values)
        config_path = os.path.join(tmpdir, "config.yaml")
        with open(config_path, "w") as fd:
            fd.write(content)
        out = subprocess.run(["./oc", "delete", "-f", config_path], capture_output=True)
        stdout = out.stdout.decode("utf-8")
        if out.returncode != 0:
            stderr = out.stderr.decode("utf-8")
        else:
            stderr = ""

    return stdout, stderr

def create_namespace(namespace):
    print("creating Namespace:", namespace)
    stdout, stderr = apply_config(namespace_template, name=namespace)
    print("stdout:\n", stdout, sep="")
    if stderr.strip():
        print("[ERROR] creating Namespace:", stderr)

def create_serviceaccount(namespace):
    print("creating ServiceAccount:", namespace)
    stdout, stderr = apply_config(serviceaccount_template, name=namespace)
    print("stdout:\n", stdout, sep="")
    if stderr.strip():
        print("[ERROR] creating ServiceAccount:", stderr)

def create_role(namespace):
    print("creating Role:", namespace)
    stdout, stderr = apply_config(role_template, name=namespace)
    print("stdout:\n", stdout, sep="")
    if stderr.strip():
        print("[ERROR] creating Role:", stderr)

def create_rolebinding(namespace):
    print("creating RoleBinding:", namespace)
    stdout, stderr = apply_config(rolebinding_template, name=namespace)
    print("stdout:\n", stdout, sep="")
    if stderr.strip():
        print("[ERROR] creating RoleBinding:", stderr)


def delete_namespace(namespace):
    print("deleting Namespace:", namespace)
    stdout, stderr = delete_config(namespace_template, name=namespace)
    print("stdout:\n", stdout, sep="")
    if stderr.strip():
        print("[ERROR] deleting Namespace:", namespace, stderr)
        sys.exit(1)

def write_sa_token(namespace, token):
    sa_found = False
    for i in range(7):
        out = subprocess.run(["./oc", "get", "serviceaccount", namespace, "-n", namespace, "-o", "json"], capture_output=True)
        stdout = out.stdout.decode("utf-8")
        if out.returncode != 0:
            stderr = out.stderr.decode("utf-8")
            if stderr.strip():
                print("[ERROR] retrieving ServiceAccount:", namespace, stderr)
                time.sleep(10)
        else:
            sa = json.loads(stdout)
            if len(sa["secrets"]) >= 2:
                sa_found = True
                break
            time.sleep(10)

    if not sa_found:
        print("[ERROR] retrieving ServiceAccount:", namespace, stderr)
        sys.exit(1)

    secret_found = False
    for secret in sa["secrets"]:
        out = subprocess.run(["./oc", "get", "secret", secret["name"], "-n", namespace, "-o", "json"], capture_output=True)
        stdout = out.stdout.decode("utf-8")
        if out.returncode != 0:
            stderr = out.stderr.decode("utf-8")
            if stderr.strip():
                print("[ERROR] retrieving secret:", secret["name"], stderr)
                continue
        else:
            sec = json.loads(stdout)
            if sec["type"] == "kubernetes.io/service-account-token":
                content = sec["data"]["token"]
                with open(token, "w") as fd:
                    fd.write(base64.b64decode(content).decode("utf-8"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--create", dest="create", type=str, required=False,
                                        help="create service account and namespace for chart testing")
    parser.add_argument("-t", "--token", dest="token", type=str, required=False,
                                        help="service account token for chart testing")
    parser.add_argument("-d", "--delete", dest="delete", type=str, required=False,
                                        help="delete service account and namespace used for chart testing")
    args = parser.parse_args()

    if args.create:
        create_namespace(args.create)
        create_serviceaccount(args.create)
        create_role(args.create)
        create_rolebinding(args.create)
        write_sa_token(args.create, args.token)
    elif args.delete:
        delete_namespace(args.delete)
    else:
        parser.print_help()
