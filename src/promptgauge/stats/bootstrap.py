"""Bootstrap: seeded percentile confidence interval of the mean difference across cases. PRD
F6.4.
"""

from collections.abc import Sequence

import numpy as np

from promptgauge.stats.mean_interval import MeanInterval


class Bootstrap:
    """Percentile bootstrap of the mean. Each call starts a fresh generator from the same seed, so
    the same differences always give the same interval whatever ran before (PRD §9 reproducibility).
    """

    def __init__(self, seed: int = 0) -> None:
        self._seed = seed

    def mean_ci(
        self,
        differences: Sequence[float],
        resamples: int = 1000,
        level: float = 0.95,
    ) -> MeanInterval:
        """Mean of `differences` (one per case) and its two-sided percentile interval."""
        if not differences:
            raise ValueError("mean_ci needs at least one difference")
        if resamples < 1:
            raise ValueError("resamples must be at least 1")
        if not 0.0 < level < 1.0:
            raise ValueError("level must be strictly between 0 and 1")
        values = np.asarray(differences, dtype=float)
        n = len(values)
        rng = np.random.default_rng(self._seed)
        indexes = rng.integers(0, n, size=(resamples, n))
        means = values[indexes].mean(axis=1)
        tail = (1.0 - level) / 2.0 * 100.0
        low, high = np.percentile(means, [tail, 100.0 - tail])
        mean = float(values.mean())
        # The sample mean is the centre of the resampling distribution, but with few resamples the
        # percentile interval can miss it by rounding; clamp so the interval always contains it.
        return MeanInterval(
            mean=mean,
            ci_low=min(float(low), mean),
            ci_high=max(float(high), mean),
            n_cases=n,
        )
