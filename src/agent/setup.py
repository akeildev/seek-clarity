#!/usr/bin/env python3
"""
Setup script for Clarity voice agent
"""

import os
import sys
import subprocess
import platform


def check_python_version():
    """Ensure Python 3.9+ is installed"""
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")


def create_venv():
    """Create virtual environment"""
    venv_path = "venv"
    if os.path.exists(venv_path):
        print(f"✓ Virtual environment already exists at {venv_path}")
        return venv_path

    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
    print(f"✓ Virtual environment created at {venv_path}")
    return venv_path


def install_requirements(venv_path):
    """Install requirements in virtual environment"""
    pip_path = os.path.join(venv_path, "bin", "pip")
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")

    print("Installing requirements...")
    subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    print("✓ Requirements installed successfully")


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = ".env"
    if os.path.exists(env_path):
        print(f"✓ .env file already exists")
        return

    print("Creating .env file...")
    env_content = """# LiveKit Configuration (use same values from main .env)
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

# OpenAI Configuration
OPENAI_API_KEY=

# ElevenLabs Configuration (optional)
ELEVEN_API_KEY=
ELEVEN_VOICE_ID=EXAVITQu4vr4xnSDxMaL
"""
    with open(env_path, "w") as f:
        f.write(env_content)
    print(f"✓ Created .env file - please add your API keys")


def main():
    """Main setup function"""
    print("Setting up Clarity Voice Agent")
    print("-" * 40)

    check_python_version()
    venv_path = create_venv()
    install_requirements(venv_path)
    create_env_file()

    print("-" * 40)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Add your API keys to src/agent/.env")
    print("2. Activate virtual environment:")
    if platform.system() == "Windows":
        print(f"   {venv_path}\\Scripts\\activate")
    else:
        print(f"   source {venv_path}/bin/activate")
    print("3. Run the agent:")
    print("   python voice_agent.py")


if __name__ == "__main__":
    main()