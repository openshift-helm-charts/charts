# Testing Guide for Cryostat Helm Chart

This guide outlines the conventions and practices for writing and executing tests in the Cryostat Helm chart project using the Helm Unittest plugin.

## Overview

Helm Unittest is a Helm plugin that allows to write declarative tests for Helm charts. It enables testing the rendered templates of a Helm chart with specified values without the need for any running Kubernetes cluster.

# Testing Guide for Cryostat Helm Chart

## Requirements

Before running tests, you need to have the following tools installed:

- **Helm:** Helm is a package manager for Kubernetes needed to manage the charts.
  `Required version: >= v3.14.4`
- **Helm Unittest Plugin:** This plugin enables unit testing for Helm charts.
  `Required version: >= v0.5.1`

## Installation

##### Installing Helm

Helm can be installed on a variety of platforms. [Official Helm installation documentation](https://helm.sh/docs/intro/install/) provides detailed instructions.

##### Installing Helm Unittest Plugin

Once Helm is installed, you can install the Helm Unittest plugin.
First, verify whether the Helm Unittest plugin has been successfully installed, you can use the following command to list all installed Helm plugins:
```bash
helm plugin list
```
This command will display a list of all plugins currently installed in your Helm environment, including the Helm Unittest plugin if it's already installed. Look for an entry named unittest in the output. If it's listed, then the Helm Unittest plugin is installed correctly. For example:
```
❯ helm plugin list

NAME    	VERSION	DESCRIPTION
unittest	0.5.1  	Unit test for helm chart in YAML with ease
to keep your chart functional and robust.
```
If the Helm Unittest plugin is not listed, you can install it using the following command:
```bash
$ helm plugin install https://github.com/helm-unittest/helm-unittest.git
```
This will install the latest version of binary into helm plugin directory.

## Writing Tests

Each test is associated with a specific Helm template and is structured to validate specific aspects of that template. Here's a general structure for writing tests:

1. **Test Suite:** A collection of tests related to a particular aspect of the chart, usually corresponding to a specific template file.
2. **Test Cases:** Each test case should focus on a single aspect or feature of the chart. Test cases can have different configurations set through the `set` directive to simulate different environments or scenarios.
3. **Assertions:** Test cases contain assertions that specify the expected output of the rendered templates. Assertions can check for the existence of objects, equality of values, matching patterns, and more.

##### Naming Conventions for Test Files
The naming convention for test files typically mirrors the name of the template they are testing with a `_test` suffix. For example:

- service.yaml ➔ service_test.yaml
- deployment.yaml ➔ deployment_test.yaml

## Directory Structure

Tests are organized under the `tests/` directory, with each test file corresponding to a template in the `templates/` directory:

```plaintext
cryostat-helm/
├── charts
│   └── cryostat
│       ├── Chart.yaml
│       ├── templates
│       │   ├── alpha_config.yaml
│       │   ├── ...
│       │   └── tests
│       │       ├── test-core-connection.yaml
│       │       └── ...
│       ├── TESTING.md
│       ├── tests
│       │   ├── alpha_config_test.yaml
│       │   ├── ...
│       │   ├── __snapshot__
│       │   └── storage_access_secret_test.yaml
│       ├── values.schema.json
│       └── values.yaml

```
In addition, Cryostat Helm chart includes integration tests located in the `templates/tests` directory and are executed using `helm test`. These tests are different from unit tests in that they involve actual deployment of resources to a Kubernetes cluster to validate the integrated operation of those resources.

## Test File Structure

Here's an example of what a test file looks like:

```yaml
suite: <Name of Test Suite>
templates:
  - <path to template from chart root>
tests:
  - it: <description of what the test does>
    set:
      <values to be set>
    asserts:
      - <assert type>:
          path: <path to value to test>
          value: <expected value>
```
## Common Assertions
- `equal`: Checks if the actual value at path equals the expected value.
- `matchRegex`: Validates if the actual string matches the given regex pattern.
- `exists`: Checks if the specified path exists in the document.
- `notExists`: Ensures the specified path does not exist in the document.

Visit [this document](https://github.com/helm-unittest/helm-unittest/blob/main/DOCUMENT.md#assertion-types) for more assertion types.
## Running Tests

Once Unittest plugin has been installed, tests can be executed by running the following command:
```bash
$ helm unittest <path-to-chart-directory>
```
In the case of `cryostat-helm`, the command would be:

```bash
$ helm unittest ./charts/cryostat
```
To run test for a specific test file, use the `-f` flag with helm unittest to specify the test file to be executed. Here's the command format:

```bash
$ helm unittest -f tests/<testfile>.yaml ./charts/<chartname>
```
This command will run the test for `service_test.yaml` file:

```bash
$ helm unittest -f tests/service_test.yaml ./charts/cryostat
```
## Additional Resources and Documentation

For more infomation on Helm and writing tests for Helm charts, the following resources can be invaluable:

### Helm Documentation

- **Helm Official Documentation:** Provides comprehensive guides, tutorials, and reference material for working with Helm.
  [Helm Documentation](https://helm.sh/docs/)

- **Helm Chart Best Practices:** A guide by the Helm community outlining best practices for creating and managing Helm charts.
  [Helm Chart Best Practices](https://helm.sh/docs/chart_best_practices/)

### Helm Unittest Plugin

- **Helm Unittest GitHub Repository:** Contains the source code, installation instructions, and detailed usage examples of the Helm Unittest plugin.
  [Helm Unittest on GitHub](https://github.com/helm-unittest/helm-unittest)
