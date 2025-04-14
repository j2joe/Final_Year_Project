from flask import Flask, make_response, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import bcrypt
from datetime import datetime, timedelta
import secrets
from flask_mail import Mail, Message
import os
import dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from flask import abort
from flask_swagger_ui import get_swaggerui_blueprint
from flasgger import Swagger

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
API_URL = '/api/swagger.json'  # Our API url (can be a static file)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Nexgen Budgets API"
    }
)

# Load environment variables
dotenv.load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Configure session to be more secure and persistent
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'nexgenbudgets.noreply@gmail.com'
app.config['MAIL_PASSWORD'] = 'zwvg mgpd dncw ybmv'
app.config['MAIL_DEFAULT_SENDER'] = ('NexGen Budgets', 'nexgenbudgets.noreply@gmail.com')

mail = Mail(app)

app.register_blueprint(swaggerui_blueprint)

app.config['SWAGGER'] = {
    'title': 'Nexgen Budgets API',
    'description': 'API documentation for Nexgen Budgets financial application',
    'uiversion': 3,
    'specs_route': '/api/docs/'  # Custom docs URL
}
Swagger(app)
# Database connection
def get_db():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'nexgen'),
            auth_plugin='mysql_native_password',
            use_pure=True
        )
        logger.debug("Database connection successful")
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        flash(f"Database connection error: {err}", "error")
        return None

# ------------------- Authentication Routes ------------------

@app.route('/api/swagger.json')
def swagger():
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "Nexgen Budgets API",
            "version": "1.0",
            "description": "API for personal finance management"
        },
        "paths": {
            "/api/data": {
                "get": {
                    "summary": "Test endpoint",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "data": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized"
                        }
                    }
                }
            },
            # Add your other endpoints here following the same pattern
            "/api/categories": {
                "get": {
                    "summary": "Get transaction categories",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["INCOME", "EXPENSE"]
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of categories",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    })


@app.route('/', methods=['GET', 'POST'])
def login():
    # Clear any existing session
    if 'logged_in' in session:
        session.clear()
        
    if request.method == 'POST':
        email = request.form['uEmail']
        password = request.form['uPassword']
        ip_address = request.remote_addr
        
        logger.debug(f"Login attempt for email: {email}")
        
        conn = None
        cursor = None
        try:
            conn = get_db()
            if conn is None:
                flash("Database connection failed", "error")
                return redirect(url_for('login'))
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                logger.debug(f"Account does not exist for: {email}")
                flash('⚠️ Account does not exist! Please sign up.', 'error')
                return redirect(url_for('signup', email=email))
            
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                cursor.execute("""
                    INSERT INTO login_attempts (user_id, status, ip_address)
                    VALUES (%s, 'success', %s)
                """, (user['id'], ip_address))
                conn.commit()
                
                # Set session variables
                session.clear()  # Clear any existing session data first
                session['user_id'] = user['id']
                session['logged_in'] = True
                session['email'] = user['email']
                session['full_name'] = user['full_name']
                
                # Force session to be saved
                session.modified = True
                
                logger.debug(f"Login successful for user ID: {user['id']}")
                flash('🎉 Login successful!', 'success')
                
                # Make sure to commit session and return the redirect directly
                return redirect(url_for('dashboard'))
            else:
                cursor.execute("""
                    INSERT INTO login_attempts (user_id, status, ip_address)
                    VALUES (%s, 'failed', %s)
                """, (user['id'], ip_address))
                conn.commit()
                logger.debug(f"Invalid password for: {email}")
                flash('❌ Invalid password!', 'error')
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash(f'⚠️ System error: {str(e)}', 'error')
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
    
    # If GET request or login failed
    return render_template('nexGen.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        data = request.form
        email = data.get("email", "").strip()
        password = data.get("password", "")
        re_password = data.get("re_password", "")
        
        # Basic validation
        if not email or '@' not in email:
            flash("Please enter a valid email address", "error")
            return redirect(url_for('signup'))
        
        # Password validation
        if len(password) < 8:
            flash("Password must be at least 8 characters", "error")
            return redirect(url_for('signup'))
        
        if not any(char.isdigit() for char in password):
            flash("Password must contain at least one number", "error")
            return redirect(url_for('signup'))
            
        if not any(char in '!@#$%^&*(),.?":{}|<>' for char in password):
            flash("Password must contain at least one special character", "error")
            return redirect(url_for('signup'))
            
        if password != re_password:
            flash("Passwords do not match", "error")
            return redirect(url_for('signup'))
        
        conn = None
        cursor = None
        try:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn = get_db()
            if conn is None:
                flash("Database connection failed", "error")
                return redirect(url_for('signup'))
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (full_name, email, phone, business_name, password, country, state)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get("full_name", "").strip(),
                email,
                data.get("phone", "").strip(),
                data.get("business_name", "").strip(),
                hashed_pw,
                data.get("country", "").strip(),
                data.get("state", "").strip()
            ))
            conn.commit()
            flash("Account created successfully!", "success")
            return redirect(url_for('login'))
            
        except mysql.connector.IntegrityError:
            flash("Email already exists!", "error")
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('sign_up.html', email=request.args.get('email', ''))

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://"
)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        # Validate email
        if not email or '@' not in email:
            flash("Please enter a valid email address", "error")
            return redirect(url_for('forgot_password'))
        
        conn = None
        cursor = None
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, full_name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user:
                # Generate secure token
                token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=1)
                
                # Store token in database
                cursor.execute("""
                    INSERT INTO password_reset_tokens (user_id, token, expires_at)
                    VALUES (%s, %s, %s)
                """, (user['id'], token, expires_at))
                conn.commit()
                
                # Create reset link
                reset_link = url_for('reset_password', token=token, _external=True)
                
                # Prepare email
                msg = Message(
                    'Password Reset Request',
                    recipients=[email]
                )
                msg.body = f"""Hello {user['full_name']},
                
We received a request to reset your password. Click the link below:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email."""
                
                # Send email
                mail.send(msg)
                
            # Always show success to prevent email enumeration
            flash("If an account exists, you'll receive a reset link shortly.📌Check SPAM folder also", "info")
            return redirect(url_for('forgot_password'))
            
        except Exception as e:
            logger.error(f"Error in password reset: {str(e)}")
            flash("An error occurred. Please try again.", "error")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')
    if not token:
        flash("Invalid reset link", "error")
        return redirect(url_for('forgot_password'))
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        if conn is None:
            flash("Database connection failed", "error")
            return redirect(url_for('forgot_password'))
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_id FROM password_reset_tokens
            WHERE token = %s AND expires_at > NOW()
        """, (token,))
        valid_token = cursor.fetchone()
        
        if not valid_token:
            flash("Invalid or expired reset link", "error")
            return redirect(url_for('forgot_password'))
        
        if request.method == 'POST':
            new_password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not new_password or len(new_password) < 8:
                flash("Password must be at least 8 characters", "error")
                return render_template('reset_password.html', token=token)
                
            if new_password != confirm_password:
                flash("Passwords do not match", "error")
                return render_template('reset_password.html', token=token)
                
            hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute("""
                UPDATE users SET password = %s
                WHERE id = %s
            """, (hashed_pw, valid_token['user_id']))
            
            cursor.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
            conn.commit()
            flash("Password updated successfully! Please login.", "success")
            return redirect(url_for('login'))
        
        return render_template('reset_password.html', token=token)
        
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('forgot_password'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ------------------- Dashboard Routes -------------------
@app.route('/dashboard')
def dashboard():
    logger.debug(f"Dashboard access attempt, session: {session}")
    
    # More explicit session checking
    if 'user_id' not in session or 'logged_in' not in session or not session['logged_in']:
        logger.warning("Unauthorized dashboard access attempt")
        flash('🔒 Please login to access dashboard', 'error')
        return redirect(url_for('login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        if conn is None:
            flash("Database connection failed", "error")
            return redirect(url_for('login'))
            
        cursor = conn.cursor(dictionary=True)
        
        # Get login history
        cursor.execute("""
            SELECT attempt_time, status, ip_address 
            FROM login_attempts 
            WHERE user_id = %s 
            ORDER BY attempt_time DESC 
            LIMIT 5
        """, (session['user_id'],))
        login_history = cursor.fetchall()

        # Get user data
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        return render_template('dashboard.html', 
                            user=user, 
                            login_history=login_history)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash(f'⚠️ Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/user_profile')
def user_profile():
    if 'logged_in' not in session or not session['logged_in']:
        flash('🔒 Please login to access your profile', 'error')
        return redirect(url_for('login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        if conn is None:
            flash("Database connection failed", "error")
            return redirect(url_for('dashboard'))
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user data
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        # Get recent login attempts
        cursor.execute("""
            SELECT attempt_time, status, ip_address 
            FROM login_attempts 
            WHERE user_id = %s 
            ORDER BY attempt_time DESC 
            LIMIT 3
        """, (session['user_id'],))
        login_history = cursor.fetchall()
        
        return render_template('user_profile.html', 
                            user=user, 
                            login_history=login_history)
        
    except Exception as e:
        flash(f'⚠️ Error loading profile: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/login_activity')
def login_activity():
    if 'logged_in' not in session or not session['logged_in']:
        flash('🔒 Please login to access login activity', 'error')
        return redirect(url_for('login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        if conn is None:
            flash("Database connection failed", "error")
            return redirect(url_for('dashboard'))
            
        cursor = conn.cursor(dictionary=True)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Get filter parameter from query string
        filter_status = request.args.get('filter', 'all')
        
        # Base query
        count_query = "SELECT COUNT(*) as total FROM login_attempts WHERE user_id = %s"
        data_query = """
            SELECT attempt_time, status, ip_address, 
                   IFNULL(device, 'Unknown') as device, 
                   IFNULL(location, 'Unknown') as location
            FROM login_attempts 
            WHERE user_id = %s
        """
        
        # Add filter conditions if needed
        params = [session['user_id']]
        if filter_status == 'success':
            count_query += " AND status = 'success'"
            data_query += " AND status = 'success'"
        elif filter_status == 'failed':
            count_query += " AND status = 'failed'"
            data_query += " AND status = 'failed'"
        
        # Get total count for pagination
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()['total']
        total_pages = max(1, (total_records + per_page - 1) // per_page)
        
        # Add sorting and pagination
        data_query += " ORDER BY attempt_time DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        # Execute the main query
        cursor.execute(data_query, params)
        login_history = cursor.fetchall()
        
        # Format dates for better display
        for entry in login_history:
            if 'attempt_time' in entry and entry['attempt_time']:
                entry['attempt_time'] = entry['attempt_time'].strftime('%b %d, %Y - %I:%M %p')
        
        # Get user data
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        # Debug logging
        logger.debug(f"Login activity loaded: {len(login_history)} records")
        
        return render_template('login_activity.html', 
                            user=user, 
                            login_history=login_history,
                            total_pages=total_pages,
                            current_page=page,
                            current_filter=filter_status)
        
    except Exception as e:
        logger.error(f"Error loading login activity: {str(e)}")
        flash(f'⚠️ Error loading login activity: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/data')
def get_data():
    """
    Test API endpoint
    ---
    tags:
      - Testing
    responses:
      200:
        description: Successful response with user data
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                message:
                  type: string
                  example: API is working
                user_info:
                  type: object
                  properties:
                    user_id:
                      type: integer
                      example: 123
                    name:
                      type: string
                      example: John Doe
                    email:
                      type: string
                      example: user@example.com
                timestamp:
                  type: string
                  format: date-time
                  example: "2023-08-15T14:30:00Z"
      401:
        description: Unauthorized access
      500:
        description: Internal server error
    """
    if 'user_id' not in session:
        abort(401, description="Unauthorized - Please login first")
    
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT full_name FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        return jsonify({
            "status": "success",
            "message": "API is working",
            "user_info": {
                "user_id": session['user_id'],
                "name": user['full_name'],
                "email": session['email']
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/reports', methods=['POST'])
def generate_report():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['type', 'start_date', 'end_date', 'format']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'Missing {field}'}), 400

    # Validate date format
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if start_date > end_date:
            return jsonify({'success': False, 'message': 'Start date cannot be after end date'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get transaction data based on report type and date range
        if data['type'] == 'monthly_summary':
            # Get monthly totals
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(date, '%Y-%m') as month,
                    SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END) as expense,
                    SUM(CASE WHEN type = 'INCOME' THEN amount ELSE -amount END) as net
                FROM transactions
                WHERE user_id = %s 
                AND date BETWEEN %s AND %s
                GROUP BY DATE_FORMAT(date, '%Y-%m')
                ORDER BY month
            """, (session['user_id'], start_date, end_date))
            
            report_data = cursor.fetchall()
            report_title = "Monthly Summary Report"
            
        elif data['type'] == 'category_breakdown':
            # Get expenses by category
            cursor.execute("""
                SELECT 
                    c.name as category,
                    SUM(t.amount) as total,
                    COUNT(t.id) as count
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s 
                AND t.date BETWEEN %s AND %s
                AND t.type = 'EXPENSE'
                GROUP BY t.category_id
                ORDER BY total DESC
            """, (session['user_id'], start_date, end_date))
            
            expense_data = cursor.fetchall()
            
            # Get income by category
            cursor.execute("""
                SELECT 
                    c.name as category,
                    SUM(t.amount) as total,
                    COUNT(t.id) as count
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s 
                AND t.date BETWEEN %s AND %s
                AND t.type = 'INCOME'
                GROUP BY t.category_id
                ORDER BY total DESC
            """, (session['user_id'], start_date, end_date))
            
            income_data = cursor.fetchall()
            
            report_data = {
                'expenses': expense_data,
                'income': income_data
            }
            report_title = "Category Breakdown Report"
            
        elif data['type'] == 'income_vs_expense':
            # Get daily income vs expense
            cursor.execute("""
                SELECT 
                    date,
                    SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END) as expense
                FROM transactions
                WHERE user_id = %s 
                AND date BETWEEN %s AND %s
                GROUP BY date
                ORDER BY date
            """, (session['user_id'], start_date, end_date))
            
            report_data = cursor.fetchall()
            report_title = "Income vs Expense Report"
            
        else:
            return jsonify({'success': False, 'message': 'Invalid report type'}), 400
        
        # Format dates for better display
        if data['type'] == 'monthly_summary':
            for entry in report_data:
                if 'month' in entry:
                    month_date = datetime.strptime(entry['month'], '%Y-%m')
                    entry['month_formatted'] = month_date.strftime('%b %Y')
        elif data['type'] == 'income_vs_expense':
            for entry in report_data:
                if 'date' in entry and entry['date']:
                    entry['date_formatted'] = entry['date'].strftime('%b %d, %Y')
        
        # For HTML format, return report content
        if data['format'] == 'html':
            return jsonify({
                'success': True,
                'report_type': data['type'],
                'title': report_title,
                'data': report_data,
                'start_date': data['start_date'],
                'end_date': data['end_date'],
                'format': 'html'
            })
        
        # For file formats (PDF/CSV), generate the file and return download URL
        elif data['format'] in ['pdf', 'csv']:
            # In a real application, you would generate the actual file here
            # For this example, we'll just return a mock download URL
            download_filename = f"report_{data['type']}_{data['start_date']}_{data['end_date']}.{data['format']}"
            download_url = url_for('download_report', filename=download_filename, _external=True)
            
            return jsonify({
                'success': True,
                'download_url': download_url,
                'format': data['format']
            })
        
        else:
            return jsonify({'success': False, 'message': 'Invalid format'}), 400
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Add this route to handle file downloads
@app.route('/download-report/<filename>')
def download_report(filename):
    # In a real application, you would generate and return the actual file
    # For this example, we'll create a simple text file
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    response = make_response("This is a sample report content")
    
    if filename.endswith('.pdf'):
        response.headers['Content-Type'] = 'application/pdf'
    elif filename.endswith('.csv'):
        response.headers['Content-Type'] = 'text/csv'
    
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/api/categories')
def get_categories():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    category_type = request.args.get('type', 'EXPENSE')
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, name FROM categories 
            WHERE user_id = %s AND type = %s
            ORDER BY name
        """, (session['user_id'], category_type))
        
        categories = cursor.fetchall()
        return jsonify(categories)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
    
    data = request.get_json()
    
    # Validation
    required_fields = ['amount', 'category_id', 'date', 'type']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'Missing {field}'}), 400
    
    # Validate amount is a positive number
    try:
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    
    # Validate date format
    try:
        transaction_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if transaction_date > datetime.now().date():
            return jsonify({'success': False, 'message': 'Future dates not allowed'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify category belongs to user
        cursor.execute("SELECT 1 FROM categories WHERE id = %s AND user_id = %s", 
                      (data['category_id'], session['user_id']))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Invalid category'}), 400
        
        cursor.execute("""
            INSERT INTO transactions 
            (user_id, category_id, amount, description, date, type, payment_method, is_recurring)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session['user_id'],
            data['category_id'],
            amount,
            data.get('description', ''),
            data['date'],
            data['type'],
            data.get('payment_method'),
            data.get('is_recurring', False)
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Transaction added'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error adding transaction: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/logout')
def logout():
    if 'user_id' in session:
        conn = None
        cursor = None
        try:
            conn = get_db()
            if conn is None:
                flash("Database connection failed", "error")
                # Even if DB fails, we should still clear the session
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_logins (user_id, activity_type)
                    VALUES (%s, 'logout')
                """, (session['user_id'],))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging logout activity: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    # Always clear the session regardless of database operation success
    session.clear()
    flash('You have been logged out successfully.', 'info')
    response = redirect(url_for('login'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True')