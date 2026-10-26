import bcrypt

print(
    bcrypt.hashpw(
        b"12",
        bcrypt.gensalt(rounds=12)
    ).decode()
)