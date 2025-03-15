import numpy as np


def regression_loss(targets, preds):
    # Extract the values from the lists of ef_field objects
    u = np.array([ef_field.value for ef_field in targets])
    v = np.array([ef_field.value for ef_field in preds])

    # Compute Euclidean distance using numpy
    dist = np.linalg.norm(u - v)

    # Compute the normalization constant
    norm = np.sqrt(len(u))

    # Return the loss dictionary
    loss = {
        "failure_score_unnormalized": dist,
        "failure_score_normalization_constant": norm,
    }
    return loss
