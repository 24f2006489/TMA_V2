from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Trek, StaffProfile, TrekkerProfile, Booking
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, 
    get_jwt, current_user, verify_jwt_in_request, get_jwt_identity
)

from functools import wraps
from datetime import datetime, timedelta

# Initialize the Flask application
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tma_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super_secret_key_for_viva' # We will need this later for login tokens
app.config['JWT_SECRET_KEY'] = 'tma_production_jwt_secret_9988_extra_secure' # Mandatory for token signing


db.init_app(app)
jwt = JWTManager(app)

# ======================================
#    @ JWT LOADER (The Token Bridge)
# ======================================
@jwt.user_identity_loader
def user_identity_lookup(user):
    # Extract the simple user id to put inside token
    return str(user.id)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    # Uses the ID from an incomming token to fetch the full user data from database
    identity = jwt_data["sub"]
    return db.session.get(User, int(identity))

# ==========================================
# 3. SECURITY GUARDS (Custom RBAC Decorator)
# ==========================================
def role_required(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()

            if claims.get("role") not in allowed_roles:
                return jsonify({"msg": f"Access denied. Required clearance: {allowed_roles}"}), 403

            
            return fn(*args, **kwargs)
        return decorator
    return wrapper



# Database Setup & Admin Injection
with app.app_context():

    # 1. Create the database file and all tables
    db.create_all()

    admin_email = 'admin@tma.com'
    admin_user = User.query.filter_by(email=admin_email).first()

    if not admin_user:
        hashed_password = generate_password_hash('admin123')

        new_admin = User(
            email=admin_email,
            password=hashed_password,
            role='admin',
            is_active=True
        )

        db.session.add(new_admin)
        db.session.commit()
        print("✅ Database created and default Admin injected successfully!")
    else:
        print("⚡ Database already exists and Admin is ready.")


# ==========================================
# 5. CORE ROUTES
# ==========================================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Missing email or password"}), 400

    user = User.query.filter_by(email=data['email']).first()

    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user, additional_claims={"role": user.role})
        return jsonify({
            "msg": "Login successful",
            "access_token": access_token, 
            "role": user.role
        }), 200
    return jsonify({"msg": "Invalid credentials"}), 401

@app.route('/register', methods=['POST'])
def register_trekker():
    data = request.get_json()

    required_fields = ['email', 'password', 'name', 'contact_details', 'emergency_contact']
    for field in required_fields:
        if not data or field not in data:
            return jsonify({"msg": f"Missing required field: {field}"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already registered"}), 409

    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        email=data['email'],
        password=hashed_password,
        role='trekker',
        is_active=True
    )

    db.session.add(new_user)
    db.session.flush()

    new_profile = TrekkerProfile(
        user_id=new_user.id,
        name=data['name'],
        contact_details=data['contact_details'],
        emergency_contact=data['emergency_contact']
    )

    db.session.add(new_profile)
    db.session.commit()

    return jsonify({
        "msg": "Registration successful! You can now log in.", 
        "user_id": new_user.id
    }), 201

# ==========================================
# ADMIN ROUTES
# ==========================================

@app.route('/admin-dashboard', methods=['GET', 'POST'])
@role_required(['admin'])
def test_admin_dashboard():
    return jsonify({
        "msg": f"Welcome to the highly secure Admin Dashboard, {current_user.email}!"
    }), 200

@app.route('/admin/staff', methods=['POST'])
@role_required(['admin']) # Only Admins can hit this endpoint
def create_staff():
    data = request.get_json()
    
    # 1. Validate Input
    required_fields = ['email', 'password', 'name', 'contact_details']
    for field in required_fields:
        if not data or field not in data:
            return jsonify({"msg": f"Missing required field: {field}"}), 400
            
    # 2. Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "A user with this email already exists"}), 409
        
    # 3. Create the Base User (The Login Credentials)
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        email=data['email'],
        password=hashed_password,
        role='staff', # Hardcoded to 'staff' so Admins can't accidentally create other Admins
        is_active=True
    )
    
    db.session.add(new_user)
    
    # 4. Flush to generate the ID
    db.session.flush() 
    
    # 5. Create the Linked Profile using the new ID
    new_profile = StaffProfile(
        user_id=new_user.id,
        name=data['name'],
        contact_details=data['contact_details']
    )
    
    db.session.add(new_profile)
    
    # 6. Lock it in!
    db.session.commit()
    
    return jsonify({
        "msg": "Staff account created successfully!", 
        "staff_id": new_user.id
    }), 201

@app.route('/admin/trek', methods=['POST'])
@role_required(['admin'])
def create_trek():
    data = request.get_json()

    # 1. Validate Core Input
    required_fields = ['name', 'location', 'difficulty', 'duration', 'available_slots', 'start_date', 'end_date']
    for field in required_fields:
        if not data or field not in data:
            return jsonify({"msg": f"Missing required field: {field}"}), 400

    # 2. Translate Strings to Date Objects
    try:
        start_d = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_d = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Invalid date format. Please use YYYY-MM-DD"}), 400

    # .get() is safe! If they don't provide a staff ID yet, it just defaults to None
    staff_id = data.get('assigned_staff_id')

    # ==========================================
    # 3. THE COLLISION BOX (10-Day Buffer Logic)
    # ==========================================

    if staff_id:
        buffer_days = timedelta(days=10)
        shadow_start = start_d - buffer_days
        shadow_end = end_d + buffer_days

        # Query the database for overlapping schedules
        overlapping_trek = Trek.query.filter(
            Trek.assigned_staff_id == staff_id,
            Trek.status != 'Cancelled',      # Don't let cancelled treks block the schedule
            Trek.end_date >= shadow_start,   # Existing trek ends after our shadow begins
            Trek.start_date <= shadow_end    # Existing trek begins before our shadow ends
        ).first()

        if overlapping_trek:
            return jsonify({
                "msg": f"Schedule Conflict: Staff is assigned to '{overlapping_trek.name}' ({overlapping_trek.start_date} to {overlapping_trek.end_date}). Violates 10-day buffer."
            }), 409

    # ==========================================
    # 4. Build and Save the Trek
    # ==========================================
        
    # If a staff_id exists, status is Approved. Otherwise, it stays Pending.
    calculated_status = 'Approved' if staff_id else 'Pending' 
    
    new_trek = Trek(
        name=data['name'],
        location=data['location'],
        difficulty=data['difficulty'],
        duration=data['duration'],
        available_slots=data['available_slots'],
        start_date=start_d,
        end_date=end_d,
        assigned_staff_id=staff_id,
        status=calculated_status # We explicitly override the default here!
    )

    db.session.add(new_trek)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback() # If the name isn't unique, safely cancel the save
        return jsonify({"msg": "Error: Trek name might already exist."}), 409

    return jsonify({
        "msg": f"Trek created successfully with status: {calculated_status}", 
        "trek_id": new_trek.id
    }), 201


@app.route('/admin/available-staff', methods=['GET'])
@role_required(['admin'])
def get_available_staff():
    # 1. Grab dates from the URL query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        return jsonify({"msg": "Missing start_date or end_date parameters"}), 400
        
    # 2. Parse the Dates
    try:
        start_d = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_d = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD"}), 400
        
    # 3. Calculate the Shadow
    buffer_days = timedelta(days=10)
    shadow_start = start_d - buffer_days
    shadow_end = end_d + buffer_days
    
    # 4. Find the Busy Staff (The Exclusion List)
    overlapping_treks = Trek.query.filter(
        Trek.status != 'Cancelled',
        Trek.end_date >= shadow_start,
        Trek.start_date <= shadow_end,
        Trek.assigned_staff_id.isnot(None) # Only check treks that actually have staff
    ).all()
    
    # Create a simple list of busy IDs (e.g., [2, 5, 8])
    busy_staff_ids = [trek.assigned_staff_id for trek in overlapping_treks]
    
    # 5. Find the Available Staff
    # We query StaffProfile so we can easily return their names to the frontend
    available_staff_query = StaffProfile.query.filter(StaffProfile.status == 'Active')
    
    if busy_staff_ids:
        # The ~ symbol means "NOT". Give me staff NOT in the busy list.
        available_staff_query = available_staff_query.filter(~StaffProfile.user_id.in_(busy_staff_ids))
        
    available_staff = available_staff_query.all()
    
    # 6. Format the Data for the Frontend Dropdown
    results = [
        {"staff_id": staff.user_id, "name": staff.name}
        for staff in available_staff
    ]
    
    return jsonify({
        "available_count": len(results),
        "staff": results
    }), 200

@app.route('/admin/staffs', methods=['GET'])
@role_required(['admin'])
def get_all_staff():
    staff_list = StaffProfile.query.all()

    results = [
        {
            "id": staff.id,
            "user_id": staff.user_id,
            "name": staff.name,
            "contact_details": staff.contact_details,
            "status": staff.status
        } for staff in staff_list
    ]

    return jsonify(results), 200

@app.route('/admin/treks', methods=['GET'])
@role_required(['admin'])
def get_all_treks():
    treks = Trek.query.all()

    results = []

    for trek in treks:
        manager_name = "Unassigned"
        if trek.manager and trek.manager.staff_profile:
            manager_name = trek.manager.staff_profile.name

        results.append({
            "id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty,
            "duration": trek.duration,
            "available_slots": trek.available_slots,
            # Translate the Python Date objects back into readable strings for the frontend
            "start_date": trek.start_date.strftime('%Y-%m-%d'),
            "end_date": trek.end_date.strftime('%Y-%m-%d'),
            "status": trek.status,
            "assigned_staff": manager_name
        })

    return jsonify(results), 200

# ==========================================
# TREKKERS ROUTES 
# ==========================================

@app.route('/treks/available', methods=['GET'])
def view_open_treks():
    open_treks = Trek.query.filter(
        Trek.status=='Open',
        Trek.available_slots > 0
    ).all()

    results = []
    for trek in open_treks:
        results.append({
            "id": trek.id,
            "name": trek.name,
            "location":trek.location,
            "difficulty":trek.difficulty,
            "duration":trek.duration,
            "available_slots":trek.available_slots,
            "start_date":trek.start_date.strftime('%Y-%m-%d'),
            "end_date":trek.end_date.strftime('%Y-%m-%d')
        })

    return jsonify({
        "count": len(results),
        "treks": results
    }), 200

@app.route('/book', methods=['POST'])
@role_required(['trekker']) # ONLY trekkers can hit this route!
def book_trek():
    data = request.get_json()
    trek_id = data.get('trek_id')
    
    if not trek_id:
        return jsonify({"msg": "Please provide a trek_id to book"}), 400
        
    # 1. Securely identify WHO is making the request using their Token
    user_id = int(get_jwt_identity()) 
    
    # 2. Find the requested Trek
    target_trek = Trek.query.get(trek_id)
    if not target_trek:
        return jsonify({"msg": "Trek not found"}), 404
        
    if target_trek.status != 'Open':
        return jsonify({"msg": "This trek is not currently open for booking"}), 400
        
    if target_trek.available_slots <= 0:
        return jsonify({"msg": "Sorry, this trek is fully booked!"}), 400
        
    # ==========================================
    # 3. EDGE CASE 1: Prevent Double Booking
    # ==========================================
    existing_booking = Booking.query.filter_by(user_id=user_id, trek_id=trek_id).first()
    if existing_booking:
        return jsonify({"msg": "You have already booked a ticket for this trek!"}), 409
        
    # ==========================================
    # 4. EDGE CASE 2: Prevent Overlapping Dates
    # ==========================================
    # We join the Trek and Booking tables to find existing trips for this specific user
    overlapping_trek = Trek.query.join(Booking).filter(
        Booking.user_id == user_id,
        Trek.end_date > target_trek.start_date, # Existing ends AFTER new one starts
        Trek.start_date < target_trek.end_date  # Existing starts BEFORE new one ends
    ).first()
    
    if overlapping_trek:
        return jsonify({
            "msg": f"Date overlap! You are already booked for '{overlapping_trek.name}' from {overlapping_trek.start_date} to {overlapping_trek.end_date}."
        }), 409

    # ==========================================
    # 5. Execute the Transaction
    # ==========================================
    new_booking = Booking(user_id=user_id, trek_id=trek_id)
    
    # Inventory Management: Decrease available slots by 1
    target_trek.available_slots -= 1 
    
    db.session.add(new_booking)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "A database error occurred during booking."}), 500
    
    return jsonify({
        "msg": f"Successfully booked your slot for {target_trek.name}!",
        "remaining_slots": target_trek.available_slots
    }), 201


@app.route('/trekker/my-booking', methods=['GET'])
@role_required(['trekker'])
def get_my_booking():
    user_id = int(get_jwt_identity())

    my_bookings = Booking.query.filter_by(user_id=user_id).all()

    results = []
    for booking in my_bookings:
        # Thanks to the 'backref' in models.py, we can just say booking.trek!
        trek  = booking.trek

        results.append({
            "booking_id": booking.id,
            "trek_id": trek.id,
            "trek_name": trek.name,
            "location": trek.location,
            "start_date": trek.start_date.strftime('%Y-%m-%d'),
            "end_date": trek.end_date.strftime('%Y-%m-%d'),
            "duration": trek.duration
        })

    return jsonify({
        "total_bookings": len(results),
        "bookings": results
    }), 200

# ==========================================
# STAFF ROUTES (Phase 6)
# ==========================================
@app.route('/staff/my-treks', methods=['GET'])
@role_required(['staff'])
def get_my_assigned_trek():
    user_id = int(get_jwt_identity())

    assigned_treks = Trek.query.filter_by(assigned_staff_id=user_id).all()

    results = []
    for trek in assigned_treks:
        # We also want to calculate how many people have booked this trek
        # len(trek.bookings) counts the number of booking records attached to this trek
        booked_count = len(trek.bookings)
        results.append({
            "trek_id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty,
            "duration": trek.duration,
            "total_capacity": trek.available_slots + booked_count, # Math to find original capacity
            "slots_remaining": trek.available_slots,
            "currently_booked": booked_count,
            "start_date": trek.start_date.strftime('%Y-%m-%d'),
            "end_date": trek.end_date.strftime('%Y-%m-%d'),
            "status": trek.status
        })

    return jsonify({
        "total_assigned": len(results),
        "treks": results
    }), 200

@app.route('/staff/trek/<int:trek_id>/status', methods=['PUT'])
@role_required(['staff'])
def update_trek_status(trek_id):
    data = request.get_json()
    new_status = data.get('status')
    
    # 1. Validate Input
    # Staff shouldn't be able to revert a trek to "Pending" (that means no staff is assigned)
    allowed_statuses = ['Approved', 'Open', 'Closed', 'Completed']
    if not new_status or new_status not in allowed_statuses:
        return jsonify({"msg": f"Invalid status. Must be one of: {allowed_statuses}"}), 400
        
    # 2. Identify the Staff Member
    staff_id = int(get_jwt_identity())
    
    # 3. Find the Trek
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"msg": "Trek not found"}), 404
        
    # ==========================================
    # 4. THE SECURITY FORTRESS (Ownership Check)
    # ==========================================
    if trek.assigned_staff_id != staff_id:
        return jsonify({"msg": "Unauthorized: You do not have permission to modify this trek."}), 403
        
    # 5. Update and Save
    trek.status = new_status
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error occurred."}), 500
        
    return jsonify({
        "msg": f"Successfully updated trek status to {new_status}",
        "trek_id": trek.id,
        "new_status": trek.status
    }), 200

@app.route('/staff/trek/<int:trek_id>/participants', methods=['GET'])
@role_required(['staff'])
def get_trek_participants(trek_id):
    staff_id = int(get_jwt_identity())

    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"msg": "Trek not found"}), 404

    if trek.assigned_staff_id != staff_id:
        return jsonify({"msg": "Unauthorized: You can only view participants for your own assigned treks."}), 403

    participants = []
    for booking in trek.bookings:
        trekker_profile = booking.user.trekker_profile

        name = trekker_profile.name if trekker_profile else "Unknown"
        name = trekker_profile.name if trekker_profile else "Unknown"
        contact = trekker_profile.contact_details if trekker_profile else "N/A"
        emergency = trekker_profile.emergency_contact if trekker_profile else "N/A"

        participants.append({
            "booking_id": booking.id,
            "trekker_id": booking.user_id,
            "name": name,
            "contact_details": contact,
            "emergency_contact": emergency
        })
        
    return jsonify({
        "trek_name": trek.name,
        "total_participants": len(participants),
        "participants": participants
    }), 200


# Start the local development server
if __name__ == '__main__':
    app.run(debug=True)
