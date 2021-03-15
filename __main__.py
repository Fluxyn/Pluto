import os, sys

if sys.platform != 'win32':
    print('[WARNING] Pluto is not compatable with your OS.')

PLUTO_VERSION = '0.0.1'

DEBUG_MODE = False
SHOW_C = False
CUSTOM_PATH = None
KEEP_FILES = False

help_message = '''usage: pluto [args] <pluto file> [output dir] [options]
    or: pluto <help>

    Options:
       -h, --help        Show help.
       
       --debug           Enable debug mode.
       --show_c          Show the generated C code.
       --keep_files      Keep the generated C file and executable file after compilation.'''

if len(sys.argv) < 2:
    print(help_message)
    sys.exit()

try:
    arg1 = [i for i in sys.argv[1:] if not i.startswith('-')][0]
    if arg1 == 'help' or '--help' in sys.argv or '-h' in sys.argv:
        print(help_message)
        sys.exit()
except:
    sys.exit()

try:
    filepath = [i for i in sys.argv[1:] if not i.startswith('-')][0]

    if len([i for i in sys.argv[1:] if not i.startswith('-')]) == 2:
        if os.path.exists([i for i in sys.argv[1:] if not istartswith('-')][1]):
            CUSTOM_PATH = [i for i in sys.argv[1:] if not istartswith('-')][1]


    options = [arg for arg in sys.argv[1:] if arg.startswith('--')]

    arguments = [i for i in sys.argv[1:] if i not in options and i not in filepath]

    for arg in arguments:
        print('Unknown argument \'' + arg + '\'') #TODO: Add arguments, such as -q for quiet mode.
        sys.exit()
        
    for option in options:
        if option == '--debug':
            DEBUG_MODE = True
        elif option == '--show_c':
            SHOW_C = True
        elif option == '--keep_files':
            KEEP_FILES = True
        else:
            print('Unknown option \'' + option + '\'')
            sys.exit()

except SystemExit:
    sys.exit()
except:
    print(help_message)
    sys.exit()
    
try:
    file = os.path.basename(filepath)
    source_code = open(filepath, 'r').read()
except:
    print('Invalid file \'' + filepath + '\'')
    sys.exit()

from complier import lex, parse, generate_code, execute_code

try:
    tokenized_code = lex(source_code, file)
    ast = parse(tokenized_code, file)
except IndexError as e:
    if DEBUG_MODE:
        print('[DEBUG] Pluto encountered a fatal error while parsing: ' + str(e) + '. This can be raised when there are no expressions in your code.')
    else:
        pass
    sys.exit()
except Exception as e:
    if DEBUG_MODE:
        print('[DEBUG] Pluto encountered a fatal error while parsing: ' + str(e))
    else:
        print('Pluto encountered a fatal error while parsing.')
    sys.exit()

try:
    c_code_list, var_list = generate_code(ast, file)
    execute_code(c_code_list, var_list, file)
except Exception as e:
    if DEBUG_MODE:
        print('[DEBUG] Pluto encountered a fatal error during execution: ' + str(e))
    else:
        print('Pluto encountered a fatal error during execution.')
    sys.exit()
