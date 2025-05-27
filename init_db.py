from app import app, db
from models import User, Chat, Message

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we need to create an admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com'
            )
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print("Admin user created!")
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db() 