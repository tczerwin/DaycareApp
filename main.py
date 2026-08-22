from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import os
from pathlib import Path


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///daycare.db'
db = SQLAlchemy(app)


class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    parent_name = db.Column(db.String(200), nullable=True)
    parent_phone = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    departed = db.Column(db.DateTime, nullable=True)
    arrived = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return '<Child %r>' % self.name


def find_image_for_child(child_name):
    """Look for an image file matching the child's name"""
    img_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img')
    if not os.path.exists(img_folder):
        return None

    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.JPG', '.PNG', '.JPG']:
        filename = f"{child_name}{ext}"
        filepath = os.path.join(img_folder, filename)
        if os.path.exists(filepath):
            return filename
    return None


@app.template_filter('get_child_image')
def get_child_image(child_name):
    """Jinja2 filter to get child image, checking filesystem"""
    img = find_image_for_child(child_name)
    return img if img else 'baby.png'


@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method  == "POST":
        child_name = request.form['name']

        # Hardcoded parent data
        parent_data = {
            'russ': ('Jennifer Davis', '(555) 234-5678'),
            'sean': ('Christopher Brown', '(555) 345-6789'),
            'john': ('Robert Smith', '(555) 123-4567'),
            'diane': ('Sarah Johnson', '(555) 456-7890'),
            'eric': ('James Wilson', '(555) 567-8901'),
            'tbag': ('Maria Garcia', '(555) 678-9012'),
            'aengi': ('David Martinez', '(555) 789-0123'),
            'jacob': ('Patty Rogowski', '(555-123-4567)'),
            'dan': ('Shirley Temple', '(555-000-0000)')
        }

        # Look for existing child in database
        existing_child = Child.query.filter_by(name=child_name).first()

        if existing_child:
            # Child exists - check if already checked in
            if existing_child.arrived and not existing_child.departed:
                children = Child.query.filter(Child.arrived != None, Child.departed == None).order_by(Child.arrived).all()
                return render_template('index.html', children=children, now=datetime.now(), error=f"{child_name} is already checked in!", stats={})
            else:
                # Child exists but not checked in - set arrival time
                existing_child.arrived = datetime.now()
                try:
                    db.session.commit()
                    return redirect('/')
                except:
                    return "There was an issue checking in the child"
        else:
            # Child doesn't exist - create new record and check in
            new_child = Child(name=child_name, arrived=datetime.now())

            # Use hardcoded parent info
            if child_name.lower() in parent_data:
                parent_name, parent_phone = parent_data[child_name.lower()]
                new_child.parent_name = parent_name
                new_child.parent_phone = parent_phone

            # Find matching image
            image_file = find_image_for_child(child_name)
            if image_file:
                new_child.image = image_file

            try:
                db.session.add(new_child)
                db.session.commit()
                return redirect('/')
            except:
                return "There was an issue checking in the child"

    else:
        sort_by = request.args.get('sort', 'time_here')  # Default sort

        children = Child.query.filter(Child.arrived != None, Child.departed == None).all()

        if sort_by == 'name':
            children = sorted(children, key=lambda x: x.name.lower())
        elif sort_by == 'checkin':
            children = sorted(children, key=lambda x: x.arrived)
        else:  # time_here (default)
            children = sorted(children, key=lambda x: datetime.now() - x.arrived, reverse=True)

        # Store UTC times as Unix timestamps for JavaScript conversion
        for child in children:
            child.arrived_timestamp = int(child.arrived.timestamp() * 1000) if child.arrived else None

        # Calculate statistics
        today = date.today()
        all_today = Child.query.filter(Child.arrived != None, db.func.date(Child.arrived) == today).all()
        checked_out = [c for c in all_today if c.departed]
        currently_here = [c for c in all_today if not c.departed]

        avg_minutes = 0
        if checked_out:
            total_minutes = sum((c.departed - c.arrived).total_seconds() / 60 for c in checked_out)
            avg_minutes = int(total_minutes / len(checked_out))

        stats = {
            'total_today': len(all_today),
            'checked_out': len(checked_out),
            'currently_here': len(currently_here),
            'avg_hours': avg_minutes // 60,
            'avg_minutes': avg_minutes % 60
        }

        return render_template('index.html', children=children, sort_by=sort_by, now=datetime.now(), stats=stats)


@app.route("/delete/<int:id>")
def delete(id):
    child_checked_out = Child.query.get_or_404(id)

    try:
        child_checked_out.departed = datetime.now()
        db.session.commit()
        return redirect("/")
    except:
        return "There was a problem checking out that child"


@app.route("/add-child", methods=["GET", "POST"])
def add_child():
    if request.method == "POST":
        child_name = request.form['name']
        parent_name = request.form.get('parent_name', '')
        parent_phone = request.form.get('parent_phone', '')
        notes = request.form.get('notes', '')
        new_child = Child(name=child_name, parent_name=parent_name, parent_phone=parent_phone, notes=notes)

        # Handle picture upload
        try:
            if 'picture' in request.files:
                file = request.files['picture']
                if file and file.filename != '':
                    img_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img')
                    if not os.path.exists(img_folder):
                        os.makedirs(img_folder)

                    file_ext = os.path.splitext(file.filename)[1]
                    filename = f"{child_name}{file_ext}"
                    filepath = os.path.join(img_folder, filename)
                    file.save(filepath)
                    new_child.image = filename
            else:
                image_file = find_image_for_child(child_name)
                if image_file:
                    new_child.image = image_file

            db.session.add(new_child)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f"Error adding child: {str(e)}"
    else:
        return render_template('add_child.html')


@app.route("/parents")
def parents_list():
    """Display all parent contact information (unique children only)"""
    children = Child.query.filter(Child.arrived != None).all()
    # Use dictionary to remove duplicates by name
    seen = {}
    for c in children:
        if c.parent_name or c.parent_phone:
            if c.name not in seen:
                seen[c.name] = (c.name, c.parent_name, c.parent_phone)

    parents = sorted(seen.values(), key=lambda x: x[0])  # Sort by child name
    return render_template("parents.html", parents=parents)


@app.route("/child/<int:id>")
def view_child(id):
    child = Child.query.get_or_404(id)
    return render_template("child_details.html", child=child)


@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    child = Child.query.get_or_404(id)

    if request.method == "POST":
        child.name = request.form['name']
        child.parent_name = request.form.get('parent_name', '')
        child.parent_phone = request.form.get('parent_phone', '')
        child.notes = request.form.get('notes', '')

        # Handle picture upload
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename != '':
                img_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img')
                if not os.path.exists(img_folder):
                    os.makedirs(img_folder)

                file_ext = os.path.splitext(file.filename)[1]
                filename = f"{child.name}{file_ext}"
                file.save(os.path.join(img_folder, filename))
                child.image = filename

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating the child'
    else:
        return render_template("update.html", child = child)


@app.route('/export-pdf')
def export_pdf():
    today = date.today()

    children = Child.query.filter(
        db.func.date(Child.arrived) == today
    ).all()

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph(f"Daycare Attendance - {today.strftime('%m/%d/%Y')}", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    table_data = [['Child Name', 'Parent Name', 'Parent Phone', 'Check In', 'Check Out', 'Status']]

    for child in children:
        check_in_time = child.arrived.strftime('%I:%M %p') if child.arrived else 'N/A'
        check_out_time = child.departed.strftime('%I:%M %p') if child.departed else 'Still Here'
        status = 'Checked Out' if child.departed else 'Still Here'
        parent_name = child.parent_name if child.parent_name else '-'
        parent_phone = child.parent_phone if child.parent_phone else '-'

        table_data.append([
            child.name,
            parent_name,
            parent_phone,
            check_in_time,
            check_out_time,
            status
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Add notes section if any child has notes
    children_with_notes = [c for c in children if c.notes]
    if children_with_notes:
        notes_title = Paragraph("Notes & Special Information", styles['Heading2'])
        elements.append(notes_title)
        elements.append(Spacer(1, 12))

        for child in children_with_notes:
            child_notes = Paragraph(f"<b>{child.name}</b>: {child.notes}", styles['Normal'])
            elements.append(child_notes)
            elements.append(Spacer(1, 8))

    doc.build(elements)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'attendance_{today}.pdf'
    )


@app.route('/hardcode-parents')
def hardcode_parents():
    """Manually set parent info for all children"""
    try:
        # Hardcoded parent data
        parent_data = {
            'john': {'name': 'Robert Smith', 'phone': '(555) 123-4567'},
            'russ': {'name': 'Jennifer Davis', 'phone': '(555) 234-5678'},
            'diane': {'name': 'Christopher Brown', 'phone': '(555) 345-6789'},
            'mom': {'name': 'Sarah Johnson', 'phone': '(555) 456-7890'},
            'dad': {'name': 'James Wilson', 'phone': '(555) 567-8901'},
            'tbag': {'name': 'Maria Garcia', 'phone': '(555) 678-9012'},
            'aengi': {'name': 'David Martinez', 'phone': '(555) 789-0123'},
        }

        count = 0
        for child in Child.query.all():
            child_name_lower = child.name.lower()
            if child_name_lower in parent_data:
                child.parent_name = parent_data[child_name_lower]['name']
                child.parent_phone = parent_data[child_name_lower]['phone']
                count += 1

        db.session.commit()
        return f"✓ Updated {count} children with hardcoded parent info! <a href='/debug-children'>Check here</a>"
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}"


@app.route('/add-all-parents')
def add_all_parents():
    """Add parent info to all children"""
    data = {
        'russ': ('Jennifer Davis', '(555) 234-5678'),
        'diane': ('Christopher Brown', '(555) 345-6789'),
        'john': ('Robert Smith', '(555) 123-4567'),
    }

    for child in Child.query.all():
        if child.name.lower() in data:
            name, phone = data[child.name.lower()]
            child.parent_name = name
            child.parent_phone = phone

    db.session.commit()
    return "✓ Done! Refresh your page."


@app.route('/test-update')
def test_update():
    """Test updating one child"""
    try:
        child = Child.query.filter_by(name='russ').first()
        if child:
            child.parent_name = 'Test Parent'
            child.parent_phone = '(555) 999-9999'
            db.session.commit()
            return f"Updated russ. Now in DB: Name={child.parent_name}, Phone={child.parent_phone}"
        else:
            return "Child 'russ' not found"
    except Exception as e:
        return f"Error: {str(e)}"


@app.route('/debug-children')
def debug_children():
    """Debug route to see all children"""
    children = Child.query.all()
    result = ""
    for child in children:
        result += f"Name: {child.name}, Image: {child.image}, Parent: {child.parent_name}, Phone: {child.parent_phone}<br>"
    return result


@app.route('/setup-parents')
def setup_parents():
    """Auto-populate parent info for children with images"""
    import random

    fake_first_names = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Jennifer', 'James', 'Jessica', 'Robert', 'Mary', 'James', 'Patricia', 'Kevin', 'Linda']
    fake_last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Wilson', 'Anderson', 'Taylor', 'Thomas']

    try:
        children = Child.query.all()
        count = 0

        for child in children:
            if child.image:
                parent_name = f"{random.choice(fake_first_names)} {random.choice(fake_last_names)}"
                parent_phone = f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"

                child.parent_name = parent_name
                child.parent_phone = parent_phone
                db.session.flush()
                count += 1

        db.session.commit()
        return f"✓ Successfully updated {count} children with parent info! <a href='/debug-children'>Check here</a>"
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}"


@app.before_request
def init_parent_data():
    """Auto-populate parent info on first request"""
    if not hasattr(app, '_parent_data_initialized'):
        app._parent_data_initialized = True

        import random
        fake_first_names = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Jennifer', 'James', 'Jessica', 'Robert', 'Mary']
        fake_last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

        for child in Child.query.all():
            if not child.parent_name:  # Only populate if empty
                parent_name = f"{random.choice(fake_first_names)} {random.choice(fake_last_names)}"
                parent_phone = f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
                child.parent_name = parent_name
                child.parent_phone = parent_phone

        db.session.commit()


@app.route('/populate-all-parents')
def populate_all_parents():
    """Populate parent info for all children"""
    import random

    names = ['Robert', 'Jennifer', 'Michael', 'Sarah', 'David', 'Emily', 'James', 'Jessica']
    last = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']

    count = 0
    for child in Child.query.all():
        child.parent_name = f"{random.choice(names)} {random.choice(last)}"
        child.parent_phone = f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
        count += 1

    db.session.commit()
    return f"✓ Populated {count} children"


@app.route('/api/child-info/<name>')
def get_child_info(name):
    """Get parent info for a child by name"""
    child = Child.query.filter_by(name=name).first()
    if child:
        return {
            'found': True,
            'parent_name': child.parent_name or '',
            'parent_phone': child.parent_phone or ''
        }
    return {'found': False}


if __name__ == '__main__':
    app.run(port = 8000, debug=True)
