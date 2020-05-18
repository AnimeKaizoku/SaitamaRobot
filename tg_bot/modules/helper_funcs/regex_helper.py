import regex

 
def regex_searcher(regex, string):
   try:
     search = regex.search(regex, string, timeout= 6)
   except TimeoutError:
     return False
   except Exception:
      return False
   return search

def infinite_loop_check(regex):
     loop_matches = [r'\((.{1,}[\+\*]){1,}\)[\+\*].', r'[\(\[].{1,}\{\d(,)?\}[\)\]]\{\d(,)?\}', r'\(.{1,}\)\{.{1,}(,)?\}\(.*\)(\+|\* |\{.*\})']
     for match in loop_matches:
          match_1 = regex.search(match, regex)
          if match_1: return True
     return False
