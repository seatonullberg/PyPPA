
def snake_case_to_pascal_case(input_string):
    """
    Converts the input string from snake_case to PascalCase
    :param input_string: (str) a snake_case string
    :return: (str) a PascalCase string
    """
    input_list = input_string.split('_')
    input_list = [i.capitalize() for i in input_list]
    output = ''.join(input_list)
    return output


def pascal_case_to_snake_case(input_string):
    """
    Converts the input string from PascalCase to snake_case
    :param input_string: (str) a PascalCase string
    :return: (str) a snake_case string
    """
    output_list = []
    for i, char in enumerate(input_string):
        if char.capitalize() == char:  # if the char is already capitalized
            if i == 0:
                output_list.append(char.lower())  # the first char is only made lowercase
            else:
                output_list.append('_')
                output_list.append(char.lower())  # other capital chars are prepended with an underscore
        else:
            output_list.append(char)
    output = ''.join(output_list)
    return output
