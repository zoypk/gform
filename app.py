from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forms.db'
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    fields = db.relationship('FormField', backref='form', lazy='dynamic')

class FormField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    field_type = db.Column(db.String(20))
    options = db.Column(db.Text)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'))

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'))
    data = db.Column(db.PickleType)

@app.route('/')
#@login_required
def index():
    forms = Form.query.all()
    return render_template('index.html', forms=forms)

@app.route('/create_form', methods=['GET', 'POST'])
# @login_required
def create_form():
    if request.method == 'POST':
        form_name = request.form.get('form_name')
        form_description = request.form.get('form_description')

        new_form = Form(name=form_name, description=form_description)
        db.session.add(new_form)
        db.session.commit()
        
        forms = Form.query.all()
        formid = forms.id
    return render_template('create_form.html', formid=formid)

@app.route('/add_field/<int:form_id>', methods=['POST'])
# @login_required
def add_field(form_id):
    form = Form.query.get(form_id)
    if not form:
        return "Form not found", 404

    field_name = request.form.get('field_name')
    field_type = request.form.get('field_type')
    field_options = request.form.get('field_options')

    new_field = FormField(name=field_name, field_type=field_type, options=field_options, form_id=form_id)
    db.session.add(new_field)
    db.session.commit()

    return redirect(url_for('create_form'))

@app.route('/view_submissions/<int:form_id>')
# @login_required
def view_submissions(form_id):
    form = Form.query.get(form_id)
    if not form:
        return "Form not found", 404

    submissions = Submission.query.filter_by(form_id=form_id).all()
    return render_template('submissions.html', form=form, submissions=submissions)

@app.route('/submit_form/<int:form_id>', methods=['POST'])
# @login_required
def submit_form(form_id):
    form = Form.query.get(form_id)
    if not form:
        return "Form not found", 404

    submitted_data = {}
    for field in form.fields:
        field_name = field.name
        field_type = field.field_type
        if field_type in ['string', 'int', 'date']:
            submitted_data[field_name] = request.form.get(field_name)
        elif field_type in ['radio', 'checkbox']:
            submitted_data[field_name] = request.form.getlist(field_name)

    new_submission = Submission(form_id=form.id, data=submitted_data)
    db.session.add(new_submission)
    db.session.commit()

    return "Form submitted successfully"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
# @login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)