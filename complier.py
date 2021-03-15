import re, sys, time, subprocess, os, contextlib
from itertools import islice
from ast import literal_eval
from distutils.ccompiler import new_compiler
from distutils.errors import CompileError, DistutilsExecError
from __main__ import PLUTO_VERSION, DEBUG_MODE, SHOW_C, CUSTOM_PATH, KEEP_FILES


def raise_error(code, error_type, lineno, file):
    if error_type == 'syntax':
        print('[SyntaxError] Unexpected token \'' + code + '\' at line', str(lineno) + ', in file \'' + file + '\'')
    elif error_type == 'type':
        print('[TypeError] Incorrect value type in \'' + code + '\' at line', str(lineno) + ', in file \'' + file + '\'')
    elif error_type == 'funcname':
        print('[NameError] Function \'' + code + '\' is not defined at line', str(lineno) + ', in file \'' + file + '\'')
    sys.exit()

tokens = {
    'STRING': ('"', '"'),
    'PAREN': ('(', ')'),
    'LINE COMMENT': ('//', '\n'),
    'INTEGER': int,
    'FLOAT': float,
    'EOL': '\n',
    'PLUS': '+',
    'MINUS': '-',
    'DIVIDE': '/',
    'MULTIPLY': '*',
    'EQUALS': '=',
    'EQUAL TO': '==',
    'IDENTIFIER': str,
}

expressions = {
    'ADDITION': ['INTEGER', 'PLUS', 'INTEGER'],
    'SUBTRACTION': ['INTEGER', 'MINUS', 'INTEGER'],
    'DIVISION': ['INTEGER', 'DIVIDE', 'INTEGER'],
    'MULTIPLICATION': ['INTEGER', 'MULTIPLY', 'INTEGER'],
    'FUNCTION CALL': ['IDENTIFIER', 'PAREN'],
    'IDENTIFIER ASSIGNMENT': (['IDENTIFIER', 'EQUALS', 'STRING'], ['IDENTIFIER', 'EQUALS', 'INTEGER'], ['IDENTIFIER', 'EQUALS', 'FLOAT']),
}

expression_trees = {
    'ADDITION': {'Binary': [{'Operator': 1}, {'Left': 0}, {'Right': 2}]},
    'SUBTRACTION': {'Binary': [{'Operator': 1}, {'Left': 0}, {'Right': 2}]},
    'DIVISION': {'Binary': [{'Operator': 1}, {'Left': 0}, {'Right': 2}]},
    'MULTIPLICATION': {'Binary': [{'Operator': 1}, {'Left': 0}, {'Right': 2}]},
    'FUNCTION CALL': {'Call': [{'Type': 0}, {'Args': 1}]},
    'IDENTIFIER ASSIGNMENT': {'Assign': [{'Operator': 1}, {'Left': 0}, {'Right': 2}]},
}

c_token_replacements = {
    tokens['PLUS']: '+',
    tokens['MINUS']: '-',
    tokens['DIVIDE']: '/',
    tokens['MULTIPLY']: '*',
    tokens['EQUALS']: '=',
    tokens['EQUAL TO']: '==',
}

c_expressions = {
    'Binary': 'Left Operator Right',
    'Assign': 'Left Operator Right',
}

c_functions = {
    
}

class advanced_c_functions:
    def print(file, lineno, var_list, value):
        value_type = value
        if any(op in value for op in ['+', '-', '/', '*']) and any(c.isdigit() for c in value):
            try:
                value_type = eval(value) #TODO: Find SAFE alteritive for evaluating string equations
            except:
                pass
        for var_dict in var_list:
            if value == list(var_dict)[0]:
                value_type = list(var_dict.values())[0]
                
        if isinstance(value_type, int):
            return f'printf("%d", {value})'
        elif isinstance(value_type, float):
            return f'printf("%f", {value})'
        elif isinstance(value_type, str):
            return f'printf("%s", {value})'
        else:
            raise_error('print', 'type', lineno, file)
        
        
        
#----- LEXER -----#

def lex(source_code, file):
    regex = []
    for token in tokens.values():
        if isinstance(token, tuple):
            regex.append(f'\{token[0]}.*?\{token[1]}')

    split_code = re.split(rf"({'|'.join(regex)}|\w*|'.*?')", source_code)
    split_code = [i for i in split_code if i not in ['', ' ']]

    token_list = []
    lineno = 1
    lineno_list = []
    for code in split_code:
        if code.endswith('\n'):
            lineno += 1
        lineno_list.append(lineno)
        for token_name, token in tokens.items():
            if isinstance(token, tuple):
                if code == token[0]:
                    raise_error(code[:1], 'syntax', lineno, file)
                elif code.startswith(token[0]) and code.startswith(token[0]):
                    token_list.append(token_name)
                    break
            elif isinstance(token, str):
                if code == token:
                    token_list.append(token_name)
                    break
            elif isinstance(token, type):
                try:
                    if isinstance(token(code), token):
                        token_list.append(token_name)
                        break
                except:
                    pass

    return list(zip(token_list, split_code, lineno_list))

#----- PARSER -----#

# TODO: Add function here to validate syntax

def parse(tokenized_code, file):
    expression_list = []
    
    for espr_name, espr in expressions.items():
        n = 0
        if isinstance(espr, tuple):
            for sub_espr in espr:
                for token_epsr in zip(*(islice(iter(list(zip(*tokenized_code))[0]), i, None) for i in range(len(sub_espr)))):
                    n += 1 # MAJOR TODO: Fix bug where vars cannot be ints
                    if list(token_epsr) == sub_espr:
                        expression_list.append((espr_name, [n - 1, n + len(sub_espr) - 1]))
        else:
            for token_epsr in zip(*(islice(iter(list(zip(*tokenized_code))[0]), i, None) for i in range(len(espr)))):
                n += 1
                if list(token_epsr) == espr:
                    expression_list.append((espr_name, [n - 1, n + len(espr) - 1]))

    expression_list.sort(key = lambda val: val[1][0])

    expr_tree_list = []

    #print(expression_list)

    for espr, espr_location in expression_list:
        espr_code = list(zip(*tokenized_code))[1][espr_location[0]:espr_location[1]]
        lineno = list(zip(*tokenized_code))[2][espr_location[0]]
        expression_tree = str(expression_trees[espr])

        for char in expression_tree:
            if char.isdigit():
                if espr_code[int(char)].startswith(tokens['STRING'][0]) and espr_code[int(char)].endswith(tokens['STRING'][1]):
                    espr_tree_code = '\'"' + espr_code[int(char)][1:-1] + '"\''
                elif espr_code[int(char)].startswith(tokens['PAREN'][0]) and espr_code[int(char)].endswith(tokens['PAREN'][1]):
                    args = espr_code[int(char)][1:-1].split(', ')
                    for arg in args:
                        try:
                            if parse(lex(arg, file), file) == []:
                                args[args.index(arg)] = arg
                            else:
                                args[args.index(arg)] = parse(lex(arg, file), file)[0]
                        except:
                            pass
                    espr_tree_code = str(args)
                    
                else:
                    espr_tree_code = '\'' + espr_code[int(char)] + '\''
                expression_tree = expression_tree.replace(char, espr_tree_code)

        expr_tree_list.append({'Line ' + str(lineno): literal_eval(expression_tree)})
        
    return expr_tree_list

#----- CODE GENERATION -----#

def generate_code(ast, file):
    c_expression_list = []
    var_list = []
    for espr in ast:
        lineno = list(espr)[0][5:]
        if list(list(espr.values())[0])[0] == 'Call':
            if list(list(list(list(espr.values()))[0].values())[0][0].values())[0] in c_functions:
                expr_template = c_functions[list(list(list(list(espr.values()))[0].values())[0][0].values())[0]]
                for char in expr_template:
                    if char.isdigit():
                        try:
                            args = list(list(list(list(espr.values()))[0].values())[0][1].values())[0]
                            call_args = generate_code(args, file)
                        except:
                            call_args = list(list(list(list(espr.values()))[0].values())[0][1].values())[0]
                        expr_template = expr_template.replace(char, call_args[int(char)])

                c_expression_list.append(expr_template)
            elif getattr(advanced_c_functions, list(list(list(list(espr.values()))[0].values())[0][0].values())[0], None):
                func = getattr(advanced_c_functions, list(list(list(list(espr.values()))[0].values())[0][0].values())[0], None)
                try:
                    args = list(list(list(list(espr.values()))[0].values())[0][1].values())[0]
                    call_args = generate_code(args, file)[0]
                except:
                    call_args = list(list(list(list(espr.values()))[0].values())[0][1].values())[0]
                argno = func.__code__.co_argcount - 3
                
                c_expression_list.append(func(file, lineno, var_list, *call_args[:argno]))
            else:
                raise_error(list(list(list(list(espr.values()))[0].values())[0][0].values())[0], 'funcname', lineno, file)
        else:
            if list(list(espr.values())[0])[0] == 'Assign' and not list(list(list(list(espr.values()))[0].values())[0][1].values())[0] in var_list:
                var_list.append({list(list(list(list(espr.values()))[0].values())[0][1].values())[0]: list(list(list(list(espr.values()))[0].values())[0][2].values())[0]})
            expr_template = c_expressions[list(list(espr.values())[0])[0]]
            if 'Left' in expr_template:
                expr_template = expr_template.replace('Left', list(list(list(list(espr.values()))[0].values())[0][1].values())[0])
            if 'Right' in expr_template:
                expr_template = expr_template.replace('Right', list(list(list(list(espr.values()))[0].values())[0][2].values())[0])
            if 'Operator' in expr_template:
                expr_template = expr_template.replace('Operator', list(list(list(list(espr.values()))[0].values())[0][0].values())[0])
           
            c_expression_list.append(expr_template)

    return c_expression_list, var_list

def execute_code(c_code_list, var_list, file):
    var_declarations = []
    for var_dict in var_list:
        var_type = type(list(var_dict.values())[0])
        if var_type == str:
            var_declarations.append('char *' + list(var_dict)[0])
        else:
            var_declarations.append(var_type + ' ' + list(var_dict)[0])

        c_code = ';\n    '.join(var_declarations) + ';\n\n    ' + ';\n    '.join(c_code_list) + ';'
    
    c_file = '''// FILE.c
//
// Auto-generated at TIME by Pluto PLUTO_VERSION for C compilation. 
// DO NOT EDIT. Changes to file may result in incorrent behavor.

#include <stdio.h>

int main(void){
    
    C_CODE

    return 0;
}'''
    filename = file.split('.')[0]
    
    c_file = c_file.replace('FILE', filename)
    c_file = c_file.replace('TIME', time.strftime('%Y.%m.%d %H:%M:%S', time.gmtime()))
    c_file = c_file.replace('PLUTO_VERSION', str(PLUTO_VERSION))
    c_file = c_file.replace('C_CODE', c_code)

    if SHOW_C:
        print('[SHOW C] C code generated from Pluto file:')
        print('===============================================================================')
        print(c_file)
        print('===============================================================================')

    if CUSTOM_PATH:
        compile_path = CUSTOM_PATH
    else:
        compile_path = os.path.expanduser('~\Documents\\')
    
    open(compile_path + filename + '.c', 'w').write(c_file)

    oldstderr = None
    @contextlib.contextmanager
    def halt_logging():
        try:
            oldstderr = os.dup(sys.stdout.fileno())
            devnull = open(os.devnull, 'w')
            os.dup2(devnull.fileno(), sys.stdout.fileno())
            yield
        finally:
            os.dup2(oldstderr, sys.stdout.fileno())
            devnull.close()

    try:
        with halt_logging():
            compiler = new_compiler()
            object_file = compiler.compile([compile_path + filename + '.c'])
            compiler.link_executable([object_file[0]], filename)
            subprocess.call(compile_path + filename)
    except (CompileError, DistutilsExecError) as e:
        if DEBUG_MODE:
            print('[DEBUG] ' + str(e) + '. C compiler not found on system.')
        else:
            print('C compiler not found on system.')
        sys.exit()
    except Exception as e:
        if DEBUG_MODE:
            print('[DEBUG] Pluto encountered a fatal error during execution: ' + str(e))
        else:
            print('Pluto encountered a fatal error during execution.')

    if not KEEP_FILES:
        if os.path.exists(compile_path + filename + '.c'):
            os.remove(compile_path + filename + '.c')
        if os.path.exists(compile_path + filename + '.exe'):
            os.remove(compile_path + filename + '.exe')
