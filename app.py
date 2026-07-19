import os
from functools import wraps
import os
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    send_from_directory
)

from models import db, User, bcrypt
from image_generator import generate_face as sd_generate_face
from match_face import find_top5_matches
from flask import send_file, session

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor


import datetime


app = Flask(__name__)


# ---------------- CONFIGURATION ----------------

app.config['SECRET_KEY'] = 'your_super_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+mysqlconnector://root:@127.0.0.1:3306/thirdeye_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SKETCH_PARTS_FOLDER'] = 'static/sketch_parts'



# ---------------- INITIALIZE EXTENSIONS ----------------

db.init_app(app)
bcrypt.init_app(app)



# ---------------- LOGIN REQUIRED ----------------

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:
            flash(
                'Please log in to access this page.',
                'danger'
            )
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function



# ---------------- DATABASE INIT ----------------

@app.cli.command("init-db")
def init_db_command():

    db.create_all()

    print("Database initialized.")



# ---------------- HOME ----------------

@app.route('/')
def home():

    return render_template('home.html')



# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']


        user = User.query.filter_by(
            username=username
        ).first()


        if user and user.check_password(password):

            session['user_id'] = user.id
            session['username'] = user.username


            flash(
                f'Welcome, {user.username}!',
                'success'
            )


            return redirect(
                url_for('sketch_constructor')
            )


        else:

            flash(
                'Invalid username or password.',
                'danger'
            )


    return render_template('login.html')



# ---------------- REGISTER ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']


        existing_user = User.query.filter_by(
            username=username
        ).first()


        if existing_user:

            flash(
                'Username already exists.',
                'danger'
            )

            return redirect(
                url_for('register')
            )


        new_user = User(
            username=username,
            password=password
        )


        db.session.add(new_user)

        db.session.commit()


        flash(
            'Account created successfully!',
            'success'
        )


        return redirect(
            url_for('login')
        )


    return render_template('register.html')



# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():

    session.clear()


    flash(
        'You have been logged out.',
        'info'
    )


    return redirect(
        url_for('home')
    )



# ---------------- SKETCH CONSTRUCTOR ----------------

@app.route('/sketch')
@login_required
def sketch_constructor():

    parts = {}

    base_path = app.config['SKETCH_PARTS_FOLDER']


    if os.path.exists(base_path):

        for category in sorted(
            os.listdir(base_path)
        ):

            cat_path = os.path.join(
                base_path,
                category
            )


            if os.path.isdir(cat_path):

                files = sorted(
                    [
                        f"{category}/{f}"
                        for f in os.listdir(cat_path)
                        if f.lower().endswith(
                            (
                                '.png',
                                '.jpg',
                                '.jpeg',
                                '.webp'
                            )
                        )
                    ]
                )


                if files:

                    parts[category] = files


    return render_template(
        'sketch.html',
        parts=parts
    )



# ---------------- AI FACE GENERATION ----------------

@app.route('/generate-face', methods=['POST'])
@login_required
def generate_face():

    try:

        data = request.get_json()

        if not data or 'features' not in data:
            return jsonify({
                'error': 'No features provided'
            }), 400

        features = data['features']

        prompt = build_face_prompt(features)

        image_path = sd_generate_face(prompt)

        return jsonify({
            "success": True,
            "image": "/" + image_path.replace("\\", "/"),
            "prompt": prompt
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


def build_face_prompt(features):

    gender = features.get(
        "gender",
        "person"
    )


    parts = []


    mapping = {

        'head': '{} face shape',
        'hair': '{} hairstyle',
        'eyebrows': '{} eyebrows',
        'eyes': '{} eyes',
        'nose': '{} nose',
        'lips': '{} lips',
        'mustach': '{} facial hair'

    }


    for key, template in mapping.items():

        value = features.get(key)


        if value and value != "Skipped":

            parts.append(
                template.format(value)
            )


    description = ", ".join(parts)


    return f"""
Ultra realistic forensic police portrait of a {gender}.

Features:
{description}

Front facing.
Neutral facial expression.
Natural skin texture.
Professional DSLR portrait.
Passport style.
White background.
Highly detailed.
"""


# ---------------- FACE RECOGNITION ----------------

@app.route('/recognition', methods=['GET', 'POST'])
@login_required
def recognition():

    results = None

    if request.method == "POST":

        if "sketch" not in request.files:
            flash("Please select an image.", "warning")
            return redirect(request.url)

        file = request.files["sketch"]

        if file.filename == "":
            flash("Please select an image.", "warning")
            return redirect(request.url)

        # Create uploads folder if it doesn't exist
        UPLOAD_FOLDER = os.path.join("static", "uploads")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}.png"

        # Full path to save the uploaded image
        upload_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save the uploaded image
        file.save(upload_path)

        # Find the best match
        results = find_top5_matches(upload_path)

        if results:

            results = [results[0]]   # Only best match

            session["report"] = {

                "name": results[0]["name"],

                "age": results[0]["age"],

                "crime": results[0]["crime"],

                "last_seen": results[0]["last_seen"],

                "similarity": results[0]["similarity"],

                "criminal_image": results[0]["image"],

                "uploaded_image": upload_path

            }

    return render_template(
        "recognition.html",
        results=results
    )

# ---------------- CRIMINAL DATABASE IMAGE SERVING ----------------

@app.route('/criminal_database/<filename>')
@login_required
def criminal_database(filename):

    return send_from_directory(
        'criminal_database',
        filename
    )
    # ---------------- GENERATE REPORT ----------------

@app.route("/generate-report")
@login_required
def generate_report():

    report = session.get("report")

    if report is None:
        flash("No investigation report found.", "warning")
        return redirect(url_for("recognition"))

    os.makedirs("static/reports", exist_ok=True)

    pdf_path = os.path.join(
        "static",
        "reports",
        "Investigation_Report.pdf"
    )

    doc = SimpleDocTemplate(
    pdf_path,
    rightMargin=25,
    leftMargin=25,
    topMargin=20,
    bottomMargin=15
)

    styles = getSampleStyleSheet()

    title = styles["Title"]
    title.alignment = TA_CENTER
    title.textColor = HexColor("#003366")

    heading = styles["Heading2"]
    heading.textColor = HexColor("#003366")

    normal = styles["BodyText"]

    elements = []

    # ---------------- TITLE ----------------

    elements.append(
        Paragraph(
            "FORENSIC FACIAL IDENTIFICATION REPORT",
            title
        )
    )

    elements.append(Spacer(1, 20))

    # ---------------- REPORT DETAILS ----------------
    # Current date and time
    now = datetime.datetime.now()

# Dynamic Report ID
    report_id = f"FFI-{now.strftime('%Y%m%d%H%M%S')}"

# Dynamic Case ID
    case_id = f"CASE-{now.strftime('%Y%m%d%H%M%S')}"

# Logged-in user
    officer = session.get("username", "Administrator")

    report_info = Table([

    ["Report ID", report_id],

    ["Case ID", case_id],

    ["Generated", now.strftime("%d-%m-%Y %I:%M %p")],

    ["Officer", officer]

], colWidths=[120,250])
    report_info.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), HexColor("#DCEEFF")),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8)
    ]))

    elements.append(report_info)

    elements.append(Spacer(1, 20))

    # ---------------- SUSPECT DETAILS ----------------

    elements.append(
        Paragraph(
            "<b>SUSPECT DETAILS</b>",
            heading
        )
    )

    suspect = Table([
        ["Name", report["name"]],
        ["Age", report["age"]],
        ["Crime", report["crime"]],
        ["Last Seen", report["last_seen"]],
        ["Similarity", str(report["similarity"]) + " %"]
    ], colWidths=[120, 250])

    suspect.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (0,-1), HexColor("#EAF4FF")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8)
    ]))

    elements.append(suspect)

    elements.append(Spacer(1, 10))

    # ---------------- IMAGE SECTION ----------------

    elements.append(
        Paragraph(
            "<b>IMAGE COMPARISON</b>",
            heading
        )
    )

    uploaded_img = Image(
        report["uploaded_image"],
        width=1.8*inch,
        height=2.0*inch
    )

    criminal_path = os.path.join(
        "criminal_database",
        report["criminal_image"]
    )

    criminal_img = Image(
        criminal_path,
        width=1.8*inch,
        height=2.0*inch
    )

    image_table = Table([
        ["Uploaded Suspect", "Matched Criminal"],
        [uploaded_img, criminal_img]
    ], colWidths=[220,220])

    image_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,0),(-1,0),HexColor("#DCEEFF")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("BOTTOMPADDING",(0,0),(-1,-1),8)
    ]))

    elements.append(image_table)

    elements.append(Spacer(1,5))

    # ---------------- SUMMARY ----------------

    elements.append(
        Paragraph(
            "<b>INVESTIGATION SUMMARY</b>",
            heading
        )
    )

    elements.append(Spacer(1,10))
    summary = f"""
    The uploaded suspect face was analysed using the AI-powered
    Forensic Facial Identification System.

    A matching criminal record was identified.

    Match Found : {report['name']}<br/>
    Similarity : {report['similarity']} %<br/>
    Crime : {report['crime']}<br/>
    Last Seen : {report['last_seen']}<br/><br/>

    <b>Conclusion:</b><br/>
    The facial recognition system identified the above individual
    as the closest match in the criminal database.

    <b>Recommendation:</b><br/>
    The suspect should undergo fingerprint, iris or DNA
    verification before legal proceedings.
     """

    elements.append(
        Paragraph(
            summary,
            normal
        )
    )

    elements.append(Spacer(1,5))
    # ---------------- SIGNATURE ----------------

    elements.append(Spacer(1, 8))

    signature = Table(
        [
            ["Investigating Officer"],
            ["____________________________"],
            ["Digital Signature"]
        ],
        colWidths=[220]
    )

    signature.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica")
    ]))

    elements.append(signature)

    elements.append(Spacer(1, 5))

    footer = Paragraph(
        "<font size='8' color='grey'>AI-Based Forensic Face Recognition System</font>",
        normal
    )

    elements.append(footer)

    # ---------------- CREATE PDF ----------------

    doc.build(elements)

    return send_file(
        pdf_path,
        as_attachment=True
    )
# ---------------- RUN APPLICATION ----------------

if __name__ == '__main__':

    app.run(debug=True)