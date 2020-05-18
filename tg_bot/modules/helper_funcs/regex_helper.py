import timeout_decorator
import re


#Not using signals because Saitama is hosted on Windows
@timeout_decorator.timeout(5, use_signals=False) 
def regex_runner(regex, string):
   search = re.search(regex, string)
   return search

 
def regex_searcher(regex, string):
   try:
     search = regex_runner(regex, string)
   except timeout_decorator.timeout_decorator.TimeoutError:
     return 'Timeout'
   except Exception as e:
     print(e)
     return 'Broken'
   return search

def infinite_loop_check(regex):
     loop_matches = [r'\((.{1,}[\+\*]){1,}\)[\+\*].', r'[\(\[].{1,}\{\d(,)?\}[\)\]]\{\d(,)?\}', r'\(.{1,}\)\{.{1,}(,)?\}\(.*\)(\+|\* |\{.*\})']
     for match in loop_matches:
          match_1 = re.search(match, regex)
          if match_1: return True
     return False
