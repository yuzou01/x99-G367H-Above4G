# Before / after evidence

## Before (stock firmware, Above4G byte = 0)

POST shows:

```
OUT OF RESOURCES
```

Linux (stock, after force-booting past the warning):

```
$ lspci -vvv -s 04:00.0 | grep "Region 1"
        Region 1: Memory at 383c10000000 (64-bit, prefetchable) [size=256M]
```

(the 16 GB BAR1 was down-sized to a 256 MB stub; NVIDIA driver then reports an
invalid BAR / the GPU is unusable for large-BAR workloads, plus a stream of
correctable PCIe AER errors)

## After (Setup:0x3A = 1 via dmpstore, no firmware change)

```
$ lspci -vvv -s 04:00.0 | grep "Region 1"
        Region 1: Memory at 383800000000 (64-bit, prefetchable) [size=16G]

$ nvidia-smi
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 550.163.01   Driver Version: 550.163.01   CUDA Version: 12.4                 |
|   0  Tesla V100-SXM2-16GB    00000000:04:00.0    Off    0   ...   16384MiB              |
+-----------------------------------------------------------------------------------------+
```

No `OUT OF RESOURCES` at POST. Only benign correctable physical-layer AER
messages remain (link-quality related, unrelated to BAR sizing).

## Board under test

- HSGM/Vulcan X99-PF4 clone, board code G367H (GHX99014)
- AMI Aptio V firmware, version 5.11 (2019-10-14), **never reflashed for this fix**
- Host bridge 8086:6F00 (Grantley), 24 GB RAM
- GPU: Tesla V100 SXM2 16 GB on an SXM2-to-PCIe adapter (BAR1 = 16 GB)
