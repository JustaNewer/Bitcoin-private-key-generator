# BIP39 Bitcoin Private Key Generator

A secure Bitcoin private key and mnemonic generator that uses multiple entropy sources to ensure high randomness and security.

## Features

- Generates 12-word mnemonic phrases (BIP39 standard)
- Generates corresponding Bitcoin private keys (multiple formats)
- Uses multiple entropy sources for enhanced security:
  - Current time (millisecond precision)
  - CPU performance counter
  - Process time
  - System random number
  - 10,000 random numbers
  - Cryptographically secure random bytes

## Prerequisites

1. Python 3.6 or higher installed
   - Download from [Python Official Website](https://www.python.org/downloads/)

2. Required files
   - generator.py (main program)
   - english.txt (BIP39 wordlist)
   - Ensure both files are in the same directory

## Usage

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)

2. Navigate to the program directory
   ```bash
   cd path/to/program/directory
   ```

3. Run the program
   ```bash
   python generator.py
   ```

4. The program will generate and display:
   - Generation timestamp
   - 12-word mnemonic phrase
   - Seed (hex format)
   - Master private key (hex format)
   - WIF format private key (wallet importable)

## Sample Output

BIP39 Mnemonic and Private Key Generator
------------------------
Generation time: 2024-01-20 14:30:25.123456
Performance counter: 12345.6789
Process time: 0.123456
Extra random length: 10000

Generated mnemonic:
word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12

Generated seed (hex):
1234...(64 character hex string)

Master private key (hex):
5678...(64 character hex string)

WIF format private key (compressed):
KxXX...(starts with K or L)

## Security Tips

1. Keep your mnemonic phrase and private keys secure and never share them
2. Run this program in an offline environment
3. Clear the display after use
4. Preferably use a new offline computer to generate keys
5. Write down the mnemonic phrase on paper immediately and store it safely

## Important Notes

- This program generates real Bitcoin private keys - use with caution
- Lost mnemonics or private keys cannot be recovered - backup safely
- Test with small amounts first
- Understand Bitcoin wallet usage before using for actual storage

## FAQ

Q: Why does it generate different mnemonics each time?  
A: This is normal. The program uses multiple random sources to ensure each mnemonic is unique.

Q: Can I use the generated private key directly?  
A: Yes, the WIF format private key can be imported into most Bitcoin wallets.

Q: Does the program need internet connection?  
A: No. This program can run completely offline.

## Disclaimer

This program is for educational and research purposes only. Users assume all risks associated with using the generated private keys for any transactions. Make sure you fully understand the importance and proper usage of Bitcoin private keys.

[中文版说明](README_CN.md)