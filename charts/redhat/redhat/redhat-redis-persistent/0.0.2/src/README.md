# Redis helm chart

A Helm chart for building and deploying a [Redis](https://github/sclorg/redis-container) application on OpenShift.

For more information about helm charts see the official [Helm Charts Documentation](https://helm.sh/).

You need to have access to a cluster for each operation with OpenShift 4, like deploying and testing.

## Values
Below is a table of each value used to configure this chart.

| Value                                       | Description | Default | Additional Information |
|---------------------------------------------| ----------- | -- | ---------------------- |
| `database_service_name`                     | The name of the OpenShift Service exposed for the database. | `redis` | - |
| `redis_password`                            | Password for the Redis connection user. |  | Expression like: `[a-zA-Z0-9]{16}` |
| `redis_version`                             | Version of Redis image to be used (6-el8, or latest). | `6-el8` |  |
| `namespace`                                 | The OpenShift Namespace where the ImageStream resides. | `redis-persistent-testing` | |
| `memory_limit`                              | Maximum amount of memory the container can use. | `521Mi` |  |
| `volume_capacity`                           | Volume space available for data, e.g. 512Mi, 2Gi. | `1Gi` |  |
