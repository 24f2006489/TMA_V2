from flask import Flask, request, jsonify
from models import db, User, Trek, StaffProfile, Booking
from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, 
    get_jwt, current_user, verify_jwt_in_request
)

from functools import wraps

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

@app.route('/admin-dashboard', methods=['GET', 'POST'])
@role_required(['admin'])
def test_admin_dashboard():
    return jsonify({
        "msg": f"Welcome to the highly secure Admin Dashboard, {current_user.email}!"
    }), 200



# Start the local development server
if __name__ == '__main__':
    app.run(debug=True)
