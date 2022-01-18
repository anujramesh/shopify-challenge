from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventorydb.db'
db = SQLAlchemy(app)

# database schema
class Inventory(db.Model):
    row_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, unique=True)
    quantity = db.Column(db.Integer)
    cost_per_unit = db.Column(db.Integer)
    total_value = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    date_last_updated = db.Column(db.DateTime, default=datetime.utcnow().replace(microsecond=0))

    def __repr__(self):
        return '<InventoryItem %r>' % self.row_id

# return value of int if string can be converted to non-negative int, return string otherwise
def validate_non_negative_int(str):
    try:
        str_as_int = int(str)
        if str_as_int >= 0:
            return str_as_int
        return str
    except:
        return str

# return value of float if string can be converted to non-negative float, return string otherwise
def validate_non_negative_float(str):
    try:
        str_as_float = float(str)
        if str_as_float >= 0:
            return str_as_float
        return str
    except:
        return str


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        item_name = request.form['itemname']
        item_id = request.form['itemid']
        item_qty = request.form['quantity']
        cost_per_unit = request.form['costperunit']

        # check that item_id, quantity, cost_per_unit are valid, non-negative
        item_id = validate_non_negative_int(item_id)
        if isinstance(item_id, str):
            return 'Item ID entered is invalid'

        item_qty = validate_non_negative_int(item_qty)
        if isinstance(item_qty, str):
            return 'Quantity entered is invalid'

        cost_per_unit = validate_non_negative_float(cost_per_unit)
        if isinstance(cost_per_unit, str):
            return 'Cost per Unit entered is invalid'

        # a standard practice for storing monetary values on a database is in terms of cents (base unit)
        cost_per_unit_cents = cost_per_unit * 100
        total_value_cents = cost_per_unit_cents * item_qty
        
        new_item = Inventory(name=item_name, item_id=item_id, quantity=item_qty, cost_per_unit=cost_per_unit_cents, total_value=total_value_cents)

        try:
            db.session.add(new_item)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your item'
    else:
        items = Inventory.query.order_by(Inventory.date_created).all()
        return render_template('index.html', items=items)


@app.route('/delete/<int:row_id>')
def delete(row_id):
    item_to_delete = Inventory.query.get_or_404(row_id)
    try:
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that item'


@app.route('/update/<int:row_id>', methods=['GET', 'POST'])
def update(row_id):
    item = Inventory.query.get_or_404(row_id)

    if request.method == 'POST':
        item.name = request.form['itemname']
        item_qty = request.form['quantity']
        cost_per_unit = request.form['costperunit']

        # check that quantity, cost_per_unit are valid, non-negative
        item_qty = validate_non_negative_int(item_qty)
        if isinstance(item_qty, str):
            return 'Quantity entered is invalid'

        cost_per_unit = validate_non_negative_float(cost_per_unit)
        if isinstance(cost_per_unit, str):
            return 'Cost per Unit entered is invalid'
        
        # express monetary values in terms of cents to store onto database
        cost_per_unit_cents = cost_per_unit * 100
        total_value_cents = cost_per_unit_cents * item_qty
        # update the values
        item.quantity = item_qty
        item.cost_per_unit = cost_per_unit_cents
        item.total_value = total_value_cents
        item.date_last_updated = datetime.utcnow().replace(microsecond=0)

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating your item'

    else:
        return render_template('update.html', item=item)


@app.route('/export', methods=['GET', 'POST'])
def export():
    conn = sqlite3.connect('inventorydb.db')
    outfile = open('csv_export.csv', 'w')
    outcsv = csv.writer(outfile)

    cursor = conn.execute('select * from Inventory')
    # dump titles of each column
    outcsv.writerow(x[0] for x in cursor.description)
    # dump rows
    outcsv.writerows(cursor.fetchall())
    outfile.close()

    items = Inventory.query.order_by(Inventory.date_created).all()
    return render_template('index.html', items=items)


if __name__ == "__main__":
    app.run(debug=True)
