# PostgreSQL helm chart

A Helm chart for building and deploying a [PostgreSQL](https://github/sclorg/postgresql-container) application on OpenShift.

For more information about helm charts see the official [Helm Charts Documentation](https://helm.sh/).

You need to have access to a cluster for each operation with OpenShift 4, like deploying and testing.

## Values
Below is a table of each value used to configure this chart.

| Value                                       | Description | Default | Additional Information |
|---------------------------------------------| ----------- | -- | ---------------------- |
| `database_service_name`                     | The name of the OpenShift Service exposed for the database. | `postgresql` | - |
| `postgresql_user`                           | Username for PostgreSQL user that will be used for accessing the database. | - | Expresion like: `user[A-Z0-9]{3}` |
| `postgresql_database`                       | Name of the PostgreSQL database accessed. | `sampledb` |  |
| `postgresql_password`                       | Password for the PostgreSQL connection user. |  | Expression like: `[a-zA-Z0-9]{16}` |
| `postgresql_version`                        | Version of PostgreSQL image to be used (12-el8, or latest). | `18-el10` |  |
| `namespace`                                 | The OpenShift Namespace where the ImageStream resides. | `openshift` | |
| `memory_limit`                              | Maximum amount of memory the container can use. | `521Mi` |  |
| `volume_capacity`                           | Volume space available for data, e.g. 512Mi, 2Gi. | `1Gi` |  |
