# Blender Translation reader
#
# Copyright (c) 2022 by Kafuji Sato
# GNU General Public License v3.0

# How it works:
#
# Read translation data from addon_path/translations/[locale]/*.csv or .tsv
# Translation file format:
#   encoding: utf_8
#   delimiter: ','(csv) / '\t'(.tsv) 
#   first line is header (skip)
#   comment starts with '#'  
#   each lines: context, key, translated

import bpy
_trans_table = {}
_trans_dir = 'lang'
_delimiters = {
    '.csv': ',',
    '.tsv': '\t',
}


# Register translations
def register():
    import os
    dir = os.path.join( os.path.dirname(__file__),  _trans_dir )
    global _trans_table

    locales = []

    try:
        for entry in os.scandir(dir):
            if entry.is_dir():
                locales.append(entry)

    except FileNotFoundError:
        print(f'{__name__} WARNING: directory not found "{dir}"')
        return

    for locale in locales:
        for entry in os.scandir(locale.path):
            _, ext = os.path.splitext(entry.name)
            if not ext in {'.csv', '.tsv'}:
                continue

            #print(f'{__name__} Loading Translation from file "{entry.name}"')

            if not _trans_table.get(locale.name, None):
                _trans_table[locale.name] = dict()
            
            delimiter = _delimiters[ext]
            
            with open(entry.path, 'r') as fp:
                next(fp) # skip first line as header
                for line_num, line in enumerate(fp):
                    
                    comment_pos = line.find('#')
                    line = line[:comment_pos]
                    
                    if len(line)<2:
                        continue

                    array = line.split(delimiter, 3)
                    if len(array) != 3:
                        print(f'{__name__} WARNING: translation format incorrect: File "{entry.name}", line {line_num+2}')
                        continue

                    (cat, eng, trans) = array
                    if cat == '':
                        cat = '*'
                    elif cat == 'O':
                        cat = 'Operator'

                    if eng=='' or trans=='':
                        continue

                    _trans_table[locale.name][(cat,eng)] = trans
                    #print(f'{__name__} {cat}:{eng}:{trans}')
    
    try:
        bpy.app.translations.register(__name__, _trans_table)
    except ValueError:
        print(f'{__name__} ERROR: bpy.app.translations.register failed')
        pass 

    return

# Unregister translations
def unregister():
    bpy.app.translations.unregister(__name__)
