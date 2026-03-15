# Amazon Linux 2023 Kernel SRPM History

This repository contains a history of **Amazon Linux 2023 kernel SRPMs**,
unpacked and normalized to make it easier to inspect how the kernel packaging evolves over time.

It is intended for:

* exploring how Amazon Linux kernel patches evolve over time
* tracking changes in kernel configurations

Each commit timestamped with the SRPM build time.

Separate branches are used for LTS kernels shipped in AL2023:

* `kernel-6.1`
* `kernel-6.12`
* `kernel-6.18`

## Contents

The repository stores the **unpacked SRPM contents**, mainly:

* `kernel.spec`
* patch files used during the build
* kernel configuration files
* packaging scripts and metadata
