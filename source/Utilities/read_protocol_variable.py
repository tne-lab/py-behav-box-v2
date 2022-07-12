def read_protocol_variable(row):
    if row[2] == "NUMBER":
        return float(row[1])
    elif row[2] == "TEXT":
        return row[1]
    elif row[2] == "BOOL":
        return bool(row[1])
    else:
        raise ValueError("Type {} for variable {} is not valid.".format(row[2], row[0]))
