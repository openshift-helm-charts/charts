# MariaDB helm chart

A Helm chart for building and deploying a [MariaDB](https://github/sclorg/mariadb-container) application on OpenShift.

For more information about helm charts see the official [Helm Charts Documentation](https://helm.sh/).

You need to have access to a cluster for each operation with OpenShift 4, like deploying and testing.

## Values
Below is a table of each value used to configure this chart.

| Value                                       | Description | Default | Additional Information |
|---------------------------------------------| ----------- | -- | ---------------------- |
| `database_service_name`                     | The name of the OpenShift Service exposed for the database. | `mariadb` | - |
| `mysql_user`                                | Username for MariaDB user that will be used for accessing the database. | - | Expresion like: `user[A-Z0-9]{3}` |
| `mysql_root_password`                       | Password for the MariaDB root user. | | Expression like: `[a-zA-Z0-9]{16}` |
| `mysql_database`                            | Name of the MariaDB database accessed. | `sampledb` |  |
| `mysql_password`                            | Password for the MariaDB connection user. |  | Expression like: `[a-zA-Z0-9]{16}` |
| `mariadb_version`                             | Version of MariaDB image to be used (10.3-el7, 10.3-el8, or latest). | `10.3-el8` |  |
| `namespace`                                 | The OpenShift Namespace where the ImageStream resides. | `openshift` | |
| `memory_limit`                              | Maximum amount of memory the container can use. | `521Mi` |  |
| `volume_capacity`                           | Volume space available for data, e.g. 512Mi, 2Gi. | `1Gi` |  |
