from flask import Flask

app = Flask(__name__)

@app.route("/")
def main():
    return "<p>OCSS Backend Docker Container</p>"