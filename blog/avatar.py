from hashlib import md5


def avatar(email, size):
    return "http://cn.gravatar.com/avatar/" + md5(email.encode()).hexdigest() +\
                                                  "?d=identicon&s=" + str(size)
