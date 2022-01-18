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


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        item_name = request.form['itemname']
        item_id = request.form['itemid']
        item_qty = request.form['quantity']
        cost_per_unit = request.form['costperunit']
        
        if len(item_name) > 100:
            return 'Item Name cannot exceed 100 characters'
        # check that item_id is a non-negative integer
        try:
            item_id = int(item_id)
        except:
            return 'Product ID must be an integer'

        if item_id < 0:
            return 'Product ID must be non-negative'

        # check that quantity is a non-negative integer
        try:
            item_qty = int(item_qty)
        except:
            return 'Quantity must be an integer'

        if item_qty < 0:
            return 'Quantity must be non-negative'

        try:
            cost_per_unit = float(cost_per_unit)
        except:
            return 'Cost per Unit value is invalid'

        if cost_per_unit < 0:
            return 'Cost per Unit must be non-negative'
        
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
        # item.quantity = request.form['quantity']
        item_qty = request.form['quantity']
        cost_per_unit = request.form['costperunit']

        # check that quantity is a non-negative integer
        try:
            item_qty = int(item_qty)
        except:
            return 'Quantity must be an integer'

        if item_qty < 0:
            return 'Quantity must be non-negative'

        item.quantity = item_qty

        try:
            cost_per_unit = float(cost_per_unit)
        except:
            return 'Cost per Unit value is invalid'

        if cost_per_unit < 0:
            return 'Cost per Unit must be non-negative'

        cost_per_unit_cents = cost_per_unit * 100
        total_value_cents = cost_per_unit_cents * item_qty
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