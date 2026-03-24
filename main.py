import auth
import views
from app import app

if __name__ == "__main__":
    app.secret_key = "GTYlv>K]0=otL=B`@z^s"  # some randomly generated string
    app.register_blueprint(views.bp)
    app.register_blueprint(auth.bp)
    app.run(debug=True)
