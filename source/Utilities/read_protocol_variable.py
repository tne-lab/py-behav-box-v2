import csv


def read_protocol_variable(row):
    if row[2] == "NUMBER":
        return float(row[1])
    elif row[2] == "TEXT":
        return row[1]
    elif row[2] == "BOOL":
        return row[1] == "True"
    elif row[2] == "PROTOCOL":
        with open(row[1], newline='') as csvfile:
            protocol_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            protocol = {}
            for row in protocol_reader:
                protocol[row[0]] = read_protocol_variable(row)
            return protocol
    else:
        raise ValueError("Type {} for variable {} is not valid.".format(row[2], row[0]))
