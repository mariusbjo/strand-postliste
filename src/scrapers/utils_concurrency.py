import os

def compute_concurrency(min_workers=2, max_workers=6):
    """
    Beregner anbefalt concurrency basert på CPU-kjerner.
    Holder seg innenfor [min_workers, max_workers].
    """
    cpu = os.cpu_count() or 2
    return min(max_workers, max(min_workers, cpu - 1))
