#!/usr/bin/env python

"""
%(scriptName)s

Description:

Given the name of a .py file, recursively search through the file and below for all modules and display their path names.

Runstrings:

%(scriptName)s  file1 [file2 ...]
   By default, show all modules.  The display is a nested indented tree.

%(scriptName)s  --user_created file1 [file2 ...]
   Show only your user-created modules, not system-provided modules.

%(scriptName)s  --one_line  file1 [file2 ...]
   Instead of the default nested tree, display all of the module paths on one line for piping into annother command.

Typical real runstring:

%(scriptName)s  --one_line --user_created   file1.py  | rcsdiff_list.py  --s

"""


import os, sys, re

sys.path.append('lib')
sys.path.append('bin')

from logging_wrappers import logging_setup, scriptName, reportError

import getopt
import logging

import imp



#====================================================

scriptName = os.path.basename(sys.argv[0])

def usage():
    print(__doc__ % {'scriptName' : scriptName,})
    sys.exit(1)


#====================================================

def module_tree(indent='', module_name=''):
    global import_list

    # if os.path.exists(module_name):

    # print(58, module_name)

    if options.get('--debug', False) == True: print(33, module_name, "xxx" + indent + "yyy")

    if indent != '':
        # print(63, imp.find_module(module_name))
        module_path = imp.find_module(module_name)[1]
        if options.get('--debug', False) == True: print(36, module_path)
        if module_path == None:
            return
        # module_path = imp.find_module(module_name.replace('.py', ''))[1]
        # module_path = imp.find_module(module_name)[1]
        # if not os.path.exists(module_path):
        #    return
    else:
        module_path = module_name

    # print(72, module_path)

    # else:
    #    import_list.append(indent + module_name + " - not_found")
    #    return

    if options.get('--debug', False) == True: print(52, module_path)

    VIRTUAL_ENV = os.environ.get('VIRTUAL_ENV','')
    if VIRTUAL_ENV != '':
        VIRTUAL_ENV = '|^' + VIRTUAL_ENV

    if '.py' not in module_path or re.search('^sys|^/usr'+VIRTUAL_ENV, module_path):
        return

    if not os.path.exists(module_path):
        return

    if options.get('--user_created', False) == True:
        # print(77, module_path)
        if '.py' in module_path and not re.search('^sys|^/usr'+VIRTUAL_ENV, module_path):
            import_list.append(indent + module_path)
    else:
        import_list.append(indent + module_path)

    path_list = list(path_list_orig)
    ignore_comment = False

    indent += '   '
    fileline = 0
    # print "Processing file: " + file
    fd = open(module_path, 'r')
    for line in fd.read().splitlines():
        fileline += 1
        if re.search('"""', line) or re.search("'''", line):
            ignore_comment = not ignore_comment

        if ignore_comment == True:
            continue

        found = re.search('sys.path.append\([\'\"]*([^\'\"\)]+)[^\'\"]*\)', line)
        if found:
            new_path = found.group(1)
            if new_path not in path_list:
                # print "Adding new_path: " + new_path
                sys.path.append(new_path)
                path_list.append(new_path)
            continue

        found = re.search('^ *from ([^ ]+) import', line)
        if found:
            module_name = found.group(1)
            if module_name not in import_list:
                # import_list.append(indent + module_name)
                module_tree(indent, module_name)
            continue

        found = re.search('^ *import (.*)', line)
        if found:
            for module_name in [x.strip() for x in found.group(1).split(',')]:
                module_name = module_name.split(' ')[0]
                module_name = module_name.split('.')[0]
                # print(126, module_name)
                if module_name not in import_list:
                    # import_list.append(indent + module_name)
                    if options.get('--debug', False) == True: print(96, module_name)
                    module_tree(indent, module_name)
                    if options.get('--debug', False) == True: print(98, module_name)
            continue

    fd.close()



#====================================================

if __name__ == '__main__':

    if len(sys.argv) == 1:
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["debug", "user_created", "one_line"])
    except getopt.GetoptError as err:
        reportError("Unrecognized runstring " + str(err))
        usage()

    logging_setup(logMsgPrefix=scriptName, logfilename=scriptName + '.log', loglevel=logging.ERROR)

    options = {}

    for opt, arg in opts:
        if opt == "--user_created":
            options[opt] = True
        elif opt == "--one_line":
            options[opt] = True
        elif opt == "--debug":
            options[opt] = True
        else:
            reportError("Unrecognized runstring option: " + opt)
            usage()

    # print(sys.modules)
    # sys.exit(1)

    path_list_orig = list(sys.path)

    files=args

    for filename in files:
        fileline = 0

        sys.path = list(path_list_orig)
        sys.path.insert(0, os.path.dirname(filename))
        # print sys.path

        import_list = []
        module_tree('', filename)

        processed_list = []
        separator = ''
        if options.get('--one_line', False) == True:
            for module_name in import_list:
                # print 156, module_name
                module_name_no_indent = module_name.strip()
                if module_name_no_indent not in processed_list:
                    sys.stdout.write(separator + module_name_no_indent)
                    separator = ' '
                    processed_list.append(module_name_no_indent)
            print
        else:
            for row in import_list:
                print(row)
