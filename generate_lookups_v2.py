# William Kavanagh
# April 2020
# Parse the files in lookupV2/all_states/* !ignore _README.txt into a more usable form.

# For every pair in RPGLite generate a lookup table of the following form:
# [state_from_with_action_choice_for_pair] : {action_0: p(win), action_1: p(win), ...}

# Example PRISM output.
# 154598:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,0,10,0,0)=0.33796182254127316
# 154599:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,1,0,0,0)=0.6523495521998637
# 154600:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,3,0,0,0)=0.5184244285351762
# 154601:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,5,0,0,0)=0.40691725228836945
# 154602:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,7,0,0,0)=0.3093155328211462
# 154603:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,2,0,0,0,0)=0.7431252835718589
# 154604:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,4,0,0,0,0)=0.6212796524027482
# 154605:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,6,0,0,0,0)=0.5475144896852222
# 154606:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,8,0,0,0,0)=0.43906510435548624
# 154607:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,10,0,0,0,0)=0.3318617957490307

# For each pair:
    # generate dictionary of state (as string) paired with p(win)
    # create file
    # for each state:
        # generate list of possible actions:
        # calculate probability of winning having performed those actions (sum of outcomes * their probability)
        # print to file
