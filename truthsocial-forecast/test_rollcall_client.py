from __future__ import annotations

import unittest
from datetime import date

from rollcall_client import RollCallClient


def row(post_id: str, posted_at: str) -> dict:
    return {
        "id": post_id,
        "date": posted_at,
        "text": f"post {post_id}",
        "post_url": f"https://truthsocial.com/@realDonaldTrump/posts/{post_id}",
        "social": {},
    }


class FakeRollCallClient(RollCallClient):
    def __init__(self, pages: dict[int, dict]) -> None:
        super().__init__()
        self.pages = pages
        self.requests: list[dict[str, object]] = []

    def _get_json(self, params: dict[str, object]) -> dict:
        self.requests.append(params)
        return self.pages[int(params["page"])]


class RollCallClientTest(unittest.TestCase):
    def test_count_uses_locally_filtered_posts_not_rollcall_total_hits(self):
        client = FakeRollCallClient(
            {
                1: {
                    "meta": {"total_hits": 37, "page_count": 1},
                    "data": [
                        row("new-image-1", "2026-05-25T20:47:25-04:00"),
                        row("new-image-2", "2026-05-25T20:10:27-04:00"),
                        row("week-start", "2026-05-24T00:23:49-04:00"),
                        row("before-week", "2026-05-23T21:59:43-04:00"),
                    ],
                }
            }
        )

        count = client.count_truth_social_posts(date(2026, 5, 24), date(2026, 5, 25), use_cache=False)

        self.assertEqual(count, 3)
        self.assertNotIn("dateFilter", client.requests[0])
        self.assertNotIn("start_date", client.requests[0])
        self.assertNotIn("end_date", client.requests[0])

    def test_truth_social_posts_paginates_until_rows_are_older_than_start(self):
        client = FakeRollCallClient(
            {
                1: {
                    "meta": {"total_hits": 99, "page_count": 3},
                    "data": [
                        row("latest", "2026-05-25T20:47:25-04:00"),
                        row("middle", "2026-05-24T00:23:49-04:00"),
                    ],
                },
                2: {
                    "meta": {"total_hits": 99, "page_count": 3},
                    "data": [
                        row("older", "2026-05-23T21:59:43-04:00"),
                    ],
                },
                3: {
                    "meta": {"total_hits": 99, "page_count": 3},
                    "data": [
                        row("too-far", "2026-05-22T21:59:43-04:00"),
                    ],
                },
            }
        )

        posts = client.truth_social_posts(date(2026, 5, 24), date(2026, 5, 25))

        self.assertEqual([post.id for post in posts], ["middle", "latest"])
        self.assertEqual([request["page"] for request in client.requests], [1, 2])


if __name__ == "__main__":
    unittest.main()
