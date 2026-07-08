import csv
import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from celery_worker import celery_app
from models import db, User, Booking, Trek
from flask_sse import sse

# The @celery_app.task decorator is the magic wand that turns this normal 
# Python function into a "Background Task" that Redis can queue.
@celery_app.task
def export_booking_history_csv(user_id, is_admin=False):
    # 1. We add an artificial 5-second delay to simulate heavy processing.
    # This proves that Flask won't freeze while this is running!
    print(f"Chef is starting the CSV export for User {user_id}...")
    time.sleep(5) 

    # 2. Fetch the user and their bookings
    user = User.query.get(user_id)
    if not user:
        return "Error: User not found."

    bookings = Booking.query.filter_by(user_id=user_id).all()

    # 3. Setup a dedicated 'exports' folder inside a 'static' directory
    # os.makedirs ensures the folder is created if it doesn't exist yet
    export_dir = os.path.join('static', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # 4. Generate a unique filename using a timestamp so files don't overwrite each other
    filename = f"booking_history_user_{user_id}_{int(time.time())}.csv"
    filepath = os.path.join(export_dir, filename)

    # 5. Build the CSV File
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write the Header Row exactly as requested in your project documentation
        writer.writerow(['User ID', 'Trek Name', 'Location', 'Booking Status', 'Start Date', 'End Date'])

        # Write the Data Rows
        for b in bookings:
            trek = b.trek
            writer.writerow([
                user.id,
                trek.name,
                trek.location,
                b.status,
                trek.start_date.strftime('%Y-%m-%d'),
                trek.end_date.strftime('%Y-%m-%d')
            ])
    filepath_url = f"/static/exports/{filename}"

    if is_admin:
        sse.publish(
            {
                "message": f"CSV export for Trekker #{user_id} is ready!",
                "link": filepath_url
            },
            type="admin_toast" 
        )
    else:
        # SILENT PING: Just tell the Trekker's table to refresh!
        sse.publish({"message": "refresh_table"}, type=f"trekker_export_{user_id}") # <-- THIS IS THE MAGIC SHIELD
                    #By adding that type argument, the backend isn't just screaming into the void.
                    # It is putting a strict label on the message
                    # If Piyush (User ID: 2) asks for a CSV, 
                    # the message goes out labeled specifically as csv_ready_2
        
    print(f"Chef finished! File saved as {filename}. Table refresh ping sent!")
    return filepath_url

# ==========================================
#  CORE EMAIL FUNCTION
# ==========================================

def send_email(to_address, subject, message, content_type="plain"):
    msg = MIMEMultipart()
    msg['To'] = to_address
    msg['From'] = 'admin@tma.com'
    msg['Subject'] = subject

    if content_type == 'html':
        msg.attach(MIMEText(message, 'html'))
    else:
        msg.attach(MIMEText(message, 'plain'))

    # The Try-Except block acts as our error radar
    try:
        with smtplib.SMTP(host='localhost', port=1025) as server:
            server.send_message(msg)
        print(f"✅ Successfully handed off email to MailHog for {to_address}!")
    except Exception as e:
        print(f"❌ Failed to connect to MailHog. Is it running? Error: {e}")

# ==========================================
#  SCHEDULED TASKS (Celery Beat)
# ==========================================

@celery_app.task
def send_daily_reminders():
    print("⏰ Clock-Watcher triggered the Daily Reminder Task!")

    trekkers = User.query.filter_by(role='trekker').all()
    emails_sent = 0
    
    for trekker in trekkers:
        if not trekker.is_active:
            continue
            
        active_bookings = Booking.query.filter_by(user_id=trekker.id, status='Confirmed').all()
        
        if active_bookings:
            profile = trekker.trekker_profile
            name = profile.name if profile else "Explorer"
            
            email_body = f"Hello {name},\n\nThis is your daily reminder from TMA! You have {len(active_bookings)} upcoming trek(s) confirmed.\n\n"
            for b in active_bookings:
                email_body += f"- {b.trek.name} starting on {b.trek.start_date}\n"
                
            email_body += "\nStay safe and keep exploring!"
            
            send_email(
                to_address=trekker.email,
                subject="🏕️ Your TMA Daily Trekking Reminder",
                message=email_body
            )
            emails_sent += 1
            
    return f"Daily reminders successfully sent to {emails_sent} trekkers via email!"

@celery_app.task
def send_monthly_report():
    print("📊 Clock-Watcher triggered the Monthly Admin Report!")

    total_trekkers = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    active_treks = Trek.query.filter(Trek.status.in_(['Open', 'Approved'])).count()
    total_bookings = Booking.query.count()

    html_report = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    TMA Monthly Operations Report
                </h2>
                <p>Hello Admin,</p>
                <p>Here is the automated summary of your platform's current status:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Registered Trekkers</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{total_trekkers}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Staff Members</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{total_staff}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Active Treks (Open/Approved)</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{active_treks}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Global Bookings</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{total_bookings}</td>
                    </tr>
                </table>
                
                <p style="margin-top: 30px; font-size: 0.9em; color: #7f8c8d;">
                    This is an automatically generated system report. Do not reply to this email.
                </p>
            </div>
        </body>
    </html>
    """

    admin_email = "admin@tma.com"

    print("📈 Sending HTML report to Admin...")

    # SAVE TO DISK FOR THE ADMIN DASHBOARD
    #==============================================================
    report_dir = os.path.join('static', 'reports')
    os.makedirs(report_dir, exist_ok=True)
    # Save the file with a timestamp so they pile up historically
    filename = f"monthly_report_{int(time.time())}.html"
    filepath = os.path.join(report_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_report)
    print(f"💾 Report saved to archive: {filepath}")
    # ==============================================================
    send_email(
        to_address=admin_email,
        subject="📊 TMA Monthly Operations Report",
        message=html_report,
        content_type="html"
    )

    return "Monthly report generated and sent successfully."

@celery_app.task
def send_sse_heartbeat():
    # This sends a tiny, invisible pulse through the radio tower.
    # Because the 'type' is 'heartbeat', the Vue frontend will completely ignore it,
    # but the physical connection will remain permanently open!
    sse.publish({"status": "alive"}, type="heartbeat")
    return "Heartbeat pulse sent."