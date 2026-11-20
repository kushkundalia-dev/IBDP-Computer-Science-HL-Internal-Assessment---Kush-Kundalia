from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Role, RoomCategory, Room, Guest, GuestNote, Reservation, Schedule
from forms import LoginForm, RegisterForm
from guest_forms import GuestForm, GuestNoteForm
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_database():
    """Initialize database with roles and sample data"""
    with app.app_context():
        db.create_all()
        
        # Create roles if they don't exist
        if Role.query.count() == 0:
            roles = [
                Role(id=1, name='HR Manager', description='Full access to personnel management'),
                Role(id=2, name='General Manager', description='Oversee operations and approve requests'),
                Role(id=3, name='Front Desk Agent', description='Manage reservations and guest services')
            ]
            db.session.add_all(roles)
            db.session.commit()
            print("✓ Roles created")
        
        # Create default admin user if no users exist
        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@hotelkk.com',
                first_name='Admin',
                last_name='User',
                phone='095120 20653',
                role_id=1,  # HR Manager
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin user created (username: admin, password: admin123)")
        
        # Create room categories if they don't exist
        if RoomCategory.query.count() == 0:
            categories = [
                RoomCategory(name='Standard Queen', description='Comfortable queen bed room', 
                           size_sqm=23, max_adults=2, max_children=0, base_price=2207),
                RoomCategory(name='Standard Twin', description='Twin beds room', 
                           size_sqm=23, max_adults=2, max_children=1, base_price=2538),
                RoomCategory(name='Superior Queen', description='Spacious queen room', 
                           size_sqm=28, max_adults=2, max_children=1, base_price=2631),
                RoomCategory(name='Suite', description='Luxury suite with closet', 
                           size_sqm=42, max_adults=2, max_children=1, base_price=3559)
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("✓ Room categories created")
        
        # Create sample rooms if they don't exist
        if Room.query.count() == 0:
            rooms = []
            # Floor 1 - Standard Queen (rooms 101-105)
            for i in range(1, 6):
                rooms.append(Room(room_number=f'10{i}', floor=1, category_id=1))
            # Floor 1 - Standard Twin (rooms 106-110)
            for i in range(6, 11):
                rooms.append(Room(room_number=f'10{i}', floor=1, category_id=2))
            # Floor 2 - Superior Queen (rooms 201-206)
            for i in range(1, 7):
                rooms.append(Room(room_number=f'20{i}', floor=2, category_id=3))
            # Floor 2 - Suites (rooms 207-210)
            for i in range(7, 11):
                rooms.append(Room(room_number=f'20{i}', floor=2, category_id=4))
            
            db.session.add_all(rooms)
            db.session.commit()
            print(f"✓ {len(rooms)} sample rooms created")

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact HR.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            # Redirect to appropriate dashboard based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Generate username from email (use email prefix)
        username = form.email.data.split('@')[0]
        
        # Check if username exists, add number if needed
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User(
            username=username,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role_id=int(form.role.data),
            is_active=True
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - redirects based on role"""
    if current_user.has_role('HR Manager'):
        return redirect(url_for('hr_dashboard'))
    elif current_user.has_role('General Manager'):
        return redirect(url_for('manager_dashboard'))
    else:
        return redirect(url_for('frontdesk_dashboard'))

@app.route('/dashboard/hr')
@login_required
def hr_dashboard():
    """HR Manager Dashboard"""
    if not current_user.has_role('HR Manager'):
        flash('Access denied. HR Manager role required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all staff members
    all_staff = User.query.order_by(User.first_name).all()
    
    # Get all roles
    roles = Role.query.all()
    
    return render_template('hr_dashboard.html', all_staff=all_staff, roles=roles)

@app.route('/add-staff', methods=['POST'])
@login_required
def add_staff():
    """Add new staff member"""
    if not current_user.has_role('HR Manager'):
        flash('Access denied. HR Manager role required.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Auto-generate username from email
        username = request.form['email'].split('@')[0]
        
        # Ensure unique username
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create new user
        new_user = User(
            username=username,
            email=request.form['email'],
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            phone=request.form['phone'],
            role_id=request.form['role_id'],
            is_active=True
        )
        new_user.set_password(request.form['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Staff member {new_user.first_name} {new_user.last_name} added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding staff: {str(e)}', 'danger')
    
    return redirect(url_for('hr_dashboard'))

@app.route('/edit-staff/<int:user_id>', methods=['POST'])
@login_required
def edit_staff(user_id):
    """Edit staff member"""
    if not current_user.has_role('HR Manager'):
        flash('Access denied. HR Manager role required.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        user.role_id = request.form['role_id']
        user.is_active = bool(int(request.form['is_active']))
        
        db.session.commit()
        flash(f'Staff member {user.first_name} {user.last_name} updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating staff: {str(e)}', 'danger')
    
    return redirect(url_for('hr_dashboard'))

@app.route('/delete-staff/<int:user_id>', methods=['POST'])
@login_required
def delete_staff(user_id):
    """Delete staff member"""
    if not current_user.has_role('HR Manager'):
        flash('Access denied. HR Manager role required.', 'danger')
        return redirect(url_for('dashboard'))
    
    if user_id == current_user.id:
        flash('Cannot delete your own account!', 'danger')
        return redirect(url_for('hr_dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        name = f"{user.first_name} {user.last_name}"
        db.session.delete(user)
        db.session.commit()
        flash(f'Staff member {name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting staff: {str(e)}', 'danger')
    
    return redirect(url_for('hr_dashboard'))

@app.route('/dashboard/manager')
@login_required
def manager_dashboard():
    """General Manager Dashboard"""
    if not (current_user.has_role('General Manager') or current_user.has_role('Front Desk Agent')):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    from datetime import date
    
    # Get all front desk staff
    front_desk_role = Role.query.filter_by(name='Front Desk Agent').first()
    front_desk_staff = User.query.filter_by(role_id=front_desk_role.id, is_active=True).all() if front_desk_role else []
    
    # Get upcoming schedules (next 7 days)
    from datetime import timedelta
    today = date.today()
    next_week = today + timedelta(days=7)
    upcoming_schedules = Schedule.query.filter(
        Schedule.shift_date >= today,
        Schedule.shift_date <= next_week
    ).order_by(Schedule.shift_date, Schedule.shift_start).all()
    
    return render_template('manager_dashboard.html',
                         front_desk_staff=front_desk_staff,
                         upcoming_schedules=upcoming_schedules)

@app.route('/toggle-duty/<int:user_id>', methods=['POST'])
@login_required
def toggle_duty(user_id):
    """Toggle staff duty status"""
    if not current_user.has_role('General Manager'):
        flash('Access denied. Only managers can change duty status.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.is_on_duty = not user.is_on_duty
    db.session.commit()
    
    return redirect(url_for('manager_dashboard'))

@app.route('/assign-schedule', methods=['POST'])
@login_required
def assign_schedule():
    """Assign a shift schedule to staff"""
    if not current_user.has_role('General Manager'):
        flash('Access denied. Only managers can assign schedules.', 'danger')
        return redirect(url_for('dashboard'))
    
    from datetime import datetime
    
    user_id = request.form.get('user_id')
    shift_date = request.form.get('shift_date')
    shift_start = request.form.get('shift_start')
    shift_end = request.form.get('shift_end')
    
    # Validate
    if not all([user_id, shift_date, shift_start, shift_end]):
        return redirect(url_for('manager_dashboard'))
    
    # Create schedule
    schedule = Schedule(
        user_id=int(user_id),
        shift_date=datetime.strptime(shift_date, '%Y-%m-%d').date(),
        shift_start=datetime.strptime(shift_start, '%H:%M').time(),
        shift_end=datetime.strptime(shift_end, '%H:%M').time(),
        assigned_by=current_user.id
    )
    db.session.add(schedule)
    db.session.commit()
    
    return redirect(url_for('manager_dashboard'))

@app.route('/delete-schedule/<int:schedule_id>', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    """Delete a schedule"""
    if not current_user.has_role('General Manager'):
        flash('Access denied. Only managers can delete schedules.', 'danger')
        return redirect(url_for('dashboard'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    
    return redirect(url_for('manager_dashboard'))

@app.route('/reports')
@login_required
def reports():
    """Reports Dashboard - Accessible by managers and front desk"""
    if not (current_user.has_role('General Manager') or current_user.has_role('Front Desk Agent')):
        flash('Access denied. Manager or Front Desk role required.', 'danger')
        return redirect(url_for('dashboard'))
    
    from datetime import date, timedelta
    from sqlalchemy import func
    
    today = date.today()
    report_date = request.args.get('date', today.isoformat())
    report_type = request.args.get('type', 'occupancy')
    
    try:
        selected_date = datetime.strptime(report_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today
    
    # Initialize report data
    occupancy_data = {}
    revenue_data = {}
    arrivals = []
    departures = []
    
    # === OCCUPANCY REPORT ===
    if report_type == 'occupancy':
        total_rooms = Room.query.count()
        
        # Get occupied rooms for selected date
        occupied_reservations = Reservation.query.filter(
            Reservation.check_in_date <= selected_date,
            Reservation.check_out_date > selected_date,
            Reservation.status.in_(['confirmed', 'checked_in'])
        ).all()
        
        occupied_rooms = len(occupied_reservations)
        occupancy_percentage = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
        
        # Breakdown by room category
        category_breakdown = db.session.query(
            RoomCategory.name,
            RoomCategory.base_price,
            func.count(Room.id).label('total_rooms'),
            func.sum(
                db.case(
                    (Reservation.id.isnot(None), 1),
                    else_=0
                )
            ).label('occupied')
        ).outerjoin(Room, Room.category_id == RoomCategory.id)\
        .outerjoin(
            Reservation,
            db.and_(
                Reservation.room_id == Room.id,
                Reservation.check_in_date <= selected_date,
                Reservation.check_out_date > selected_date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            )
        ).group_by(RoomCategory.id).all()
        
        occupancy_data = {
            'date': selected_date,
            'total_rooms': total_rooms,
            'occupied_rooms': occupied_rooms,
            'available_rooms': total_rooms - occupied_rooms,
            'occupancy_percentage': round(occupancy_percentage, 2),
            'category_breakdown': category_breakdown
        }
    
    # === REVENUE REPORT ===
    elif report_type == 'revenue':
        # Date range for revenue report
        start_date_str = request.args.get('start_date', (today - timedelta(days=30)).isoformat())
        end_date_str = request.args.get('end_date', today.isoformat())
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=30)
            end_date = today
        
        # Total revenue from checked-in and checked-out reservations
        total_revenue = db.session.query(
            func.sum(Reservation.total_amount)
        ).filter(
            Reservation.status.in_(['checked_in', 'checked_out']),
            Reservation.check_in_date >= start_date,
            Reservation.check_in_date <= end_date
        ).scalar() or 0
        
        # Revenue by room category
        category_revenue = db.session.query(
            RoomCategory.name,
            func.count(Reservation.id).label('bookings'),
            func.sum(Reservation.total_amount).label('revenue')
        ).join(Room, Room.category_id == RoomCategory.id)\
        .join(Reservation, Reservation.room_id == Room.id)\
        .filter(
            Reservation.status.in_(['checked_in', 'checked_out']),
            Reservation.check_in_date >= start_date,
            Reservation.check_in_date <= end_date
        ).group_by(RoomCategory.id).all()
        
        # Calculate metrics
        total_bookings = db.session.query(func.count(Reservation.id)).filter(
            Reservation.status.in_(['checked_in', 'checked_out']),
            Reservation.check_in_date >= start_date,
            Reservation.check_in_date <= end_date
        ).scalar() or 0
        
        adr = (total_revenue / total_bookings) if total_bookings > 0 else 0  # Average Daily Rate
        
        # RevPAR (Revenue Per Available Room)
        total_rooms = Room.query.count()
        days_in_period = (end_date - start_date).days + 1
        available_room_nights = total_rooms * days_in_period
        revpar = (total_revenue / available_room_nights) if available_room_nights > 0 else 0
        
        revenue_data = {
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': total_revenue,
            'total_bookings': total_bookings,
            'adr': round(adr, 2),
            'revpar': round(revpar, 2),
            'category_revenue': category_revenue
        }
    
    # === ARRIVALS/DEPARTURES REPORT ===
    elif report_type == 'arrivals':
        arrivals = Reservation.query.filter(
            Reservation.check_in_date == selected_date,
            Reservation.status.in_(['confirmed', 'checked_in'])
        ).join(Guest).join(Room).all()
        
        departures = Reservation.query.filter(
            Reservation.check_out_date == selected_date,
            Reservation.status.in_(['confirmed', 'checked_in'])
        ).join(Guest).join(Room).all()
    
    return render_template('reports.html',
                         report_type=report_type,
                         selected_date=selected_date,
                         occupancy_data=occupancy_data,
                         revenue_data=revenue_data,
                         arrivals=arrivals,
                         departures=departures)

@app.route('/dashboard/frontdesk')
@login_required
def frontdesk_dashboard():
    """Front Desk Agent Dashboard"""
    if not current_user.has_role('Front Desk Agent'):
        flash('Access denied. Front Desk Agent role required.', 'danger')
        return redirect(url_for('dashboard'))
    
    from datetime import date
    today = date.today()
    
    # Get statistics
    total_guests = Guest.query.count()
    total_rooms = Room.query.count()
    
    # Today's arrivals and departures
    todays_arrivals = Reservation.query.filter(
        Reservation.check_in_date == today,
        Reservation.status == 'confirmed'
    ).count()
    
    todays_departures = Reservation.query.filter(
        Reservation.check_out_date == today,
        Reservation.status == 'checked_in'
    ).count()
    
    # Current occupancy
    occupied_rooms = Reservation.query.filter(
        Reservation.status == 'checked_in'
    ).count()
    
    # Recent guests (last 10)
    recent_guests = Guest.query.order_by(Guest.created_at.desc()).limit(5).all()
    
    return render_template('frontdesk_dashboard.html',
                         total_guests=total_guests,
                         total_rooms=total_rooms,
                         todays_arrivals=todays_arrivals,
                         todays_departures=todays_departures,
                         occupied_rooms=occupied_rooms,
                         recent_guests=recent_guests)

# Guest Management Routes
@app.route('/guests')
@login_required
def guests_list():
    """List all guests"""
    search = request.args.get('search', '')
    
    if search:
        guests = Guest.query.filter(
            db.or_(
                Guest.first_name.ilike(f'%{search}%'),
                Guest.last_name.ilike(f'%{search}%'),
                Guest.email.ilike(f'%{search}%'),
                Guest.phone.ilike(f'%{search}%')
            )
        ).order_by(Guest.last_visit.desc().nullslast(), Guest.created_at.desc()).all()
    else:
        guests = Guest.query.order_by(Guest.last_visit.desc().nullslast(), Guest.created_at.desc()).all()
    
    total_guests = Guest.query.count()
    
    return render_template('guests/list.html', guests=guests, total_guests=total_guests, search=search)

@app.route('/guests/add', methods=['GET', 'POST'])
@login_required
def add_guest():
    """Add new guest"""
    if not current_user.can_edit():
        flash('You cannot add guests while off duty.', 'warning')
        return redirect(url_for('guests_list'))
    
    form = GuestForm()
    if form.validate_on_submit():
        guest = Guest(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            id_proof_type=form.id_proof_type.data,
            id_proof_number=form.id_proof_number.data,
            address=form.address.data
        )
        db.session.add(guest)
        db.session.commit()
        
        flash(f'Guest {guest.first_name} {guest.last_name} added successfully!', 'success')
        return redirect(url_for('guest_profile', guest_id=guest.id))
    
    return render_template('guests/add.html', form=form)

@app.route('/guests/<int:guest_id>')
@login_required
def guest_profile(guest_id):
    """View guest profile"""
    guest = Guest.query.get_or_404(guest_id)
    notes = GuestNote.query.filter_by(guest_id=guest_id).order_by(GuestNote.created_at.desc()).all()
    
    return render_template('guests/profile.html', guest=guest, notes=notes)

@app.route('/guests/<int:guest_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_guest(guest_id):
    """Edit guest information"""
    if not current_user.can_edit():
        flash('You cannot edit guests while off duty.', 'warning')
        return redirect(url_for('guest_profile', guest_id=guest_id))
    
    guest = Guest.query.get_or_404(guest_id)
    form = GuestForm(obj=guest)
    
    if form.validate_on_submit():
        guest.first_name = form.first_name.data
        guest.last_name = form.last_name.data
        guest.email = form.email.data
        guest.phone = form.phone.data
        guest.id_proof_type = form.id_proof_type.data
        guest.id_proof_number = form.id_proof_number.data
        guest.address = form.address.data
        
        db.session.commit()
        flash('Guest information updated successfully!', 'success')
        return redirect(url_for('guest_profile', guest_id=guest_id))
    
    return render_template('guests/edit.html', form=form, guest=guest)

@app.route('/guests/<int:guest_id>/add-note', methods=['GET', 'POST'])
@login_required
def add_guest_note(guest_id):
    """Add note to guest profile (requires manager approval)"""
    if not current_user.can_edit():
        flash('You cannot add notes while off duty.', 'warning')
        return redirect(url_for('guest_profile', guest_id=guest_id))
    
    guest = Guest.query.get_or_404(guest_id)
    form = GuestNoteForm()
    
    if form.validate_on_submit():
        note = GuestNote(
            guest_id=guest_id,
            note_text=form.note_text.data,
            created_by=current_user.id,
            is_approved=current_user.has_role('General Manager')  # Auto-approve for managers
        )
        
        if note.is_approved:
            note.approved_by = current_user.id
            note.approval_date = datetime.utcnow()
        
        db.session.add(note)
        db.session.commit()
        
        if note.is_approved:
            flash('Note added successfully!', 'success')
        else:
            flash('Note submitted for manager approval.', 'info')
        
        return redirect(url_for('guest_profile', guest_id=guest_id))
    
    return render_template('guests/add_note.html', form=form, guest=guest)

# Check-in Route
@app.route('/reservations/<int:reservation_id>/checkin', methods=['POST'])
@login_required
def check_in(reservation_id):
    """Process guest check-in"""
    # Check if front desk agent is on duty
    if current_user.has_role('Front Desk Agent') and not current_user.is_on_duty:
        flash('You must be on duty to perform check-in.', 'danger')
        return redirect(url_for('reservations_list'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.status != 'confirmed':
        flash('This reservation cannot be checked in. Current status: ' + reservation.status, 'error')
        return redirect(url_for('reservations_list'))
    
    from datetime import datetime
    reservation.status = 'checked_in'
    reservation.actual_check_in = datetime.now()
    db.session.commit()
    
    flash(f'Successfully checked in {reservation.guest.first_name} {reservation.guest.last_name} to Room {reservation.room.room_number}', 'success')
    return redirect(url_for('reservations_list'))

# Check-out Route
@app.route('/reservations/<int:reservation_id>/checkout', methods=['POST'])
@login_required
def check_out(reservation_id):
    """Process guest check-out"""
    # Check if front desk agent is on duty
    if current_user.has_role('Front Desk Agent') and not current_user.is_on_duty:
        flash('You must be on duty to perform check-out.', 'danger')
        return redirect(url_for('reservations_list'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.status != 'checked_in':
        flash('This reservation cannot be checked out. Current status: ' + reservation.status, 'error')
        return redirect(url_for('reservations_list'))
    
    from datetime import datetime
    reservation.status = 'checked_out'
    reservation.actual_check_out = datetime.now()
    
    # Update guest stats
    guest = reservation.guest
    guest.total_stays += 1
    guest.total_spent += reservation.total_amount
    guest.last_visit = reservation.check_out_date
    
    db.session.commit()
    
    flash(f'Successfully checked out {reservation.guest.first_name} {reservation.guest.last_name} from Room {reservation.room.room_number}', 'success')
    return redirect(url_for('reservations_list'))

# Modify Reservation Route
@app.route('/reservations/<int:reservation_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_reservation(reservation_id):
    """Edit reservation details"""
    # Check if front desk agent is on duty
    if current_user.has_role('Front Desk Agent') and not current_user.is_on_duty:
        flash('You must be on duty to edit reservations.', 'danger')
        return redirect(url_for('reservations_list'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.status in ['checked_out', 'cancelled']:
        flash('Cannot edit completed or cancelled reservations.', 'error')
        return redirect(url_for('reservations_list'))
    
    if request.method == 'POST':
        from datetime import datetime
        
        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')
        num_adults = int(request.form.get('num_adults', 1))
        num_children = int(request.form.get('num_children', 0))
        special_requests = request.form.get('special_requests', '')
        
        # Parse dates
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        # Check if room is available for new dates (excluding current reservation)
        conflicting = Reservation.query.filter(
            Reservation.room_id == reservation.room_id,
            Reservation.id != reservation.id,
            Reservation.status.in_(['confirmed', 'checked_in']),
            db.or_(
                db.and_(Reservation.check_in_date <= check_in, Reservation.check_out_date > check_in),
                db.and_(Reservation.check_in_date < check_out, Reservation.check_out_date >= check_out),
                db.and_(Reservation.check_in_date >= check_in, Reservation.check_out_date <= check_out)
            )
        ).first()
        
        if conflicting:
            flash('Room is not available for the selected dates.', 'error')
            return render_template('edit_reservation.html', reservation=reservation)
        
        # Update reservation
        reservation.check_in_date = check_in
        reservation.check_out_date = check_out
        reservation.num_adults = num_adults
        reservation.num_children = num_children
        reservation.special_requests = special_requests
        
        # Recalculate total
        num_nights = (check_out - check_in).days
        reservation.total_amount = reservation.room.category.base_price * num_nights
        
        db.session.commit()
        
        flash('Reservation updated successfully!', 'success')
        return redirect(url_for('reservations_list'))
    
    return render_template('edit_reservation.html', reservation=reservation)

# Cancel Reservation Route
@app.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    """Cancel a reservation"""
    # Check if front desk agent is on duty
    if current_user.has_role('Front Desk Agent') and not current_user.is_on_duty:
        flash('You must be on duty to cancel reservations.', 'danger')
        return redirect(url_for('reservations_list'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.status == 'checked_out':
        flash('Cannot cancel a completed reservation.', 'error')
        return redirect(url_for('reservations_list'))
    
    if reservation.status == 'cancelled':
        flash('Reservation is already cancelled.', 'warning')
        return redirect(url_for('reservations_list'))
    
    reservation.status = 'cancelled'
    db.session.commit()
    
    flash(f'Reservation {reservation.reservation_code} has been cancelled.', 'success')
    return redirect(url_for('reservations_list'))

# Reservations Route
@app.route('/reservations')
@login_required
def reservations_list():
    """View all reservations"""
    from datetime import date
    today = date.today()
    
    # Get filter parameter
    filter_type = request.args.get('filter', 'active')
    
    if filter_type == 'active':
        # Current and upcoming reservations
        reservations = Reservation.query.filter(
            Reservation.status.in_(['confirmed', 'checked_in']),
            Reservation.check_out_date >= today
        ).order_by(Reservation.check_in_date).all()
    elif filter_type == 'today':
        # Today's check-ins and check-outs
        reservations = Reservation.query.filter(
            db.or_(
                Reservation.check_in_date == today,
                Reservation.check_out_date == today
            )
        ).order_by(Reservation.check_in_date).all()
    elif filter_type == 'arrivals':
        # Today's arrivals
        reservations = Reservation.query.filter(
            Reservation.check_in_date == today,
            Reservation.status == 'confirmed'
        ).order_by(Reservation.check_in_date).all()
    elif filter_type == 'departures':
        # Today's departures
        reservations = Reservation.query.filter(
            Reservation.check_out_date == today,
            Reservation.status == 'checked_in'
        ).order_by(Reservation.check_out_date).all()
    else:
        # All reservations
        reservations = Reservation.query.order_by(Reservation.check_in_date.desc()).all()
    
    return render_template('reservations.html', reservations=reservations, filter_type=filter_type, today=today)

# Room Status Route
@app.route('/rooms')
@login_required
def rooms_status():
    """View all rooms and their status"""
    from datetime import date
    today = date.today()
    
    # Get all rooms with their categories
    rooms = Room.query.order_by(Room.room_number).all()
    
    # Build room status information
    room_status_list = []
    for room in rooms:
        # Check if room is currently occupied
        current_reservation = Reservation.query.filter(
            Reservation.room_id == room.id,
            Reservation.status == 'checked_in',
            Reservation.check_in_date <= today,
            Reservation.check_out_date > today
        ).first()
        
        # Check for upcoming reservation today
        upcoming_today = Reservation.query.filter(
            Reservation.room_id == room.id,
            Reservation.check_in_date == today,
            Reservation.status == 'confirmed'
        ).first()
        
        # Check for departure today
        departing_today = Reservation.query.filter(
            Reservation.room_id == room.id,
            Reservation.check_out_date == today,
            Reservation.status == 'checked_in'
        ).first()
        
        status = 'available'
        guest_name = None
        reservation = None
        
        if current_reservation:
            status = 'occupied'
            guest_name = f"{current_reservation.guest.first_name} {current_reservation.guest.last_name}"
            reservation = current_reservation
        elif departing_today:
            status = 'departing'
            guest_name = f"{departing_today.guest.first_name} {departing_today.guest.last_name}"
            reservation = departing_today
        elif upcoming_today:
            status = 'arriving'
            guest_name = f"{upcoming_today.guest.first_name} {upcoming_today.guest.last_name}"
            reservation = upcoming_today
        
        room_status_list.append({
            'room': room,
            'status': status,
            'guest_name': guest_name,
            'reservation': reservation
        })
    
    # Get statistics
    total_rooms = len(rooms)
    occupied = sum(1 for r in room_status_list if r['status'] == 'occupied')
    available = sum(1 for r in room_status_list if r['status'] == 'available')
    arriving = sum(1 for r in room_status_list if r['status'] == 'arriving')
    departing = sum(1 for r in room_status_list if r['status'] == 'departing')
    
    return render_template('rooms.html', 
                         room_status_list=room_status_list,
                         total_rooms=total_rooms,
                         occupied=occupied,
                         available=available,
                         arriving=arriving,
                         departing=departing)

# Guest Booking Route (Public - No Login Required)
@app.route('/guest', methods=['GET', 'POST'])
def guest_booking():
    """Public booking page for guests"""
    if request.method == 'POST':
        from datetime import datetime
        
        # Get form data
        category_id = request.form.get('category_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')
        num_adults = int(request.form.get('num_adults', 1))
        num_children = int(request.form.get('num_children', 0))
        special_requests = request.form.get('special_requests', '')
        
        # Parse dates
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        # Find or create guest
        guest = Guest.query.filter_by(email=email).first() if email else None
        if not guest:
            guest = Guest(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone
            )
            db.session.add(guest)
            db.session.flush()  # Get guest.id without committing
        
        # Find available room of the selected category
        category = RoomCategory.query.get_or_404(category_id)
        available_room = None
        
        for room in category.rooms:
            # Check if room is available for the dates
            conflicting_reservations = Reservation.query.filter(
                Reservation.room_id == room.id,
                Reservation.status.in_(['confirmed', 'checked_in']),
                db.or_(
                    db.and_(Reservation.check_in_date <= check_in, Reservation.check_out_date > check_in),
                    db.and_(Reservation.check_in_date < check_out, Reservation.check_out_date >= check_out),
                    db.and_(Reservation.check_in_date >= check_in, Reservation.check_out_date <= check_out)
                )
            ).first()
            
            if not conflicting_reservations:
                available_room = room
                break
        
        if not available_room:
            flash('Sorry, no rooms of this category are available for the selected dates.', 'error')
            categories = RoomCategory.query.all()
            return render_template('guest_booking.html', categories=categories)
        
        # Calculate total price
        num_nights = (check_out - check_in).days
        total_price = category.base_price * num_nights
        
        # Generate unique reservation code
        import random
        import string
        reservation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Create reservation
        reservation = Reservation(
            reservation_code=reservation_code,
            guest_id=guest.id,
            room_id=available_room.id,
            check_in_date=check_in,
            check_out_date=check_out,
            num_adults=num_adults,
            num_children=num_children,
            room_rate=category.base_price,
            total_amount=total_price,
            special_requests=special_requests,
            status='confirmed'
        )
        db.session.add(reservation)
        db.session.commit()
        
        flash(f'Booking confirmed! Room {available_room.room_number} reserved for {num_nights} nights. Total: ₹{total_price:,.2f}', 'success')
        return redirect(url_for('index'))
    
    # Get available room categories
    categories = RoomCategory.query.all()
    return render_template('guest_booking.html', categories=categories)

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
