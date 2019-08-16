from textwrap import dedent

def multisegment_number(number_str):
    output = ""
    spacer = " " * 3

    for line in range(1,4):
        for num in number_str:
            output += segment(num).split('\n')[line] + spacer
        output+='\n'
    return output


def segment(number):
    return dedent(
        {
            "0": """
                ┏━┓
                ┃ ┃
                ┗━┛""",
            "1": """
                  ┃
                  ┃
                  ┃""",
            "2": """
                ━━┓
                ┏━┛
                ┗━━""",
            "3": """
                ━━┓
                ━━┫
                ━━┛""",
            "4": """
                ┃ ┃
                ┗━┫
                  ┃""",
            "5": """
                ┏━━
                ┗━┓
                ━━┛""",
            "6": """
                ┏━━
                ┣━┓
                ┗━┛""",
            "7": """
                ━━┓
                  ┃
                  ┃""",
            "8": """
                ┏━┓
                ┣━┫
                ┗━┛""",
            "9": """
                ┏━┓
                ┗━┫
                ━━┛""",
        }[number]
    )

