# Contains secondary helper functions


def erroronezero():
    ''' error message '''
    print 'Please enter 0 or 1!'


def errornumber():
    ''' error message '''
    print 'Please enter a valid number!'


def strip(s):
    '''Strip spaces from left and right'''
    s = s.lstrip()
    s = s.rstrip()
    return s


def gettokens(s):
    '''Return list of words in the problem'''
    replacelist = ['-', ',', '.', '?', '!', '&']
    s = s.lower()
    for c in replacelist:
        s = s.replace(c, ' ')
    return s.strip().split()


def mass(db, s, tokens, t):
    '''Return mass of property of query is non-zero and 0 o.w. '''
    if s == 'problems':
        problem = db.problems.find_one({'tokens': tokens})
        return problem[t]
    elif s == 'questions':
        question = db.problems.find_one({'tokens': tokens})
        return question[t]