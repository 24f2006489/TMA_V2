from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Trek, StaffProfile, TrekkerProfile, Booking
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, 
    get_jwt, current_user, verify_jwt_in_request, get_jwt_identity
)
from flask_sse import sse
from flask_caching import Cache

from functools import wraps
from datetime import datetime, timedelta

# Initialize the Flask application
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tma_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super_secret_key_for_viva' # We will need this later for login tokens
app.config['JWT_SECRET_KEY'] = 'tma_production_jwt_secret_9988_extra_secure' # Mandatory for token signing

# ==========================================
#  SSE REDIS CONFIG 
# ==========================================
app.config['REDIS_URL'] = 'redis://localhost:6379/2'

# ==========================================
#  CACHING CONFIG 
# ==========================================
app.config.from_mapping({
    "CACHE_TYPE": 'RedisCache',
    "CACHE_REDIS_URL" : 'redis://localhost:6379/3',
    "CACHE_DEFAULT_TIMEOUT" : 300
})

db.init_app(app)
jwt = JWTManager(app)
cache = Cache(app)

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
#  SECURITY GUARDS (Custom RBAC Decorator)
# ==========================================
def role_required(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_id = get_jwt_identity()

            # 1. Check if the role is permitted
            if claims.get("role") not in allowed_roles:
                return jsonify({"msg": f"Access denied. Required clearance: {allowed_roles}"}), 403

            # 2. EMERGENCY SHIELD: Verify the user isn't blacklisted mid-session!
            user = db.session.get(User, int(user_id))
            if not user or not user.is_active:
                return jsonify({"msg": "Account deactivated. Access revoked."}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# ==========================================
#  CORE ROUTES
# ==========================================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Missing email or password"}), 400

    user = User.query.filter_by(email=data['email']).first()

    if user and not user.is_active:
        return jsonify({"msg": "This account has been deactivated. Please contact support."}), 403

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

@app.route('/admin/dashboard/stats', methods=['GET'])
@role_required(['admin'])
@cache.cached(timeout=120, key_prefix='admin_dashboard_stats')
def get_admin_stats():
    total_trekkers = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_treks = Trek.query.count()
    total_bookings = Booking.query.count()
    
    return jsonify({
        "total_trekkers": total_trekkers,
        "total_staff": total_staff,
        "total_treks": total_treks,
        "total_bookings": total_bookings
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

@app.route('/admin/staff/<int:staff_id>', methods=['PUT'])
@role_required(['admin'])
def update_staff(staff_id):
    # 1. Verify the target
    target_user = User.query.get(staff_id)
    
    if not target_user or target_user.role != 'staff':
        return jsonify({"msg": "Staff member not found."}), 404
        
    profile = target_user.staff_profile
    if not profile:
        return jsonify({"msg": "Staff profile data is missing."}), 404
        
    data = request.get_json()
    
    # 2. Apply updates
    if 'name' in data:
        profile.name = data['name']
        
    if 'contact_details' in data:
        profile.contact_details = data['contact_details']
        
    db.session.commit()
    
    return jsonify({
        "msg": "Staff profile updated successfully.",
        "name": profile.name,
        "contact_details": profile.contact_details
    }), 200


@app.route('/admin/staff/<int:staff_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_staff(staff_id):
    target_user = User.query.get(staff_id)
    
    if not target_user or target_user.role != 'staff':
        return jsonify({"msg": "Staff member not found."}), 404
        
    # 1. Fetch all active treks assigned to this staff member
    active_treks = Trek.query.filter(
        Trek.assigned_staff_id == staff_id,
        Trek.status.in_(['Approved', 'Open', 'Closed'])
    ).all()
    
    # ==========================================
    # 2. THE BOOKING SHIELD (Validation Pass)
    # ==========================================
    # If even ONE trek has a booking, the entire deletion is blocked.
    for trek in active_treks:
        if len(trek.bookings) > 0:
            return jsonify({
                "msg": f"Action Denied: Cannot delete this staff member. The trek '{trek.name}' they are assigned to already has {len(trek.bookings)} booking(s)."
            }), 400
            
    # ==========================================
    # 3. THE CASCADE REVERT (Mutation Pass)
    # ==========================================
    # If we made it past the shield, it means 0 bookings exist.
    # We detach the staff and revert the treks to the empty 'Pending' state.
    for trek in active_treks:
        trek.assigned_staff_id = None
        trek.status = 'Pending'
        
    # 4. Safe to Delete the Staff Member
    profile = target_user.staff_profile
    if profile:
        db.session.delete(profile)
        
    db.session.delete(target_user)
    
    # 5. Commit everything simultaneously
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error occurred during deletion."}), 500
    
    return jsonify({
        "msg": f"Staff member successfully deleted. {len(active_treks)} trek(s) have been reverted to 'Pending'."
    }), 200



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
        cache.clear()
    except Exception as e:
        db.session.rollback() # If the name isn't unique, safely cancel the save
        return jsonify({"msg": "Error: Trek name might already exist."}), 409

    return jsonify({
        "msg": f"Trek created successfully with status: {calculated_status}", 
        "trek_id": new_trek.id
    }), 201

@app.route('/admin/trek/<int:trek_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_trek(trek_id):
    trek = Trek.query.get(trek_id)

    if not trek:
        return jsonify({"msg": "Trek not found."}), 404

    # Prevent deletion if bookings exist
    if len(trek.bookings) > 0:
        return jsonify({
            "msg": f"Action Denied: Cannot delete '{trek.name}' because {len(trek.bookings)} trekkers have already booked it. Please cancel the trek instead."
        }), 400

    db.session.delete(trek)
    db.session.commit()
    cache.clear()

    return jsonify({"msg": f"Trek '{trek.name}' has been successfully deleted."}), 200

@app.route('/admin/trek/<int:trek_id>', methods=['PUT'])
@role_required(['admin'])
def update_trek(trek_id):
    trek = Trek.query.get(trek_id)

    if not trek:
        return jsonify({"msg": "Trek not found."}), 404

    data = request.get_json()

    has_bookings = len(trek.bookings) > 0

    # 1. ALWAYS ALLOWED (Superficial changes)
    if 'name' in data:
        trek.name = data['name']
    if 'difficulty' in data:
        trek.difficulty = data['difficulty']

    # 2. CONDITIONAL CHANGES (Core details)
    # Check if the admin is trying to change a restricted field
    restricted_fields = ['location', 'duration', 'start_date', 'end_date']
    attempting_restricted_update = any(field in data for field in restricted_fields)

    if has_bookings and attempting_restricted_update:
        return jsonify({
            "msg": "Action Denied: You cannot change the location or dates of this trek because users have already booked it. You may only fix typos in the name or difficulty."
        }), 400

    # if there are no booking, apply the core change
    if not has_bookings:
        if 'location' in data:
            trek.location = data['location']
        if 'duration' in data:
            trek.duration = data['duration']

        try:
            if 'start_date' in data:
                trek.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            if 'end_date' in data:
                trek.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid date format. Please use YYYY-MM-DD"}), 400

        
        db.session.commit()
        cache.clear()
    
    return jsonify({
        "msg": f"Trek '{trek.name}' updated successfully.",
        "has_bookings": has_bookings
    }), 200

@app.route('/admin/trek/<int:trek_id>/cancel', methods=['PUT'])
@role_required(['admin'])
def emergency_cancel_trek(trek_id):
    trek = Trek.query.get(trek_id)

    if not trek:
        return jsonify({"msg": "Trek not found"}), 404

    if trek.status == 'Canceled':
        return jsonify({"msg": "This trek is already canceled."}), 400

    # 1. Change the status
    trek.status = 'Canceled'

    # 2. Free up the Staff Member!
    # By setting this to None, Rohit's 10-day buffer is instantly cleared for these dates.
    freed_staff = trek.assigned_staff_id
    trek.assigned_staff_id = None

    db.session.commit()
    cache.clear()

    sse.publish(
        {
            "message": f"🚨 EMERGENCY: The '{trek.name}' trek has been officially CANCELLED by administration.",
            "trek_id": trek.id
        },
        type="emergency_alert"
    )

    return jsonify({
        "msg": f"EMERGENCY OVERRIDE: Trek '{trek.name}' has been officially cancelled.",
        "freed_staff_id": freed_staff,
        "new_status": trek.status
    }), 200


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

# This route is to assign staff to existing trek
@app.route('/admin/trek/<int:trek_id>/assign', methods=['PUT'])
@role_required(['admin'])
def assign_staff_to_trek(trek_id):
    data = request.get_json()
    new_staff_id = data.get('staff_id')

    if not new_staff_id:
        return jsonify({"msg": "Please provide a staff_id to assign."}), 400

    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"msg": "Trek not found."}), 404

    target_staff = User.query.get(new_staff_id)
    if not target_staff or target_staff.role != 'staff':
        return jsonify({"msg": "Valid staff member not found."}), 404

    buffer_days = timedelta(days=10)
    shadow_start = trek.start_date - buffer_days
    shadow_end = trek.end_date + buffer_days

    overlapping_trek = Trek.query.filter(
        Trek.assigned_staff_id == new_staff_id,
        Trek.status != 'Cancelled',
        Trek.id != trek.id, # Ignore the current trek in case this is a re-assignment
        Trek.end_date >= shadow_start,
        Trek.start_date <= shadow_end
    ).first()

    if overlapping_trek:
        return jsonify({
            "msg": f"Schedule Conflict: Staff is already assigned to '{overlapping_trek.name}' ({overlapping_trek.start_date} to {overlapping_trek.end_date}). Violates 10-day buffer."
        }), 409

    trek.assigned_staff_id = new_staff_id

    if trek.status == 'Pending':
        trek.status = 'Approved'

    db.session.commit()
    cache.clear()

    return jsonify({
        "msg": f"Staff member successfully assigned to '{trek.name}'.",
        "trek_id": trek.id,
        "assigned_staff_id": trek.assigned_staff_id,
        "new_status": trek.status
    }), 200


@app.route('/admin/staffs', methods=['GET'])
@role_required(['admin'])
def get_all_staff():
    search_query = request.args.get('search')

    query = StaffProfile.query

    if search_query:
        if search_query.isdigit(): # if you type a number, then search by ID
            query = query.filter(StaffProfile.user_id == int(search_query))
        else: # if you type a word, then search by name
            query = query.filter(StaffProfile.name.ilike(f"%{search_query}%"))

    staff_list = query.all()

    results = [
        {
            "id": staff.id,
            "user_id": staff.user_id,
            "name": staff.name,
            "contact_details": staff.contact_details,
            "status": staff.status
        } for staff in staff_list
    ]

    return jsonify({"count": len(results), "staff": results}), 200

@app.route('/admin/treks', methods=['GET'])
@role_required(['admin'])
def get_all_treks():
    search_query = request.args.get('search')

    query = Trek.query
    
    if search_query:
        if search_query.isdigit():
            query = query.filter(Trek.id == int(search_query))
        else:
            query = query.filter(Trek.name.ilike(f"%{search_query}%"))

    treks = query.all()

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
            "start_date": trek.start_date.strftime('%Y-%m-%d'),
            "end_date": trek.end_date.strftime('%Y-%m-%d'),
            "status": trek.status,
            "assigned_staff": manager_name
        })

    return jsonify({"count": len(results), "treks": results}), 200

@app.route('/admin/trekkers', methods=['GET'])
@role_required(['admin'])
def get_all_trekkers():
    search_query = request.args.get('search')

    # We must join TrekkerProfile so we can access the 'name' column for searching
    query = User.query.filter_by(role="trekker").outerjoin(TrekkerProfile)

    if search_query:
        if search_query.isdigit():
            query = query.filter(User.id == int(search_query))
        else:
            query = query.filter(TrekkerProfile.name.ilike(f"%{search_query}%"))

    trekkers = query.all()

    results = []
    for user in trekkers:
        profile = user.trekker_profile

        booking_history = []
        for booking in user.bookings:
            booking_history.append({
                "booking_id": booking.id,
                "trek_name": booking.trek.name,
                "start_date": booking.trek.start_date.strftime('%Y-%m-%d'),
                "status": booking.trek.status
            })

        results.append({
            "user_id": user.id,
            "email": user.email,
            "name": profile.name if profile else "N/A",
            "contact_details": profile.contact_details if profile else "N/A",
            "emergency_contact": profile.emergency_contact if profile else "N/A",
            "is_active": user.is_active,
            "total_bookings": len(booking_history),
            "bookings": booking_history
        })
    return jsonify({
        "total_trekkers": len(results),
        "trekkers": results
    }), 200

@app.route('/admin/bookings', methods=['GET'])
@role_required(['admin'])
def get_all_global_bookings():
    all_bookings = Booking.query.all()

    results = []
    for b in all_bookings:
        profile = b.user.trekker_profile

        results.append({
            "booking_id": b.id,
            "trek_id": b.trek_id,
            "trek_name": b.trek.name,
            "trek_start_date": b.trek.start_date.strftime('%Y-%m-%d'),
            "user_id": b.user_id,
            "trekker_name": profile.name if profile else "Unknown",
            "trekker_email": b.user.email
        })
    return jsonify({
        "total_global_booking": len(results),
        "bookings": results
    }), 200

@app.route('/admin/user/<int:user_id>/blacklist', methods=['PUT'])
@role_required(['admin'])
def toggle_user_status(user_id):
    target_user = User.query.get(user_id)

    if not target_user:
        return jsonify({"msg": "User not found"}), 404

    if target_user.role == 'admin':
        return jsonify({"msg": "Action Denied. Cannot modify Admin status."}), 403

    target_user.is_active = not target_user.is_active

    db.session.commit()

    status_msg = "Activated" if target_user.is_active else "Blacklisted"

    return jsonify({
        "msg": f"User {target_user.email} is now {status_msg}.",
        "user_id": target_user.id,
        "is_active": target_user.is_active
    }), 200

# ==========================================
# TREKKERS ROUTES 
# ==========================================

@app.route('/trekker/profile', methods=['PUT'])
@role_required(['trekker'])
def update_trekker_profile():
    # 1. Identify the Trekker
    user_id = int(get_jwt_identity())
    
    # 2. Fetch their specific profile using the linked user_id
    profile = TrekkerProfile.query.filter_by(user_id=user_id).first()
    
    if not profile:
        return jsonify({"msg": "Profile not found"}), 404
        
    data = request.get_json()
    
    if 'name' in data:
        profile.name = data['name']
    
    if 'contact_details' in data:
        profile.contact_details = data['contact_details']
        
    if 'emergency_contact' in data:
        profile.emergency_contact = data['emergency_contact']
        
    # 4. Save Changes
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error occurred while updating profile."}), 500
        
    return jsonify({
        "msg": "Profile updated successfully!",
        "contact_details": profile.contact_details,
        "emergency_contact": profile.emergency_contact
    }), 200

@app.route('/treks/available', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
            # <-- Caches the specific search for 60 seconds
            # By setting query_string=True, 
            # Redis is smart enough to save a different copy for every unique search filter!
def view_open_treks():
    search_location = request.args.get('location')
    search_difficulty = request.args.get('difficulty')
    search_duration = request.args.get('duration')

    query = Trek.query.filter(Trek.status == 'Open', Trek.available_slots > 0)

    if search_location:
        # ilike() makes it case-insensitive. The % symbols act as wildcards.
        # So "kash" will successfully find "Jammu & Kashmir"
        query = query.filter(Trek.location.ilike(f"%{search_location}%"))

    if search_difficulty:
        query = query.filter(Trek.difficulty.ilike(search_difficulty))

    if search_duration:
        # URL parameters are always strings, so we convert to int for math
        try:
            duration_int = int(search_duration)
            query = query.filter(Trek.duration <= duration_int)
        except ValueError:
            pass

    filtered_treks = query.all()

    results = []
    for trek in filtered_treks:
        results.append({
            "id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty,
            "duration": trek.duration,
            "available_slots": trek.available_slots,
            "start_date": trek.start_date.strftime('%Y-%m-%d'),
            "end_date": trek.end_date.strftime('%Y-%m-%d')
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

        # --- CACHE INVALIDATION ---
        cache.clear()
        cache.delete_memoized('get_trek_participants', target_trek.id) # Surgically deletes ONLY this trek's staff roster cache!

        # ---SSE BROADCAST FOR ADMIN---
        sse.publish(
            {
                "message": f"New booking recieved for {target_trek.name}!",
                "trek_id": target_trek.id,
                "booking_id": new_booking.id,
                "new_available_slots": target_trek.available_slots
            },
            type="admin_dashboard_update"
        )
        # ------------------------------------

        # ---- Filterd SSE BROADCAST FOR STAFF---
        if target_trek.assigned_staff_id:
            sse.publish(
                {
                    "message": f"A new participant booked your trek: {target_trek.name}!",
                    "trek_id": target_trek.id,
                    "new_available_slots": target_trek.available_slots
                },
                type=f"staff_alert_{target_trek.assigned_staff_id}"
            )

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
            "duration": trek.duration,
            "status": trek.status
        })

    return jsonify({
        "total_bookings": len(results),
        "bookings": results
    }), 200

@app.route('/trekker/booking/<int:booking_id>', methods=['DELETE'])
@role_required(['trekker'])
def cancel_booking(booking_id):
    user_id = int(get_jwt_identity())

    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify({"msg": "Booking not found"}), 404

    if booking.user_id != user_id:
        return jsonify({"msg": "Unauthorized: You can only cancel your own bookings."}), 403

    if booking.status == 'Cancelled':
        return jsonify({"msg": "This booking is already cancelled."}), 400

    trek = booking.trek

    if trek.status in ['Completed', 'Cancelled']:
        return jsonify({"msg": f"Action Denied: This trek is already {trek.status}."}), 400

    booking.status = 'Cancelled'

    trek.available_slots += 1

    try:
        db.session.commit()

        # --- CACHE INVALIDATION ---
        cache.clear()
        cache.delete_memoized('get_trek_participants', trek.id) # <-- NEW: Keep staff rosters accurate!

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error occured during cancellation."}), 500

    return jsonify({
        "msg": f"Successfully cancelled your booking for '{trek.name}'.",
        "trek_id": trek.id,
        "new_available_slots": trek.available_slots,
        "booking_status": booking.status
    }), 200

@app.route('/trekker/export-history', methods=['POST'])
@role_required(['trekker'])
def trigger_csv_export():
    user_id = int(get_jwt_identity())

    # 2. Import the task INSIDE the route 
    # (Doing this at the top of the file would cause a circular import error!)
    from tasks import export_booking_history_csv

    # Pin the ticket to the board! 
    # The .delay() command is what sends this to Redis instead of running it here .
    export_booking_history_csv.delay(user_id)

    # Immediately return to the user without waiting for the file to generate
    return jsonify({
        "msg": "Your CSV export has started in the background! We will notify you when it is ready.",
        "status": "processing"
    }), 202
# ==========================================
# STAFF ROUTES (Phase 6)
# ==========================================

@app.route('/staff/profile', methods=['PUT'])
@role_required(['staff'])
def update_staff_profile():
    user_id = int(get_jwt_identity())

    profile = StaffProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify({"msg": "Profile not found"}), 404

    data = request.get_json()

    if 'name' in data:
        profile.name = data['name']
    if 'contact_details' in data:
        profile.contact_details = data['contact_details']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error occured while updating profile."}), 500

    return jsonify({
        "msg": "Profile updated successfully!",
        "name": profile.name,
        "contact_details": profile.contact_details
    }), 200

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
        cache.clear()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error occurred."}), 500
        
    return jsonify({
        "msg": f"Successfully updated trek status to {new_status}",
        "trek_id": trek.id,
        "new_status": trek.status
    }), 200

@app.route('/staff/trek/<int:trek_id>/slots', methods=['PUT'])
@role_required(['staff'])
def update_trek_slot(trek_id):
    data = request.get_json()
    new_slots = data.get('available_slots')

    if new_slots is None or not isinstance(new_slots, int) or new_slots < 0:
        return jsonify({"msg": "Please provide a valid 'available_slots' integer (0 or greater)."}), 400

    staff_id = int(get_jwt_identity())

    trek = Trek.query.get(trek_id)

    if not trek:
        return jsonify({"msg": "Trek not found."}), 404

    if trek.assigned_staff_id != staff_id:
        return jsonify({"msg": "Unauthorized: You dont have the permission to modify this trek's inventory."}), 403

    trek.available_slots = new_slots

    try:
        db.session.commit()
        cache.clear()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error occured."}), 500

    return jsonify({
        "msg": f"Successfully updated inventory. {new_slots} slots are now available.",
        "trek_id": trek.id,
        "new_available_slots": trek.available_slots
    }), 200

@app.route('/staff/trek/<int:trek_id>/participants', methods=['GET'])
@role_required(['staff'])
@cache.memoize(timeout=300) # <-- Caches this specific trek's roster for 5 minutes
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

# ==========================================
#  SSE BLUEPRINT (Phase 8 - Radio Tower)
# ==========================================
app.register_blueprint(sse, url_prefix='/stream')

# Start the local development server
if __name__ == '__main__':
    app.run(debug=True)
