import os
from datetime import timedelta

import torch
from torch import distributed as dist


def get_local_rank() -> int:
    return int(os.getenv("LOCAL_RANK", 0))


def get_rank() -> int:
    return int(os.getenv("RANK", 0))


def get_world_size() -> int:
    return int(os.getenv("WORLD_SIZE", 1))


def is_dist_initialized() -> bool:
    return dist.is_available() and dist.is_initialized()


def init_distributed(timeout_seconds: int = 1800):
    backend = "nccl" if torch.cuda.is_available() else "gloo"
    if is_dist_initialized():
        return
    dist.init_process_group(backend=backend,
                            rank=get_rank(),
                            world_size=get_world_size(),
                            timeout=timedelta(seconds=timeout_seconds))
    if torch.cuda.is_available():
        torch.cuda.set_device(get_local_rank())


def cleanup_distributed():
    if is_dist_initialized():
        dist.destroy_process_group()


def synchronize():
    if get_world_size() > 1 and is_dist_initialized():
        dist.barrier()


def ddp_all_reduce_sum(tensor: torch.Tensor) -> torch.Tensor:
    if get_world_size() > 1 and is_dist_initialized():
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
    return tensor
