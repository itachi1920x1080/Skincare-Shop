Darling Skincare Store 🧴
A modern, responsive e-commerce web application for skincare products. This project features a Python (Flask) backend, a dynamic shopping cart system, and a custom bank payment (ABA Pay) QR integration.

🚀 Features
Template Inheritance: Uses a master base.html to maintain a consistent header and footer across all pages.

Dynamic Shopping Cart: A JavaScript-powered cart that handles adding/removing items and real-time total calculations.

Payment Integration: A dedicated QR payment modal for local bank transfers.

Feedback System: A dedicated page for user feedback that connects directly to the Python backend.

Responsive Design: Built with CSS Grid and Flexbox to ensure the store looks great on mobile, tablet, and desktop.

📂 Project Structure
For the application to run correctly, the files must be organized in the following hierarchy:

Plaintext
/Skincare-Shop-v
├── app.py              # Flask Backend & Routes
├── templates/          # HTML Templates (Jinja2)
│   ├── base.html       # Master Layout (Header/Footer)
│   ├── index.html      # Home Hero Page
│   ├── products.html   # Product Grid
│   ├── feedback.html   # Feedback Form
│   └── login.html      # User Authentication
└── static/             # Static Assets
    ├── CSS/
    │   └── Style.css   # Main Stylesheet
    ├── JS/
    │   └── Style-js.js # Cart & Modal Logic
    └── image/          # Product & Logo Images
🛠️ Installation & Setup
Clone the project to your local machine.

Initialize a virtual environment (recommended):

Bash
python -m venv .venv
.venv\Scripts\activate
Install Flask:

Bash
pip install flask
Run the application:

Bash
python app.py
Access the store: Open http://127.0.0.1:5000 in your web browser.

🔧 Technical Details
Backend: Flask (Python 3.x)

Frontend: HTML5, CSS3, JavaScript (Vanilla ES6)

Animations: AOS (Animate On Scroll) library

Icons: Font Awesome 6.0

📜 Credits
Darling Skincare is a Team build project © 2026. All rights reserved.