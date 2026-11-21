import unittest
from task_list import visible_tasks

class TaskListTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"id": 1, "archived": False}, {"id": 2, "archived": True}]

    def test_default_hides_archive(self):
        self.assertEqual(visible_tasks(self.rows), self.rows[:1])

    def test_explicit_false_hides_archive(self):
        self.assertEqual(visible_tasks(self.rows, False), self.rows[:1])

    def test_true_includes_archive_in_order(self):
        self.assertEqual(visible_tasks(self.rows, True), self.rows)

    def test_empty_and_input_preserved(self):
        original = [dict(row) for row in self.rows]
        self.assertEqual(visible_tasks([], False), [])
        visible_tasks(self.rows, False)
        self.assertEqual(self.rows, original)

if __name__ == "__main__":
    unittest.main()
