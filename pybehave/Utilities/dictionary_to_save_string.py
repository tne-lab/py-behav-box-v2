def dictionary_to_save_string(dic):
    if dic is not None:
        save_string = ""
        count = 0
        for key in dic:
            save_string += "{}={}".format(key, str(dic[key]))
            if count < len(dic) - 1:
                save_string += "|"
            count += 1
        return save_string
    else:
        return None

