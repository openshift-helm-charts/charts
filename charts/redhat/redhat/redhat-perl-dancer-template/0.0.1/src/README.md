# Perl application template with no database helm chart

A Helm chart for building and deploying a [Dancer-ex](https://github/sclorg/dancer-ex) application on OpenShift.

For more information about helm charts see the official [Helm Charts Documentation](https://helm.sh/).

You need to have access to a cluster for each operation with OpenShift 4, like deploying and testing.

## Values
Below is a table of each value used to configure this chart.

| Value                    | Description                                                                                             | Default                                    | Additional Information |
|--------------------------|---------------------------------------------------------------------------------------------------------|--------------------------------------------|------------------------|
| `name`                   | The name assigned to all of the frontend objects defined in this helm chart.                            | `dancer-example`                           |                        |
| `namespace`              | The OpenShift Namespace where the ImageStream resides.                                                  | `dancer-example`                           |                        |
| `perl_version `          | Specify PERL imagestream tag.                                                                           | `5.30-ubi8`                                |                        |
| `memory_limit`           | Maximum amount of memory the container can use.                                                         | `521Mi`                                    |                        |
| `application_domain`     | The exposed hostname that will route to the httpd service, if left blank a value will be defaulted.     |                                            |                        |
| `context_dir`            | Set this to the relative path to your project if it is not in the root of your repository.              |                                            |                        |
| `cpan_mirror`            | The custom CPAN mirror URL.                                                                             |                                            |                        |
| `github_webhook_secret`  | Github trigger secret. A difficult to guess string encoded as part of the webhook URL. Not encrypted.   |                                            |                        |
| `source_repository_url`  | The URL of the repository with your application source code.                                            | `https://github.com/sclorg/cakephp-ex.git` |                        |
| `source_repository_ref`  | Set this to a branch name, tag or other ref of your repository if you are not using the default branch. | `master`                                   |                        |
| `perl_apache2_reload`    | Set this to \"true\" to enable automatic reloading of modified Perl modules.                            |                                            |                        |
| `secret_key_base`        | Your secret key for verifying the integrity of signed cookies.                                          |                                            |                        |

