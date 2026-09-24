import os
from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', Config.PORT))
    print("=" * 70)
    print("  DNAura — DNA Sequence Classification & Prediction System")
    print(f"  Starting server on http://127.0.0.1:{port}")
    print("=" * 70)
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG, use_reloader=False)
