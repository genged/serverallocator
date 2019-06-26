# Server Allocator

A command line utility to allocate Apps that require resources to Servers that have resources.
Resources supported: 
 - CPU
 - Memory
 - Disk space (WIP)

Allocator also supported anti-affinity labels

Example:
```bash
$ ./cli.py --resources-file tests/data/resources.yml
node1:
  apps: [someapp5, someapp6, cluster1-node1, someapp9]
node2:
  apps: [someapp2, someapp4, someapp7, cluster1-node2]
node3:
  apps: [someapp1, someapp3, someapp77, cluster1-node3]
node4:
  apps: [someapp8]
```

Using the python API:
```python
from allocation import allocator
alloc = allocator.Allocator([allocator.Server(32, 16, 1000)], [allocator.App(12, 12, 500)])
print(alloc.allocate())
```
Outputs:
```python
[{'node': Server(memory=32, cpu=16, disk=1000, name='server-rroledczuc'), 
  'apps': [App(memory=12, cpu=12, disk=500, name='app-fxvedwnjkg', antiAffinityLabels=None)]}]
```
