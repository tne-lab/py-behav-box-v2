def find_closing_paren(pstr, ind):
    counter = 1
    cind = ind
    while counter > 0 and cind < len(pstr) - 1:
        cind += 1
        if pstr[cind] == '(':
            counter += 1
        elif pstr[cind] == ')':
            counter -= 1
    if counter == 0:
        return cind
    else:
        return None
