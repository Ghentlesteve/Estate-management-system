from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Resident, DuesCategory, Payment, Complaint, Announcement, AuditLog
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estate_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create admin user and default data
def create_default_data():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('Admin@2026'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
        
        # Create default dues categories
        categories = [
            {'name': 'Monthly Levy', 'amount': 5000, 'frequency': 'monthly'},
            {'name': 'Security Levy', 'amount': 2000, 'frequency': 'monthly'},
            {'name': 'Waste Management', 'amount': 1500, 'frequency': 'monthly'},
            {'name': 'Annual Maintenance', 'amount': 15000, 'frequency': 'yearly'}
        ]
        
        for cat_data in categories:
            if not DuesCategory.query.filter_by(name=cat_data['name']).first():
                cat = DuesCategory(**cat_data)
                db.session.add(cat)
        db.session.commit()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        # SECURED: Prevent non-admins from loading the administrator stats dashboard
        if current_user.role != 'admin':
            flash('Access denied!', 'error')
            return redirect(url_for('resident_dashboard'))

        # Dashboard stats
        total_residents = Resident.query.count()
        active_residents = Resident.query.filter_by(is_active=True).count()
        inactive_residents = Resident.query.filter_by(is_active=False).count()
        pending_complaints = Complaint.query.filter_by(status='pending').count()
        recent_payments = Payment.query.order_by(Payment.payment_date.desc()).limit(5).all()
        recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
        
        # Calculate total dues collected this month
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        monthly_collections = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.payment_date >= start_of_month,
            Payment.status == 'completed'
        ).scalar() or 0
        
        return render_template('index.html', 
                             total_residents=total_residents,
                             active_residents=active_residents,
                             inactive_residents=inactive_residents,
                             pending_complaints=pending_complaints,
                             monthly_collections=monthly_collections,
                             recent_payments=recent_payments,
                             recent_complaints=recent_complaints)
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # SECURITY FILTER: Catch suspended accounts instantly
            if user.role == 'suspended':
                flash('Your account has been deactivated. Please contact the EXCO Admin.', 'error')
                return render_template('login.html')
            login_user(user)
            
            # ROUTE ACCORDING TO ROLE
            if user.role == 'resident':
                return redirect(url_for('resident_dashboard'))
            else:
                return redirect(url_for('index')) # Admins & Staff go to main dashboard
                
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Temporary placeholder placeholder route for the Resident Dashboard view
@app.route('/resident_dashboard')
@login_required
def resident_dashboard():
    # Make sure this is a resident, if not bounce them out to index
    if current_user.role != 'resident' or not current_user.resident_id:
        return redirect(url_for('index'))
        
    # Query database values belonging EXCLUSIVELY to this resident's profile link
    resident_profile = Resident.query.get_or_404(current_user.resident_id)
    personal_payments = Payment.query.filter_by(resident_id=resident_profile.id).order_by(Payment.payment_date.desc()).all()
    personal_complaints = Complaint.query.filter_by(resident_id=resident_profile.id).order_by(Complaint.created_at.desc()).all()
    
    return render_template('resident_dashboard.html', 
                           resident=resident_profile, 
                           payments=personal_payments, 
                           complaints=personal_complaints)

# Residents Management
@app.route('/residents')
@login_required
def residents():
    # SECURED: Prevent non-admins from browsing the estate directory listings
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('resident_dashboard'))

    search = request.args.get('search', '')
    if search:
        residents_list = Resident.query.filter(
            db.or_(
                Resident.first_name.contains(search),
                Resident.last_name.contains(search),
                Resident.house_number.contains(search),
                Resident.email.contains(search)
            )
        ).all()
    else:
        residents_list = Resident.query.all()
    return render_template('residents.html', residents=residents_list, search=search)

@app.route('/add_resident', methods=['GET', 'POST'])
@login_required
def add_resident():
    # SECURED: Prevent residents from fabricating identity ledger records
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('resident_dashboard'))

    if request.method == 'POST':
        resident = Resident(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            house_number=request.form.get('house_number'),
            occupant_count=int(request.form.get('occupant_count', 1)),
            vehicle_count=int(request.form.get('vehicle_count', 0))
        )
        db.session.add(resident)
        db.session.commit()
        flash('Resident added successfully!', 'success')
        return redirect(url_for('residents'))
    return render_template('add_resident.html')

@app.route('/resident/<int:id>')
@login_required
def view_resident(id):
    # SECURED: Restrict residents so they can only look up their personal history maps
    if current_user.role == 'resident' and current_user.resident_id != id:
        flash('Access denied! You can only view your own profile.', 'error')
        return redirect(url_for('resident_dashboard'))

    resident = Resident.query.get_or_404(id)
    payments = Payment.query.filter_by(resident_id=id).order_by(Payment.payment_date.desc()).all()
    complaints = Complaint.query.filter_by(resident_id=id).order_by(Complaint.created_at.desc()).all()
    return render_template('view_resident.html', 
                         resident=resident, 
                         payments=payments, 
                         complaints=complaints)

@app.route('/resident/<int:id>/generate_account', methods=['POST'])
@login_required
def generate_resident_account(id):
    # Security: Only admins can provision entry accounts
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('resident_dashboard'))

    resident = Resident.query.get_or_404(id)
    
    # Safety Check: Verify they don't already have an account setup
    if resident.user_account:
        flash('This resident already has an active account provisioned.', 'warning')
        return redirect(url_for('view_resident', id=id))

    # Check if a User table row already exists with this exact email to avoid conflicts
    if User.query.filter_by(username=resident.email).first():
        flash(f"An account with username '{resident.email}' already exists in the system database.", 'error')
        return redirect(url_for('view_resident', id=id))

    # Provision the User account profile entry mapping
    new_user = User(
        username=resident.email,  # Using email as username makes it unique and easy to remember
        password=generate_password_hash('Resident@2026'), # Standardized generic default password
        role='resident',
        resident_id=resident.id
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    flash(f"Portal access activated for {resident.first_name}! Credentials sent to estate ledger.", "success")
    return redirect(url_for('view_resident', id=id))


@app.route('/toggle_resident_status/<int:id>', methods=['POST'])
@login_required
def toggle_resident_status(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('resident_dashboard'))

    resident = Resident.query.get_or_404(id)
    status_selection = request.form.get('status')
    
    if status_selection == 'inactive':
        resident.is_active = False
        # SUSPEND ACCOUNT: Change role to 'suspended' so they can no longer log in
        if resident.user_account:
            resident.user_account.role = 'suspended'
        flash(f"Status for {resident.first_name} updated to Inactive. Portal access suspended.", "success")
        
    elif status_selection == 'active':
        resident.is_active = True
        # RESTORE ACCOUNT: If they have a login account, restore their 'resident' privileges
        if resident.user_account:
            resident.user_account.role = 'resident'
        flash(f"Status for {resident.first_name} updated to Active. Portal access restored.", "success")
        
    db.session.commit()
    return redirect(url_for('residents'))

# Dues Management
@app.route('/dues')
@login_required
def dues():
    # SECURED: Block users from reviewing core pricing metric systems
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('resident_dashboard'))

    residents = Resident.query.filter_by(is_active=True).all()
    categories = DuesCategory.query.filter_by(is_active=True).all()
    return render_template('dues.html', residents=residents, categories=categories)

@app.route('/record_payment', methods=['POST'])
@login_required
def record_payment():
    # SECURED: Deny unauthorized payment entry creation access
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('resident_dashboard'))

    resident_id = request.form.get('resident_id')
    category_id = request.form.get('category_id')
    amount = float(request.form.get('amount'))
    payment_method = request.form.get('payment_method')
    
    category = DuesCategory.query.get(category_id)
    
    # Calculate period
    if category.frequency == 'monthly':
        period_start = datetime.now().replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:  # yearly
        period_start = datetime.now().replace(month=1, day=1)
        period_end = datetime.now().replace(year=datetime.now().year + 1, month=1, day=1) - timedelta(days=1)
    
    payment = Payment(
        resident_id=resident_id,
        dues_category_id=category_id,
        amount=amount,
        payment_method=payment_method,
        reference_number=f"PAY-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}",
        period_start=period_start,
        period_end=period_end,
        status='completed',
        receipt_number=f"RCP-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    )
    db.session.add(payment)
    db.session.commit()
    flash('Payment recorded successfully!', 'success')
    return redirect(url_for('dues'))

# Complaints Management
@app.route('/complaints')
@login_required
def complaints():
    complaints_list = Complaint.query.order_by(Complaint.created_at.desc()).all()
    residents_list = Resident.query.filter_by(is_active=True).all()
    
    return render_template('complaints.html', 
                           complaints=complaints_list, 
                           residents=residents_list) 

@app.route('/add_complaint', methods=['POST'])
@login_required
def add_complaint():
    complaint = Complaint(
        resident_id=request.form.get('resident_id'),
        category=request.form.get('category'),
        subject=request.form.get('subject'),
        description=request.form.get('description'),
        priority=request.form.get('priority', 'medium')
    )
    db.session.add(complaint)
    db.session.commit()
    flash('Complaint submitted successfully!', 'success')
    return redirect(url_for('complaints'))

@app.route('/update_complaint/<int:id>', methods=['POST'])
@login_required
def update_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    complaint.status = request.form.get('status')
    complaint.resolution_notes = request.form.get('resolution_notes')
    db.session.commit()
    flash('Complaint updated successfully!', 'success')
    return redirect(url_for('complaints'))

# Announcements
@app.route('/announcements')
@login_required
def announcements():
    announcements_list = Announcement.query.filter_by(is_published=True).order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=announcements_list)

@app.route('/add_announcement', methods=['POST'])
@login_required
def add_announcement():
    announcement = Announcement(
        title=request.form.get('title'),
        content=request.form.get('content'),
        category=request.form.get('category'),
        is_urgent=bool(request.form.get('is_urgent', False)),
        created_by=current_user.id
    )
    db.session.add(announcement)
    db.session.commit()
    flash('Announcement published successfully!', 'success')
    return redirect(url_for('announcements'))

if __name__ == '__main__':
    with app.app_context():
        create_default_data()
    app.run(debug=True, host='0.0.0.0', port=5000)