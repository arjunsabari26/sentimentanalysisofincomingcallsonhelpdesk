import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.utils import secure_filename
from models import db, User, CallRecord
from utils import analyze_audio
from datetime import datetime
import csv
import io
from flask_mail import Mail, Message

def generate_response(sentiment):
    if sentiment == 'Positive':
        return "Thank you for your positive feedback. We are glad that your issue has been resolved and that you are satisfied with our service. If you need any further assistance, please feel free to contact us anytime."
    elif sentiment == 'Neutral':
        return "Thank you for contacting our support team. We appreciate your feedback and will continue working to improve our services. If you have any further questions or concerns, please let us know and we will be happy to assist you."
    elif sentiment == 'Negative':
        return "We sincerely apologize for the inconvenience you experienced. Your concern is very important to us and our support team will prioritize resolving the issue as quickly as possible. Thank you for bringing this to our attention."
    return ""

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'super_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)

# Flask-Mail configuration (Loaded from .env)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')

mail = Mail(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@helpdesk.com').first():
        admin_user = User(email='admin@helpdesk.com', password=generate_password_hash('password'), role='admin')
        db.session.add(admin_user)
        db.session.commit()
    if not User.query.filter_by(email='agent@helpdesk.com').first():
        agent_user = User(email='agent@helpdesk.com', password=generate_password_hash('password'), role='agent')
        db.session.add(agent_user)
        db.session.commit()


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html')
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists.', 'danger')
            return render_template('signup.html')
            
        new_user = User(email=email, password=generate_password_hash(password), role='agent')
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    calls = CallRecord.query.all()
    total_calls = len(calls)
    positive_calls = sum(1 for c in calls if c.sentiment == 'Positive')
    neutral_calls = sum(1 for c in calls if c.sentiment == 'Neutral')
    negative_calls = sum(1 for c in calls if c.sentiment == 'Negative')
    
    recent_negative = CallRecord.query.filter_by(sentiment='Negative', is_read=False).order_by(CallRecord.date.desc()).first()
    
    return render_template('dashboard.html', 
                           total=total_calls, positive=positive_calls, 
                           neutral=neutral_calls, negative=negative_calls,
                           recent_negative=recent_negative)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        if 'audio_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['audio_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            analysis = analyze_audio(filepath)
            
            if analysis['success']:
                call_record = CallRecord(
                    customer_name=customer_name,
                    audio_filename=filename,
                    transcript=analysis['transcript'],
                    sentiment=analysis['sentiment'],
                    confidence=analysis['confidence'],
                    summary=analysis['summary'],
                    keywords=analysis['keywords'],
                    customer_response=generate_response(analysis['sentiment'])
                )
                db.session.add(call_record)
                db.session.commit()
                flash('Call analyzed successfully!', 'success')
                return redirect(url_for('result', call_id=call_record.id))
            else:
                flash(f"Error analyzing audio: {analysis['error']}", 'danger')
                
    return render_template('upload.html')

@app.route('/result/<int:call_id>')
@login_required
def result(call_id):
    call = CallRecord.query.get_or_404(call_id)
    if not call.is_read:
        call.is_read = True
        db.session.commit()
    return render_template('result.html', call=call)

@app.route('/transcript/<int:call_id>')
@login_required
def transcript(call_id):
    call = CallRecord.query.get_or_404(call_id)
    return render_template('transcript.html', call=call)

@app.route('/history')
@login_required
def history():
    sentiment_filter = request.args.get('sentiment')
    search_query = request.args.get('search')
    query = CallRecord.query
    if sentiment_filter:
        query = query.filter_by(sentiment=sentiment_filter)
    if search_query:
        query = query.filter(CallRecord.customer_name.contains(search_query))
    
    calls = query.order_by(CallRecord.date.desc()).all()
    return render_template('history.html', calls=calls)

@app.route('/analytics')
@login_required
def analytics():
    calls = CallRecord.query.all()
    
    # Simple logic to group calls by day of week
    daily_data = {
        'Positive': [0]*7,
        'Negative': [0]*7,
        'Neutral': [0]*7
    }
    
    for call in calls:
        day_idx = call.date.weekday() # 0 is Monday
        if call.sentiment in daily_data:
            daily_data[call.sentiment][day_idx] += 1
            
    return render_template('analytics.html', calls=calls, daily_data=daily_data)


@app.route('/download-report')
@login_required
def download_report():
    import csv
    from io import StringIO
    from flask import make_response
    
    calls = CallRecord.query.order_by(CallRecord.date.desc()).all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Customer Name', 'Sentiment', 'Confidence (%)', 'Date', 'Transcript'])
    
    for call in calls:
        cw.writerow([
            call.id,
            call.customer_name,
            call.sentiment,
            f"{call.confidence:.2f}" if call.confidence is not None else "0.00",
            call.date.strftime('%Y-%m-%d %H:%M'),
            call.transcript
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=helpdesk_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    calls = CallRecord.query.order_by(CallRecord.date.desc()).all()
    return render_template('admin.html', users=users, calls=calls)

@app.route('/export/csv')
@login_required
def export_csv():
    calls = CallRecord.query.order_by(CallRecord.date.desc()).all()
    
    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow(['Call ID', 'Customer Name', 'Sentiment', 'Confidence', 'Date', 'Transcript'])
    for c in calls:
        writer.writerow([c.id, c.customer_name, c.sentiment, c.confidence, c.date.strftime("%Y-%m-%d %H:%M:%S"), c.transcript])
    
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        as_attachment=True,
        download_name='calls_export.csv',
        mimetype='text/csv'
    )

@app.route('/save_response/<int:call_id>', methods=['POST'])
@login_required
def save_response(call_id):
    call = CallRecord.query.get_or_404(call_id)
    new_response = request.form.get('customer_response')
    if new_response:
        call.customer_response = new_response
        db.session.commit()
        return jsonify({'success': True, 'message': 'Response saved successfully!'})
    return jsonify({'success': False, 'message': 'No response content provided.'}), 400

@app.route('/send_email/<int:call_id>', methods=['POST'])
@login_required
def send_email(call_id):
    call = CallRecord.query.get_or_404(call_id)
    
    # In a real scenario, we might have the customer's email in the CallRecord
    # For now, we'll use a placeholder or the agent's email for testing
    customer_email = "customer@example.com" # Placeholder
    
    msg = Message(f'Support Response for Call #{call.id}',
                  recipients=[customer_email])
    msg.body = f"Hello {call.customer_name},\n\n{call.customer_response}\n\nBest regards,\nHelpdesk Team"
    
    try:
        mail.send(msg)
        return jsonify({'success': True, 'message': f'Response emailed to {customer_email} successfully!'})
    except Exception as e:
        print(f"ERROR Sending Customer Email: {e}")
        # Identify if it's a configuration issue
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            error_msg = "Email credentials (EMAIL_USER, EMAIL_PASS) are not set. Check your .env file."
        else:
            error_msg = f"Email sending failed: {str(e)}. Check your configuration or log for details."
            
        # Fallback to console
        print(f"DEBUG: Sending email to customer regarding call #{call.id}")
        print(f"DEBUG: Content: {call.customer_response}")
        return jsonify({
            'success': False, 
            'message': error_msg,
            'fallback': True,
            'info': 'The response was logged to the server console instead.'
        })


@app.route('/delete_call/<int:call_id>', methods=['POST'])
@login_required
def delete_call(call_id):
    call = CallRecord.query.get_or_404(call_id)
    # Also delete the associated audio file if it exists
    if call.audio_filename:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], call.audio_filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error deleting file {filepath}: {e}")
            
    db.session.delete(call)
    db.session.commit()
    flash(f'Call record #{call_id} and associated files have been deleted.', 'success')
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
