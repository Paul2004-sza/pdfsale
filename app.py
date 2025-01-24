import os
import stripe
from flask import Flask, render_template, send_from_directory, request, redirect, url_for
from dotenv import load_dotenv

app = Flask(__name__)


load_dotenv()

stripe_keys = {
    'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
    'secret_key': os.getenv('STRIPE_SECRET_KEY'),
}

stripe.api_key = stripe_keys['secret_key']


UPLOAD_FOLDER = r'C:\Users\Sut Zaw Aung\OneDrive\Desktop\products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

products = [
    {'id': 1, 'name': 'Product 1', 'price': 10, 'file': 'doc1.pdf'},
    {'id': 2, 'name': 'Product 2', 'price': 15, 'file': 'doc2.pdf'},
    {'id': 3, 'name': 'Product 3', 'price': 20, 'file': 'doc3.pdf'},
]

@app.route('/')
def index():
    return render_template('index.html', products=products, stripe_key=stripe_keys['publishable_key'])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return render_template('product_detail.html', product=product, stripe_key=stripe_keys['publishable_key'])
    return "Product not found", 404

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    product_id = request.form['product_id']
    product = next((p for p in products if str(p['id']) == product_id), None)

    if not product:
        return "Product not found", 404


    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product['name'],
                },
                'unit_amount': product['price'] * 100,  # Amount in cents
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('payment_success', _external=True),
        cancel_url=url_for('payment_cancel', _external=True),
    )
    return redirect(session.url, code=303)

@app.route('/success')
def payment_success():
    return "Payment Successful! Thank you for your purchase."

@app.route('/cancel')
def payment_cancel():
    return "Payment Cancelled."


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
