import PyInstaller.__main__
import os
import shutil

def build_executable():
    # Clean existing build and dist directories
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    # Base configuration
    config = [
        'main.py',
        '--name=KarabelaTrade',
        '--onefile',
        '--noconsole',
        '--clean',
        '--log-level=INFO',
        # Hidden imports
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=MetaTrader5',
        '--hidden-import=matplotlib',
        '--hidden-import=pytz',
        '--hidden-import=tabulate',
        '--hidden-import=ta',
        '--hidden-import=requests',
        '--hidden-import=discord_webhook',
        '--hidden-import=tkinter',
        '--hidden-import=queue',
        '--hidden-import=threading',
        # Add data files
        '--add-data=MQL5;MQL5',
        '--add-data=requirements.txt;.',
        '--add-data=*.md;.',
        '--add-data=*.txt;.',
    ]

    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')

    # Create a simple icon file if it doesn't exist
    icon_path = os.path.join('static', 'icon.ico')
    if not os.path.exists(icon_path):
        try:
            import base64
            # Simple icon data (a basic icon in base64)
            icon_data = """
            AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAAMMOAADDDgAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABsbGwAYmJiAHBwcAF1dXUC
            eHh4Anp6egJ7e3sCfHx8Anz8/AJ7e3sCenp6Anh4eAJ1dXUCcHBwAWJiYgBsbGwAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAbGxsAGJiYgBwcHABdXV1Anh4eAJ6enoC/Pz8Anzc3AJ7UVECenh4Anh2dgJ1dXUCcHBw
            AWJiYgBsbGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAABsbGwAYmJiAHBwcAF1dXUCeHh4Anp6egJ8fHwCfHx8Anzc3AJ7
            UVECenh4Anh2dgJ1dXUCcHBwAWJiYgBsbGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbGxsAGJiYgBwcHABdXV1Anh4eAJ6en
            oC/Pz8Anzc3AJ7UVECenh4Anh2dgJ1dXUCcHBwAWJiYgBsbGwAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABsbGwAYmJiAHBw
            cAF1dXUCeHh4Anp6egJ8fHwCfHx8Anzc3AJ7UVECenh4Anh2dgJ1dXUCcHBwAWJiYgBsbGwA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAbGxsAGJiYgBwcHABdXV1Anh4eAJ6enoC/Pz8Anzc3AJ7UVECenh4Anh2dgJ1
            dXUCcHBwAWJiYgBsbGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABsbGwAYmJiAHBwcAF1dXUCeHh4Anp6egJ8fHwCfH
            x8Anzc3AJ7UVECenh4Anh2dgJ1dXUCcHBwAWJiYgBsbGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbGxsAGJiYgBwcHAB
            dXV1Anh4eAJ6enoC/Pz8Anzc3AJ7UVECenh4Anh2dgJ1dXUCcHBwAWJiYgBsbGwAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAZGRkAW9vbwJ2dnYCeXl5AnV1dQJwcHABZGRkAQAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGRkZAFvb28CdnZ2Anl5eQJ1dXUCcHBwAWRk
            ZAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==
            """
            icon_bytes = base64.b64decode(icon_data)
            with open(icon_path, 'wb') as f:
                f.write(icon_bytes)
            # Add icon to config
            config.append(f'--icon={icon_path}')
        except Exception as e:
            print(f"Warning: Could not create icon file: {str(e)}")

    # Run PyInstaller
    PyInstaller.__main__.run(config)

if __name__ == '__main__':
    build_executable()
    print("Build completed! Check the 'dist' directory for KarabelaTrade.exe")
