from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "darling_secret_key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")
@app.route("/products")
def products():
    return render_template("products.html")


@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    # if request.method == 'POST':
    #     # Get data from the form
    #     name = request.form.get('name')
    #     message = request.form.get('message')
        
    #     # In a real app, you'd save this to a database here
    #     print(f"Feedback from {name}: {message}")
        
    #     # Send a pop-up message to the next page
    #     flash("Thank you! We've received your feedback.")
        return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
