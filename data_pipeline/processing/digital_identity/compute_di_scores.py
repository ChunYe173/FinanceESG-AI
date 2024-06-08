"""
Library to compute different digital identity scores
"""
import math


def sigmoid(x, k=0.25, x0=10):
    return 1 / (1 + math.exp(-k * (x - x0)))


def inverse_sigmoid(x, k=0.25, x0=10):
    return 1 / (1 + math.exp(k * (x - x0)))


def get_ws_rank(keywords: list[str], total_time: list[float], errors: list[str], page_warnings: list[str],
                duplicate_pages: list[str]):
    rank = 1
    rank += 2 * sigmoid(len(keywords))
    rank += 3 * inverse_sigmoid(total_time, k=3, x0=2)
    rank += 2 * inverse_sigmoid(len(errors))
    rank += inverse_sigmoid(len(page_warnings))
    rank += inverse_sigmoid(len(duplicate_pages))
    rank = round(rank / 10, ndigits=4)
    return rank


def get_digital_score(linkedin_followers: int, ws_rank: float,
                      mean_linkedin_followers: float, mean_ws_rank: float,
                      frequency_ratio: float = 0.1345):
    """Calculate digital score based on specified frequency ratio."""
    return (
            linkedin_followers * frequency_ratio / mean_linkedin_followers
            + ws_rank / mean_ws_rank
    )
