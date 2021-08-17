# Nova u-Verifier

Nova u-Verifier is a container based active test agent

## Description

Nova μ-Verifiers are standalone, lightweight Verifiers deployed within network environment, and are capable of running Active tests independently.

You can run the Active tests On-demand or at configurable schedules and export test results to Apache Kafka.

Irrespective of a small-scale or large-scale distributed customer network environment, μ-Verifiers provide the ease of running various Active tests in their environment by deploying them in the network. The test result output can be consumed through Apache Kafka as required. The output can be generated in the YAML or JSON format.

This release includes the μ-Verifier application and a sample input configuration file.

The following Active tests are supported on the μ-Verifier:
• Ping Active Test
• TWAMP Reflector Test
• IPERF3 Client Active Test
• Over-The-Top Video Active Test
• Continuous Two Way Active Measurement Protocol Test
• IPERF3 Server Test

## Getting Started

### Dependencies

ConfigMap for specific test configuration must be loaded on Kubernetes to initiate the pod.
Sample configuration files for ConfigMap are included:
- PING Active Test: config-ping.json
- IPERF3 Client Active Test: `config-iperfClient.json`
- Continuous Two Way Active Measurement Protocol Test: `config-ctwamp.json`
- TWAMP Reflector Test: `config-twampRef.json`
- IPERF3 Server Test: `config-iperfServer.json`

### Installing

Loading configuration to configmap:
* copy the sample configuration file to config.json
* edit config.json if needed
* load to configmap using the following command:
```
$ cp <config-xxx.json> config.json
$ vi config.json
$ kubectl create configmap <configMap name> --from-file=<path to>config.json
```

### Executing program

* How to run the program
* Step-by-step bullets
```
$ helm3 install <name of pod> <location of helm chart> --set image=<image repository> --set testconfig=<configMap to use> --set name=<name of pod>
```

## Help

To check status of Pod, run the following command
```
$ kubectl logs <pod-name>
```

## License

Please refer to exfo_software-license-agreement-global_en.pdf file for details
https://www.exfo.com/en/resources/legal-documentation/terms-conditions/software-license-agreement/

## Acknowledgments

This product may include software developed by the following people and organizations with the following copyright notices:

• OpenSSL Project for use in the OpenSSL Toolkit. (http://www.openssl.org/). Copyright (c) 1998-2003. The OpenSSL Project. All rights reserved.
• APACHE KAFKA (https://kafka.apache.org/) © 2017 Apache Software Foundation under the terms of the Apache License v2. Apache Kafka, Kafka, and the Kafka logo are either registered trademarks or trademarks of The Apache Software Foundation in the United States and other countries.
• Docker (https://www.docker.com/) © 2020 Docker Inc. All rights reserved

All other trademarks or service marks are the property of their respective owners.

Any third party software provided to you is distributed under the terms of the license agreements associated with that third party software.