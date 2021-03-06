import json
import re
import datetime

import logging
import copy


logger = logging.getLogger(__name__)

def composite_prepare_data_for_subfield(data, field, subfield):
    try:
        # don't modify actual data
        data = copy.deepcopy(data)

        fieldname = field['field_name']
        field_data_str = data.get(fieldname)

        if field_data_str:
            field_data_dict = json.loads(field_data_str)
            subfieldname = subfield['field_name']
            subfield_data = field_data_dict.get(subfieldname)

            if subfield_data:
                data[fieldname + '-' + subfieldname] = subfield_data
    except Exception as e:
        logger.error(e)

    return data

def composite_prepare_subfield_for_scheming(field, subfield):
    try:
        # don't modify actual subfield
        subfield = copy.deepcopy(subfield)

        # get the field_name right
        subfield['field_name'] = field['field_name'] + '-' + subfield['field_name']
    except Exception as e:
        logger.error(e)

    return subfield

def _json2dict_or_empty(value, field_name = ""):
    try:
        json_dict = json.loads(value)
    except Exception as e:
        logger.warn("Field " + field_name + "('" + str(value) + "') could not be parsed: " + str(e))
        json_dict = {}
    return (json_dict)

def _json2list_or_empty(value, field_name = ""):
    try:
        json_list = json.loads(value)
    except Exception as e:
        logger.warn("Field " + field_name + "('" + str(value) + "') could not be parsed: " + str(e))
        json_list = []
    return (json_list)

def composite_is_list(value):
    '''
    Template helper funciton.
    Returns true if the value is a list.
    '''
    return isinstance(value, list)

def composite_join_list(value, sep=', '):
    '''
    Template helper function.
    Returns the list joined by separator.
    '''
    if value:
        if composite_is_list(value):
            return (sep.join(value))
    return str(value)

def composite_get_as_dict(value):
    '''
    Template helper funciton.
    Returns the value as a dictionary. If if is already
    a dictionary, the original value is returned. If it is
    a json dump, it will be parsed into a dictionary. Otherwise
    an empty dictionary is returned.
    '''
    if isinstance(value, dict):
        return value
    else:
        return(_json2dict_or_empty(value))

def composite_get_label_dict(field_list):
    '''
    Converts a list of dictionaries containing the keys
    "field_name" and "label" into a single dictionary
    with "field_name" value as key and "label" as value.
    If label is not defined, the field name is used as
    label. 
    '''

    label_dict = {}
    for field in field_list:
        name = field.get('field_name', '')
        label_dict[name] = field.get('label', name)
    return label_dict

def composite_get_choices_dict(field_list):
    '''
    Converts a list of dictionaries containing the keys
    "field_name" and "choices" into a single dictionary
    with "field_name" value as key and "choices" as value.
    If choices is not defined, then an empty list is assigned.
    '''

    choices_dict = {}
    for field in field_list:
        name = field.get('field_name', '')
        choices_dict[name] = field.get('choices', [])
    return choices_dict

def composite_get_name_list(field_list):
    '''
    Converts a list of dictionaries containing the key
    "field_name" into list of field names.
    '''

    name_list = []
    for field in field_list:
        name = field.get('field_name', '')
        if name:
            name_list += [name]
    return name_list

def composite_get_value_dict(field_name, data):
    '''
    Template helper function.
    Get data from composite_text-field from either field_name (if the
    field comes from the database) or construct from several subfields -
    entries in case data wasn't saved yet, i.e. a validation error occurred.
    '''
 
    def build_value_dict():
        fields = [re.match(field_name + "-.+", key) for key in data.keys()]
        fields = sorted([r.string for r in fields if r])
        value_dict = {}

        for field in fields:
            if data[field] is not None:
                subfield = field.split("-",1)[1]
                value_dict[subfield] = data[field]
        return value_dict

    value_dict = {}

    form_value = build_value_dict()

    if form_value:
       value_dict = form_value
    else:
       db_value = data.get(field_name)
       if db_value:
           if isinstance(db_value, dict):
               value_dict = db_value
           else:
               value_dict = _json2dict_or_empty(db_value)

    return value_dict

def composite_repeating_get_value_dict_list(field_name, subfields, data, field_blanks = 1, include_empty = True):
    '''
    Template helper function.
    Get data from composite_text-field from either field_name (if the
    field comes from the database) or construct from several subfields -
    entries in case data wasn't saved yet, i.e. a validation error occurred.
    '''

    def dict_is_empty(dictionary):
        is_empty = not bool([a for a in dictionary.values() if a != ''])
        return is_empty

    def remove_empty_dicts(dict_list):
        non_empty_list = []
        for item in dict_list:
            if not dict_is_empty(item):
                non_empty_list += [item]
        return non_empty_list

    def build_value_dict_list():
        fields = [re.match(field_name + "-.+", key) for key in data.keys()]
        fields = sorted([r.string for r in fields if r])

        value_dict = {}

        for field in fields:
            if data[field] is not None:
                index = int(field.split('-', 2)[1])
                subfield = field.split('-', 2)[2]

                if not value_dict.has_key(index):
                   value_dict[index] = {}
                value_dict[index][subfield] = data[field]

        value_dict_list = [element[1] for element in sorted(value_dict.items())]

        return value_dict_list

    value_dict_list = []

    form_value = build_value_dict_list()

    if form_value:
       value_dict_list = form_value
    else:
       db_value = data.get(field_name)
       if db_value:
           if isinstance(db_value, list):
               value_dict_list = db_value
           else:
               value_dict_list = _json2list_or_empty(db_value)
           # Compatibility
           if isinstance(value_dict_list, dict):
               value_dict_list = [value_dict_list]


    # Build empty dictionary for initial form
    if not value_dict_list:
       loop_lim = max (field_blanks+1, 2)
       value_dict_list = [] 
       for  x in range (1, loop_lim):
           blank_dict = {}
           for subfield in subfields:
               blank_dict[subfield['field_name']] = ''
           value_dict_list += [blank_dict]

    if not include_empty:
        value_dict_list = remove_empty_dicts(value_dict_list)

    return value_dict_list

def composite_is_mail(value):
    EMAIL_REGEX = r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$"
    if re.match(EMAIL_REGEX, value):
        return True
    return False

def composite_get_markup(text):
    
    markup_text = []

    for token in text.split(' '):
        if token.find('@')>=0:
            markup_text += ['<b><a href="mailto:' + token + '" target="_top">' + token + '</a></b>']
        elif token.find('http://')>=0 or token.find('https://')>=0:
            # format [tag](link)
            if token.find('[')==0:
                start_tag = token.find('[') + 1
                end_tag = token.find(']', start_tag)
                tag = token[start_tag:end_tag]
                link = token[end_tag+1:]
                markup_text += ['<b><a href="' + link + '">' + tag + '</a></b>']
            else:
                # plain format
				start = token.find('//') + len('//')
				end = token.find('/', start)
				tag = token[start:end]
				markup_text += ['<b><a href="' + token + '">' + tag + '</a></b>']
        else:
            markup_text += [token]
    return ' '.join(markup_text)


def composite_get_default_value(text):
    if text == "composite_current_year":
        now = datetime.datetime.now()
        return str(now.year)
    return text

