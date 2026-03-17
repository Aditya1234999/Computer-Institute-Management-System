from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = "balaji_secret_key"

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('home.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s",
            (uname, pwd)
        )
        admin = cur.fetchone()
        conn.close()

        if admin:
            session['admin'] = uname
            return redirect('/dashboard')
        else:
            return "Invalid Login"

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')
    return render_template('admin_dashboard.html')

# ---------------- ENROLL STUDENT ----------------
from datetime import datetime

@app.route('/enroll', methods=['POST'])
def enroll():
    try:
        data = request.json

        if not data.get('dob'):
            raise Exception("DOB is required")

        dob_str = data['dob']

        # handle both formats safely
        try:
            dob = datetime.strptime(dob_str, "%d/%m/%Y").date()
        except ValueError:
            try:
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except ValueError:
                dob = datetime.strptime(dob_str, "%m/%d/%Y").date()

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO students (name, dob, address, mobile)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            data['name'],
            dob,
            data['address'],
            data['mobile']
        ))

        student_id = cur.fetchone()[0]

        cur.execute("""
            SELECT id, total_fee FROM courses WHERE course_name=%s
        """, (data['course'],))

        course_id, total_fee = cur.fetchone()

        # Convert to Decimal for currency subtraction
        from decimal import Decimal
        paid = Decimal(str(data['fees_paid']))
        remaining = total_fee - paid

        # CHECK BATCH LIMIT
        batch_timing = data.get('batch_timing')
        if batch_timing:
            cur.execute("""
                SELECT COUNT(*) FROM admissions WHERE batch_timing = %s
            """, (batch_timing,))
            count = cur.fetchone()[0]
            if count >= 30:
                conn.close()
                return jsonify({"error": f"Batch '{batch_timing}' is full (Max 30 students). Please select another batch."}), 400

        cur.execute("""
            INSERT INTO admissions
            (student_id, course_id, fees_paid, total_fee, remaining_fee, academic_year, typing_mode, batch_timing, admission_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            student_id,
            course_id,
            paid,
            total_fee,
            remaining,
            data.get('academic_year'),
            data.get('typing_mode'),
            batch_timing
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "remaining_fee": remaining
        })

    except Exception as e:
        print("ENROLL ERROR:", e)
        return jsonify({"error": str(e)}), 500




# ---------------- TRACK FEES ----------------
@app.route('/track-fees/<query>')
def track_fees(query):
    conn = get_db()
    cur = conn.cursor()

    # Check if query is digits (Mobile) or string (Name)
    if query.isdigit():
        sql = """
            SELECT s.name, c.course_name,
                   a.total_fee, a.fees_paid, a.remaining_fee, s.id
            FROM students s
            JOIN admissions a ON s.id = a.student_id
            JOIN courses c ON a.course_id = c.id
            WHERE s.mobile=%s
        """
        cur.execute(sql, (query,))
    else:
        # Search by name (case insensitive partial match)
        sql = """
            SELECT s.name, c.course_name,
                   a.total_fee, a.fees_paid, a.remaining_fee, s.id
            FROM students s
            JOIN admissions a ON s.id = a.student_id
            JOIN courses c ON a.course_id = c.id
            WHERE LOWER(s.name) LIKE LOWER(%s)
        """
        cur.execute(sql, ('%' + query + '%',))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": "Student not found"})

    # Return list of results (even if just one)
    results = []
    for row in rows:
        results.append({
            "name": row[0],
            "course": row[1],
            "total_fee": row[2],
            "paid": row[3],
            "remaining": row[4],
            "student_id": row[5]
        })

    return jsonify(results)

# ---------------- UPDATE FEES ----------------
@app.route('/update-fees', methods=['POST'])
def update_fees():
    try:
        data = request.json
        student_id = data.get('student_id')
        
        # New Edit Logic
        if 'total_fee' in data and 'fees_paid' in data:
            total = float(data['total_fee'])
            paid = float(data['fees_paid'])
            remaining = total - paid
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE admissions 
                SET total_fee=%s, fees_paid=%s, remaining_fee=%s 
                WHERE student_id=%s
            """, (total, paid, remaining, student_id))
            conn.commit()
            conn.close()
            return jsonify({"success": True, "new_remaining": remaining})

        # Old Logic (just in case, though we will likely use the new one primarily)
        new_paid = data.get('new_paid') # Amount being added
        if not student_id or not new_paid:
            return jsonify({"error": "Missing data"}), 400

        conn = get_db()
        cur = conn.cursor()
        
        # Get current details
        cur.execute("SELECT fees_paid, total_fee FROM admissions WHERE student_id=%s", (student_id,))
        res = cur.fetchone()
        if not res:
            return jsonify({"error": "Admission not found"}), 404
            
        current_paid, total_fee = res
        from decimal import Decimal
        
        amount_to_add = Decimal(str(new_paid))
        updated_paid = current_paid + amount_to_add
        updated_remaining = total_fee - updated_paid
        
        if updated_remaining < 0:
             return jsonify({"error": "Paid amount exceeds total fee"}), 400

        cur.execute("""
            UPDATE admissions 
            SET fees_paid=%s, remaining_fee=%s 
            WHERE student_id=%s
        """, (updated_paid, updated_remaining, student_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "new_remaining": str(updated_remaining)})

    except Exception as e:
        print("UPDATE ERROR:", e)
        return jsonify({"error": str(e)}), 500

# ---------------- VIEW STUDENTS ----------------
@app.route('/students')
def students():
    year = request.args.get('year', 'All')
    conn = get_db()
    cur = conn.cursor()

    if year == 'All':
        cur.execute("""
            SELECT s.id, s.name, s.mobile, c.course_name, a.academic_year
            FROM students s
            JOIN admissions a ON s.id = a.student_id
            JOIN courses c ON a.course_id = c.id
            ORDER BY a.academic_year DESC NULLS LAST, s.id DESC
        """)
    else:
        cur.execute("""
            SELECT s.id, s.name, s.mobile, c.course_name, a.academic_year
            FROM students s
            JOIN admissions a ON s.id = a.student_id
            JOIN courses c ON a.course_id = c.id
            WHERE a.academic_year = %s
            ORDER BY s.id DESC
        """, (year,))

    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

# ---------------- DELETE STUDENT ----------------
@app.route('/delete-student', methods=['POST'])
def delete_student():
    try:
        data = request.json
        sid = data.get('student_id')
        
        conn = get_db()
        cur = conn.cursor()
        
        # Delete admission first (foreign key)
        cur.execute("DELETE FROM admissions WHERE student_id=%s", (sid,))
        # Delete student
        cur.execute("DELETE FROM students WHERE id=%s", (sid,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        print("DELETE ERROR:", e)
        return jsonify({"error": str(e)}), 500

# ---------------- STUDENT DETAILS ----------------
@app.route('/student/<int:sid>')
def student_details(sid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.name, s.dob, s.address, s.mobile,
               c.course_name, a.total_fee, a.fees_paid, a.remaining_fee
        FROM students s
        JOIN admissions a ON s.id = a.student_id
        JOIN courses c ON a.course_id = c.id
        WHERE s.id=%s
    """, (sid,))

    row = cur.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            "name": row[0], "dob": str(row[1]),
            "address": row[2], "mobile": row[3], "course": row[4],
            "total_fee": row[5], "paid": row[6], "remaining": row[7]
        })
    return jsonify({"error": "Student not found"}), 404





# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
