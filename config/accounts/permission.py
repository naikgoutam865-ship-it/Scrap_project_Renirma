def is_user(user):
    return user.role == 'user'


def is_dealer(user):
    return user.role == 'dealer'


def is_artist(user):
    return user.role == 'artist'


def can_upload_scrap(user):
    return user.role == 'user'


def can_request_scrap(user):
    return user.role in ['dealer', 'artist']


def can_create_product(user):
    return user.role == 'artist'


def can_place_order(user):
    return user.role == 'user'
