from flask import Flask, render_template, request, redirect, url_for, session, abort,jsonify
import mysql.connector
import secrets


app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Harsha@2003',
    'database': 'coffee'
}

# Establish a connection to the database
db_connection = mysql.connector.connect(**db_config)
cursor = db_connection.cursor()

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Display menu items
@app.route('/menu')
def menu():
    cursor.execute('SELECT * FROM menu_items')
    menu_items = cursor.fetchall()
    return render_template('menu.html', menu_items=menu_items)

# Add a new menu item
@app.route('/add_menu_item', methods=['GET', 'POST'])
def add_menu_item():
    if request.method == 'POST':
        item_name = request.form['item_name']
        item_price = request.form['item_price']

        # Insert the new menu item into the database
        cursor.execute('INSERT INTO menu_items (item_name, item_price) VALUES (%s, %s)', (item_name, item_price))
        db_connection.commit()

        return redirect(url_for('menu'))

    return render_template('add_menu_item.html')

# In app.py
from flask import jsonify

@app.route('/remove_menu_item/<int:item_id>', methods=['POST'])
def remove_menu_item(item_id):
    try:
        # Delete the menu item from the database
        cursor.execute('DELETE FROM menu_items WHERE item_id = %s', (item_id,))
        db_connection.commit()

        # Return success response
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error deleting item: {e}")
        # Return error response
        return jsonify({'status': 'error'}), 500


# Admin Dashboard route
@app.route('/admin_dashboard')
def admin_dashboard():
    # Check if the user is an admin based on the session
    is_admin = session.get('is_admin', False)

    if not is_admin:
        # Redirect non-admin users to the login page
        return redirect(url_for('login'))

    # Fetch menu items from the database
    cursor.execute('SELECT item_id, item_name, item_price FROM menu_items')
    menu_items = [dict(zip(cursor.column_names, row)) for row in cursor.fetchall()]

    # Pass the is_admin and menu_items variables to the template
    return render_template('admin_dashboard.html', is_admin=is_admin, menu_items=menu_items)





# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the provided credentials are valid for admin
        cursor.execute('SELECT * FROM admins WHERE username = %s AND password = %s', (username, password))
        admin = cursor.fetchone()

        if admin:
            # Store admin status in the session
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

# Order route
@app.route('/order/<int:item_id>', methods=['GET', 'POST'])
def order(item_id):
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        quantity = int(request.form['quantity'])

        # Get the selected menu item
        cursor.execute('SELECT * FROM menu_items WHERE item_id = %s', (item_id,))
        menu_item = cursor.fetchone()

        if menu_item:
            total_price = menu_item[2] * quantity

            # Insert the order into the orders table
            cursor.execute('INSERT INTO orders (customer_name, item_id, quantity, total_price) VALUES (%s, %s, %s, %s)',
                           (customer_name, item_id, quantity, total_price))
            db_connection.commit()

            return redirect(url_for('menu'))

    # If it's a GET request or form submission fails, render the order page
    cursor.execute('SELECT * FROM menu_items WHERE item_id = %s', (item_id,))
    menu_item = cursor.fetchone()
    return render_template('order.html', menu_item=menu_item)

# Display all orders
@app.route('/orders')
def orders():
    # Assuming you have an 'item_name' column in the 'menu_items' table
    cursor.execute('SELECT orders.order_id, orders.customer_name, menu_items.item_name, orders.quantity, orders.total_price, orders.order_date FROM orders JOIN menu_items ON orders.item_id = menu_items.item_id')
    all_orders = cursor.fetchall()

    return render_template('orders.html', all_orders=all_orders)


# Update menu item route
@app.route('/update_menu_item/<int:item_id>', methods=['GET', 'POST'])
def update_menu_item(item_id):
    if request.method == 'POST':
        # Get updated values from the form
        updated_name = request.form['updated_name']
        updated_price = float(request.form['updated_price'])

        # Update the menu item in the database
        cursor.execute('UPDATE menu_items SET item_name = %s, item_price = %s WHERE item_id = %s',
                       (updated_name, updated_price, item_id))
        db_connection.commit()

        return redirect(url_for('menu'))

    # Fetch the existing details of the menu item
    cursor.execute('SELECT * FROM menu_items WHERE item_id = %s', (item_id,))
    existing_item = cursor.fetchone()

    return render_template('update_menu_item.html', item=existing_item)

# Logout route
@app.route('/logout')
def logout():
    # Clear the admin status from the session
    session.pop('is_admin', None)
    return redirect(url_for('login'))

# Route to handle "Add to Cart" requests
@app.route('/add_to_cart', methods=['POST'])
@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    try:
        quantity = int(request.json['quantity'])

        # Validate quantity (ensure it's a positive value)
        if quantity <= 0:
            return jsonify({'error': 'Invalid quantity'}), 400

        # Get the selected menu item
        cursor.execute('SELECT * FROM menu_items WHERE item_id = %s', (item_id,))
        menu_item = cursor.fetchone()

        if not menu_item:
            return jsonify({'error': 'Menu item not found'}), 404

        # Add the item to the cart in the database
        cursor.execute('INSERT INTO cart (item_id, quantity) VALUES (%s, %s) ON DUPLICATE KEY UPDATE quantity = quantity + %s',
                       (item_id, quantity, quantity))
        db_connection.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

