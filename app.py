import os
import json
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, session, flash, send_file
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Form, Field, Submission
from openpyxl import Workbook
from io import BytesIO

load_dotenv()

app = Flask(__name__)

# ================= CONFIG =================

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "supersecretkey")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ================= DATABASE INIT =================

def init_db():
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

init_db()

# ================= LOGIN PROTECTION =================

def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))

            if role and session.get("role") != role:
                flash("Access denied")
                return redirect(url_for("login"))

            return func(*args, **kwargs)

        return wrapper
    return decorator

# ================= AUTH =================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("staff_dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= ADMIN =================

@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    forms = Form.query.all()
    users = User.query.all()
    submissions = Submission.query.all()
    return render_template("admin/dashboard.html",
                           forms=forms,
                           users=users,
                           submissions=submissions)


@app.route("/admin/create_form", methods=["GET", "POST"])
@login_required(role="admin")
def create_form():

    if request.method == "POST":

        form_name = request.form.get("form_name")

        new_form = Form(name=form_name)
        db.session.add(new_form)
        db.session.commit()

        for key in request.form:
            if key.startswith("label_"):
                index = key.split("_")[1]

                label = request.form.get(f"label_{index}")
                field_type = request.form.get(f"type_{index}")
                options = request.form.get(f"options_{index}")

                new_field = Field(
                    form_id=new_form.id,
                    label=label,
                    field_type=field_type,
                    options=options
                )

                db.session.add(new_field)

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/create_form.html")


@app.route("/admin/edit_form/<int:form_id>", methods=["GET", "POST"])
@login_required(role="admin")
def edit_form(form_id):

    form = Form.query.get_or_404(form_id)
    fields = Field.query.filter_by(form_id=form_id).all()

    if request.method == "POST":

        form.name = request.form.get("form_name")

        submitted_ids = request.form.getlist("field_id")

        for field in fields:
            if str(field.id) not in submitted_ids:
                db.session.delete(field)

        for field_id in submitted_ids:
            field = Field.query.get(int(field_id))
            field.label = request.form.get(f"label_{field_id}")
            field.field_type = request.form.get(f"type_{field_id}")
            field.options = request.form.get(f"options_{field_id}")
            field.required = True if request.form.get(f"required_{field_id}") else False

        for key in request.form:
            if key.startswith("new_label_"):
                index = key.split("_")[2]

                new_field = Field(
                    form_id=form.id,
                    label=request.form.get(f"new_label_{index}"),
                    field_type=request.form.get(f"new_type_{index}"),
                    options=request.form.get(f"new_options_{index}"),
                    required=True if request.form.get(f"new_required_{index}") else False
                )
                db.session.add(new_field)

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/edit_form.html",
                           form=form,
                           fields=fields)


@app.route("/admin/view_submissions/<int:form_id>")
@login_required(role="admin")
def view_submissions(form_id):

    form = Form.query.get_or_404(form_id)
    fields = Field.query.filter_by(form_id=form_id).all()
    submissions = Submission.query.filter_by(form_id=form_id).all()

    parsed_submissions = []

    for submission in submissions:
        parsed_submissions.append(json.loads(submission.data))

    return render_template("admin/view_submissions.html",
                           form=form,
                           fields=fields,
                           submissions=parsed_submissions)


@app.route("/admin/export_excel/<int:form_id>")
@login_required(role="admin")
def export_excel(form_id):

    form = Form.query.get_or_404(form_id)
    submissions = Submission.query.filter_by(form_id=form_id).all()
    fields = Field.query.filter_by(form_id=form_id).all()

    wb = Workbook()
    ws = wb.active
    ws.title = form.name

    headers = [field.label for field in fields]
    ws.append(headers)

    for submission in submissions:
        data = json.loads(submission.data)
        row = [data.get(field.label, "") for field in fields]
        ws.append(row)

    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return send_file(file_stream,
                     download_name=f"{form.name}.xlsx",
                     as_attachment=True)

# ================= STAFF =================

@app.route("/staff/dashboard")
@login_required(role="staff")
def staff_dashboard():
    forms = Form.query.all()
    return render_template("staff/dashboard.html", forms=forms)


@app.route("/staff/my_submissions")
@login_required(role="staff")
def my_submissions():

    submissions = Submission.query.filter_by(
        user_id=session["user_id"]
    ).all()

    parsed = [json.loads(sub.data) for sub in submissions]

    return render_template("staff/my_submissions.html",
                           submissions=parsed)

# ================= FILL FORM =================

@app.route("/fill/<int:form_id>", methods=["GET", "POST"])
@login_required()
def fill_form(form_id):

    form = Form.query.get_or_404(form_id)
    fields = Field.query.filter_by(form_id=form_id).all()

    if request.method == "POST":

        data = {}

        for field in fields:
            if field.field_type == "checkbox":
                data[field.label] = request.form.getlist(field.label)
            else:
                data[field.label] = request.form.get(field.label)

        new_submission = Submission(
            form_id=form.id,
            user_id=session["user_id"],
            data=json.dumps(data)
        )

        db.session.add(new_submission)
        db.session.commit()

        return redirect(url_for("staff_dashboard"))

    return render_template("staff/fill_form.html",
                           form=form,
                           fields=fields)

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)