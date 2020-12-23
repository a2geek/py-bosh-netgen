# Motivation

Utility to assist in generating BOSH cloud-config network sections.
Some tooling (looking at you, Genesis!) do not allow lazy IP selection and instead
require explicitly defined networks, including reserved static IP addresses.
Additional annoyance is done by not paying attention to what addresses have already
been assigned, leading to confusion when deploying infrastructure.

# Installation

As with everything Python, use the `requirements.txt`:
```
$ pip install -r requirements.txt
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
  dns: [192.168.5.1]
networks:
- name: jumpbox
  size: 2
  static: 1
- name: vault
  size: 4
  static: 3
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
    dns:
    - 192.168.5.1
    gateway: 192.168.123.1
    range: 192.168.123.0/24
    reserved:
    - 192.168.123.0 - 192.168.123.1
    - 192.168.123.4 - 192.168.123.255
    static:
    - 192.168.123.2
  type: manual
- name: vault
  subnets:
  - azs:
    - z1
    - z2
    - z3
    dns:
    - 192.168.5.1
    gateway: 192.168.123.1
    range: 192.168.123.0/24
    reserved:
    - 192.168.123.0 - 192.168.123.3
    - 192.168.123.8 - 192.168.123.255
    static:
    - 192.168.123.4 - 192.168.123.6
  type: manual
```