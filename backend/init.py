from app import app
from models import db, User, Trek, StaffProfile, TrekkerProfile, Booking
from werkzeug.security import generate_password_hash
from datetime import date

def seed_database():
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")

        # 2. Inject Admin
        if not User.query.filter_by(email='admin@tma.com').first():
            admin = User(email='admin@tma.com', password=generate_password_hash('admin123'), role='admin', is_active=True)
            db.session.add(admin)
            print("✅ Admin account injected.")

        # 3. Inject Trekkers 
        if not User.query.filter_by(email='explorer_amit@gmail.com').first():
            trekker1 = User(email='explorer_amit@gmail.com', password=generate_password_hash('amit123'), role='trekker', is_active=True)
            trekker2 = User(email='piyush.dev@gmail.com', password=generate_password_hash('piyush123'), role='trekker', is_active=True)
            db.session.add_all([trekker1, trekker2])
            db.session.flush()

            t_profile1 = TrekkerProfile(user_id=trekker1.id, name='Amit Patel', contact_details='+91 9988776655', emergency_contact='Brother: +91 9988112233')
            t_profile2 = TrekkerProfile(user_id=trekker2.id, name='Piyush Maharana', contact_details='+91 8877665544', emergency_contact='Father: Raj Kumar Maharana')
            db.session.add_all([t_profile1, t_profile2])
            print("✅ Trekkers (Amit & Piyush) added.")

        # 4. Inject Staff
        if not User.query.filter_by(email='guide_rohit@tma.com').first():
            staff1 = User(email='guide_rohit@tma.com', password=generate_password_hash('staff123'), role='staff', is_active=True)
            staff2 = User(email='guide_sarah@tma.com', password=generate_password_hash('staff123'), role='staff', is_active=True)
            db.session.add_all([staff1, staff2])
            db.session.flush()

            s_profile1 = StaffProfile(user_id=staff1.id, name='Rohit Sharma', contact_details='+91 7766554433')
            s_profile2 = StaffProfile(user_id=staff2.id, name='Sarah Connor', contact_details='+91 6655443322')
            db.session.add_all([s_profile1, s_profile2])
            print("✅ Staff members added.")

        # 5. Inject Treks
        if Trek.query.count() == 0:
            s1 = User.query.filter_by(email='guide_rohit@tma.com').first()
            s2 = User.query.filter_by(email='guide_sarah@tma.com').first()

            trek1 = Trek(name='Kashmir Great Lakes Trek', location='Jammu & Kashmir', difficulty='Hard', duration=7, available_slots=14, start_date=date(2026, 8, 10), end_date=date(2026, 8, 17), assigned_staff_id=s1.id, status='Approved')
            trek2 = Trek(name='Valley of Flowers Trek', location='Uttarakhand', difficulty='Moderate', duration=5, available_slots=20, start_date=date(2026, 8, 29), end_date=date(2026, 9, 2), assigned_staff_id=s2.id, status='Approved')
            trek3 = Trek(name='Leh Ladakh', location='Leh', difficulty='Hard', duration=7, available_slots=15, start_date=date(2026, 8, 13), end_date=date(2026, 8, 20), assigned_staff_id=None, status='Pending')
            db.session.add_all([trek1, trek2, trek3])
            print("✅ Treks added.")

        # 6. Inject a Booking (Amit booking Kashmir)
        if Booking.query.count() == 0:
            t1 = User.query.filter_by(email='explorer_amit@gmail.com').first()
            tr1 = Trek.query.filter_by(name='Kashmir Great Lakes Trek').first()
            
            # Using the new 'status' field you added to models.py!
            b1 = Booking(user_id=t1.id, trek_id=tr1.id, status='Confirmed') 
            db.session.add(b1)
            print("✅ Initial booking created.")

        db.session.commit()
        print("🚀 Database seeding complete! You can now run app.py")

if __name__ == '__main__':
    seed_database()