from collection.models import Object_types, Attribute, Data_point
import json
import datetime
import os
from django.db.models import Count, Max



# Clear --------------------------------------------------

def clear_object_types():
    Object_types.objects.all().delete()


def clear_attributes():
    Attribute.objects.all().delete()



# Populate --------------------------------------------------

def populate_object_types():

    path = "collection/static/webservice files/db_backup/object_types/"
    backup_files = os.listdir(path)
    with open(path + backup_files[-1], "r") as backup_file:
        lines = backup_file.readlines()

    records_dict = json.loads(lines[0])
    # records = [{"id":"n1", "text" : "Thing", "li_attr": {}, "parent":"#"}, {"id":"n2", "text" : "Object" , "li_attr": {}, "parent":"n1"}, {"id":"n3", "text": "Living thing", "li_attr": {}, "parent":"n2"}, {"id":"n4", "text": "Plant", "li_attr": {"attribute_values": [{"attribute":"Kingdom",                    "operation":"=", "value":"Plantae"}, {"attribute":"Does photosynthesis",                    "operation":"=", "value":True } ] }, "a_attr":{"scientific":["Plantae"]}, "parent":"n3"}, {"id":"n5", "text":"Tree", "li_attr": {"attribute_values": [{"attribute":"Has woody tissue",                    "operation":"=", "value":True}, { "attribute":"Age",                   "operation":"<", "value":"7000"}]},  "parent":"n4"}, {"id":"n6", "text": "Oak", "li_attr": {"attribute_values": [{"attribute":"Produces nuts",                    "operation": "=", "value":True}, { "attribute":"Has leaves",                    "operation":"=", "value":True }, {"attribute":"Age",                   "operation":"<", "value":"700"}, {"attribute":"Age",                   "operation": "<", "value":"100"}, { "attribute":"Weight",                    "operation":"<", "value":"9000" } ] }, "a_attr":{ "synonyms": ["oak tree"], "scientific": ["Quercus"]}, "parent":"n5"}, {"id":"n7", "text": "Chestnut", "li_attr": {"attribute_values": [{"attribute":"Produces nuts",                    "operation":"=", "value":True }, { "attribute":"Produces berries",                    "operation":"=", "value":False }, { "attribute":"Age",                   "operation":"<", "value":"400"}, {"attribute":"Height",                   "operation":"<", "value":"130"}, {"attribute":"Weight",                    "operation":"<", "value":"10000"}]}, "a_attr":{"scientific": ["Castanea"]}, "parent":"n5" }, {"id":"n8", "text": "Flower", "li_attr": {"attribute_values": [{"attribute":"Has petals",                    "operation":"=", "value":True } ] }, "parent":"n4"}, {"id":"n9", "text":"Lily", "li_attr": {"attribute_values": [{"attribute":"Petal color",                    "operation":"=", "value":"yellow"}]}, "parent":"n8"}, {"id":"n10", "text":"Animal", "li_attr": {"attribute_values": [{"attribute":"Kingdom",                    "operation": "=", "value":"Animalia"}]}, "a_attr":{"synonyms": ["Creature"], "scientific": ["Animalia"]}, "parent":"n2"} ]
    # records = [{"id":"n1", "text" : "Thing", "li_attr": {}, "parent":"#"}, {"id":"n2", "text" : "Object" , "li_attr": {}, "parent":"n1"}, {"id":"n3", "text": "Living thing", "li_attr": {}, "parent":"n2"}, {"id":"n4", "text": "Plant", "li_attr": {"attribute_values": [{"attribute":"Kingdom", "attribute_id":11, "operation":"=", "value":"Plantae"}, {"attribute":"Does photosynthesis", "attribute_id":12, "operation":"=", "value":True } ] }, "a_attr":{"scientific":["Plantae"]}, "parent":"n3"}, {"id":"n5", "text":"Tree", "li_attr": {"attribute_values": [{"attribute":"Has woody tissue", "attribute_id":13, "operation":"=", "value":True}, { "attribute":"Age", "attribute_id":8, "operation":"<", "value":"7000"}]},  "parent":"n4"}, {"id":"n6", "text": "Oak", "li_attr": {"attribute_values": [{"attribute":"Produces nuts", "attribute_id":14, "operation":"=", "value":True }, { "attribute":"Has leaves", "attribute_id":15, "operation":"=", "value":True }, {"attribute":"Age", "attribute_id":8, "operation":"<", "value":"700"}, {"attribute":"Age", "attribute_id":8, "operation":"<", "value":"100" }, { "attribute":"Weight", "attribute_id":16, "operation":"<", "value":"9000" } ] }, "a_attr":{ "synonyms": ["oak tree"], "scientific": ["Quercus"]}, "parent":"n5"}, {"id":"n7", "text": "Chestnut", "li_attr": {"attribute_values": [{"attribute":"Produces nuts", "attribute_id":14, "operation":"=", "value":True }, { "attribute":"Produces berries", "attribute_id":17, "operation":"=", "value":False }, { "attribute":"Age", "attribute_id":8, "operation":"<", "value":"400"}, {"attribute":"Height", "attribute_id":18, "operation":"<", "value":"130"}, {"attribute":"Weight", "attribute_id":16, "operation":"<", "value":"10000"}]}, "a_attr":{ "scientific":["Castanea"]}, "parent":"n5" }, {"id":"n8", "text": "Flower", "li_attr": {"attribute_values": [{"attribute":"Has petals", "attribute_id":19, "operation":"=", "value":True } ] }, "parent":"n4"}, {"id":"n9", "text":"Lily", "li_attr": {"attribute_values": [{"attribute":"Petal color", "attribute_id":20, "operation":"=", "value":"yellow"}]}, "parent":"n8"}, {"id":"n10", "text":"Animal", "li_attr": {"attribute_values": [{"attribute":"Kingdom", "attribute_id":11, "operation": "=", "value":"Animalia"}]}, "a_attr":{"synonyms": ["Creature"], "scientific": ["Animalia"]}, "parent":"n2"} ]
    # records_dict = [ { "id":"n1", "text":"Thing", "li_attr":{  }, "parent":"#" }, { "id":"n2", "text":"Object", "li_attr":{  }, "parent":"n1" }, { "id":"n3", "text":"Living thing", "li_attr":{  }, "parent":"n2" }, { "id":"n4", "text":"Plant", "li_attr":{ "attribute_values":[ { "attribute":"Kingdom", "attribute_id":11, "operation":"=", "value":"Plantae" }, { "attribute":"Does photosynthesis", "attribute_id":12, "operation":"=", "value":True } ] }, "a_attr":{ "scientific":[ "Plantae" ] }, "parent":"n3" }, { "id":"n5", "text":"Tree", "li_attr":{ "attribute_values":[ { "attribute":"Has woody tissue", "attribute_id":13, "operation":"=", "value":True }, { "attribute":"Age", "attribute_id":8, "operation":"<", "value":7000 } ] }, "parent":"n4" }, { "id":"n6", "text":"Oak", "li_attr":{ "attribute_values":[ { "attribute":"Produces nuts", "attribute_id":14, "operation":"=", "value":True }, { "attribute":"Has leaves", "attribute_id":15, "operation":"=", "value":True }, { "attribute":"Age", "attribute_id":8, "operation":"<", "value":700 }, { "attribute":"Age", "attribute_id":8, "operation":"<", "value":100 }, { "attribute":"Weight", "attribute_id":16, "operation":"<", "value":9000 } ] }, "a_attr":{ "synonyms":[ "oak tree" ], "scientific":[ "Quercus" ] }, "parent":"n5" }, { "id":"n7", "text":"Chestnut", "li_attr":{ "attribute_values":[ { "attribute":"Produces nuts", "attribute_id":14, "operation":"=", "value":True }, { "attribute":"Produces berries", "attribute_id":17, "operation":"=", "value":False }, { "attribute":"Age", "attribute_id":8, "operation":"<", "value":400 }, { "attribute":"Height", "attribute_id":18, "operation":"<", "value":130 }, { "attribute":"Weight", "attribute_id":16, "operation":"<", "value":10000 } ] }, "a_attr":{ "scientific":[ "Castanea" ] }, "parent":"n5" }, { "id":"n8", "text":"Flower", "li_attr":{ "attribute_values":[ { "attribute":"Has petals", "attribute_id":19, "operation":"=", "value":True } ] }, "parent":"n4" }, { "id":"n9", "text":"Lily", "li_attr":{ "attribute_values":[ { "attribute":"Petal color", "attribute_id":20, "operation":"=", "value":"yellow" } ] }, "parent":"n8" }, { "id":"n10", "text":"Animal", "li_attr":{ "attribute_values":[ { "attribute":"Kingdom", "attribute_id":11, "operation":"=", "value":"Animalia" } ] }, "a_attr":{ "synonyms":[ "Creature" ], "scientific":[ "Animalia" ] }, "parent":"n2" } ]
    for record in records_dict:
        if isinstance(record,dict):
            obj_type_record = Object_types( id=record.get('id'), 
                                            parent=record.get('parent'), 
                                            name=record.get('text'), 
                                            li_attr=json.dumps(record.get('li_attr')), 
                                            a_attr=json.dumps(record.get('a_attr')),)
            obj_type_record.save()

def populate_attributes():

    path = "collection/static/webservice files/db_backup/attributes/"
    backup_files = os.listdir(path)
    with open(path + backup_files[-1], "r") as backup_file:
        lines = backup_file.readlines()

    attributes = json.loads(lines[0])

    print("------------------------------------------")
    print("------------------------------------------")
    print(attributes)
    print("------------------------------------------")
    print("------------------------------------------")
    # attributes = [{"attribute_name": "Country", "attribute_id": 1, "description": "this is a good option", "format_specification": {"fields": {"column": {"type": "string", "min_length": 4, "max_length": 52, "max_nulls": 10000}}}, "first_applicable_object": "n1"}, {"attribute_name": "Year", "attribute_id": 2, "description": "this is a good option", "format_specification": {"fields": {"column": {"type": "int", "min": 1995, "max": 2011, "sign": "positive", "max_nulls": 10000}}}, "first_applicable_object": "n1"}, {"attribute_name": "Count", "attribute_id": 3, "description": "this is a good option", "format_specification": {"fields": {"column": {"type": "int", "min": 0, "max": 45559, "sign": "non-negative", "max_nulls": 10000}}}, "first_applicable_object": "n1"}, {"attribute_name": "Rate", "attribute_id": 4, "description": "this is a good option", "format_specification": {"fields": {"column": {"type": "real", "min": 0.0, "max": 139.1, "sign": "non-negative", "max_nulls": 10000}}}, "first_applicable_object": "n1"}, {"attribute_name": "Source", "attribute_id": 5, "description": "this is a good option", "format_specification": {"fields": {"column": {"type": "string", "min_length": 3, "max_length": 28, "max_nulls": 10000}}}, "first_applicable_object": "n1"}, {"attribute_name": "Source Type", "attribute_id": 6, "description": "this is a good option", "format_specification": {"fields": {"column": {"type": "string", "min_length": 2, "max_length": 2, "max_nulls": 10000, "allowed_values": ["CJ", "PH"]}}}, "first_applicable_object": "n1"}, {"attribute_name": "Leaf Coverage", "attribute_id": 7, "description": "The percentage of the ground that is in shadow when the sun is shining from directly above.", "format_specification": {"fields": {"column": {"type": "real", "min":0.0, "max":1.0}}}, "first_applicable_object": "n1"}, {"attribute_name": "Age", "attribute_id": 8, "description": "number of years in existence", "format_specification": {"fields": {"column": {"type": "int", "min": 0, "max": 1000000}}}, "first_applicable_object": "n1"}, {"attribute_name": "New Test Attribute", "attribute_id": 9, "description": "some description", "format_specification": {"fields": {"column": {"type": "int", "min": 4, "max": 34}}}, "first_applicable_object": "n1"}, {"attribute_name": "test attribute 123", "attribute_id": 10, "description": "slkfskl", "format_specification": {"fields": {"column": {"type": "string", "min_length": 2, "max_length": 6}}}, "first_applicable_object": "n1"}, {"attribute_name": "Kingdom", "attribute_id": 11, "description": "animal kingdom", "format_specification": {"fields": {"column": {"type": "string", "min_length": 2, "max_length": 20}}}, "first_applicable_object": "n1"}, {"attribute_name": "Does photosynthesis", "attribute_id": 12, "description": "", "format_specification": {"fields": {"column": {"type": "bool"}}}, "first_applicable_object": "n1"}, {"attribute_name": "Has woody tissue", "attribute_id": 13, "description": "", "format_specification": {"fields": {"column": {"type": "bool"}}}, "first_applicable_object": "n1"}, {"attribute_name": "Produces nuts", "attribute_id": 14, "description": "", "format_specification": {"fields": {"column": {"type": "bool"}}}, "first_applicable_object": "n1"}, {"attribute_name": "Has leaves", "attribute_id": 15, "description": "", "format_specification": {"fields": {"column": {"type": "bool"}}}, "first_applicable_object": "n1"}, {"attribute_name": "Weight", "attribute_id": 16, "description": "in kg", "format_specification": {"fields": {"column": {"type": "real", "min": 0.0, "max": 1000000000000000.0}}}, "first_applicable_object": "n1"}, {"attribute_name": "Produces berries", "attribute_id": 17, "description": "", "format_specification": {"fields": {"column": {"type": "bool"}}}, "first_applicable_object": "n1"}, {"attribute_name": "Height", "attribute_id": 18, "description": "in m", "format_specification": {"fields": {"column": {"type": "real", "min": 0.0, "max": 1000000000000000.0}}}, "first_applicable_object": "n1"}, {"attribute_name": "Has petals", "attribute_id": 19, "description": "", "format_specification": {"fields": {"column": {"type": "bool"}}}, "first_applicable_object": "n1"}, {"attribute_name": "Petal color", "attribute_id": 20, "description": "", "format_specification": {"fields": {"column": {"type": "string", "min_length": 2, "max_length": 20}}}, "first_applicable_object": "n1"}]
    # attributes = [ { "attribute_name":"Country", "attribute_id":1, "data_type":"string", "expected_valid_period":3153600000, "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":4, "max_length":52, "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Year", "attribute_id":2, "data_type":"int", "expected_valid_period":3153600000, "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"int", "min":1995, "max":2011, "sign":"positive", "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Count", "attribute_id":3, "data_type":"int", "expected_valid_period":3153600000, "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"int", "min":0, "max":45559, "sign":"non-negative", "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Rate", "attribute_id":4, "data_type":"real", "expected_valid_period":3153600000, "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"real", "min":0.0, "max":139.1, "sign":"non-negative", "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Source", "attribute_id":5, "data_type":"string", "expected_valid_period":3153600000, "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":3, "max_length":28, "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Source Type", "attribute_id":6, "data_type":"string", "expected_valid_period":3153600000, "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":2, "max_length":2, "max_nulls":10000, "allowed_values":[ "CJ", "PH" ] } } }, "first_applicable_object":"n1" }, { "attribute_name":"Leaf Coverage", "attribute_id":7, "data_type":"real", "expected_valid_period":3153600000, "description":"The percentage of the ground that is in shadow when the sun is shining from directly above.", "format_specification":{ "fields":{ "column":{ "type":"real", "min":0.0, "max":1.0 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Age", "attribute_id":8, "data_type":"int", "expected_valid_period":3153600000, "description":"number of years in existence", "format_specification":{ "fields":{ "column":{ "type":"int", "min":0, "max":1000000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"New Test Attribute", "attribute_id":9, "data_type":"int", "expected_valid_period":3153600000, "description":"some description", "format_specification":{ "fields":{ "column":{ "type":"int", "min":4, "max":34 } } }, "first_applicable_object":"n1" }, { "attribute_name":"test attribute 123", "attribute_id":10, "data_type":"string", "expected_valid_period":3153600000, "description":"slkfskl", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":2, "max_length":6 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Kingdom", "attribute_id":11, "data_type":"string", "expected_valid_period":3153600000, "description":"animal kingdom", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":2, "max_length":20 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Does photosynthesis", "attribute_id":12, "data_type":"bool", "expected_valid_period":3153600000, "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Has woody tissue", "attribute_id":13, "data_type":"bool", "expected_valid_period":3153600000, "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Produces nuts", "attribute_id":14, "data_type":"bool", "expected_valid_period":3153600000, "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Has leaves", "attribute_id":15, "data_type":"bool", "expected_valid_period":3153600000, "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Weight", "attribute_id":16, "data_type":"bool", "expected_valid_period":3153600000, "description":"in kg", "format_specification":{ "fields":{ "column":{ "type":"real", "min":0.0, "max":1000000000000000.0 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Produces berries", "attribute_id":17, "data_type":"bool", "expected_valid_period":3153600000, "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Height", "attribute_id":18, "data_type":"real", "expected_valid_period":3153600000, "description":"in m", "format_specification":{ "fields":{ "column":{ "type":"real", "min":0.0, "max":1000000000000000.0 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Has petals", "attribute_id":19, "data_type":"bool", "expected_valid_period":3153600000, "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Petal color", "attribute_id":20, "data_type":"string", "expected_valid_period":3153600000, "description":"", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":2, "max_length":20 } } }, "first_applicable_object":"n1" } ]
    # [{"attribute_name":"Country", "attribute_id":1, "data_type":"string", "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":4, "max_length":52, "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Year", "attribute_id":2, "data_type":"int", "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"int", "min":1995, "max":2011, "sign":"positive", "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Count", "attribute_id":3, "data_type":"int", "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"int", "min":0, "max":45559, "sign":"non-negative", "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Rate", "attribute_id":4, "data_type":"real", "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"real", "min":0.0, "max":139.1, "sign":"non-negative", "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Source", "attribute_id":5, "data_type":"string", "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":3, "max_length":28, "max_nulls":10000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Source Type", "attribute_id":6, "data_type":"string", "description":"this is a good option", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":2, "max_length":2, "max_nulls":10000, "allowed_values":[ "CJ", "PH" ] } } }, "first_applicable_object":"n1" }, { "attribute_name":"Leaf Coverage", "attribute_id":7, "data_type":"real", "description":"The percentage of the ground that is in shadow when the sun is shining from directly above.", "format_specification":{ "fields":{ "column":{ "type":"real", "min":0.0, "max":1.0 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Age", "attribute_id":8, "data_type":"int", "description":"number of years in existence", "format_specification":{ "fields":{ "column":{ "type":"int", "min":0, "max":1000000 } } }, "first_applicable_object":"n1" }, { "attribute_name":"New Test Attribute", "attribute_id":9, "data_type":"int", "description":"some description", "format_specification":{ "fields":{ "column":{ "type":"int", "min":4, "max":34 } } }, "first_applicable_object":"n1" }, { "attribute_name":"test attribute 123", "attribute_id":10, "data_type":"string", "description":"slkfskl", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":2, "max_length":6 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Kingdom", "attribute_id":11, "data_type":"string", "description":"animal kingdom", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":2, "max_length":20 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Does photosynthesis", "attribute_id":12, "data_type":"bool", "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Has woody tissue", "attribute_id":13, "data_type":"bool", "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Produces nuts", "attribute_id":14, "data_type":"bool", "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Has leaves", "attribute_id":15, "data_type":"bool", "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Weight", "attribute_id":16, "data_type":"bool", "description":"in kg", "format_specification":{ "fields":{ "column":{ "type":"real", "min":0.0, "max":1000000000000000.0 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Produces berries", "attribute_id":17, "data_type":"bool", "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Height", "attribute_id":18, "data_type":"real", "description":"in m", "format_specification":{ "fields":{ "column":{ "type":"real", "min":0.0, "max":1000000000000000.0 } } }, "first_applicable_object":"n1" }, { "attribute_name":"Has petals", "attribute_id":19, "data_type":"bool", "description":"", "format_specification":{ "fields":{ "column":{ "type":"bool" } } }, "first_applicable_object":"n1" }, { "attribute_name":"Petal color", "attribute_id":20, "data_type":"string", "description":"", "format_specification":{ "fields":{ "column":{ "type":"string", "min_length":2, "max_length":20 } } }, "first_applicable_object":"n1" } ]
    for attribute in attributes:
        attribute_record = Attribute(id=attribute['id'], 
                                    name=attribute['name'], 
                                    expected_valid_period=attribute['expected_valid_period'], 
                                    description=attribute['description'], 
                                    format_specification=json.dumps(attribute['format_specification']), 
                                    first_applicable_object=attribute['first_applicable_object'], )
        attribute_record.save()



# Backup DB --------------------------------------------------

def backup_object_types():
    result_list = []
    object_types = Object_types.objects.all()
    for object_type in object_types:
        object_type_dict = {'id':object_type.id, 
                            'parent':object_type.parent, 
                            'text':object_type.name}
        
        if object_type.li_attr is not None:
            object_type_dict['li_attr'] = json.loads(object_type.li_attr)

        if object_type.a_attr is not None:
            object_type_dict['a_attr'] = json.loads(object_type.a_attr)

        result_list.append(object_type_dict)

    file_path = "collection/static/webservice files/db_backup/object_types/" + str(datetime.datetime.now()).replace(':','') + ".json"
    # file_path = str(datetime.datetime.now()).replace(':','') + ".json"
    with open(file_path, "w") as file:
            file.write(json.dumps(result_list))
    return True


def backup_attributes():
    result_list = []
    attributes = Attribute.objects.all()
    for attribute in attributes:
        result_list.append({'id':attribute.id, 
                            'name':attribute.name, 
                            'description':attribute.description, 
                            'expected_valid_period':attribute.expected_valid_period, 
                            'format_specification':json.loads(attribute.format_specification), 
                            'first_applicable_object':attribute.first_applicable_object})

    file_path = "collection/static/webservice files/db_backup/attributes/" + str(datetime.datetime.now()).replace(':','') + ".json"
    # file_path = str(datetime.datetime.now()).replace(':','') + ".json"
    with open(file_path, "w") as file:
        file.write(json.dumps(result_list))
    return True


# ===========================================================================
# Clean Data ================================================================
# ===========================================================================
def remove_datapoints_with_the_wrong_datatype():
    numeric_attribute_ids = list(Attribute.objects.filter(data_type__in=['real', 'int']).values_list('id', flat=True))
    numeric_violating_datapoints = Data_point.objects.filter(attribute_id__in=numeric_attribute_ids).filter(numeric_value__isnull=True)
    numeric_violating_datapoints.delete()

    boolean_attribute_ids = list(Attribute.objects.filter(data_type='boolean').values_list('id', flat=True))
    boolean_violating_datapoints = Data_point.objects.filter(attribute_id__in=boolean_attribute_ids).filter(boolean_value__isnull=True)
    boolean_violating_datapoints.delete()

    string_attribute_ids = list(Attribute.objects.filter(data_type='string').values_list('id', flat=True))
    string_violating_datapoints = Data_point.objects.filter(attribute_id__in=string_attribute_ids).filter(string_value__isnull=True)
    string_violating_datapoints.delete()

    return 'success'


def remove_duplicates():
    unique_fields = ['object_id', 'attribute_id', 'value_as_string', 'numeric_value', 'string_value', 'boolean_value', 'valid_time_start', 'valid_time_end', 'data_quality']

    duplicates = (
        Data_point.objects.values(*unique_fields)
        .order_by()
        .annotate(max_id=Max('id'), count_id=Count('id'))
        .filter(count_id__gt=1)
    )

    for duplicate in duplicates:
        (
            Data_point.objects
            .filter(**{x: duplicate[x] for x in unique_fields})
            .exclude(id=duplicate['max_id'])
            .delete()
    )