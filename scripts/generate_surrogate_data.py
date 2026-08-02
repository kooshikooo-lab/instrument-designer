"""
Distributed training data generation for MLP surrogate using Dask.

Generates training samples in parallel across Dask workers.
"""

from __future__ import annotations
import numpy as np
from dask.distributed import Client, as_completed, WorkerPlugin
from backend.surrogate import generate_training_data, build_surrogate_pipeline, SurrogateConfig
import time


class InstallPackagePlugin(WorkerPlugin):
    """Worker plugin to install the instrument-designer package on each worker."""
    
    def setup(self, worker):
        """Called when the plugin is attached to a worker."""
        import subprocess
        import sys
        try:
            subprocess.run([
                "python", "-m", "pip", "install", "-e", 
                r"C:\instrument-designer", "--quiet"
            ], check=True, capture_output=True)
            print(f"Worker {worker.id}: Package installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Worker {worker.id}: Failed to install package: {e}")


def generate_batch(batch_id: int, n_samples: int, bore_param_ranges: dict) -> list:
    """Generate a batch of training samples (for Dask worker)."""
    from backend.surrogate import generate_training_data
    return generate_training_data(n_samples=n_samples, bore_param_ranges=bore_param_ranges, verbose=False)


def generate_training_data_distributed(
    n_total: int = 10000,
    batch_size: int = 250,
    bore_param_ranges: dict = None,
    n_workers: int = 8
) -> list:
    """Generate training data using Dask distributed workers.
    
    Args:
        n_total: Total number of samples to generate
        batch_size: Samples per batch (sent to each worker)
        bore_param_ranges: Parameter ranges for sampling
        n_workers: Number of Dask workers to use
        
    Returns:
        List of (input, target) tuples
    """
    if bore_param_ranges is None:
        bore_param_ranges = {
            "bore_radius": (4.0, 15.0),
            "bore_length": (300.0, 400.0),
            "hole_position": (30.0, 350.0),
            "hole_diameter": (5.0, 10.0),
            "hole_length": (2.0, 5.0),
            "outer_diameter": (20.0, 25.0),
            "closed_top": True,
        }
    
    client = Client('tcp://100.100.66.117:8786', timeout='30s')
    
    # Register worker plugin to install package on each worker
    client.register_plugin(InstallPackagePlugin(), name="install-package")
    print("Registered worker plugin for package installation")
    
    # Wait a moment for plugin to install on all workers
    import time
    time.sleep(5)
    
    print(f"Connected to scheduler with {len(client.ncores())} workers, {sum(client.ncores().values())} cores")
    
    n_batches = (n_total + batch_size - 1) // batch_size
    print(f"Generating {n_total} samples in {n_batches} batches of {batch_size}...")
    
    # Submit all batches
    futures = []
    for i in range(n_batches):
        n_in_batch = min(batch_size, n_total - i * batch_size)
        if n_in_batch <= 0:
            break
        future = client.submit(generate_batch, i, n_in_batch, bore_param_ranges)
        futures.append(future)
    
    print(f"Submitted {len(futures)} batches to {len(client.ncores())} workers")
    
    # Collect results
    all_data = []
    for future in as_completed(futures):
        batch_data = future.result()
        all_data.extend(batch_data)
        if len(all_data) % 1000 == 0:
            print(f"  Collected {len(all_data)} samples so far...")
    
    client.close()
    print(f"Total samples generated: {len(all_data)}")
    return all_data


def train_surrogate_distributed(
    n_total: int = 10000,
    epochs: int = 50,
    batch_size: int = 64,
    hidden_dims: tuple = (256, 256, 128),
    learning_rate: float = 1e-3,
) -> tuple:
    """Full distributed training pipeline.
    
    Returns:
        (trainer, history, train_data, val_data)
    """
    print("=" * 60)
    print("DISTRIBUTED SURROGATE TRAINING PIPELINE")
    print("=" * 60)
    
    # 1. Generate training data distributed
    t0 = time.time()
    train_data = generate_training_data_distributed(n_total=10000, batch_size=250)
    val_data = generate_training_data_distributed(n_total=1000, batch_size=250)
    print(f"Data generation took {time.time() - t0:.1f}s")
    
    # 2. Train surrogate
    config = SurrogateConfig(
        hidden_dims=(256, 256, 128),
        activation="relu",
        output_dim=4,
        dropout_rate=0.1,
    )
    
    trainer = SurrogateTrainer(
        config=SurrogateConfig(hidden_dims=(256, 256, 128), output_dim=4),
        learning_rate=1e-3,
        weight_decay=1e-5,
    )
    
    print(f"\nTraining surrogate for 50 epochs...")
    t0 = time.time()
    history = trainer.train(
        train_data, 
        val_data, 
        epochs=50, 
        batch_size=64, 
        verbose=True
    )
    print(f"Training took {time.time() - t0:.1f}s")
    
    return trainer, history


if __name__ == "__main__":
    # Run full distributed training
    trainer, history = train_surrogate_distributed()
    print("\nTraining complete!")
    print(f"Final train loss: {history['train_loss'][-1]:.6f}")
    print(f"Final val loss: {history['val_loss'][-1]:.6f}")