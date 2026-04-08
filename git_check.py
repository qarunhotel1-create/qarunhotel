import subprocess
import os

def run_git():
    commands = [
        ["git", "remote", "-v"],
        ["git", "status"],
        ["git", "rev-parse", "HEAD"],
        ["git", "rev-parse", "origin/main"]
    ]
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with code {e.returncode}")
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
        print("-" * 20)

if __name__ == "__main__":
    run_git()
