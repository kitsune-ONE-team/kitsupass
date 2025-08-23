# kitsupass

## Usage

```
Usage:
    kitsupass init
        Initialize new password storage and set a password for encryption.
        Reencrypt existing password storage using a new password.
    kitsupass [ls] [subfolder]
        List passwords.
    kitsupass find pass-names...
    	List passwords that match pass-names.
    kitsupass [show] pass-name
        Show existing password.
    kitsupass otp pass-name
        Generate an OTP code.
    kitsupass insert pass-name
        Insert new password using your preferred editor.
    kitsupass edit pass-name
        Insert a new password or edit an existing one using your preferred editor.
    kitsupass rm pass-name
        Remove existing password.
    kitsupass mv old-path new-path
        Renames or moves old-path to new-path.
    kitsupass cp old-path new-path
        Copies old-path to new-path.
    kitsupass help
        Show this text.
    kitsupass version
        Show version information.
```

## Installation

```
python -m pip install --user --upgrade git+https://github.com/kitsune-ONE-team/kitsupass.git
```


## Requirements

- `SecretStorage`
- `bottle`
- `jwskate`
- `pyotp`
