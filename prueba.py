
import string
import random

def gen_password(chars = string.ascii_uppercase + string.digits + string.ascii_lowercase, N=30):
	return ''.join(random.choice(chars) for _ in range(int(N)))

print(gen_password())