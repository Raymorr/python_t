from simplecrypt import decrypt

with open("encrypted.bin", "rb") as inp:
    encrypted = inp.read()

with open("passwords.txt", "r") as inp:
    passw = inp.read()

with open("1.txt", "wb") as wr:
    for i in passw.split():
        try:
            q = decrypt(i, encrypted)
        except:
            pass
        else:
            wr.write(q)