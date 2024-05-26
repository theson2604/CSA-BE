import operator

ops = {
    "equal": operator.eq, 
    "not equal": operator.ne, 
    "in": lambda x,y: x in y, 
    "not in": lambda x,y: x not in y, 
    "or": operator.or_, 
    "and": operator.and_ 
}

def use_operator(cond1, cond2, op: str):
    if op in ops:
        return ops[op](cond1, cond2)
    else:
        raise ValueError(f"Unsupported operation: {op}")