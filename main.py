
"""
REPORT SHOT - Professional Content Reporting System
Developed by Sabit AI
Run: python app.py
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'report-shot-secure-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reportshot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Bad words detection
BAD_WORDS = ['hate', 'spam', 'scam', 'fraud', 'cheat', 'kill', 'violent', 'abuse', 'harass', 'threat']

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reporter_name = db.Column(db.String(100), nullable=False)
    reported_item = db.Column(db.String(200), nullable=False)
    item_type = db.Column(db.String(50), default='user')
    reason = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='other')
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.String(20), default='medium')
    flagged = db.Column(db.Boolean, default=False)
    admin_notes = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# HTML Template
def render_page(title, content):
    # Navigation based on user session
    nav_html = ""
    if 'user_id' in session:
        username = session.get('username', 'User')
        nav_html = f'''
        <a href="/dashboard" class="nav-link"><i class="fas fa-home"></i> Dashboard</a>
        <a href="/submit" class="nav-link"><i class="fas fa-flag"></i> New Report</a>
        <a href="/reports" class="nav-link"><i class="fas fa-list"></i> My Reports</a>
        '''
        if session.get('is_admin'):
            nav_html += '<a href="/admin" class="nav-link admin-btn"><i class="fas fa-crown"></i> Admin Panel</a>'
        nav_html += f'<a href="/profile" class="nav-link"><i class="fas fa-user"></i> {username}</a>'
        nav_html += '<a href="/logout" class="nav-link logout-btn"><i class="fas fa-sign-out-alt"></i> Logout</a>'
    else:
        nav_html = '''
        <a href="/" class="nav-link"><i class="fas fa-home"></i> Home</a>
        <a href="/about" class="nav-link"><i class="fas fa-info-circle"></i> About</a>
        <a href="/login" class="nav-link"><i class="fas fa-sign-in-alt"></i> Login</a>
        <a href="/register" class="nav-link register-btn"><i class="fas fa-user-plus"></i> Register</a>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | REPORT SHOT</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary: #4361ee;
            --primary-dark: #3a56d4;
            --secondary: #7209b7;
            --success: #4cc9f0;
            --danger: #f72585;
            --warning: #f8961e;
            --sabit-ai: #00c9ff;
            --dark: #212529;
            --light: #f8f9fa;
            --gray: #6c757d;
            --gray-light: #e9ecef;
            --border: #dee2e6;
            --shadow: 0 4px 12px rgba(0,0,0,0.08);
            --radius: 12px;
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Inter',sans-serif; background:#f5f7fa; color:var(--dark); line-height:1.6; }}
        .container {{ max-width:1400px; margin:0 auto; padding:0 20px; }}
        
        /* Header */
        .header {{ background:white; box-shadow:var(--shadow); padding:15px 0; position:sticky; top:0; z-index:1000; }}
        .header-content {{ display:flex; justify-content:space-between; align-items:center; }}
        .logo-container {{ display:flex; align-items:center; gap:15px; }}
        .logo-icon {{ width:50px; height:50px; background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); border-radius:12px; display:flex; align-items:center; justify-content:center; color:white; font-size:24px; font-weight:bold; }}
        .logo-text {{ display:flex; flex-direction:column; }}
        .logo {{ font-family:'Poppins',sans-serif; font-size:28px; font-weight:700; background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
        .tagline {{ font-size:14px; color:var(--gray); }}
        .nav {{ display:flex; gap:15px; align-items:center; }}
        .nav-link {{ text-decoration:none; color:var(--dark); font-weight:500; padding:8px 16px; border-radius:8px; transition:all 0.3s; display:flex; align-items:center; gap:8px; }}
        .nav-link:hover {{ background:var(--gray-light); color:var(--primary); }}
        .register-btn {{ background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); color:white !important; }}
        .logout-btn {{ background:var(--danger); color:white !important; }}
        .admin-btn {{ background:linear-gradient(135deg,var(--warning) 0%,#ff9a3c 100%); color:white !important; }}
        
        /* Hero */
        .hero {{ background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); color:white; padding:80px 0; text-align:center; margin-bottom:60px; border-radius:0 0 var(--radius) var(--radius); }}
        .hero h1 {{ font-size:48px; font-weight:700; margin-bottom:20px; }}
        
        /* Cards */
        .card {{ background:white; border-radius:var(--radius); padding:30px; margin-bottom:30px; box-shadow:var(--shadow); }}
        .card-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:25px; padding-bottom:15px; border-bottom:2px solid var(--gray-light); }}
        .card-title {{ font-size:24px; font-weight:600; color:var(--dark); }}
        
        /* Forms */
        .form-group {{ margin-bottom:25px; }}
        .form-label {{ display:block; margin-bottom:8px; font-weight:500; }}
        .form-control {{ width:100%; padding:14px; border:2px solid var(--border); border-radius:8px; font-family:'Inter',sans-serif; font-size:16px; }}
        .form-control:focus {{ outline:none; border-color:var(--primary); }}
        
        /* Buttons */
        .btn {{ display:inline-flex; align-items:center; gap:10px; padding:14px 28px; font-family:'Inter',sans-serif; font-size:16px; font-weight:600; border:none; border-radius:8px; cursor:pointer; text-decoration:none; transition:all 0.3s; }}
        .btn:hover {{ transform:translateY(-2px); box-shadow:0 8px 20px rgba(0,0,0,0.1); }}
        .btn-primary {{ background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); color:white; }}
        .btn-success {{ background:linear-gradient(135deg,#2ecc71 0%,#27ae60 100%); color:white; }}
        .btn-danger {{ background:linear-gradient(135deg,var(--danger) 0%,#e91e63 100%); color:white; }}
        .btn-secondary {{ background:var(--gray-light); color:var(--dark); }}
        .btn-sabit {{ background:linear-gradient(135deg,var(--sabit-ai) 0%,#00a8ff 100%); color:white; }}
        
        /* Alerts */
        .alert {{ padding:20px; border-radius:8px; margin-bottom:25px; display:flex; align-items:center; gap:15px; }}
        .alert-success {{ background:rgba(76,201,240,0.1); border-left:4px solid var(--success); color:#036; }}
        .alert-danger {{ background:rgba(247,37,133,0.1); border-left:4px solid var(--danger); color:#800; }}
        .alert-warning {{ background:rgba(248,150,30,0.1); border-left:4px solid var(--warning); color:#854; }}
        
        /* Tables */
        .table-container {{ overflow-x:auto; border-radius:8px; box-shadow:var(--shadow); }}
        table {{ width:100%; border-collapse:collapse; background:white; }}
        th {{ background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); color:white; padding:18px; text-align:left; }}
        td {{ padding:16px; border-bottom:1px solid var(--border); }}
        tr:hover {{ background:rgba(67,97,238,0.05); }}
        
        /* Badges */
        .badge {{ display:inline-block; padding:6px 12px; border-radius:20px; font-size:12px; font-weight:600; }}
        .badge-pending {{ background:rgba(248,150,30,0.1); color:var(--warning); border:1px solid var(--warning); }}
        .badge-approved {{ background:rgba(76,201,240,0.1); color:var(--success); border:1px solid var(--success); }}
        .badge-rejected {{ background:rgba(247,37,133,0.1); color:var(--danger); border:1px solid var(--danger); }}
        .badge-under-review {{ background:rgba(67,97,238,0.1); color:var(--primary); border:1px solid var(--primary); }}
        .badge-flagged {{ background:rgba(247,37,133,0.2); color:var(--danger); border:1px dashed var(--danger); }}
        
        /* Stats */
        .stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:25px; margin-bottom:40px; }}
        .stat-card {{ background:white; padding:30px; border-radius:var(--radius); box-shadow:var(--shadow); text-align:center; }}
        .stat-number {{ font-size:48px; font-weight:700; background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
        .stat-label {{ font-size:16px; color:var(--gray); }}
        
        /* Auth */
        .auth-container {{ max-width:500px; margin:80px auto; }}
        .auth-card {{ background:white; padding:50px; border-radius:var(--radius); box-shadow:var(--shadow); }}
        
        /* Footer */
        .footer {{ background:var(--dark); color:white; padding:60px 0 30px; margin-top:80px; }}
        .footer-content {{ display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:40px; }}
        .footer-section {{ flex:1; min-width:250px; }}
        
        /* Profile */
        .profile-avatar {{ width:120px; height:120px; background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:48px; font-weight:bold; margin:0 auto 20px; }}
        
        @media (max-width:768px) {{
            .hero h1 {{ font-size:36px; }}
            .stats-grid {{ grid-template-columns:1fr; }}
            .auth-card {{ padding:30px; }}
            .nav {{ flex-direction:column; align-items:flex-start; }}
            .footer-content {{ flex-direction:column; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo-container">
                    <div class="logo-icon">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <div class="logo-text">
                        <h1 class="logo">REPORT SHOT</h1>
                        <p class="tagline">Powered by Sabit AI</p>
                    </div>
                </div>
                <nav class="nav">
                    {nav_html}
                </nav>
            </div>
        </div>
    </header>

    <main class="main-content">
        <div class="container">
            {content}
        </div>
    </main>

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
                        <div style="width:40px; height:40px; background:linear-gradient(135deg,var(--primary) 0%,var(--sabit-ai) 100%); border-radius:8px; display:flex; align-items:center; justify-content:center; color:white;">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <div>
                            <h3 style="font-size:20px; margin:0;">REPORT SHOT</h3>
                            <p style="color:var(--gray-light); font-size:12px; margin:0;">Professional Reporting System</p>
                        </div>
                    </div>
                    <p style="color:var(--gray-light); margin-bottom:20px;">Advanced content reporting platform for safer online communities.</p>
                    <div style="background:rgba(0,201,255,0.1); padding:10px 20px; border-radius:20px; display:inline-flex; align-items:center; gap:10px;">
                        <i class="fas fa-code" style="color:var(--sabit-ai);"></i>
                        <span>Developed by <strong>Sabit AI</strong></span>
                    </div>
                </div>
                
                <div class="footer-section">
                    <h3 style="margin-bottom:20px;">Quick Links</h3>
                    <div style="display:flex; flex-direction:column; gap:10px;">
                        <a href="/" style="color:var(--gray-light); text-decoration:none;"><i class="fas fa-home"></i> Home</a>
                        <a href="/about" style="color:var(--gray-light); text-decoration:none;"><i class="fas fa-info-circle"></i> About</a>
                        <a href="/login" style="color:var(--gray-light); text-decoration:none;"><i class="fas fa-sign-in-alt"></i> Login</a>
                        <a href="/register" style="color:var(--gray-light); text-decoration:none;"><i class="fas fa-user-plus"></i> Register</a>
                    </div>
                </div>
                
                <div class="footer-section">
                    <h3 style="margin-bottom:20px;">Contact</h3>
                    <div style="display:flex; flex-direction:column; gap:10px;">
                        <p style="color:var(--gray-light);"><i class="fas fa-envelope"></i> support@reportshot.com</p>
                        <p style="color:var(--gray-light);"><i class="fas fa-phone"></i> +1 (555) 123-4567</p>
                        <p style="color:var(--gray-light);"><i class="fas fa-map-marker-alt"></i> Dhaka, Bangladesh</p>
                    </div>
                </div>
                
                <div class="footer-section">
                    <h3 style="margin-bottom:20px;">Powered By</h3>
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
                        <div style="width:50px; height:50px; background:linear-gradient(135deg,var(--sabit-ai) 0%,#00a8ff 100%); border-radius:10px; display:flex; align-items:center; justify-content:center; color:white; font-size:24px;">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div>
                            <h4 style="margin:0; color:white;">Sabit AI</h4>
                            <p style="color:var(--gray-light); font-size:12px; margin:0;">Artificial Intelligence Solutions</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="border-top:1px solid rgba(255,255,255,0.1); margin-top:40px; padding-top:20px; text-align:center; color:var(--gray-light); font-size:14px;">
                <p>© 2024 REPORT SHOT. All rights reserved. | Developed by Sabit AI Team</p>
            </div>
        </div>
    </footer>

    <script>
        function updateStatus(reportId, status) {{
            if(!confirm('Are you sure?')) return;
            fetch('/admin/update_report', {{
                method:'POST',
                headers:{{'Content-Type':'application/json'}},
                body:JSON.stringify({{report_id:reportId, status:status}})
            }})
            .then(r=>r.json())
            .then(data=>{{
                if(data.success) location.reload();
                else alert('Error: ' + data.error);
            }});
        }}
        
        function showNotes(reportId) {{
            const notes = prompt('Enter admin notes:');
            if(notes !== null) {{
                fetch('/admin/add_notes', {{
                    method:'POST',
                    headers:{{'Content-Type':'application/json'}},
                    body:JSON.stringify({{report_id:reportId, notes:notes}})
                }})
                .then(r=>r.json())
                .then(data=>{{
                    if(data.success) location.reload();
                    else alert('Error: ' + data.error);
                }});
            }}
        }}
    </script>
</body>
</html>'''

# Initialize Database
def init_database():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='admin').first():
            print("🔧 Creating admin user...")
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@reportshot.com',
                password_hash=generate_password_hash('Admin@123'),
                is_admin=True,
                is_active=True
            )
            db.session.add(admin_user)
            
            # Create regular user
            regular_user = User(
                username='john',
                email='john@example.com',
                password_hash=generate_password_hash('User@123'),
                is_admin=False,
                is_active=True
            )
            db.session.add(regular_user)
            
            # Create sample reports
            sample_reports = [
                Report(
                    reporter_id=2,
                    reporter_name='john',
                    reported_item='user123',
                    reason='Spamming messages in chat',
                    category='spam',
                    status='approved',
                    flagged=True,
                    admin_notes='Account suspended for 7 days'
                ),
                Report(
                    reporter_id=2,
                    reporter_name='john',
                    reported_item='post456',
                    reason='Hate speech in comments',
                    category='hate',
                    status='pending',
                    flagged=True
                ),
                Report(
                    reporter_id=2,
                    reporter_name='john',
                    reported_item='user789',
                    reason='Suspicious account behavior',
                    category='other',
                    status='under_review',
                    flagged=False
                )
            ]
            
            for report in sample_reports:
                db.session.add(report)
            
            db.session.commit()
            print("✅ Database initialized successfully!")
            print("👑 Admin: admin / Admin@123")
            print("👤 User: john / User@123")

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    
    content = '''
    <section class="hero">
        <div class="container">
            <h1>Welcome to REPORT SHOT</h1>
            <p>Professional content reporting platform powered by Sabit AI. Submit reports, track status, and help maintain a safe community.</p>
            <div style="display:flex; gap:20px; justify-content:center; margin-top:40px; flex-wrap:wrap;">
                <a href="/register" class="btn btn-primary" style="padding:16px 40px; font-size:18px;">
                    <i class="fas fa-user-plus"></i> Get Started Free
                </a>
                <a href="/login" class="btn btn-secondary" style="padding:16px 40px; font-size:18px;">
                    <i class="fas fa-sign-in-alt"></i> Sign In
                </a>
            </div>
        </div>
    </section>
    
    <section style="text-align:center; margin-bottom:60px;">
        <h2 style="font-size:36px; margin-bottom:20px;">Why Choose Report Shot?</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <i class="fas fa-shield-alt" style="font-size:48px; color:#4361ee; margin-bottom:20px;"></i>
                <h3 style="margin-bottom:10px;">Secure Reporting</h3>
                <p style="color:#6c757d;">AI-powered security with encrypted reports</p>
            </div>
            <div class="stat-card">
                <i class="fas fa-bolt" style="font-size:48px; color:#4cc9f0; margin-bottom:20px;"></i>
                <h3 style="margin-bottom:10px;">Fast Response</h3>
                <p style="color:#6c757d;">AI-assisted review within 24 hours</p>
            </div>
            <div class="stat-card">
                <i class="fas fa-robot" style="font-size:48px; color:#00c9ff; margin-bottom:20px;"></i>
                <h3 style="margin-bottom:10px;">Sabit AI</h3>
                <p style="color:#6c757d;">Powered by advanced AI technology</p>
            </div>
        </div>
    </section>
    '''
    return render_template_string(render_page("Home", content))

@app.route('/about')
def about():
    content = '''
    <section class="hero">
        <div class="container">
            <h1>About REPORT SHOT</h1>
            <p>Professional Content Reporting System powered by Sabit AI</p>
        </div>
    </section>
    
    <div class="card" style="margin-top:40px;">
        <div class="card-header">
            <h2 class="card-title"><i class="fas fa-info-circle"></i> Our Mission</h2>
        </div>
        <p style="font-size:18px; color:#6c757d; margin-bottom:20px;">
            REPORT SHOT is designed to create safer online communities through an advanced, AI-powered reporting system. 
            We combine cutting-edge technology with user-friendly design to make content moderation efficient and effective.
        </p>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title"><i class="fas fa-users"></i> Development Team</h2>
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:30px; margin:20px 0;">
            <div style="text-align:center; padding:30px; border:1px solid #dee2e6; border-radius:12px;">
                <div class="profile-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <h3 style="margin-bottom:10px;">Sabit AI</h3>
                <p style="color:#6c757d; margin-bottom:15px;">Lead AI Developer</p>
                <p>Advanced AI algorithms, machine learning models, and intelligent automation systems.</p>
            </div>
            
            <div style="text-align:center; padding:30px; border:1px solid #dee2e6; border-radius:12px;">
                <div class="profile-avatar">
                    <i class="fas fa-code"></i>
                </div>
                <h3 style="margin-bottom:10px;">Development Team</h3>
                <p style="color:#6c757d; margin-bottom:15px;">Full Stack Developers</p>
                <p>Backend systems, database architecture, API development, and system integration.</p>
            </div>
        </div>
    </div>
    '''
    return render_template_string(render_page("About Us", content))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect('/dashboard')
    
    flash_html = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash_html = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> All fields are required!</div>'
        elif password != confirm_password:
            flash_html = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Passwords do not match!</div>'
        elif User.query.filter_by(username=username).first():
            flash_html = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Username already exists!</div>'
        elif User.query.filter_by(email=email).first():
            flash_html = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Email already registered!</div>'
        else:
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_admin=False,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect('/dashboard')
    
    content = f'''
    <div class="auth-container">
        <div class="auth-card">
            <div style="text-align:center; margin-bottom:40px;">
                <div style="width:80px; height:80px; background:linear-gradient(135deg,#4361ee 0%,#00c9ff 100%); border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; color:white; font-size:32px;">
                    <i class="fas fa-user-plus"></i>
                </div>
                <h1 style="font-size:32px; font-weight:700; margin-bottom:10px; background:linear-gradient(135deg,#4361ee 0%,#00c9ff 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Create Account</h1>
                <p style="color:#6c757d;">Join REPORT SHOT today</p>
            </div>
            {flash_html}
            <form method="POST">
                <div class="form-group">
                    <label class="form-label"><i class="fas fa-user"></i> Username</label>
                    <input type="text" name="username" class="form-control" placeholder="Enter username" required>
                </div>
                <div class="form-group">
                    <label class="form-label"><i class="fas fa-envelope"></i> Email Address</label>
                    <input type="email" name="email" class="form-control" placeholder="Enter email" required>
                </div>
                <div class="form-group">
                    <label class="form-label"><i class="fas fa-lock"></i> Password</label>
                    <input type="password" name="password" class="form-control" placeholder="Create password" required>
                </div>
                <div class="form-group">
                    <label class="form-label"><i class="fas fa-lock"></i> Confirm Password</label>
                    <input type="password" name="confirm_password" class="form-control" placeholder="Confirm password" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%; margin-top:20px;">
                    <i class="fas fa-user-plus"></i> Create Account
                </button>
            </form>
            <div style="text-align:center; margin-top:30px;">
                <p style="color:#6c757d;">Already have an account? <a href="/login" style="color:#4361ee; font-weight:600;">Sign In</a></p>
            </div>
        </div>
    </div>
    '''
    return render_template_string(render_page("Register", content))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/dashboard')
    
    flash_html = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash_html = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Account is deactivated!</div>'
            else:
                session['user_id'] = user.id
                session['username'] = user.username
                session['is_admin'] = user.is_admin
                return redirect('/dashboard')
        else:
            flash_html = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Invalid username or password!</div>'
    
    content = f'''
    <div class="auth-container">
        <div class="auth-card">
            <div style="text-align:center; margin-bottom:40px;">
                <div style="width:80px; height:80px; background:linear-gradient(135deg,#4361ee 0%,#00c9ff 100%); border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; color:white; font-size:32px;">
                    <i class="fas fa-sign-in-alt"></i>
                </div>
                <h1 style="font-size:32px; font-weight:700; margin-bottom:10px; background:linear-gradient(135deg,#4361ee 0%,#00c9ff 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Welcome Back</h1>
                <p style="color:#6c757d;">Sign in to your account</p>
            </div>
            {flash_html}
            <form method="POST">
                <div class="form-group">
                    <label class="form-label"><i class="fas fa-user"></i> Username</label>
                    <input type="text" name="username" class="form-control" placeholder="Enter username" required>
                </div>
                <div class="form-group">
                    <label class="form-label"><i class="fas fa-lock"></i> Password</label>
                    <input type="password" name="password" class="form-control" placeholder="Enter password" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%; margin-top:20px;">
                    <i class="fas fa-sign-in-alt"></i> Sign In
                </button>
            </form>
            <div style="text-align:center; margin-top:30px;">
                <p style="color:#6c757d;">Don't have an account? <a href="/register" style="color:#4361ee; font-weight:600;">Register Now</a></p>
            </div>
            
            <div class="card" style="margin-top:30px; padding:20px;">
                <h3 style="margin-bottom:15px; color:#4361ee;"><i class="fas fa-key"></i> Demo Accounts</h3>
                <div style="background:#f8f9fa; padding:15px; border-radius:8px; margin-bottom:15px;">
                    <p style="margin-bottom:5px; font-weight:600; color:#00c9ff;">👑 Administrator</p>
                    <p style="margin:0; font-size:14px;"><strong>Username:</strong> admin</p>
                    <p style="margin:0; font-size:14px;"><strong>Password:</strong> Admin@123</p>
                </div>
                <div style="background:#f8f9fa; padding:15px; border-radius:8px;">
                    <p style="margin-bottom:5px; font-weight:600; color:#4361ee;">👤 Regular User</p>
                    <p style="margin:0; font-size:14px;"><strong>Username:</strong> john</p>
                    <p style="margin:0; font-size:14px;"><strong>Password:</strong> User@123</p>
                </div>
            </div>
        </div>
    </div>
    '''
    return render_template_string(render_page("Login", content))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_reports = Report.query.filter_by(reporter_id=session['user_id']).order_by(Report.created_at.desc()).limit(5).all()
    
    # Generate reports HTML
    reports_html = ''
    if user_reports:
        for report in user_reports:
            status_class = f'badge-{report.status.replace(" ", "-")}'
            status_text = report.status.replace('_', ' ').title()
            flag_badge = '<span class="badge badge-flagged"><i class="fas fa-flag"></i> Flagged</span>' if report.flagged else ''
            
            reports_html += f'''
            <tr>
                <td>#{report.id:04d}</td>
                <td>{report.reported_item}</td>
                <td>{report.category.title()}</td>
                <td><span class="badge {status_class}">{status_text}</span></td>
                <td>{report.created_at.strftime("%b %d, %Y")}</td>
                <td>{flag_badge}</td>
            </tr>
            '''
    else:
        reports_html = '''
        <tr>
            <td colspan="6" style="text-align:center; padding:40px; color:#6c757d;">
                <i class="fas fa-inbox" style="font-size:48px; margin-bottom:20px;"></i>
                <p>No reports submitted yet</p>
                <a href="/submit" class="btn btn-primary" style="margin-top:20px;">
                    <i class="fas fa-flag"></i> Submit Your First Report
                </a>
            </td>
        </tr>
        '''
    
    # User stats
    total_reports = Report.query.filter_by(reporter_id=session['user_id']).count()
    pending_reports = Report.query.filter_by(reporter_id=session['user_id'], status='pending').count()
    approved_reports = Report.query.filter_by(reporter_id=session['user_id'], status='approved').count()
    
    content = f'''
    <div style="margin:40px 0;">
        <h1 style="font-size:36px; margin-bottom:10px;">Welcome back, {session['username']}!</h1>
        <p style="color:#6c757d; font-size:18px;">Your reporting dashboard</p>
        {f'<div style="background:linear-gradient(135deg,#f8961e 0%,#ff9a3c 100%); color:white; padding:10px 20px; border-radius:20px; display:inline-flex; align-items:center; gap:10px; margin-top:10px;"><i class="fas fa-crown"></i> Administrator Account</div>' if session.get('is_admin') else ''}
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{total_reports}</div>
            <div class="stat-label">Total Reports</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{pending_reports}</div>
            <div class="stat-label">Pending</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{approved_reports}</div>
            <div class="stat-label">Approved</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(user_reports)}</div>
            <div class="stat-label">Recent Reports</div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title"><i class="fas fa-history"></i> Recent Reports</h2>
            <div>
                <a href="/submit" class="btn btn-primary">
                    <i class="fas fa-plus"></i> New Report
                </a>
                <a href="/reports" class="btn btn-secondary">
                    <i class="fas fa-list"></i> View All
                </a>
            </div>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Report ID</th>
                        <th>Reported Item</th>
                        <th>Category</th>
                        <th>Status</th>
                        <th>Date</th>
                        <th>Flags</th>
                    </tr>
                </thead>
                <tbody>
                    {reports_html}
                </tbody>
            </table>
        </div>
    </div>
    '''
    return render_template_string(render_page("Dashboard", content))

@app.route('/submit', methods=['GET', 'POST'])
def submit_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    flash_html = ''
    if request.method == 'POST':
        reported_item = request.form.get('reported_item')
        item_type = request.form.get('item_type')
        reason = request.form.get('reason')
        category = request.form.get('category')
        
        if not reported_item or not reason:
            flash_html = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Required fields missing!</div>'
        else:
            # Check for bad words
            flagged = any(bad_word in reason.lower() for bad_word in BAD_WORDS)
            
            report = Report(
                reporter_id=session['user_id'],
                reporter_name=session['username'],
                reported_item=reported_item,
                item_type=item_type,
                reason=reason,
                category=category,
                flagged=flagged
            )
            
            db.session.add(report)
            db.session.commit()
            
            alert_type = 'warning' if flagged else 'success'
            alert_icon = 'exclamation-triangle' if flagged else 'check-circle'
            alert_msg = 'Report submitted! (Flagged for review)' if flagged else 'Report submitted successfully!'
            
            flash_html = f'<div class="alert alert-{alert_type}"><i class="fas fa-{alert_icon}"></i> {alert_msg}</div>'
    
    content = f'''
    <div style="margin:40px 0;">
        <h1 style="font-size:36px; margin-bottom:10px;">Submit New Report</h1>
        <p style="color:#6c757d; font-size:18px;">Help us keep the community safe</p>
    </div>
    
    {flash_html}
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title"><i class="fas fa-exclamation-triangle"></i> Report Details</h2>
        </div>
        <form method="POST">
            <div class="form-group">
                <label class="form-label"><i class="fas fa-tag"></i> What are you reporting?</label>
                <select name="item_type" class="form-control">
                    <option value="user">User Account</option>
                    <option value="post">Post/Content</option>
                    <option value="comment">Comment</option>
                </select>
            </div>
            
            <div class="form-group">
                <label class="form-label"><i class="fas fa-id-card"></i> Item ID or URL *</label>
                <input type="text" name="reported_item" class="form-control" placeholder="Enter user ID, post URL, or specific identifier" required>
            </div>
            
            <div class="form-group">
                <label class="form-label"><i class="fas fa-folder"></i> Category</label>
                <select name="category" class="form-control">
                    <option value="spam">Spam</option>
                    <option value="abuse">Harassment/Abuse</option>
                    <option value="hate">Hate Speech</option>
                    <option value="other">Other</option>
                </select>
            </div>
            
            <div class="form-group">
                <label class="form-label"><i class="fas fa-comment"></i> Reason for Report *</label>
                <textarea name="reason" class="form-control" rows="6" placeholder="Please describe in detail why you are reporting this content..." required></textarea>
            </div>
            
            <div style="display:flex; gap:20px; margin-top:30px;">
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-paper-plane"></i> Submit Report
                </button>
                <a href="/dashboard" class="btn btn-secondary">
                    <i class="fas fa-times"></i> Cancel
                </a>
            </div>
        </form>
    </div>
    '''
    return render_template_string(render_page("Submit Report", content))

@app.route('/reports')
def user_reports():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_reports = Report.query.filter_by(reporter_id=session['user_id']).order_by(Report.created_at.desc()).all()
    
    reports_html = ''
    if user_reports:
        for report in user_reports:
            status_class = f'badge-{report.status.replace(" ", "-")}'
            status_text = report.status.replace('_', ' ').title()
            flag_badge = '<span class="badge badge-flagged"><i class="fas fa-flag"></i> Flagged</span>' if report.flagged else ''
            
            reports_html += f'''
            <tr>
                <td>#{report.id:04d}</td>
                <td>{report.reported_item}</td>
                <td>{report.category.title()}</td>
                <td>{report.reason[:100]}{'...' if len(report.reason) > 100 else ''}</td>
                <td><span class="badge {status_class}">{status_text}</span></td>
                <td>{report.created_at.strftime("%b %d, %Y")}</td>
                <td>{flag_badge}</td>
            </tr>
            '''
    else:
        reports_html = '''
        <tr>
            <td colspan="7" style="text-align:center; padding:40px; color:#6c757d;">
                <i class="fas fa-inbox" style="font-size:48px; margin-bottom:20px;"></i>
                <p>No reports submitted yet</p>
                <a href="/submit" class="btn btn-primary" style="margin-top:20px;">
                    <i class="fas fa-flag"></i> Submit Your First Report
                </a>
            </td>
        </tr>
        '''
    
    content = f'''
    <div style="margin:40px 0;">
        <h1 style="font-size:36px; margin-bottom:10px;">My Reports</h1>
        <p style="color:#6c757d; font-size:18px;">View all your submitted reports</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{len(user_reports)}</div>
            <div class="stat-label">Total Reports</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len([r for r in user_reports if r.status == 'pending'])}</div>
            <div class="stat-label">Pending</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len([r for r in user_reports if r.status == 'approved'])}</div>
            <div class="stat-label">Approved</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len([r for r in user_reports if r.flagged])}</div>
            <div class="stat-label">Flagged</div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title"><i class="fas fa-list"></i> All Reports</h2>
            <a href="/submit" class="btn btn-primary">
                <i class="fas fa-plus"></i> New Report
            </a>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Reported Item</th>
                        <th>Category</th>
                        <th>Reason</th>
                        <th>Status</th>
                        <th>Date</th>
                        <th>Flags</th>
                    </tr>
                </thead>
                <tbody>
                    {reports_html}
                </tbody>
            </table>
        </div>
    </div>
    '''
    return render_template_string(render_page("My Reports", content))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    user = User.query.get(session['user_id'])
    report_count = Report.query.filter_by(reporter_id=user.id).count()
    
    content = f'''
    <div style="margin:40px 0;">
        <h1 style="font-size:36px; margin-bottom:10px;">My Profile</h1>
        <p style="color:#6c757d; font-size:18px;">Manage your account settings</p>
    </div>
    
    <div style="display:flex; gap:30px; flex-wrap:wrap;">
        <div class="card" style="flex:1; min-width:300px;">
            <div class="card-header">
                <h2 class="card-title"><i class="fas fa-user"></i> Account Information</h2>
            </div>
            <div style="padding:20px 0; text-align:center;">
                <div class="profile-avatar">
                    {user.username[0].upper()}
                </div>
                <h3 style="font-size:24px; margin-bottom:5px;">{user.username}</h3>
                <p style="color:#6c757d;">{user.email}</p>
                <p style="color:#6c757d; font-size:14px; margin-bottom:30px;">Member since {user.created_at.strftime("%B %d, %Y")}</p>
                
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:20px; margin-bottom:30px;">
                    <div style="text-align:center; padding:20px; background:#f8f9fa; border-radius:8px;">
                        <div style="font-size:32px; font-weight:bold; color:#4361ee;">{report_count}</div>
                        <div style="color:#6c757d;">Reports</div>
                    </div>
                    <div style="text-align:center; padding:20px; background:#f8f9fa; border-radius:8px;">
                        <div style="font-size:32px; font-weight:bold; color:#4cc9f0;">{Report.query.filter_by(reporter_id=user.id, status='approved').count()}</div>
                        <div style="color:#6c757d;">Approved</div>
                    </div>
                </div>
                
                <div style="border-top:1px solid #dee2e6; padding-top:20px;">
                    <h4 style="margin-bottom:15px; color:#212529;">Account Type</h4>
                    <div style="display:flex; justify-content:center; gap:10px;">
                        {'<span class="badge" style="background:rgba(248,150,30,0.1);color:#f8961e;">Administrator</span>' if user.is_admin else '<span class="badge" style="background:rgba(76,201,240,0.1);color:#4cc9f0;">Standard User</span>'}
                        {'<span class="badge" style="background:rgba(76,201,240,0.1);color:#4cc9f0;">Active</span>' if user.is_active else '<span class="badge" style="background:rgba(247,37,133,0.1);color:#f72585;">Inactive</span>'}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card" style="flex:1; min-width:300px;">
            <div class="card-header">
                <h2 class="card-title"><i class="fas fa-cog"></i> Settings</h2>
            </div>
            <div style="padding:20px 0;">
                <div style="margin-bottom:30px;">
                    <h4 style="margin-bottom:15px; color:#212529;">Change Password</h4>
                    <form>
                        <div class="form-group">
                            <input type="password" class="form-control" placeholder="Current password">
                        </div>
                        <div class="form-group">
                            <input type="password" class="form-control" placeholder="New password">
                        </div>
                        <div class="form-group">
                            <input type="password" class="form-control" placeholder="Confirm new password">
                        </div>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Update Password
                        </button>
                    </form>
                </div>
                
                <div style="border-top:1px solid #dee2e6; margin-top:30px; padding-top:20px;">
                    <h4 style="margin-bottom:15px; color:#212529;"><i class="fas fa-bell"></i> Notification Settings</h4>
                    <div style="display:flex; flex-direction:column; gap:10px;">
                        <label style="display:flex; align-items:center; gap:10px;">
                            <input type="checkbox" checked>
                            <span>Email notifications for report updates</span>
                        </label>
                        <label style="display:flex; align-items:center; gap:10px;">
                            <input type="checkbox" checked>
                            <span>Weekly report summary</span>
                        </label>
                        <label style="display:flex; align-items:center; gap:10px;">
                            <input type="checkbox">
                            <span>Promotional emails</span>
                        </label>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return render_template_string(render_page("My Profile", content))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/dashboard')
    
    # Admin stats
    total_reports = Report.query.count()
    pending_reports = Report.query.filter_by(status='pending').count()
    flagged_reports = Report.query.filter_by(flagged=True).count()
    total_users = User.query.count()
    
    # Recent reports
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Generate reports HTML
    reports_html = ''
    if recent_reports:
        for report in recent_reports:
            status_class = f'badge-{report.status.replace(" ", "-")}'
            status_text = report.status.replace('_', ' ').title()
            flag_badge = '<span class="badge badge-flagged"><i class="fas fa-flag"></i></span>' if report.flagged else ''
            
            reports_html += f'''
            <tr>
                <td>#{report.id:04d}</td>
                <td>{report.reporter_name}</td>
                <td>{report.reported_item}</td>
                <td>{report.category.title()}</td>
                <td><span class="badge {status_class}">{status_text}</span>{flag_badge}</td>
                <td>{report.created_at.strftime("%b %d, %Y")}</td>
                <td>
                    <div style="display:flex; gap:5px;">
                        <button onclick="updateStatus({report.id}, 'approved')" class="btn btn-success" style="padding:6px 12px; font-size:12px;">
                            <i class="fas fa-check"></i> Approve
                        </button>
                        <button onclick="updateStatus({report.id}, 'rejected')" class="btn btn-danger" style="padding:6px 12px; font-size:12px;">
                            <i class="fas fa-times"></i> Reject
                        </button>
                    </div>
                </td>
            </tr>
            '''
    
    # Users HTML
    users_html = ''
    if recent_users:
        for user in recent_users:
            admin_badge = '<span class="badge" style="background:rgba(248,150,30,0.1);color:#f8961e;">Admin</span>' if user.is_admin else ''
            active_badge = '<span class="badge" style="background:rgba(76,201,240,0.1);color:#4cc9f0;">Active</span>' if user.is_active else '<span class="badge" style="background:rgba(247,37,133,0.1);color:#f72585;">Inactive</span>'
            
            users_html += f'''
            <tr>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>{user.created_at.strftime("%b %d, %Y")}</td>
                <td>{admin_badge} {active_badge}</td>
            </tr>
            '''
    
    content = f'''
    <div style="margin:40px 0;">
        <h1 style="font-size:36px; margin-bottom:10px;">Admin Dashboard</h1>
        <p style="color:#6c757d; font-size:18px;">Manage reports, users, and platform settings</p>
        <div style="background:linear-gradient(135deg,#f8961e 0%,#ff9a3c 100%); color:white; padding:10px 20px; border-radius:20px; display:inline-flex; align-items:center; gap:10px; margin-top:10px;">
            <i class="fas fa-crown"></i> Administrator Control Panel
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{total_reports}</div>
            <div class="stat-label">Total Reports</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{pending_reports}</div>
            <div class="stat-label">Pending</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{flagged_reports}</div>
            <div class="stat-label">Flagged</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{total_users}</div>
            <div class="stat-label">Users</div>
        </div>
    </div>
    
    <div style="display:flex; gap:30px; margin-top:30px; flex-wrap:wrap;">
        <div class="card" style="flex:2; min-width:300px;">
            <div class="card-header">
                <h2 class="card-title"><i class="fas fa-flag"></i> Recent Reports</h2>
                <div style="display:flex; gap:10px;">
                    <a href="/admin/reports?status=pending" class="btn btn-warning" style="padding:10px 20px;">
                        <i class="fas fa-clock"></i> Pending ({pending_reports})
                    </a>
                    <a href="/admin/reports?status=flagged" class="btn btn-danger" style="padding:10px 20px;">
                        <i class="fas fa-flag"></i> Flagged ({flagged_reports})
                    </a>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Reporter</th>
                            <th>Reported Item</th>
                            <th>Category</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {reports_html if recent_reports else '''
                        <tr>
                            <td colspan="7" style="text-align:center; padding:40px; color:#6c757d;">
                                No reports found
                            </td>
                        </tr>
                        '''}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card" style="flex:1; min-width:300px;">
            <div class="card-header">
                <h2 class="card-title"><i class="fas fa-users"></i> Recent Users</h2>
                <a href="/admin/users" class="btn btn-primary">
                    <i class="fas fa-user-cog"></i> Manage
                </a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Joined</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users_html if recent_users else '''
                        <tr>
                            <td colspan="4" style="text-align:center; padding:20px; color:#6c757d;">
                                No users found
                            </td>
                        </tr>
                        '''}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    return render_template_string(render_page("Admin Dashboard", content))

@app.route('/admin/update_report', methods=['POST'])
def update_report():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    report_id = data.get('report_id')
    status = data.get('status')
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'})
    
    report.status = status
    if status in ['approved', 'rejected']:
        report.resolved_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/add_notes', methods=['POST'])
def add_notes():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    report_id = data.get('report_id')
    notes = data.get('notes')
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'})
    
    report.admin_notes = notes
    report.status = 'under_review'
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/init')
def init():
    """Initialize database route"""
    try:
        init_database()
        content = '''
        <div style="text-align:center; padding:100px 20px;">
            <div style="width:100px; height:100px; background:linear-gradient(135deg,#4361ee 0%,#00c9ff 100%); border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 30px; color:white; font-size:48px;">
                <i class="fas fa-check"></i>
            </div>
            <h1 style="font-size:36px; margin-bottom:20px;">Database Initialized!</h1>
            <div style="max-width:400px; margin:0 auto; background:white; padding:30px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.08);">
                <h3>Demo Accounts:</h3>
                <div style="background:#f8f9fa; padding:15px; border-radius:8px; margin-bottom:15px;">
                    <p style="margin:0; font-weight:600; color:#f8961e;"><i class="fas fa-crown"></i> Administrator</p>
                    <p style="margin:5px 0 0;">Username: <strong>admin</strong></p>
                    <p style="margin:0;">Password: <strong>Admin@123</strong></p>
                </div>
                <div style="background:#f8f9fa; padding:15px; border-radius:8px;">
                    <p style="margin:0; font-weight:600; color:#4361ee;"><i class="fas fa-user"></i> Regular User</p>
                    <p style="margin:5px 0 0;">Username: <strong>john</strong></p>
                    <p style="margin:0;">Password: <strong>User@123</strong></p>
                </div>
                <div style="margin-top:20px; padding-top:20px; border-top:1px solid #dee2e6;">
                    <a href="/login" class="btn btn-primary" style="width:100%;">
                        <i class="fas fa-sign-in-alt"></i> Go to Login
                    </a>
                </div>
            </div>
        </div>
        '''
        return render_template_string(render_page("Database Initialized", content))
    except Exception as e:
        content = f'''
        <div style="text-align:center; padding:100px 20px;">
            <h1 style="color:#f72585;">Error: {str(e)}</h1>
            <a href="/" class="btn btn-primary">Go Home</a>
        </div>
        '''
        return render_template_string(render_page("Error", content))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Auto-initialize if no users exist
        if User.query.count() == 0:
            init_database()
    
    print("\n" + "="*60)
    print("🚀 REPORT SHOT - Professional Reporting System")
    print("="*60)
    print("✨ Features:")
    print("  • Professional Modern UI with Sabit AI Branding")
    print("  • User Registration & Login System")
    print("  • Report Submission with AI-Powered Analysis")
    print("  • Complete Admin Control Panel")
    print("  • Real-time Status Updates")
    print("  • User Profile Management")
    print("\n🔗 Access URLs:")
    print("  Homepage:      http://localhost:5000")
    print("  About Page:    http://localhost:5000/about")
    print("  Login:         http://localhost:5000/login")
    print("  Register:      http://localhost:5000/register")
    print("  Dashboard:     http://localhost:5000/dashboard")
    print("  Admin Panel:   http://localhost:5000/admin")
    print("  Initialize DB: http://localhost:5000/init")
    print("\n👤 Demo Accounts:")
    print("  Admin: admin / Admin@123")
    print("  User:  john / User@123")
    print("\n💻 Developed by: Sabit AI")
    print("="*60)
    print("\n✅ READY FOR RENDER DEPLOYMENT")
    print("="*60)
    
    app.run(debug=True, port=5000)
