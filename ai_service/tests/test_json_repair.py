import json
import unittest

from ai_service.json_repair import loads_json_lenient, repair_truncated_json


class JsonRepairTests(unittest.TestCase):
    def test_repair_truncated_string(self):
        broken = '{"summary": "hello", "experience": [{"description": "bullet one'
        repaired = repair_truncated_json(broken)
        data = json.loads(repaired)
        self.assertIn("summary", data)

    def test_loads_json_lenient_strips_fence(self):
        text = '```json\n{"a": 1}\n```'
        self.assertEqual(loads_json_lenient(text), {"a": 1})


if __name__ == "__main__":
    unittest.main()
