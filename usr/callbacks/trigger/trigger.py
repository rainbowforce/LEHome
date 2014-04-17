#!/usr/bin/env python
# encoding: utf-8

from util.log import *

class trigger_callback:
    def callback(self, action = None,
            trigger  = None, 
            pre_value = None):
        DEBUG("* trigger callback: %s, action: %s pre_value: %s" %(trigger, action, pre_value))
        return True, "pass"
