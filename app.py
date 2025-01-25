import os
import stripe
from flask import Flask, render_template, send_from_directory, request, redirect, url_for
from dotenv import load_dotenv
import fitz

# Flask app initialization
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Stripe keys
stripe_keys = {
    'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
    'secret_key': os.getenv('STRIPE_SECRET_KEY'),
}
stripe.api_key = stripe_keys['secret_key']

# File paths
UPLOAD_FOLDER = r'static\products'
PREVIEW_FOLDER = r'static\product_previews'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



class Product:
    def __init__(self, id, name, price, file):
        self.id = id
        self.name = name
        self.price = price
        self.file = file
        self.preview_url = None


products = [
    Product(1, 'PDF file 1', 10, 'doc1.pdf'),
    Product(2, 'PDF file 2', 15, 'doc2.pdf'),
    Product(3, 'PDF file 3', 20, 'doc3.pdf'),
]


def generate_pdf_preview(pdf_file, preview_filename):
    if not os.path.exists(PREVIEW_FOLDER):
        os.makedirs(PREVIEW_FOLDER)

    preview_path = os.path.join(PREVIEW_FOLDER, preview_filename)
    doc = fitz.open(pdf_file)
    page = doc.load_page(0)
    pix = page.get_pixmap()
    pix.save(preview_path)



@app.route('/')
def index():
    for product in products:
        preview_filename = f"{product.file.split('.')[0]}_preview.png"
        preview_url = url_for('download_preview', filename=preview_filename)
        if not os.path.exists(os.path.join(PREVIEW_FOLDER, preview_filename)):
            generate_pdf_preview(os.path.join(UPLOAD_FOLDER, product.file), preview_filename)
        product.preview_url = preview_url

    return render_template('index.html', products=products, stripe_key=stripe_keys['publishable_key'])



@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p.id == product_id), None)
    if product:
        preview_url = url_for('download_preview', filename=f"{product.file.split('.')[0]}_preview.png")
        return render_template('product_detail.html', product=product, preview_url=preview_url,
                               stripe_key=stripe_keys['publishable_key'])
    return "Product not found", 404



@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    product_id = int(request.form['product_id'])
    product = next((p for p in products if p.id == product_id), None)

    if not product:
        return "Product not found", 404

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product.name,
                },
                'unit_amount': product.price * 100,
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
    return render_template('success.html')



@app.route('/cancel')
def payment_cancel():
    return render_template('cancel.html')


@app.route('/download_preview/<filename>')
def download_preview(filename):
    return send_from_directory(PREVIEW_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
