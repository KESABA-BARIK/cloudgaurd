from flask import Flask
from flask_cors import CORS

from routes.logs_routes import logs_bp
from routes.baseline_routes import baseline_bp
from routes.ml_routes import ml_bp
from routes.dashboard_routes import dashboard_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(logs_bp)
app.register_blueprint(baseline_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(dashboard_bp)

if __name__ == '__main__':
    app.run(debug=True)