import sys
from app import ImageBackupApp

if __name__ == '__main__':
    app = ImageBackupApp(sys.argv)
    sys.exit(app.run())