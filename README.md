# BIP39 Bitcoin Private Key Generator

A secure Bitcoin private key and mnemonic generator that uses multiple entropy sources to ensure high randomness and security.
you can enter /dist to use the exe file

## Core Features

- Generates BIP39 standard mnemonic phrases (12 or 24 words)
- Creates Bitcoin private keys in multiple formats (Hex, WIF)
- Uses extensive entropy collection methods for maximum security
- Available in both GUI and command-line interfaces
- Can be used completely offline for cold storage solutions

## Security Design

This generator employs a sophisticated multi-layered approach to randomness:

1. **System Time-Based Entropy**
   - Current timestamp (millisecond precision)
   - Performance counter values
   - Process execution time

2. **Hardware-Based Entropy**
   - CPU usage patterns
   - Memory allocation statistics
   - I/O operation timing
   - Network interface information
   - MAC address
   - System performance metrics

3. **Software-Based Entropy**
   - Cryptographically secure random number generator
   - Multiple hash function operations
   - Thread competition entropy
   - Process ID and execution environment
   - File system metadata sampling

4. **Mixing Algorithm**
   - All entropy sources are combined with XOR operations
   - Final SHA-256 hash applied to create the seed for mnemonic generation
   - Follows BIP39 specification for mnemonic creation and validation

## Installation

### Prerequisites

1. Python 3.6 or higher
   - Download from [Python Official Website](https://www.python.org/downloads/)

2. Required dependencies:
   ```bash
   pip install psutil tkinter
   ```

3. Required files:
   - generator.py (core logic)
   - gui.py (graphical interface)
   - english.txt (BIP39 wordlist)

### Executable Version

You can run the program directly as an executable:

1. Download the latest release from the project page
2. No installation required - simply run the .exe file
3. All dependencies are included in the executable

## Usage Instructions

### GUI Method (Recommended for Most Users)

1. Launch the application:
   - If using Python: `python gui.py`
   - If using executable: double-click the .exe file

2. Select mnemonic length (12 or 24 words)

3. Click "Generate Random Mnemonic"

4. The application will display:
   - Mnemonic phrase
   - Seed (hex format)
   - Master private key (hex format)
   - WIF format private key (wallet importable)

5. Copy and securely store your keys

### Command Line Method

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)

2. Navigate to the program directory
   ```bash
   cd path/to/program/directory
   ```

3. Run the program
   ```bash
   python generator.py
   ```

4. Follow the on-screen instructions to:
   - Generate a completely random mnemonic, or
   - Create a partially customized mnemonic

## Technical Details

### BIP39 Implementation

The generator implements the Bitcoin Improvement Proposal 39 (BIP39) standard for creating mnemonic sentences:

1. Secure entropy is generated (128 bits for 12 words, 256 bits for 24 words)
2. A checksum is calculated by taking the first (entropy-length/32) bits of the SHA-256 hash of the entropy
3. The entropy is combined with the checksum
4. The resulting sequence is split into 11-bit groups
5. Each 11-bit group is mapped to a word from the BIP39 wordlist
6. The mnemonic seed is derived using PBKDF2-HMAC-SHA512 with 2048 iterations
7. BIP32 derivation is used to generate the master private key

### Key Formats

The generator produces several formats of the same private key:

- **Raw Entropy**: The initial randomness used to create the mnemonic
- **Mnemonic**: Human-readable phrase (12 or 24 words) that encodes the entropy
- **Seed**: Extended key material derived from the mnemonic (64 bytes)
- **Master Private Key**: The root key for the HD wallet structure (32 bytes)
- **WIF Private Key**: Wallet Import Format - widely compatible encoded format

## Security Recommendations

1. **Offline Generation**: For maximum security, use this program on an air-gapped computer that has never and will never connect to the internet

2. **Physical Security**: Write down your mnemonic phrase on paper and store in a secure location like a safe

3. **Test Before Use**: Always send a small amount first and verify you can access it before storing significant funds

4. **Multi-Location Backups**: Consider storing backups of your mnemonic in multiple secure physical locations

5. **Avoid Digital Storage**: Don't store your mnemonic or private keys in digital form (no screenshots, digital documents, emails, or cloud storage)

## FAQ

**Q: Why does the generator create different mnemonics every time?**  
A: This is by design. The program uses multiple random sources to ensure each mnemonic is unique and unpredictable.

**Q: Is this compatible with hardware wallets like Ledger or Trezor?**  
A: Yes, the generated 12/24-word mnemonics follow the BIP39 standard and can be imported into most hardware wallets.

**Q: What's the advantage of using this over wallet-generated keys?**  
A: This generator uses multiple entropy sources and can be run completely offline, potentially providing better randomness than some wallet implementations.

**Q: Can I use a portion of a custom mnemonic?**  
A: Yes, the program supports generating mnemonics with some custom words in specified positions.

**Q: How secure is the randomness?**  
A: The program combines cryptographically secure random number generation with system entropy from multiple sources, making predictability extremely difficult.

## Disclaimer

This program is for educational and research purposes only. Users assume all risks associated with cryptocurrency storage and key management. Always verify your backup process and ensure you understand how to properly secure and use cryptographic keys before storing significant value.

[中文版说明](README_CN.md)
