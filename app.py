import copy
import os
import time
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request, send_from_directory

# Load environment variables from .env file if present
load_dotenv()

app = Flask(__name__, static_folder=None)

# ==========================================
# Sample Tasks (Preserved from TaskFlow)
# ==========================================
SAMPLE_TASKS = [
    {
        "id": "1",
        "name": "Design MVP landing page mockup in Figma",
        "project": "Website Launch",
        "priority": "High",
        "dueDate": "2026-10-30",
        "status": "In Progress"
    },
    {
        "id": "2",
        "name": "Setup user authentication & secure session tokens",
        "project": "Backend API",
        "priority": "High",
        "dueDate": "2026-11-02",
        "status": "Pending"
    },
    {
        "id": "3",
        "name": "Draft seed fundraising pitch deck",
        "project": "Fundraising",
        "priority": "Medium",
        "dueDate": "2026-11-10",
        "status": "Pending"
    },
    {
        "id": "4",
        "name": "Conduct user interviews with 5 beta testers",
        "project": "Customer Discovery",
        "priority": "Medium",
        "dueDate": "2026-10-28",
        "status": "Completed"
    },
    {
        "id": "5",
        "name": "Configure production SSL & domain DNS settings",
        "project": "DevOps",
        "priority": "Low",
        "dueDate": "2026-10-25",
        "status": "Completed"
    }
]

# In-memory tasks store (used when Supabase is not configured)
in_memory_tasks = copy.deepcopy(SAMPLE_TASKS)

# ==========================================
# Supabase Client Initialization
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = None

if SUPABASE_URL and SUPABASE_KEY and "your-project-id" not in SUPABASE_URL:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[TaskFlow] Successfully connected to Supabase PostgreSQL!")
    except Exception as e:
        print(f"[TaskFlow] Warning: Could not connect to Supabase: {e}")
        print("[TaskFlow] Falling back to in-memory tasks store.")
        supabase = None
else:
    print("[TaskFlow] Info: Running with in-memory storage. Add SUPABASE_URL and SUPABASE_KEY in .env to use Supabase.")

def format_db_task_to_frontend(row):
    """Format Supabase DB row (snake_case due_date) to frontend format (camelCase dueDate)."""
    if not row:
        return None
    return {
        "id": str(row.get("id")),
        "name": row.get("name") or "",
        "project": row.get("project") or "General",
        "dueDate": row.get("due_date") or row.get("dueDate") or "",
        "priority": row.get("priority") or "Medium",
        "status": row.get("status") or "Pending"
    }

# ==========================================
# 1. Frontend Asset Serving
# ==========================================
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Allowed extensions for frontend static assets
SAFE_STATIC_EXTENSIONS = (
    ".css",
    ".js",
    ".png",
    ".svg",
    ".jpg",
    ".jpeg",
    ".ico",
    ".woff",
    ".woff2"
)

@app.route("/")
def serve_index():
    """Serve the TaskFlow frontend index.html."""
    return send_from_directory(PROJECT_ROOT, "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    """
    Safely serve frontend static assets (style.css, script.js, icons).
    Protects against path traversal and blocks access to Python source files,
    environment files, virtual environments, and other sensitive files.
    """
    normalized = os.path.normpath(filename)
    if normalized.startswith("..") or normalized.startswith("/") or normalized.startswith("\\"):
        abort(404)

    is_safe_ext = any(filename.lower().endswith(ext) for ext in SAFE_STATIC_EXTENSIONS)
    is_sensitive = (
        filename.startswith(".")
        or filename.endswith((".py", ".env", ".json", ".lock", ".md", ".txt", ".sql"))
        or "venv" in filename.lower()
    )

    if is_safe_ext and not is_sensitive:
        file_path = os.path.join(PROJECT_ROOT, normalized)
        if os.path.isfile(file_path):
            return send_from_directory(PROJECT_ROOT, normalized)

    abort(404)

# ==========================================
# 2. REST API Endpoints for Tasks
# ==========================================

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Return all tasks."""
    if supabase:
        try:
            response = supabase.table("tasks").select("*").order("created_at", desc=True).execute()
            tasks_list = [format_db_task_to_frontend(r) for r in response.data]
            return jsonify(tasks_list), 200
        except Exception as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify(in_memory_tasks), 200

@app.route("/api/tasks", methods=["POST"])
def create_task():
    """Create a new task."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    name = data.get("name", "").strip() if isinstance(data.get("name"), str) else ""
    if not name:
        return jsonify({"error": "Task name is required"}), 400

    task_id = str(int(time.time() * 1000))
    project = (data.get("project") or "General").strip()
    due_date = data.get("dueDate", "")
    priority = (data.get("priority") or "Medium").strip()
    status = (data.get("status") or "Pending").strip()

    new_task = {
        "id": task_id,
        "name": name,
        "project": project,
        "dueDate": due_date,
        "priority": priority,
        "status": status
    }

    if supabase:
        try:
            db_payload = {
                "id": task_id,
                "name": name,
                "project": project,
                "due_date": due_date,
                "priority": priority,
                "status": status
            }
            res = supabase.table("tasks").insert(db_payload).execute()
            if res.data:
                return jsonify(format_db_task_to_frontend(res.data[0])), 201
            return jsonify(new_task), 201
        except Exception as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    in_memory_tasks.insert(0, new_task)
    return jsonify(new_task), 201

@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    """Update an existing task by ID."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    if "name" in data:
        name = data.get("name", "").strip() if isinstance(data.get("name"), str) else ""
        if not name:
            return jsonify({"error": "Task name cannot be empty"}), 400

    if supabase:
        try:
            check = supabase.table("tasks").select("*").eq("id", str(task_id)).limit(1).execute()
            if not check.data:
                return jsonify({"error": f"Task with ID '{task_id}' not found"}), 404

            db_update = {}
            if "name" in data:
                db_update["name"] = data["name"].strip()
            if "project" in data:
                db_update["project"] = (data.get("project") or "General").strip()
            if "dueDate" in data:
                db_update["due_date"] = data.get("dueDate", "")
            if "priority" in data:
                db_update["priority"] = (data.get("priority") or "Medium").strip()
            if "status" in data:
                db_update["status"] = (data.get("status") or "Pending").strip()

            res = supabase.table("tasks").update(db_update).eq("id", str(task_id)).execute()
            if res.data:
                return jsonify(format_db_task_to_frontend(res.data[0])), 200
            return jsonify({"error": f"Failed to update task '{task_id}'"}), 500
        except Exception as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    task = next((t for t in in_memory_tasks if t["id"] == str(task_id)), None)
    if not task:
        return jsonify({"error": f"Task with ID '{task_id}' not found"}), 404

    if "name" in data:
        task["name"] = data["name"].strip()
    if "project" in data:
        task["project"] = (data.get("project") or "General").strip()
    if "dueDate" in data:
        task["dueDate"] = data.get("dueDate", "")
    if "priority" in data:
        task["priority"] = (data.get("priority") or "Medium").strip()
    if "status" in data:
        task["status"] = (data.get("status") or "Pending").strip()

    return jsonify(task), 200

@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete an existing task by ID."""
    global in_memory_tasks

    if supabase:
        try:
            check = supabase.table("tasks").select("id").eq("id", str(task_id)).limit(1).execute()
            if not check.data:
                return jsonify({"error": f"Task with ID '{task_id}' not found"}), 404

            supabase.table("tasks").delete().eq("id", str(task_id)).execute()
            return jsonify({
                "message": "Task deleted successfully",
                "deletedTaskId": str(task_id)
            }), 200
        except Exception as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    task = next((t for t in in_memory_tasks if t["id"] == str(task_id)), None)
    if not task:
        return jsonify({"error": f"Task with ID '{task_id}' not found"}), 404

    in_memory_tasks = [t for t in in_memory_tasks if t["id"] != str(task_id)]
    return jsonify({
        "message": "Task deleted successfully",
        "deletedTaskId": str(task_id)
    }), 200

@app.route("/api/tasks/reset", methods=["POST"])
def reset_tasks():
    """Restore the original sample tasks."""
    global in_memory_tasks

    if supabase:
        try:
            # Clear existing tasks
            supabase.table("tasks").delete().neq("id", "0").execute()
            # Insert sample tasks with snake_case due_date
            sample_db_rows = []
            for t in SAMPLE_TASKS:
                sample_db_rows.append({
                    "id": t["id"],
                    "name": t["name"],
                    "project": t["project"],
                    "due_date": t["dueDate"],
                    "priority": t["priority"],
                    "status": t["status"]
                })
            supabase.table("tasks").insert(sample_db_rows).execute()
            res = supabase.table("tasks").select("*").order("created_at", desc=False).execute()
            tasks_list = [format_db_task_to_frontend(r) for r in res.data]
            return jsonify({
                "message": "Sample tasks restored successfully",
                "tasks": tasks_list,
                "count": len(tasks_list)
            }), 200
        except Exception as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    in_memory_tasks = copy.deepcopy(SAMPLE_TASKS)
    return jsonify({
        "message": "Sample tasks restored successfully",
        "tasks": in_memory_tasks,
        "count": len(in_memory_tasks)
    }), 200

@app.route("/api/tasks", methods=["DELETE"])
def clear_all_tasks():
    """Clear all tasks."""
    global in_memory_tasks

    if supabase:
        try:
            supabase.table("tasks").delete().neq("id", "0").execute()
            return jsonify({
                "message": "All tasks cleared successfully",
                "tasks": []
            }), 200
        except Exception as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    in_memory_tasks.clear()
    return jsonify({
        "message": "All tasks cleared successfully",
        "tasks": []
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
