from mycroft import MycroftSkill, intent_file_handler


class EasyShoppingAdvanced(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('advanced.shopping.easy.intent')
    def handle_advanced_shopping_easy(self, message):
        self.speak_dialog('advanced.shopping.easy')


def create_skill():
    return EasyShoppingAdvanced()

