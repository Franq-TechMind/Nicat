from app import create_app
import os

config_class = 'config.ProductionConfig' if os.environ.get('FLASK_ENV') == 'production' else 'config.DevelopmentConfig'
app = create_app(config_class)

if __name__ == '__main__':
    app.run(debug=True)
