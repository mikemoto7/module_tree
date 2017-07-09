#!/usr/bin/env python

"""
%(scriptName)s

Description:

Given the name of a .py file, recursively search through the file and below for all modules and display their path names.  Given the name of a ddirectory, do the same search for all scripts in the directory and below.

Runstrings:

%(scriptName)s  file1 [file2 ...]
%(scriptName)s  dir1 [dir2 ...]
%(scriptName)s  file1 dir1 [...]  # a mix of files and directories
   By default, show all modules.  The display is a nested indented tree.

%(scriptName)s  --user_created file1 [file2 ...]
   Show only your user-created modules, not system-provided modules.

%(scriptName)s  --one_line  file1 [file2 ...]
   Instead of the default nested tree, display all of the module paths on one line for piping into another command.

%(scriptName)s  --do_not_report_missing file1 [file2 ...]
   The default behavior is to report missing modules.  Using this option, missing modules will not be reported.  But they will still be displayed in the output.


Typical real runstring:

%(scriptName)s  --one_line --user_created   file1.py  | rcsdiff_list.py  --s

"""


import os, sys, re
import getopt
import logging

import imp
# import import_lib  # not available yet

scriptDir = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(scriptDir+'/lib')
sys.path.append(scriptDir+'/bin')

from logging_wrappers import logging_setup, scriptName, reportError
from dir_tree import dir_tree




#====================================================

scriptName = os.path.basename(sys.argv[0])

def usage():
    print(__doc__ % {'scriptName' : scriptName,})
    sys.exit(1)


#====================================================

global import_list
import_list = []

def module_tree_for_dir_tree(fullfilename='', indent='', module_filename=''):
    # print(62, "module_tree_for_dir_tree", fullfilename, indent, module_filename)
    rc, results = module_tree(indent, module_filename=fullfilename)
    return rc, results



def module_tree(indent='', module_filename=''):
    global import_list
    global path_list_orig

    not_found_flag = ''

    VIRTUAL_ENV = os.environ.get('VIRTUAL_ENV','')

    if indent == '':  # top level
        sys.path.append(os.path.dirname(module_filename))
        path_list_orig = list(sys.path)  # Use the same starting list of paths for each module file name search

        if not os.path.exists(module_filename):
            if options.get('--do_not_report_missing', False) == False:
                not_found_flag = ',NOT_FOUND'
    else:  # From imports in scripts
        # print(117, module_filename, not_found_flag, sys.path)
        sys.path = path_list_orig
        not_found_flag = ',NOT_FOUND'
        for module_path in sys.path:
            if os.path.exists(module_path + '/' + module_filename):
                module_filename = module_path + '/' + module_filename
                not_found_flag = ''
                break
            module_name = module_filename.replace('.py', '')
            if os.path.isdir(module_path + '/' + module_name):
                module_filename = module_path + '/' + module_name
                not_found_flag = ''
                break
            try:
                module_object = imp.find_module(module_name)
                # print(103, module_object)
                if module_object[1] != None:
                    module_filename = module_object[1]
                    not_found_flag = ''
                break
            except ImportError as err:
                continue

    if VIRTUAL_ENV != '':
        VIRTUAL_ENV = '|^' + VIRTUAL_ENV
        
    if not re.search('^sys|^/usr'+VIRTUAL_ENV, module_filename):
        # This is a user-created module, so remember it.
        import_list.append(indent + module_filename + not_found_flag)
    else:
        # This is a system module.
        if options.get('--user_created', False) == False:
            # The user did not ask for user-created modules only, so remember this system module.
            import_list.append(indent + module_filename + not_found_flag)
        return 0, 'system module'  # Don't go any deeper into a system module.
    # print(79, module_filename) 

    # if '.py' not in module_filename:
    #     return 0, '.py not in module_filename'

    if not os.path.exists(module_filename):
        return 0, module_filename + ' does not exist'

    ignore_comment = False

    indent += '   '
    fileline = 0
    # print "Processing file: " + file
    fd = open(module_filename, 'r')
    for line in fd.read().splitlines():
        fileline += 1
        if re.search('"""', line) or re.search("'''", line):
            ignore_comment = not ignore_comment

        if ignore_comment == True:
            continue

        found = re.search('sys.path.append\([\'\"]*([^\'\"\)]+)[^\'\"]*\)', line)
        if found:
            new_path = found.group(1)
            if new_path not in sys.path:
                # print "Adding new_path: " + new_path
                sys.path.append(new_path)
            continue

        found = re.search('^ *from ([^ ]+) import', line)
        if found:
            module_filename = found.group(1) + '.py'
            if module_filename not in import_list:
                # import_list.append(indent + module_filename)
                module_tree(indent, module_filename)
            continue

        found = re.search('^ *import (.*)', line)
        if found:
            for module_filename in [x.strip() for x in found.group(1).split(',')]:
                module_filename = module_filename.split(' ')[0]
                module_filename = module_filename.split('.')[0]
                module_filename += '.py'
                # print(126, module_filename)
                if module_filename not in import_list:
                    # import_list.append(indent + module_filename)
                    if options.get('--debug', False) == True: print(96, module_filename)
                    module_tree(indent, module_filename)
                    if options.get('--debug', False) == True: print(98, module_filename)
            continue

    fd.close()

    return 0, 'success'

#====================================================

if __name__ == '__main__':

    if len(sys.argv) == 1:
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["debug", "user_created", "one_line", "do_not_report_missing"])
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
        elif opt == "--do_not_report_missing":
            options[opt] = True
        elif opt == "--debug":
            options[opt] = True
        else:
            reportError("Unrecognized runstring option: " + opt)
            usage()

    # print(sys.modules)
    # sys.exit(1)

    # curr_dir = os.getcwd()

    path_list_orig = list(sys.path)  # Use the same starting list of paths for each module file name search

    files_or_dirs=args

    for file_or_dir_name in files_or_dirs:
        sys.path = list(path_list_orig)

        # sys.path.insert(0, curr_dir)

        # dirpath = os.path.dirname(file_or_dir_name)
        # if dirpath[0] != '/':
        #     dirpath = curr_dir + '/' + dirpath
        #     # file_or_dir_name = curr_dir + '/' + file_or_dir_name
        # sys.path.insert(0, dirpath)
        # # print(219, sys.path)

        if os.path.isdir(file_or_dir_name):
            # print(213, file_or_dir_name)
            # dir_tree( start_dir=file_or_dir_name, filename_mask='.py', func=module_tree, indent='', module_filename=file_or_dir_name)
            # dir_tree( start_dir=file_or_dir_name, filename_mask='.py', func=module_tree, args=[indent='', module_filename=file_or_dir_name])
            rc, results = dir_tree( start_dir=file_or_dir_name, filename_mask='\.py$', func=module_tree_for_dir_tree, indent='', module_filename=file_or_dir_name)
            # rc, results = dir_tree( start_dir=file_or_dir_name, filename_mask='\.py$')
            if rc != 0:
                print("line", 220, "ERROR", results)
                sys.exit(rc)
            # for row in results:
            #     print(row)
        else:
            fileline = 0
            module_tree('', file_or_dir_name)

        processed_list = []
        separator = ''
        if options.get('--one_line', False) == True:
            for module_filename in import_list:
                # print 156, module_filename
                module_filename_no_indent = module_filename.strip()
                if module_filename_no_indent not in processed_list:
                    sys.stdout.write(separator + module_filename_no_indent)
                    separator = ' '
                    processed_list.append(module_filename_no_indent)
            print
        else:
            for row in import_list:
                print(row)





