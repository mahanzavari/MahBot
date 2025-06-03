import os
import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, shell=False):
    """Run a command and log its output."""
    try:
        if isinstance(command, str):
            logger.info(f"Running command: {command}")
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            logger.info(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        if result.stdout:
            logger.info(f"Command output: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        raise

def setup_colab_environment():
    """Set up the environment for running the application on Google Colab."""
    logger.info("Setting up Colab environment...")
    
    try:
        # Install system dependencies
        run_command('apt-get update')
        run_command('apt-get install -y postgresql postgresql-contrib libpq-dev')
        
        # Start PostgreSQL service
        run_command('service postgresql start')
        
        # Create database and user
        run_command('sudo -u postgres psql -c "CREATE USER colab_user WITH PASSWORD \'colab_password\';"')
        run_command('sudo -u postgres psql -c "CREATE DATABASE MahBot_db;"')
        run_command('sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE MahBot_db TO colab_user;"')
        
        # Force uninstall numpy 2.x and install numpy 1.x
        run_command([sys.executable, '-m', 'pip', 'uninstall', '-y', 'numpy'])
        run_command([sys.executable, '-m', 'pip', 'install', 'numpy==1.24.3'])
        
        # Install Python dependencies with specific versions
        run_command([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Install specific versions of torch and transformers
        run_command([sys.executable, '-m', 'pip', 'install', 'torch==2.1.0', 'transformers==4.36.2'])
        
        # Install other dependencies
        run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        # Download required models
     
        
        # Create .env file
        env_content = """SECRET_KEY=colab-secret-key
DATABASE_URL=postgresql://colab_user:13831377@localhost:5432/MahBot_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        
        logger.info("Environment setup completed!")
    except Exception as e:
        logger.error(f"Error during environment setup: {str(e)}")
        raise

def initialize_database():
    """Initialize the database with migrations."""
    logger.info("Initializing database...")
    try:
        # Set environment variables for Flask
        os.environ['FLASK_APP'] = 'app.py'
        
        # Initialize database
        run_command('flask db init')
        run_command('flask db migrate -m "Initial migration"')
        run_command('flask db upgrade')
        
        logger.info("Database initialization completed!")
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise

def setup_ngrok():
    """Set up ngrok for external access."""
    logger.info("Setting up ngrok...")
    try:
        run_command([sys.executable, '-m', 'pip', 'install', 'pyngrok'])
        
        from pyngrok import ngrok
        ngrok_tunnel = ngrok.connect(5000)
        logger.info(f'Public URL: {ngrok_tunnel.public_url}')
        return ngrok_tunnel
    except Exception as e:
        logger.error(f"Error setting up ngrok: {str(e)}")
        raise

def check_gpu():
    """Check if GPU is available."""
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
            return True
        else:
            logger.info("No GPU detected, using CPU")
            return False
    except Exception as e:
        logger.warning(f"Error checking GPU: {str(e)}")
        return False

def main():
    """Main function to run the application on Colab."""
    try:
        # Check GPU availability
        check_gpu()
        
        # Setup environment
        setup_colab_environment()
        
        # Initialize database
        initialize_database()
        
        # Setup ngrok
        ngrok_tunnel = setup_ngrok()
        
        # Start Flask application
        logger.info("Starting Flask application...")
        run_command('python app.py')
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during setup: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'ngrok_tunnel' in locals():
            ngrok_tunnel.close()

if __name__ == '__main__':
    main() 