from src import app
from flask import Flask, render_template
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/index1/')
def about():
    return render_template('index1.html')
if __name__ == "__main__":
    app.run(debug=True)
