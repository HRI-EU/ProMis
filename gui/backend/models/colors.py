import random

colors = ['aqua', 'aquamarine', 'bisque', 'black',
          'blue', 'blueViolet', 'brown', 'chocolate',
          'coral', 'crimson', 'cyan', 'dodgerBlue',
          'fireBrick', 'forestGreen', 'fuchsia', 'gold',
          'gray', 'green', 'indianRed', 'indigo', 'khaki',
          'lavender', 'lime', 'linen', 'magenta', 'maroon',
          'moccasin', 'navy', 'olive', 'orange', 'orangeRed',
          'orchid', 'peru', 'pink', 'plum', 'purple', 'red',
          'salmon', 'sienna', 'silver', 'slateGray', 'springGreen',
          'tan', 'teal', 'thistle', 'tomato', 'turquoise', 'violet',
          'wheat', 'white', 'yellow']

def get_random_color():
    return colors[random.randint(0, len(colors) - 1)]
