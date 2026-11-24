"""Placeholder for future TransJakarta demand model training.

No model is trained by this initial project setup.

Future implementation should:
- load only data/processed/transjakarta_model_ready.csv;
- keep corridor and direction in a reproducible categorical encoding;
- use a chronological train-validation split;
- exclude pay-card and other personally identifying fields;
- evaluate baseline and candidate models without future-data leakage.
"""


def train() -> None:
    """Placeholder; intentionally does not train or save a model."""
    raise NotImplementedError(
        "Model training is not implemented in the initial project setup."
    )


if __name__ == "__main__":
    train()
