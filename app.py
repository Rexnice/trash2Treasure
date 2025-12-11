
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import uuid

from models import db, User, WasteItem, PickupRequest, Reward
from config import Config


app = Flask(__name__)
app.config.from_object(Config)




# For Render deployment
if 'RENDER' in os.environ:
    # Use PostgreSQL on Render
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url


# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            user_type=user_type,
            address=address,
            phone=phone
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        
        flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type == 'household':
        waste_items = WasteItem.query.filter_by(user_id=current_user.id).order_by(WasteItem.created_at.desc()).limit(5).all()
        total_points = sum([item.points_earned for item in waste_items])
        upcoming_pickups = PickupRequest.query.filter_by(user_id=current_user.id, status='confirmed').order_by(PickupRequest.scheduled_date).limit(3).all()
        
        return render_template('dashboard.html', 
                             waste_items=waste_items,
                             total_points=total_points,
                             upcoming_pickups=upcoming_pickups)
    
    elif current_user.user_type == 'company':
        pending_pickups = PickupRequest.query.filter_by(company_id=current_user.id, status='pending').order_by(PickupRequest.created_at).all()
        scheduled_pickups = PickupRequest.query.filter_by(company_id=current_user.id, status='confirmed').order_by(PickupRequest.scheduled_date).all()
        
        return render_template('dashboard.html',
                             pending_pickups=pending_pickups,
                             scheduled_pickups=scheduled_pickups)

@app.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    if request.method == 'POST':
        # Handle file upload
        file = request.files.get('waste_image')
        filename = None
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            filename = url_for('static', filename=f'uploads/{filename}')
        
        # Get waste data
        waste_type = request.form.get('waste_type')
        weight = float(request.form.get('weight'))
        material = request.form.get('material')
        description = request.form.get('description')
        
        # Calculate points (simplified)
        points = int(weight * 10)  # 10 points per kg
        
        # Create waste item
        waste_item = WasteItem(
            user_id=current_user.id,
            waste_type=waste_type,
            material=material,
            weight_kg=weight,
            image_url=filename,
            description=description,
            points_earned=points,
            status='pending'
        )
        
        db.session.add(waste_item)
        db.session.commit()
        
        # Add reward
        reward = Reward(
            user_id=current_user.id,
            points=points,
            source='waste_submission',
            description=f'{weight}kg of {waste_type} recycled'
        )
        
        db.session.add(reward)
        db.session.commit()
        
        flash('Waste item uploaded successfully! Points earned: ' + str(points))
        return redirect(url_for('dashboard'))
    
    return render_template('scan.html')

@app.route('/schedule-pickup', methods=['GET', 'POST'])
@login_required
def schedule_pickup():
    if request.method == 'POST':
        waste_item_id = request.form.get('waste_item_id')
        company_id = request.form.get('company_id')
        scheduled_date_str = request.form.get('scheduled_date')
        notes = request.form.get('notes')
        
        # Convert string to datetime
        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
        
        # Get waste item
        waste_item = WasteItem.query.get(waste_item_id)
        
        # Create pickup request
        pickup_request = PickupRequest(
            user_id=current_user.id,
            company_id=company_id,
            waste_item_id=waste_item_id,
            scheduled_date=scheduled_date,
            address=current_user.address,
            notes=notes,
            status='pending'
        )
        
        # Update waste item status
        waste_item.status = 'scheduled'
        waste_item.scheduled_pickup = scheduled_date
        
        db.session.add(pickup_request)
        db.session.commit()
        
        flash('Pickup scheduled successfully!')
        return redirect(url_for('dashboard'))
    
    # Get user's waste items that are pending
    waste_items = WasteItem.query.filter_by(user_id=current_user.id, status='pending').all()
    
    # Get recycling companies
    companies = User.query.filter_by(user_type='company').all()
    
    return render_template('schedule.html', waste_items=waste_items, companies=companies)

@app.route('/pickup-requests')
@login_required
def pickup_requests():
    if current_user.user_type == 'household':
        requests = PickupRequest.query.filter_by(user_id=current_user.id).order_by(PickupRequest.created_at.desc()).all()
    else:
        requests = PickupRequest.query.filter_by(company_id=current_user.id).order_by(PickupRequest.created_at.desc()).all()
    
    return render_template('pickup_requests.html', pickup_requests=requests)

@app.route('/update-pickup-status/<pickup_id>', methods=['POST'])
@login_required
def update_pickup_status(pickup_id):
    pickup = PickupRequest.query.get_or_404(pickup_id)
    new_status = request.form.get('status')
    
    # Update status
    pickup.status = new_status
    
    # If completed, update waste item status
    if new_status == 'completed':
        pickup.waste_item.status = 'collected'
    
    db.session.commit()
    flash('Pickup status updated!')
    return redirect(url_for('pickup_requests'))

@app.route('/api/companies')
@login_required
def get_companies():
    companies = User.query.filter_by(user_type='company').all()
    companies_data = [{
        'id': company.id,
        'name': company.name,
        'address': company.address,
        'phone': company.phone
    } for company in companies]
    
    return jsonify(companies_data)

@app.route('/api/user-stats')
@login_required
def user_stats():
    if current_user.user_type == 'household':
        total_waste = db.session.query(db.func.sum(WasteItem.weight_kg)).filter_by(user_id=current_user.id).scalar() or 0
        total_points = db.session.query(db.func.sum(WasteItem.points_earned)).filter_by(user_id=current_user.id).scalar() or 0
        items_recycled = WasteItem.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            'total_waste': total_waste,
            'total_points': total_points,
            'items_recycled': items_recycled
        })
    
    return jsonify({'error': 'Not a household user'})

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    current_user.name = request.form.get('name')
    current_user.address = request.form.get('address')
    current_user.phone = request.form.get('phone')
    current_user.city = request.form.get('city')
    current_user.state = request.form.get('state')
    current_user.zip_code = request.form.get('zip_code')
    
    db.session.commit()
    flash('Profile updated successfully!')
    return redirect(url_for('profile'))

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)


























"""
Project Structure
trash2treasure/
├── app.py
├── requirements.txt
├── config.py
├── .gitignore
├── README.md
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── uploads/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── scan.html
│   ├── schedule.html
│   ├── pickup_requests.html
│   ├── login.html
│   ├── register.html
│   └── profile.html
└── models.py
"""