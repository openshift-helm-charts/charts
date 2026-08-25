# Valkey helm chart

A Helm chart for building and deploying a [Valkey](https://github/sclorg/valkey-container) application on OpenShift.

For more information about helm charts see the official [Helm Charts Documentation](https://helm.sh/).

You need to have access to a cluster for each operation with OpenShift 4, like deploying and testing.

## Values
Below is a table of each value used to configure this chart.

| Value                   | Description                                                 | Default                     | Additional Information |
|-------------------------|-------------------------------------------------------------|-----------------------------| ---------------------- |
| `database_service_name` | The name of the OpenShift Service exposed for the database. | `valkey`                    | - |
| `valkey_password`       | Password for the Valkey connection user.                    |                             | Expression like: `[a-zA-Z0-9]{16}` |
| `valkey_version`        | Version of Valkey image to be used (6-el8, or latest).      | `6-el8`                     |  |
| `namespace`             | The OpenShift Namespace where the ImageStream resides.      | `valkey-persistent-testing` | |
| `memory_limit`          | Maximum amount of memory the container can use.             | `521Mi`                     |  |
| `volume_capacity`       | Volume space available for data, e.g. 512Mi, 2Gi.           | `1Gi`                       |  |
