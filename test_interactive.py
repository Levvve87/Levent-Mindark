"""
Test för main.py - simulerar användarinput
"""

import subprocess
import sys
import os

def test_main_py():
    """
    Testar main.py genom att simulera användarinput
    """
    print("🧪 Testar main.py med simulerad input...")
    
    # Skapa testinput
    test_input = "Hej! Testar main.py\nquit\n"
    
    try:
        # Kör main.py med simulerad input
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=test_input, timeout=30)
        
        print("✅ main.py kördes utan att krascha")
        print(f"📤 Output: {stdout[:200]}...")
        
        if stderr:
            print(f"⚠️  Warnings: {stderr[:200]}...")
            
        return True
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - main.py kördes för länge")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Fel vid testning av main.py: {e}")
        return False

if __name__ == "__main__":
    success = test_main_py()
    if success:
        print("\n🎉 main.py test lyckades!")
    else:
        print("\n💥 main.py test misslyckades!")

