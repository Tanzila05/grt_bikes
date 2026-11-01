from flask import Flask, render_template, request, send_file
from flask_mysqldb import MySQL

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

import os
import random
from datetime import datetime

import config

app = Flask(__name__)

# ================= MYSQL CONFIG =================

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['MYSQL_PORT'] = config.MYSQL_PORT

if config.MYSQL_SSL_CA:
    app.config['MYSQL_CUSTOM_OPTIONS'] = {
        'ssl': {'ca': config.MYSQL_SSL_CA}
    }

mysql = MySQL(app)


INVOICE_FOLDER = "invoices"
if not os.path.exists(INVOICE_FOLDER):
    os.makedirs(INVOICE_FOLDER)

# ================= HOME =================

@app.route('/')
def index():
    return render_template('index.html')

# ================= SUBMIT =================

@app.route('/submit', methods=['POST'])
def submit():

    customer_name   = request.form['customer_name']
    phone           = request.form['phone']
    address         = request.form['address']
    bike_name       = request.form['bike_name']
    bike_model      = request.form['bike_model']
    registration_no = request.form['registration_no']
    engine_no       = request.form['engine_no']
    chassis_no      = request.form['chassis_no']
    amount          = float(request.form['amount'])

    gst          = round(amount * 0.18, 2)
    total        = round(amount + gst, 2)
    invoice_no   = "GRT" + str(random.randint(1000, 9999))
    current_date = datetime.now().strftime("%d-%m-%Y")

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO bills(
            invoice_no, customer_name, phone, address,
            bike_name, bike_model, registration_no,
            engine_no, chassis_no, amount, gst, total, date
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        invoice_no, customer_name, phone, address,
        bike_name, bike_model, registration_no,
        engine_no, chassis_no, amount, gst, total, current_date
    ))
    mysql.connection.commit()
    cur.close()

    # ================= PDF =================

    pdf_path = f"invoices/{invoice_no}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    c.setFillColorRGB(0.05, 0.1, 0.2)
    c.rect(0, 730, width, 90, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(50, 775, "GRT BIKES")
    c.setFont("Helvetica", 13)
    c.drawString(50, 752, "Premium Second Hand Bike Showroom")
    c.drawString(50, 735, "Chennai, Tamil Nadu | +91 9876543210")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(400, 680, "INVOICE")
    c.setFont("Helvetica", 12)
    c.drawString(400, 655, f"Invoice No : {invoice_no}")
    c.drawString(400, 635, f"Date       : {current_date}")

    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.roundRect(40, 560, 530, 70, 10, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, 610, "Customer Details")
    c.setFont("Helvetica", 12)
    c.drawString(50, 590, f"Name    : {customer_name}")
    c.drawString(50, 572, f"Phone   : {phone}")
    c.drawString(300, 590, f"Address : {address}")

    bike_data = [
        ["Bike Details",    "Information"],
        ["Bike Name",       bike_name],
        ["Bike Model",      bike_model],
        ["Registration No", registration_no],
        ["Engine No",       engine_no],
        ["Chassis No",      chassis_no],
    ]
    table = Table(bike_data, colWidths=[220, 280])
    table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 12),
        ('BACKGROUND',    (0,1), (0,-1), colors.HexColor("#dbeafe")),
        ('GRID',          (0,0), (-1,-1), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, 360)

    payment_data = [
        ["Bike Amount",  f"Rs. {amount:,.2f}"],
        ["GST (18%)",    f"Rs. {gst:,.2f}"],
        ["Total Amount", f"Rs. {total:,.2f}"],
    ]
    payment_table = Table(payment_data, colWidths=[220, 220])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor("#111827")),
        ('TEXTCOLOR',     (0,0), (-1,-1), colors.white),
        ('FONTNAME',      (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 13),
        ('GRID',          (0,0), (-1,-1), 1, colors.white),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING',    (0,0), (-1,-1), 12),
    ]))
    payment_table.wrapOn(c, width, height)
    payment_table.drawOn(c, 300, 220)

    c.setFillColor(colors.grey)
    c.setFont("Helvetica", 11)
    c.drawString(50, 130, "Thank you for choosing GRT BIKES.")
    c.drawString(50, 110, "This is a computer generated invoice.")
    c.drawString(50, 90,  "Contact : +91 9876543210")

    c.setFillColor(colors.black)
    c.line(420, 160, 530, 160)
    c.drawString(435, 145, "Authorized Signature")

    c.save()

    return send_file(pdf_path, as_attachment=True)

# ================= SEARCH =================

@app.route('/search')
def search():
    query       = request.args.get('q', '').strip()
    filter_by   = request.args.get('filter', 'all')

    cur = mysql.connection.cursor()

    if query:
        if filter_by == 'customer':
            cur.execute("""
                SELECT * FROM bills
                WHERE customer_name LIKE %s
                ORDER BY id DESC
            """, (f'%{query}%',))

        elif filter_by == 'invoice':
            cur.execute("""
                SELECT * FROM bills
                WHERE invoice_no LIKE %s
                ORDER BY id DESC
            """, (f'%{query}%',))

        elif filter_by == 'bike':
            cur.execute("""
                SELECT * FROM bills
                WHERE bike_name LIKE %s OR bike_model LIKE %s
                ORDER BY id DESC
            """, (f'%{query}%', f'%{query}%'))

        elif filter_by == 'phone':
            cur.execute("""
                SELECT * FROM bills
                WHERE phone LIKE %s
                ORDER BY id DESC
            """, (f'%{query}%',))

        else:
            cur.execute("""
                SELECT * FROM bills
                WHERE customer_name LIKE %s
                   OR invoice_no    LIKE %s
                   OR bike_name     LIKE %s
                   OR phone         LIKE %s
                ORDER BY id DESC
            """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
    else:
        cur.execute("SELECT * FROM bills ORDER BY id DESC")

    data = cur.fetchall()
    cur.close()

    total_revenue = round(sum(row[10] for row in data), 2) if data else 0
    total_gst     = round(sum(row[11] for row in data), 2) if data else 0
    grand_total   = round(sum(row[12] for row in data), 2) if data else 0

    return render_template(
        'search.html',
        data=data,
        query=query,
        filter_by=filter_by,
        total_revenue=total_revenue,
        total_gst=total_gst,
        grand_total=grand_total
    )

# ================= RUN =================

if __name__ == '__main__':
    app.run(debug=True)
