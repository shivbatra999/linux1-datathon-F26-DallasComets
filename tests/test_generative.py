import unittest
from unittest.mock import Mock, patch

import httpx

from backend.generative import (
    GenerationUnavailable,
    _prediction,
    generate_summary,
    owner_summary,
)
from backend.predictive import ModelUnavailable


class GenerativeSummaryTests(unittest.TestCase):
    @patch("backend.generative.httpx.post")
    def test_model_receives_aggregates_and_prediction_only(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": "Sales are healthy."}}]
        }
        post.return_value = response

        result = generate_summary(
            2800,
            2,
            [{"item_id": 2, "reason": "paired", "source": "model"}],
        )

        self.assertEqual(result, "Sales are healthy.")
        body = post.call_args.kwargs["json"]
        prompt = body["messages"][1]["content"]
        self.assertIn("28.00", prompt)
        self.assertIn("2", prompt)
        self.assertIn("item_id", prompt)
        self.assertNotIn("customer@example.com", prompt)
        self.assertNotIn("password", prompt.lower())
        self.assertNotIn("token", prompt.lower())
        self.assertNotIn("reasoning_format", body)
        self.assertEqual(body["max_tokens"], 48)
        self.assertEqual(
            body["chat_template_kwargs"],
            {"enable_thinking": False},
        )

    @patch("backend.generative.httpx.post")
    def test_hidden_reasoning_is_not_returned(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "<think>private reasoning</think>Sales are healthy."
                }
            }]
        }
        post.return_value = response

        self.assertEqual(
            generate_summary(1000, 1, []),
            "Sales are healthy.",
        )

    @patch("backend.generative.httpx.post")
    def test_prompt_echo_is_removed(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": (
                        "We need to write exactly two concise sentences for a "
                        "restaurant store owner. Sales are steady. Feature the popular item."
                    )
                }
            }]
        }
        post.return_value = response

        self.assertEqual(
            generate_summary(1000, 1, []),
            "Sales are steady. Feature the popular item.",
        )

    @patch("backend.generative.httpx.post")
    def test_prompt_only_response_is_rejected(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": (
                        "We need to write exactly two concise sentences. "
                        "Return only the final two sentences. "
                        "Prediction basis: Tea is popular."
                    )
                }
            }]
        }
        post.return_value = response

        with self.assertRaisesRegex(GenerationUnavailable, "instructions"):
            generate_summary(1000, 1, [])

    @patch("backend.generative.httpx.post")
    def test_instruction_echo_is_rejected_instead_of_displayed(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": (
                        "Write two short sentences for a restaurant owner. "
                        "Sentence one: summarize the sales. Sentence two: give one practical tip."
                    )
                }
            }]
        }
        post.return_value = response

        with self.assertRaisesRegex(GenerationUnavailable, "instructions"):
            generate_summary(1000, 1, [])

    @patch("backend.generative.httpx.post")
    def test_answer_after_reasoning_paragraph_is_selected(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": (
                        "I should summarize the verified sales and give a tip.\n\n"
                        "Final answer: Sales are steady. Consider featuring the popular item."
                    )
                }
            }]
        }
        post.return_value = response

        self.assertEqual(
            generate_summary(1000, 1, []),
            "Sales are steady. Consider featuring the popular item.",
        )

    @patch("backend.generative.httpx.post", side_effect=httpx.HTTPError("offline"))
    def test_model_failure_is_explicit(self, post):
        with self.assertRaises(GenerationUnavailable):
            generate_summary(1000, 1, [])

    @patch(
        "backend.generative.httpx.post",
        side_effect=httpx.ReadTimeout("slow Granite response"),
    )
    def test_model_timeout_is_explicit(self, post):
        with self.assertRaisesRegex(GenerationUnavailable, "timed out"):
            generate_summary(1000, 1, [])

    @patch("backend.generative.load_model", side_effect=ModelUnavailable("missing"))
    def test_prediction_model_failure_is_explicit(self, load_model):
        client = Mock()
        orders = Mock()
        orders.select.return_value = orders
        orders.eq.return_value = orders
        orders.ilike.return_value = orders
        orders.execute.return_value.data = []
        menu = Mock()
        menu.select.return_value = menu
        menu.eq.return_value = menu
        menu.order.return_value = menu
        menu.execute.return_value.data = [
            {"id": "item-1", "name": "Box", "is_available": True}
        ]
        client.table.side_effect = [orders, menu]

        with self.assertRaises(GenerationUnavailable):
            owner_summary(client, "business-1")
        load_model.assert_called_once()

    @patch("backend.generative.load_model")
    @patch("backend.generative.recommend", return_value=[
        {"item_id": 2, "reason": "Popular choice: ordered in 1 of 1 past orders.", "source": "fallback"}
    ])
    def test_prediction_translates_item_name(self, recommend, load_model):
        load_model.return_value = {
            "item_ids": [1, 2],
            "model": Mock(),
        }

        result = _prediction(
            [
                {"id": "item-a", "name": "Bowl", "is_available": True},
                {"id": "item-b", "name": "Tea", "is_available": True},
            ],
            [["item-a"]],
        )

        self.assertEqual(result[0]["reason"], "Tea is a popular choice based on the completed order history.")
        recommend.assert_called_once()

    @patch("backend.generative.load_model")
    @patch("backend.generative.recommend", return_value=[
        {"item_id": 2, "reason": "Popular choice: ordered in 1 of 1 past orders.", "source": "fallback"}
    ])
    def test_prediction_name_mapping_uses_database_rows(self, recommend, load_model):
        load_model.return_value = {
            "item_ids": [1, 2],
            "model": Mock(),
        }

        result = _prediction(
            [
                {"id": "item-a", "name": "Box", "is_available": True},
                {"id": "item-b", "name": "Tea", "is_available": True},
            ],
            [["item-a"]],
        )

        self.assertEqual(result[0]["item_id"], 2)
        self.assertNotIn("string indices must be integers", str(result))

    @patch("backend.generative.generate_summary", return_value="Summary")
    @patch("backend.generative._prediction", return_value=[
        {"item_id": 2, "reason": "paired", "source": "model"}
    ])
    def test_owner_summary_scopes_queries_to_business(self, prediction, summary):
        client = Mock()
        orders = Mock()
        orders.select.return_value = orders
        orders.eq.return_value = orders
        orders.ilike.return_value = orders
        orders.execute.return_value.data = [
            {"id": "order-1", "total": "14.00"}
        ]
        menu = Mock()
        menu.select.return_value = menu
        menu.eq.return_value = menu
        menu.order.return_value = menu
        menu.execute.return_value.data = [
            {"id": "item-1", "name": "Box", "is_available": True}
        ]
        lines = Mock()
        lines.select.return_value = lines
        lines.in_.return_value = lines
        lines.execute.return_value.data = [
            {"order_id": "order-1", "menu_item_id": "item-1"}
        ]
        client.table.side_effect = [orders, menu, lines]

        result = owner_summary(client, "business-1")

        self.assertEqual(result, {
            "text": "Summary",
            "prediction_reason": [
                {"item_id": 2, "reason": "paired", "source": "model"}
            ],
            "source": "model",
        })
        orders.eq.assert_any_call("business_id", "business-1")
        self.assertEqual(summary.call_args.args[0:2], (1400, 1))
        prediction.assert_called_once_with(
            [{"id": "item-1", "name": "Box", "is_available": True}],
            [["item-1"]],
        )


if __name__ == "__main__":
    unittest.main()
