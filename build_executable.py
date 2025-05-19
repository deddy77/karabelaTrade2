import PyInstaller.__main__
import os
import shutil

def build_executable():
    # Clean existing build and dist directories
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    # PyInstaller configuration
    PyInstaller.__main__.run([
        'main.py',
        '--name=KarabelaTrade',
        '--onefile',
        '--noconsole',
        '--add-data=MQL5;MQL5',
        '--add-data=requirements.txt;.',
        '--add-data=*.md;.',
        '--add-data=*.txt;.',
        '--clean',
        '--log-level=INFO',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=MetaTrader5',
        '--hidden-import=matplotlib',
        '--hidden-import=pytz',
        '--hidden-import=tabulate',
        '--hidden-import=ta',
        '--hidden-import=requests',
        '--hidden-import=discord_webhook'
    ])

if __name__ == '__main__':
    build_executable()
    print("Build completed! Check the 'dist' directory for KarabelaTrade.exe")
