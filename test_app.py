import json
import unittest
from app import app, SAMPLE_TASKS

class TaskFlowApiTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Reset sample tasks before each test
        self.client.post('/api/tasks/reset')

    # ------------------------------------------------------------------
    # Step 1: Static Asset & Frontend Serving Tests
    # ------------------------------------------------------------------
    def test_serve_index(self):
        """GET / should serve index.html with 200 OK."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>TaskFlow', response.data)
        self.assertIn(b'tasksTableBody', response.data)

    def test_serve_style_css(self):
        """GET /style.css should serve CSS asset with 200 OK."""
        response = self.client.get('/style.css')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'--primary', response.data)

    def test_serve_script_js(self):
        """GET /script.js should serve JavaScript asset with 200 OK."""
        response = self.client.get('/script.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TaskFlow', response.data)

    def test_security_blocks_python_and_sensitive_files(self):
        """GET /app.py or other sensitive files should return 404 Not Found."""
        for sensitive_path in ['/app.py', '/.venv', '/.env', '/package.json']:
            response = self.client.get(sensitive_path)
            self.assertEqual(response.status_code, 404, f"Path {sensitive_path} should be blocked")

    # ------------------------------------------------------------------
    # Step 2: REST API CRUD Tests
    # ------------------------------------------------------------------
    def test_get_tasks(self):
        """GET /api/tasks should return the initial list of tasks."""
        response = self.client.get('/api/tasks')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(SAMPLE_TASKS))
        self.assertEqual(data[0]['id'], '1')
        self.assertEqual(data[0]['name'], SAMPLE_TASKS[0]['name'])

    def test_create_task_success(self):
        """POST /api/tasks with valid data should return 201 Created and the new task."""
        new_task_payload = {
            "name": "Write unit tests for Flask backend",
            "project": "Testing",
            "dueDate": "2026-11-05",
            "priority": "High",
            "status": "In Progress"
        }
        response = self.client.post(
            '/api/tasks',
            data=json.dumps(new_task_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        created = response.get_json()
        self.assertIn('id', created)
        self.assertEqual(created['name'], new_task_payload['name'])
        self.assertEqual(created['project'], 'Testing')
        self.assertEqual(created['priority'], 'High')
        self.assertEqual(created['status'], 'In Progress')

        # Verify task is present in list
        get_res = self.client.get('/api/tasks')
        tasks = get_res.get_json()
        self.assertEqual(len(tasks), len(SAMPLE_TASKS) + 1)
        self.assertEqual(tasks[0]['id'], created['id'])

    def test_create_task_validation_error(self):
        """POST /api/tasks with empty or missing name should return 400 Bad Request."""
        # Missing name
        res1 = self.client.post(
            '/api/tasks',
            data=json.dumps({"project": "Design"}),
            content_type='application/json'
        )
        self.assertEqual(res1.status_code, 400)
        self.assertIn('error', res1.get_json())

        # Empty name
        res2 = self.client.post(
            '/api/tasks',
            data=json.dumps({"name": "   "}),
            content_type='application/json'
        )
        self.assertEqual(res2.status_code, 400)
        self.assertIn('error', res2.get_json())

    def test_update_task_success(self):
        """PUT /api/tasks/<id> should update fields and return 200 OK."""
        update_payload = {
            "name": "Design MVP landing page mockup in Figma (Revised)",
            "status": "Completed"
        }
        response = self.client.put(
            '/api/tasks/1',
            data=json.dumps(update_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        updated = response.get_json()
        self.assertEqual(updated['id'], '1')
        self.assertEqual(updated['name'], update_payload['name'])
        self.assertEqual(updated['status'], 'Completed')
        # Preserved unchanged fields
        self.assertEqual(updated['project'], 'Website Launch')

    def test_update_task_not_found(self):
        """PUT /api/tasks/<nonexistent> should return 404 Not Found."""
        response = self.client.put(
            '/api/tasks/999999',
            data=json.dumps({"name": "Ghost task"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.get_json())

    def test_delete_task_success(self):
        """DELETE /api/tasks/<id> should remove task and return 200 OK."""
        response = self.client.delete('/api/tasks/2')
        self.assertEqual(response.status_code, 200)
        res_json = response.get_json()
        self.assertEqual(res_json['deletedTaskId'], '2')

        # Verify task is no longer in tasks
        get_res = self.client.get('/api/tasks')
        ids = [t['id'] for t in get_res.get_json()]
        self.assertNotIn('2', ids)

    def test_delete_task_not_found(self):
        """DELETE /api/tasks/<nonexistent> should return 404 Not Found."""
        response = self.client.delete('/api/tasks/999999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.get_json())

    def test_clear_all_and_reset_tasks(self):
        """DELETE /api/tasks clears all, and POST /api/tasks/reset restores sample data."""
        # Clear all
        del_res = self.client.delete('/api/tasks')
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(len(self.client.get('/api/tasks').get_json()), 0)

        # Reset
        reset_res = self.client.post('/api/tasks/reset')
        self.assertEqual(reset_res.status_code, 200)
        restored_tasks = self.client.get('/api/tasks').get_json()
        self.assertEqual(len(restored_tasks), len(SAMPLE_TASKS))

if __name__ == '__main__':
    unittest.main()

