from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return '''
    <script>alert("test")</script>
    Hello, World!
    '''
