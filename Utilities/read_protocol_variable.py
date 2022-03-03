def read_protocol_variable(row):
    match row[2]:
        case "NUMBER":
            return float(row[1])
        case "TEXT":
            return row[1]
        case _:
            raise ValueError("Type {} for variable {} is not valid.".format(row[2], row[0]))
