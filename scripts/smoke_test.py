import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd):
    print(f"[smoke] running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=False)


def main():
    parser = argparse.ArgumentParser("Unified train pipeline smoke runner")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    config_dir = Path(__file__).resolve().parents[1] / "configs"
    configs = [
        "mnist_mlp.yaml",
        "mnist_conv.yaml",
        "cifar_resnet18.yaml",
        "cifar_wideresnet.yaml",
        "coco128_fasterrcnn.yaml",
        "coco128_retinanet.yaml",
    ]

    failed = []
    for config_name in configs:
        config_path = str(config_dir / config_name)
        result = run_cmd([
            args.python,
            "-m",
            "scripts.train",
            "--config",
            config_path,
        ])
        if result.returncode != 0:
            failed.append(config_name)

    # DDP smoke sample.
    ddp_result = run_cmd([
        "torchrun",
        "--nproc_per_node=2",
        "-m",
        "scripts.train",
        "--config",
        str(config_dir / "mnist_mlp.yaml"),
        "--distributed",
    ])
    if ddp_result.returncode != 0:
        failed.append("ddp_mnist_mlp")

    if failed:
        print(f"[smoke] failed cases: {failed}")
        sys.exit(1)
    print("[smoke] all checks passed")


if __name__ == "__main__":
    main()
