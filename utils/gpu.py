import os
import sys
from typing import Dict

import torch


def require_gpu() -> None:
    if not torch.cuda.is_available():
        print("GPU REQUIRED — TRAINING ABORTED")
        sys.exit(1)


def gpu_snapshot() -> Dict[str, float | str]:
    idx = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(idx)
    allocated = torch.cuda.memory_allocated(idx) / (1024 ** 3)
    reserved = torch.cuda.memory_reserved(idx) / (1024 ** 3)
    total = props.total_memory / (1024 ** 3)
    return {
        "device": torch.cuda.get_device_name(idx),
        "total_vram_gb": round(total, 3),
        "allocated_gb": round(allocated, 3),
        "reserved_gb": round(reserved, 3),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "not-set"),
    }
