import json
import threading
import time
import urllib.request
import urllib.error
import unittest
from app import app, SAMPLE_TASKS

PORT = 5002
BASE_URL = f"http://127.0.0.1:{PORT}"

def run_server():
    app.run(port=PORT, use_reloader=False)

class TaskFlowLiveE2ETestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_thread = threading.Thread(target=run_server, daemon=True)
        cls.server_thread.start()
        # Give the server a moment to spin up
        time.sleep(1.5)

    def http_request(self, path, method="GET", data=None):
        url = f"{BASE_URL}{path}"
        headers = {}
        encoded_data = None
        if data is not None:
            headers['Content-Type'] = 'application/json'
            encoded_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                body = resp.read().decode('utf-8')
                try:
                    json_data = json.loads(body)
                except Exception:
                    json_data = None
                return status, json_data, body
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            try:
                json_data = json.loads(body)
            except Exception:
                json_data = None
            return e.code, json_data, body

    def test_01_frontend_assets_served_safely(self):
        """Verify frontend assets are served correctly and sensitive files are blocked."""
        # 1. index.html
        status, _, body = self.http_request('/')
        self.assertEqual(status, 200)
        self.assertIn('<title>TaskFlow', body)
        self.assertIn('script.js', body)
        self.assertIn('style.css', body)

        # 2. style.css
        status, _, body = self.http_request('/style.css')
        self.assertEqual(status, 200)
        self.assertIn('--primary', body)

        # 3. script.js
        status, _, body = self.http_request('/script.js')
        self.assertEqual(status, 200)
        self.assertIn("API_BASE_URL = '/api/tasks'", body)
        self.assertIn("loadTasksFromApi", body)

        # 4. Sensitive files blocked (404)
        for sensitive in ['/app.py', '/.venv', '/.env', '/package.json']:
            status, _, _ = self.http_request(sensitive)
            self.assertEqual(status, 404, f"Sensitive path {sensitive} must be blocked with 404")

    def test_02_load_initial_tasks(self):
        """Verify initial tasks are fetched from GET /api/tasks matching sample tasks."""
        status, tasks, _ = self.http_request('/api/tasks')
        self.assertEqual(status, 200)
        self.assertIsInstance(tasks, list)
        self.assertGreaterEqual(len(tasks), 5)
        # Check standard fields are present
        first_task = tasks[0]
        for field in ['id', 'name', 'project', 'dueDate', 'priority', 'status']:
            self.assertIn(field, first_task)

    def test_03_create_task(self):
        """Verify task creation via POST /api/tasks."""
        new_task = {
            "name": "Integration Sprint Planning",
            "project": "Q4 Roadmap",
            "dueDate": "2026-11-15",
            "priority": "High",
            "status": "In Progress"
        }
        status, created, _ = self.http_request('/api/tasks', method='POST', data=new_task)
        self.assertEqual(status, 201)
        self.assertIn('id', created)
        self.assertEqual(created['name'], new_task['name'])
        self.assertEqual(created['project'], new_task['project'])

        # Confirm it appears in GET /api/tasks
        status, tasks, _ = self.http_request('/api/tasks')
        self.assertEqual(status, 200)
        self.assertTrue(any(t['id'] == created['id'] for t in tasks))
        TaskFlowLiveE2ETestCase.created_task_id = created['id']

    def test_04_edit_task(self):
        """Verify task update via PUT /api/tasks/<id>."""
        task_id = getattr(TaskFlowLiveE2ETestCase, 'created_task_id', '1')
        update_data = {
            "name": "Integration Sprint Planning (Approved)",
            "status": "Completed"
        }
        status, updated, _ = self.http_request(f'/api/tasks/{task_id}', method='PUT', data=update_data)
        self.assertEqual(status, 200)
        self.assertEqual(updated['id'], task_id)
        self.assertEqual(updated['name'], update_data['name'])
        self.assertEqual(updated['status'], 'Completed')

        # Confirm persisted in GET /api/tasks
        status, tasks, _ = self.http_request('/api/tasks')
        matching = next((t for t in tasks if t['id'] == task_id), None)
        self.assertIsNotNone(matching)
        self.assertEqual(matching['name'], update_data['name'])
        self.assertEqual(matching['status'], 'Completed')

    def test_05_delete_task(self):
        """Verify task deletion via DELETE /api/tasks/<id>."""
        task_id = getattr(TaskFlowLiveE2ETestCase, 'created_task_id', '1')
        status, res, _ = self.http_request(f'/api/tasks/{task_id}', method='DELETE')
        self.assertEqual(status, 200)
        self.assertEqual(res['deletedTaskId'], task_id)

        # Confirm it disappeared from GET /api/tasks
        status, tasks, _ = self.http_request('/api/tasks')
        self.assertFalse(any(t['id'] == task_id for t in tasks))

    def test_06_clear_all_and_reset(self):
        """Verify Settings: Clear All (DELETE /api/tasks) and Reset Sample Data (POST /api/tasks/reset)."""
        # 1. Clear All
        status, res, _ = self.http_request('/api/tasks', method='DELETE')
        self.assertEqual(status, 200)
        status, tasks, _ = self.http_request('/api/tasks')
        self.assertEqual(len(tasks), 0)

        # 2. Reset Sample Data
        status, res, _ = self.http_request('/api/tasks/reset', method='POST')
        self.assertEqual(status, 200)
        status, tasks, _ = self.http_request('/api/tasks')
        self.assertEqual(len(tasks), len(SAMPLE_TASKS))

if __name__ == '__main__':
    unittest.main()

