import operator

ops = {
    "equal": operator.eq, 
    "not equal": operator.ne, 
    "in": lambda x,y: x in y, 
    "not in": lambda x,y: x not in y, 
    "or": operator.or_, 
    "and": operator.and_,
    "gt": operator.gt,
    "lt": operator.lt,
    "ge": operator.ge,
    "le": operator.le
}

def use_operator(cond1, cond2, op: str):
    if op in ops:
        return ops[op](cond1, cond2)
    else:
        raise ValueError(f"Unsupported operation: {op}")
    
def dict_to_tuple(d):
    return tuple(sorted((k, dict_to_tuple(v) if isinstance(v, dict) else v) for k, v in d.items()))

def extend_unique_records(ref_records, records):
    set_ref_records = set(dict_to_tuple(record) for record in ref_records)
    missing = [record for record in records if dict_to_tuple(record) not in set_ref_records]
    ref_records.extend(missing)