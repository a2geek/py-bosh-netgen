# Motivation

Utility to assist in generating BOSH cloud-config network sections.
Some tooling (looking at you, Genesis!) do not allow lazy IP selection and instead
require explicitly defined networks, including reserved static IP addresses.
Additional annoyance is done by not paying attention to what addresses have already
been assigned, leading to confusion when deploying infrastructure.

# Future Ideas

* 'reserved' processing maybe needs to use netaddr.IPSet if ranges become disjointed.
* Load existing configuration to ensure IPs don't get reassigned (and deal with the details of expanded IP space by splitting or adding to the subnets).
* Might need to target what subnets are applied; thinking of an "external" or routable IP addresses versus internal IP addresses.

# Installation

As with everything Python, use the `requirements.txt`:
```
$ pip3 install -r requirements.txt
```

# Example

```
$ python3 netgen.py --config sample-config.yml --output asdf.yml
```

Sample input:
```
subnets:
- azs: [z1,z2,z3]
  range: 192.168.123.0/24
  reserved:
  - 192.168.123.1-192.168.123.5
  dns: [192.168.5.1]
  cloud_properties:
    fake: true
    test: 'yes'
networks:
- name: jumpbox
  size: 2
  static: 1
- name: vault
  size: 4
  static: 3
- name: cf
  size: 64
  static: 4
```

Generates the following cloud-config networks section (in `asdf.yml`):
```
networks:
- name: jumpbox
  subnets:
  - azs:
    - z1
    - z2
    - z3
    cloud_properties:
      fake: true
      test: 'yes'
    dns:
    - 192.168.5.1
    gateway: 192.168.123.1
    range: 192.168.123.0/24
    reserved:
    - 192.168.123.0 - 192.168.123.5
    - 192.168.123.8 - 192.168.123.255
    static:
    - 192.168.123.6
  type: manual
- name: vault
  subnets:
  - azs:
    - z1
    - z2
    - z3
    cloud_properties:
      fake: true
      test: 'yes'
    dns:
    - 192.168.5.1
    gateway: 192.168.123.1
    range: 192.168.123.0/24
    reserved:
    - 192.168.123.0 - 192.168.123.7
    - 192.168.123.12 - 192.168.123.255
    static:
    - 192.168.123.8 - 192.168.123.10
  type: manual
- name: cf
  subnets:
  - azs:
    - z1
    - z2
    - z3
    cloud_properties:
      fake: true
      test: 'yes'
    dns:
    - 192.168.5.1
    gateway: 192.168.123.1
    range: 192.168.123.0/24
    reserved:
    - 192.168.123.0 - 192.168.123.11
    - 192.168.123.76 - 192.168.123.255
    static:
    - 192.168.123.12 - 192.168.123.15
  type: manual
```