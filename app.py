from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Pet, Vet, Appointment, MedicalRecord
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-this-secret-key'
db.init_app(app)


# ---------- Helpers ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access only.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper


# ---------- Public Routes ----------
@app.route('/')
def index():
    pets = Pet.query.count()
    appts = Appointment.query.count()
    vets = Vet.query.count()
    upcoming = Appointment.query.filter_by(status='Pending').limit(5).all()
    return render_template('index.html', pet_count=pets, appt_count=appts,
                           vet_count=vets, upcoming=upcoming)


# ---------- Auth ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))
        user = User(username=username,
                    password=generate_password_hash(password),
                    role='owner')
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('login.html', mode='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html', mode='login')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('index'))


# ---------- Pets ----------
@app.route('/pets')
def pets():
    all_pets = Pet.query.order_by(Pet.id.desc()).all()
    return render_template('pets.html', pets=all_pets)


@app.route('/add_pet', methods=['POST'])
@login_required
def add_pet():
    pet = Pet(
        name=request.form['name'],
        species=request.form['species'],
        breed=request.form.get('breed', ''),
        age=request.form.get('age') or None,
        owner=request.form['owner'],
        owner_id=session.get('user_id'),
        notes=request.form.get('notes', '')
    )
    db.session.add(pet)
    db.session.commit()
    flash(f'{pet.name} added successfully!', 'success')
    return redirect(url_for('pets'))


@app.route('/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if request.method == 'POST':
        pet.name = request.form['name']
        pet.species = request.form['species']
        pet.breed = request.form.get('breed', '')
        pet.age = request.form.get('age') or None
        pet.owner = request.form['owner']
        pet.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Pet updated.', 'success')
        return redirect(url_for('pets'))
    return render_template('pets.html', pets=Pet.query.all(), edit_pet=pet)


@app.route('/delete_pet/<int:pet_id>')
@login_required
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    db.session.delete(pet)
    db.session.commit()
    flash(f'{pet.name} removed.', 'info')
    return redirect(url_for('pets'))


# ---------- Vets ----------
@app.route('/vets')
def vets():
    all_vets = Vet.query.all()
    return render_template('vets.html', vets=all_vets)


@app.route('/add_vet', methods=['POST'])
@login_required
@admin_required
def add_vet():
    vet = Vet(
        name=request.form['name'],
        specialty=request.form['specialty'],
        phone=request.form.get('phone', ''),
        available=True
    )
    db.session.add(vet)
    db.session.commit()
    flash(f'Vet {vet.name} added.', 'success')
    return redirect(url_for('vets'))


@app.route('/toggle_vet/<int:vet_id>')
@login_required
@admin_required
def toggle_vet(vet_id):
    vet = Vet.query.get_or_404(vet_id)
    vet.available = not vet.available
    db.session.commit()
    return redirect(url_for('vets'))


# ---------- Appointments ----------
@app.route('/appointments')
def appointments():
    appts = Appointment.query.order_by(Appointment.id.desc()).all()
    vets_list = Vet.query.filter_by(available=True).all()
    pets_list = Pet.query.all()
    return render_template('appointments.html', appts=appts,
                           vets=vets_list, pets=pets_list)


@app.route('/book', methods=['POST'])
@login_required
def book():
    appt = Appointment(
        pet_id=request.form['pet_id'],
        vet_id=request.form.get('vet_id') or None,
        date=request.form['date'],
        time=request.form['time'],
        reason=request.form['reason'],
        status='Pending'
    )
    db.session.add(appt)
    db.session.commit()
    flash('Appointment booked!', 'success')
    return redirect(url_for('appointments'))


@app.route('/appointment/<int:appt_id>/<status>')
@login_required
def update_appointment(appt_id, status):
    if status not in ['Pending', 'Confirmed', 'Done', 'Cancelled']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('appointments'))
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = status
    db.session.commit()
    flash('Appointment updated.', 'success')
    return redirect(url_for('appointments'))


@app.route('/delete_appointment/<int:appt_id>')
@login_required
def delete_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    db.session.delete(appt)
    db.session.commit()
    flash('Appointment deleted.', 'info')
    return redirect(url_for('appointments'))


# ---------- Medical Records ----------
@app.route('/records/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def records(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if request.method == 'POST':
        rec = MedicalRecord(
            pet_id=pet_id,
            date=request.form['date'],
            diagnosis=request.form['diagnosis'],
            treatment=request.form['treatment'],
            vet_name=request.form.get('vet_name', '')
        )
        db.session.add(rec)
        db.session.commit()
        flash('Medical record added.', 'success')
        return redirect(url_for('records', pet_id=pet_id))
    return render_template('records.html', pet=pet, records=pet.records)


# ---------- Admin Dashboard ----------
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    pets_all = Pet.query.all()
    appts = Appointment.query.all()
    return render_template('admin.html', users=users, pets=pets_all, appts=appts)


# ---------- Boot ----------
with app.app_context():
    db.create_all()
    # Seed data
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin',
                            password=generate_password_hash('admin123'),
                            role='admin'))
    if Vet.query.count() == 0:
        db.session.add_all([
            Vet(name='Dr. Sarah Smith', specialty='General Practice', phone='077-1234567'),
            Vet(name='Dr. Tom Perera', specialty='Surgery', phone='077-7654321'),
            Vet(name='Dr. Mia Chen', specialty='Dentistry', phone='077-1112222'),
        ])
    db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)