from operator import delitem

from cv2 import detail_ImageFeatures
from mycroft import MycroftSkill, intent_handler
from mycroft.util import LOG
from mycroft.skills.context import removes_context
from adapt.intent import IntentBuilder
import time
import cv2
import os
import sys
from multiprocessing import Process, Queue
import csv
import json

sys.path.append('/opt/mycroft/skills/easy-shopping-advanced-skill')
from cvAPI import getDetail, getObjLabel

LOGSTR = '********************====================########## '
# 'NO TEST': use the image taken by the camera
# 'TEST': use the image in /photo folder, 
# In both mode, camera will work normally, i.e. take the photo, save the photo
MODE = 'NO TEST'

def take_photo(img_queue):
    '''
    Do taking photo
    '''
    LOG.info(LOGSTR + 'take photo process start')
    cap = cv2.VideoCapture(0)
    img_name = 'cap_img_' + str(time.time()) + '.jpg'
    img_path = '/opt/mycroft/skills/sandbox-git-skill.yuyang0828/photo/' + img_name

    #<-- Take photo in specific time duration -->
    cout = 0
    while True:
        ret, frame = cap.read()
        cv2.waitKey(1)
        cv2.imshow('capture', frame)
        cout += 1 
        if cout == 50:
            img_queue.put(img_path)
            cv2.imwrite(img_path, frame)
            break

    cap.release()
    cv2.destroyAllWindows()
    LOG.info(LOGSTR + 'take photo process end')
    os._exit(0)


def generate_str(possible_list):
    '''
    Generate string for Mycroft to speak it

    Args: 
        possible_list: array list with len = 3, each element is a string
    Returns:
        a string, e.g. possible_list = ['a', 'b', 'c'], res = 'a, b, and c'
    '''
    res = ''
    if len(possible_list) == 3:
        res = possible_list[0] + ' ' + \
            possible_list[1] + ' and ' + possible_list[2]
    elif len(possible_list) == 2:
        res = possible_list[0] + ' and ' + possible_list[1]
    elif len(possible_list) == 1:
        res = possible_list[0]

    return res


#========================= new params and functions for case 3 ==============================

CSV_FIELD_NAME = ['objectLabel', 'objectLogo', 'objectText', 'objectColor']
CSV_FILE_NAME = 'store.csv'


def write_to_csv(row):
    with open(CSV_FILE_NAME, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELD_NAME)
        writer.writerow(row)
        f.close()

def check_category_in_csv(category):
    with open(CSV_FILE_NAME, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            categorys = row['objectLabel']
            if category in categorys:
                return row
        return {}

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


class EasyShoppingAdvanced(MycroftSkill):
    
    def __init__(self):
        MycroftSkill.__init__(self)
        self.category_str = ''
        self.color_str = ''
        self.brand_str = ''
        self.kw_str = ''
        self.img_multi = ''
        self.img_hand = ''
        self.detail = ''
        self.log.info(LOGSTR + "_init_ EasyShoppingSkill")

    # ============================ use case 1 ============================
    @intent_handler('view.goods.intent')
    def handle_view_goods(self, message):
        self.speak_dialog('take.photo')
        self.img_multi = ''
        self.img_hand = ''

        #create another process to do the photo taking
        img_queue = Queue()
        take_photo_process = Process(target=take_photo, args=(img_queue,))
        take_photo_process.daemon = True
        take_photo_process.start()
        take_photo_process.join()
        self.img_multi = img_queue.get()

        self.speak('I find some goods here, you can ask me whatever goods you want.', expect_response=True)

    @intent_handler('is.there.any.goods.intent')
    def handle_is_there_any_goods(self, message):
        if self.img_multi == '':
            self.handle_no_context1(message)

        else:
            # call cv api, and get result. 
            try:
                self.log.info(LOGSTR + 'actual img path')
                self.log.info(self.img_multi)
                if MODE == 'TEST':
                    self.log.info(LOGSTR + 'testing mode, use another image')
                    self.img_multi = '/opt/mycroft/skills/sandbox-git-skill.yuyang0828/photo/multi.jpeg'

                objectlist = getObjLabel.getObjectsThenLabel(self.img_multi)
                label_list = []
                loc_list = []
                detected = 0

                category_label = message.data.get('category')

                for obj in objectlist['objectList']:
                    label_list.append(obj['name'])
                    loc_list.append(obj['loc'])
            
            
                for i in range(0,len(label_list)):
                    label_str = generate_str(label_list[i])
                    label_str = label_str.lower()
            
                    if category_label is not None:
                        if category_label in label_str:
                            self.speak_dialog('yes.goods',
                                        {'category': category_label,
                                        'location': loc_list[i]})
                            detected = 1
                            break
                    else:
                        continue

                if detected == 0:
                    self.speak_dialog('no.goods',
                    {'category': category_label})

            except Exception as e:
                self.log.error((LOGSTR + "Error: {0}").format(e))
                self.speak_dialog(
                "exception", {"action": "calling computer vision API"})


    def handle_no_context1(self, message):
        self.speak('Please let me have a look at what\'s in front of you first.')
        take_photo = self.ask_yesno('do.you.want.to.take.a.photo')
        if take_photo == 'yes':
            self.handle_view_goods(message)
        elif take_photo == 'no':
            self.speak('OK. I won\'t take photo')
        else:
            self.speak('I cannot understand what you are saying')


    # ============================ use case 2 ============================
    @intent_handler(IntentBuilder('ViewItemInHand').require('ViewItemInHandKeyWord'))
    def handle_view_item_in_hand(self, message):
        self.speak_dialog('take.photo')
        self.img_multi = ''
        self.img_hand = ''

        # create another process to do the photo taking
        img_queue = Queue()
        take_photo_process = Process(target=take_photo, args=(img_queue,))
        take_photo_process.daemon = True
        take_photo_process.start()
        take_photo_process.join()
        self.img_hand = img_queue.get()

        # call cv api, and get result. 
        try:
            self.log.info(LOGSTR + 'actual img path')
            self.log.info(self.img_hand)
            if MODE == 'TEST':
                self.log.info(LOGSTR + 'testing mode, use another image')
                self.img_hand = '/opt/mycroft/skills/sandbox-git-skill.yuyang0828/photo/2.jpeg'

            detail = getDetail.getDetail(self.img_hand)
            self.detail = detail

            self.category_str = generate_str(detail['objectLabel'])

            if self.category_str != '':
                self.set_context('getDetailContext')
                self.speak_dialog(
                    'item.category', {'category': self.category_str}, expect_response=True)

                self.brand_str = generate_str(detail['objectLogo'])

                color_list = []
                for color in detail['objectColor']:
                    color_list.append(color['colorName'])
                self.color_str = generate_str(color_list)

                self.kw_str = ' '.join(detail['objectText'])

            else:
                self.remove_context('getDetailContext')
                self.speak(
                    'I cannot understand what is in your hand. Maybe turn around it and let me see it again', expect_response=True)
                

        except Exception as e:
            self.log.error((LOGSTR + "Error: {0}").format(e))
            self.speak_dialog(
                "exception", {"action": "calling computer vision API"})
    
    def handle_ask_item_detail(self, detail, detail_str):
        if detail_str == '':
            self.speak_dialog(
            'cannot.get', {'detail': detail}, expect_response=True)
        else:
            dialog_str = 'item.' + detail
            self.speak_dialog(dialog_str, {detail: detail_str}, expect_response=True)

    @intent_handler(IntentBuilder('AskItemCategory').require('Category').require('getDetailContext').build())
    def handle_ask_item_category(self, message):
        self.handle_ask_item_detail('category', self.category_str)

    @intent_handler(IntentBuilder('AskItemColor').require('Color').require('getDetailContext').build())
    def handle_ask_item_color(self, message):
        self.handle_ask_item_detail('color', self.color_str)

    @intent_handler(IntentBuilder('AskItemBrand').require('Brand').require('getDetailContext').build())
    def handle_ask_item_brand(self, message):
        self.handle_ask_item_detail('brand', self.brand_str)

    @intent_handler(IntentBuilder('AskItemKw').require('Kw').require('getDetailContext').build())
    def handle_ask_item_keywords(self, message):
        self.handle_ask_item_detail('keyword', self.kw_str)

    @intent_handler(IntentBuilder('AskItemInfo').require('Info').require('getDetailContext').build())
    def handle_ask_item_complete_info(self, message):
        if self.color_str == '':
            self.handle_ask_item_detail('color', self.color_str)
        else:
            self.speak_dialog('item.complete.info', {
                          'category': self.category_str, 'color': self.color_str})
        self.handle_ask_item_detail('brand', self.brand_str)
        self.handle_ask_item_detail('keyword', self.kw_str)


    # @intent_handler(IntentBuilder('FinishOneItem').require('Finish').require('getDetailContext').build())
    # @removes_context('getDetailContext')
    # def handle_finish_current_item(self, message):
    #     self.speak('Got you request. Let\'s continue shopping!')
    #     self.types_str = ''
    #     self.color_str = ''
    #     self.logo_str = ''
    #     self.kw_str = ''
    #     self.img_hand = ''
    #     self.img_multi = ''
    

    @intent_handler(IntentBuilder('NotTakeItem').require('NotTake').require('getDetailContext').build())
    @removes_context('getDetailContext')
    def handle_finish_current_item_not_take(self, message):
        self.speak('Got you request. Let\'s continue shopping!')
        self.types_str = ''
        self.color_str = ''
        self.logo_str = ''
        self.kw_str = ''
        self.img_hand = ''
        self.img_multi = ''
        self.detail = ''

    @intent_handler(IntentBuilder('TakeItem').require('Take').require('getDetailContext').build())
    @removes_context('getDetailContext')
    def handle_finish_current_item_take(self, message):
        write_to_csv(self.detail)
        self.speak('Got you request. Let\'s continue shopping!')
        self.types_str = ''
        self.color_str = ''
        self.logo_str = ''
        self.kw_str = ''
        self.img_hand = ''
        self.img_multi = ''
        self.detail = ''
    
    
    

    @intent_handler(IntentBuilder('NoContext').one_of('Category', 'Color', 'Brand', 'Kw', 'Info'))
    def handle_no_context2(self, message):
        self.speak('Please let me have a look at what\'s on your hand first.')
        take_photo = self.ask_yesno('do.you.want.to.take.a.photo')
        if take_photo == 'yes':
            self.handle_view_item_in_hand(message)
        elif take_photo == 'no':
            self.speak('OK. I won\'t take photo')
        else:
            self.speak('I cannot understand what you are saying')
    

    # ============================ use case 3 ============================
    @intent_handler('have.bought.intent')
    def handle_is_there_any_goods(self, message):
        ask_category = message.data.get('category')
        category_detail = check_category_in_csv(ask_category)
        if category_detail: 
            # dic is not empty

            tell_detail = self.ask_yesno('do.you.want.to.know.detail.about.you.have.bought')

            if tell_detail == 'yes':
                
                this_category_str = generate_str(string_to_array(category_detail['objectLabel']))

                this_brand_str = generate_str(string_to_array(category_detail['objectLogo']))

                this_color_str = generate_str(get_color_array(category_detail['objectColor']))

                this_kw_str = ' '.join(string_to_array(category_detail['objectText']))

                if this_color_str == '':
                    self.handle_ask_item_detail('color', this_color_str)
                else:
                    self.speak_dialog('item.complete.info', {
                          'category': this_category_str, 'color': this_color_str})
                    self.handle_ask_item_detail('brand', this_brand_str)
                    self.handle_ask_item_detail('keyword', this_kw_str)

        else:
            # dic is empty
            self.speak_dialog('do.not.bought.item', {'category': ask_category})
        


def create_skill():
    return EasyShoppingAdvanced()
