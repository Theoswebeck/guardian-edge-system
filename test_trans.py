from deep_translator import GoogleTranslator
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_trans.py <text>")
        return
    text = sys.argv[1]
    translated = GoogleTranslator(source='auto', target='en').translate(text)
    print(f"Original: {text}")
    print(f"Translated: {translated}")

if __name__ == '__main__':
    main()
