from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return '''
    <script>alert("PoC by machiavelli")</script>
    <h1>PoC by machiavelli</h1>
    '''
