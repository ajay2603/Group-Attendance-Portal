from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import cloudinary
import cloudinary.uploader
import cv2
from dotenv import load_dotenv
from .main import upload_and_recognize  # Import the function from main.py

# Initialize Flask app
app = Flask(__name__)

load_dotenv()
# Configure PostgreSQL database
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Define AttendanceRecord model
class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    teacher = db.Column(db.String(100), nullable=False)
    recognized_names = db.Column(db.Text, nullable=False)  # Store as comma-separated string
    image_url = db.Column(db.String(500), nullable=False)  # Cloudinary URL
    count = db.Column(db.Integer, nullable=False)

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Failed. Check your username and password.')
    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Dashboard route
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.name)

# Upload route
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'})
        
        if file:
            # Read the image file
            file_bytes = file.read()

            # Process the image and get recognized names
            recognized_names, processed_image = upload_and_recognize(file_bytes)

            # Upload the processed image to Cloudinary
            _, processed_image_bytes = cv2.imencode('.jpg', processed_image)
            processed_upload_result = cloudinary.uploader.upload(processed_image_bytes.tobytes())
            processed_image_url = processed_upload_result['secure_url']

            # Save to PostgreSQL database
            new_record = AttendanceRecord(
                date=request.form.get('date'),
                class_name=request.form.get('class'),
                subject=request.form.get('subject'),
                teacher=request.form.get('teacher'),
                recognized_names=','.join(recognized_names),
                image_url=processed_image_url,
                count=len(recognized_names)
            )
            db.session.add(new_record)
            db.session.commit()

            return jsonify({
                'success': True,
                'names': recognized_names,
                'count': len(recognized_names),
                'processed_image': processed_image_url
            })
        
        return jsonify({'success': False, 'error': 'File upload failed'})
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)})

# Reset route
@app.route('/reset', methods=['POST'])
@login_required
def reset():
    try:
        # Get parameters from the request
        data = request.get_json()  # Parse JSON data from the request
        date = data.get('date')
        class_name = data.get('class')
        subject = data.get('subject')
        teacher = data.get('teacher')

        # Fetch records matching the parameters
        records = AttendanceRecord.query.filter(
            AttendanceRecord.date == date,
            AttendanceRecord.class_name == class_name,
            AttendanceRecord.subject == subject,
            AttendanceRecord.teacher == teacher
        ).all()

        # Delete associated images from Cloudinary and records from the database
        for record in records:
            if record.image_url:
                # Extract public ID from the Cloudinary URL
                public_id = record.image_url.split('/')[-1].split('.')[0]
                cloudinary.uploader.destroy(public_id)  # Delete image from Cloudinary
            db.session.delete(record)  # Delete record from the database

        db.session.commit()
        return jsonify({'success': True, 'message': 'Reset successful!'})
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/resetall', methods=['POST'])
@login_required
def resetall():
    try:
        # Fetch all records from the database
        records = AttendanceRecord.query.all()

        # Delete all associated images from Cloudinary and records from the database
        for record in records:
            if record.image_url:
                # Extract public ID from the Cloudinary URL
                public_id = record.image_url.split('/')[-1].split('.')[0]
                cloudinary.uploader.destroy(public_id)  # Delete image from Cloudinary
            db.session.delete(record)  # Delete record from the database

        db.session.commit()
        return jsonify({'success': True, 'message': 'Reset All successful!'})
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)})

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)