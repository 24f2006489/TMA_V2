from flask import Flask
from models import db, User, Trek, StaffProfile, Booking
from werkzeug.security import generate_password_hash

# Initialize the Flask application
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tma_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super_secret_key_for_viva' # We will need this later for login tokens

# Connect the SQLAlchemy tools to this specific app
db.init_app(app)

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


# Start the local development server
if __name__ == '__main__':
    app.run(debug=True)
