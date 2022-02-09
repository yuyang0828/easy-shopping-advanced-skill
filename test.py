import csv
import json

CSV_FIELD_NAME = ['objectLabel', 'objectLogo', 'objectText', 'objectColor']
CSV_FILE_NAME = 'test.csv'


def write_to_csv(row):
    with open(CSV_FILE_NAME, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELD_NAME)
        writer.writerow(row)
        f.close()

def check_category_in_csv(category):
    with open(CSV_FILE_NAME, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            categorys = string_to_array(row['objectLabel'])
            if category in categorys:
                return row
        return {}

cc = []
cc.append('test5')
cc.append('test6')
cc.append('test7')
row = {'objectLabel':cc, 'objectLogo':['d','e', 'f'], 
'objectText':['tell', 'me', 'something'], 
'objectColor':[]}

# print(row)
def string_to_array(s):
    s_ws_bracket = s[2:-2]
    s_w_comma = s_ws_bracket.replace('\', \'', ',')
    return s_w_comma.split(',')

def get_color_array(s):
    s_ws_bracket = s[1:-1]
    if not s_ws_bracket:
        return []
    s_array = s_ws_bracket.split('}, {')
    res = []
    for ele in s_array:
        if ele[0] != '{':
            ele = '{' + ele
        if ele[-1] != '}':
            ele = ele + '}'
        ele = ele.replace('\'', '"')
        ele_json = json.loads(ele)
        res.append(ele_json['colorname'])
    return res


write_to_csv(row)
a = check_category_in_csv('test7')
if check_category_in_csv('test7'):
    print(get_color_array(a['objectColor']))
    # b = a['objectColor'][1:-1]
    # c = b.split('}, {')
    # print('============')
    # res = []
    # for i in c:
    #     if i[0] != '{':
    #         i = '{' + i
    #     if i[-1] != '}':
    #         i = i+ '}'
    #     print(i)
    #     ii = i.replace('\'', '"')
    #     print(ii)
    #     xx = json.loads(ii)
    #     print(xx)
    #     print(xx['colorname'])
    # c = json.loads(b)
    # print('ccc')
    # print(c)
    # c = b.replace('\', \'', ',')
    # print(c)
    # print(c.split(','))
    
