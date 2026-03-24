from datetime import datetime
from functools import wraps
from uuid import uuid4
import jwt
from flask import Blueprint, request, redirect, session, url_for, render_template
from app import app
from db import task_storage, users
# https://flask.palletsprojects.com/en/2.3.x/tutorial/views/

bp = Blueprint("tasks", __name__, template_folder="tasks")


def get_user_tasks(username):
    return {
        task_id: task_info for task_id, task_info in task_storage.items()
        if task_info["username"] == username
    }


def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = session.get("token")
        if not token:
            return redirect(url_for("auth.login"))
        try:
            payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            username = payload["username"]
            if username not in users:
                return redirect(url_for("auth.login"))
            session["username"] = username
        except jwt.exceptions.DecodeError:
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper


@bp.get("/")
@auth_required
def list_tasks():
    completed_flag = request.args.get("completed")  # fetch the query parameter
    if completed_flag and completed_flag.lower() not in ("true", "false"):
        completed_flag = None
    flag_mapping = {"true": True, "false": False}
    # return all user tasks if query parameter was not provided
    tasks = get_user_tasks(session["username"])
    if completed_flag:
        # filter only not completed tasks
        tasks = {
            task_id: task_info for task_id, task_info in tasks.items()
            if task_info["is_completed"] == flag_mapping[completed_flag.lower()]
        }
    return render_template("dashboard.html", tasks=tasks)


@bp.get("/new_task")
@auth_required
def get_create_task_page():
    return render_template("new_task.html")


@bp.post("/new_task")
@auth_required
def create_task():
    task_id = uuid4().hex  # generate task ID
    task_info = {
        # get `title` from the form
        "title": request.form.get("title", "Missed title"),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # get current time
        "is_completed": False,  # by default a new task is not completed
        "username": session["username"],  # save who requested to create task
    }
    task_storage[task_id] = task_info  # save the task in the storage
    return redirect(url_for("tasks.list_tasks"))


@bp.post("/edit_task/<task_id>")
@auth_required
def edit_task(task_id):
    task_info = task_storage.get(task_id)
    if not task_info or task_info["username"] != session["username"]:
        return redirect(url_for("tasks.list_tasks"))
    task_info["title"] = request.form.get("title", task_info["title"])
    task_info["is_completed"] = request.form.get("is_completed") == "on"
    return redirect(url_for("tasks.list_tasks"))


@bp.post("/delete_task/<task_id>")
@auth_required
def delete_task(task_id):
    task_info = task_storage.get(task_id)
    if task_info and task_info["username"] == session["username"]:
        del task_storage[task_id]
    return redirect(url_for("tasks.list_tasks"))
