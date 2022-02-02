def get_zeros(counter):
    if 1 <= counter <= 9:
        return '00'
    elif 10 <= counter <= 99:
        return '0'
    else:
        return ''
