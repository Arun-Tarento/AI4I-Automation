import sys
import shutil
from pathlib import Path


def switch_environment(env_name):
    """Switch to specified environment by copying env file"""
    env_file = Path(f".env.{env_name}")
    target = Path(".env")
    
    if not env_file.exists():
        print(f"❌ Environment file {env_file} not found")
        sys.exit(1)
    
    shutil.copy(env_file, target)
    print(f"✅ Switched to {env_name} environment")
    print(f"   Using: {env_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python switch_env.py <sandbox|dev|prod>")
        sys.exit(1)
    
    switch_environment(sys.argv[1])