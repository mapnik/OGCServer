""" Change SafeConfigParser behavior to treat options without values as
    non-existent.
"""

from ConfigParser import SafeConfigParser as OrigSafeConfigParser

class SafeConfigParser(OrigSafeConfigParser):
    
    def items_with_value(self, section):
        finallist = []
        items = self.items(section)
        for item in items:
            if item[1] != '':
                finallist.append(item)
        return finallist
    
    def has_option_with_value(self, section, option):
        if self.has_option(section, option):
            if self.get(section, option) == '':
                return False
        else:
            return False
        return True