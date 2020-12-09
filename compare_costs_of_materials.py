from helper_fns import *

for p in pairs:
    states = 0
    major_mistakes_possible = 0
    minor_mistakes_possible = 0
    total_cost_of_second_best = 0.0 
    with open("lookupV2/beta/action_listing/"+p+".txt","r") as f:
        for b in f.readlines():
            possible_actions = b.split("{")[1][:-2]
            probs = []
            current_num = ""
            for c in possible_actions:
                if c in ["1","2","3","4","5","6","7","8","9","0","."]:
                    current_num += c
                elif current_num != "":
                    probs += [float(current_num)]
                    current_num = ""
            if current_num != "":
                probs += [float(current_num)]
                current_num = ""
            if(max(probs) > 0.1 and len(probs) > 1):
                states += 1
                if max(probs) - min(probs) > 0.1:
                    minor_mistakes_possible += 1
                if max(probs) - min(probs) > 0.3:
                    major_mistakes_possible += 1
                total_cost_of_second_best += max(probs) - sorted(probs)[-2]
    
    print("{0} has {1} states. {2} where minor mistakes are possible, {3} where major mistakes are possible. The average cost of the 2nd best move is {4}".format(p, states, minor_mistakes_possible/states, major_mistakes_possible/states, total_cost_of_second_best/states))


# ## TANGO OUTPUT:
# KA has 158648 states. 0.8490494680046392 where minor mistakes are possible, 0.2910405425848419 where major mistakes are possible. The average cost of the 2nd best move is 0.08787644640966018
# KW has 144797 states. 0.8670552566696824 where minor mistakes are possible, 0.3445789622713178 where major mistakes are possible. The average cost of the 2nd best move is 0.09069853139222454
# KR has 49695 states. 0.8664050709326894 where minor mistakes are possible, 0.330978971727538 where major mistakes are possible. The average cost of the 2nd best move is 0.10370780420565452
# KH has 215461 states. 0.8187653450044323 where minor mistakes are possible, 0.2884976863562315 where major mistakes are possible. The average cost of the 2nd best move is 0.06013432458773894
# KM has 163431 states. 0.9038064993789428 where minor mistakes are possible, 0.24397452135763717 where major mistakes are possible. The average cost of the 2nd best move is 0.0453998054224688
# KB has 72649 states. 0.8555107434376248 where minor mistakes are possible, 0.3196740491954466 where major mistakes are possible. The average cost of the 2nd best move is 0.08824248427369868
# KG has 173258 states. 0.8746435951009477 where minor mistakes are possible, 0.3181440395248704 where major mistakes are possible. The average cost of the 2nd best move is 0.08222053088456954
# AW has 62509 states. 0.8588843206578253 where minor mistakes are possible, 0.33702346862051863 where major mistakes are possible. The average cost of the 2nd best move is 0.10215886384360322
# AR has 128341 states. 0.8820953553424081 where minor mistakes are possible, 0.318440716528623 where major mistakes are possible. The average cost of the 2nd best move is 0.09174147053552373
# AH has 102161 states. 0.8352208768512446 where minor mistakes are possible, 0.27348988361507814 where major mistakes are possible. The average cost of the 2nd best move is 0.061556045066118184
# AM has 145959 states. 0.9102008098164553 where minor mistakes are possible, 0.23106488808501016 where major mistakes are possible. The average cost of the 2nd best move is 0.04076378839263001
# AB has 151490 states. 0.8683609479173543 where minor mistakes are possible, 0.288342464849165 where major mistakes are possible. The average cost of the 2nd best move is 0.08744323942174453
# AG has 152862 states. 0.8856681189569677 where minor mistakes are possible, 0.3146040219282752 where major mistakes are possible. The average cost of the 2nd best move is 0.07966182484855228
# WR has 122013 states. 0.8920197028185521 where minor mistakes are possible, 0.4129887798841107 where major mistakes are possible. The average cost of the 2nd best move is 0.10210776900821934
# WH has 96496 states. 0.826852926546178 where minor mistakes are possible, 0.31837589122865195 where major mistakes are possible. The average cost of the 2nd best move is 0.07386672670369442
# WM has 135274 states. 0.9251962683146798 where minor mistakes are possible, 0.30627467214690185 where major mistakes are possible. The average cost of the 2nd best move is 0.06142259894731905
# WB has 139470 states. 0.8833584283358429 where minor mistakes are possible, 0.3490284649028465 where major mistakes are possible. The average cost of the 2nd best move is 0.09082090112569102
# WG has 143785 states. 0.8880481274124561 where minor mistakes are possible, 0.3802065584031714 where major mistakes are possible. The average cost of the 2nd best move is 0.09320443766735129
# RH has 178218 states. 0.8571468650753572 where minor mistakes are possible, 0.33563388658833565 where major mistakes are possible. The average cost of the 2nd best move is 0.06825594300238476
# RM has 134971 states. 0.9314297145312697 where minor mistakes are possible, 0.2599891828615036 where major mistakes are possible. The average cost of the 2nd best move is 0.0444566457238978
# RB has 58971 states. 0.8766512353529701 where minor mistakes are possible, 0.31883468145359584 where major mistakes are possible. The average cost of the 2nd best move is 0.060511390344407105
# RG has 143842 states. 0.9030811584933469 where minor mistakes are possible, 0.33137748362786945 where major mistakes are possible. The average cost of the 2nd best move is 0.06988607068867089
# HM has 194921 states. 0.8972455507615906 where minor mistakes are possible, 0.24322674314209347 where major mistakes are possible. The average cost of the 2nd best move is 0.03201564392753871
# HB has 203672 states. 0.8417013629757649 where minor mistakes are possible, 0.2972131662673318 where major mistakes are possible. The average cost of the 2nd best move is 0.0635369689009709
# HG has 209583 states. 0.8555894323489978 where minor mistakes are possible, 0.3330088795369853 where major mistakes are possible. The average cost of the 2nd best move is 0.0633116495135525
# MB has 153190 states. 0.9124420654089692 where minor mistakes are possible, 0.216215157647366 where major mistakes are possible. The average cost of the 2nd best move is 0.04019433350740702
# MG has 133216 states. 0.9278389983185203 where minor mistakes are possible, 0.24900162142685564 where major mistakes are possible. The average cost of the 2nd best move is 0.03886579262250705
# BG has 164874 states. 0.8902555891165375 where minor mistakes are possible, 0.30166066208134695 where major mistakes are possible. The average cost of the 2nd best move is 0.06934187834346152

# ## BETA OUTPUT:
# KA has 64775 states. 0.8702277113083752 where minor mistakes are possible, 0.23505982246236976 where major mistakes are possible. The average cost of the 2nd best move is 0.08545036588189925
# KW has 70111 states. 0.88297128838556 where minor mistakes are possible, 0.2995107757698507 where major mistakes are possible. The average cost of the 2nd best move is 0.10065797093180488
# KR has 70988 states. 0.874119569504705 where minor mistakes are possible, 0.2832732292781879 where major mistakes are possible. The average cost of the 2nd best move is 0.08740956640558738
# KH has 134946 states. 0.8319846457101359 where minor mistakes are possible, 0.16895647147747989 where major mistakes are possible. The average cost of the 2nd best move is 0.05328979517732526
# KM has 161216 states. 0.9216330885271933 where minor mistakes are possible, 0.26798208614529573 where major mistakes are possible. The average cost of the 2nd best move is 0.03713340139936521
# KB has 131022 states. 0.8553143746851674 where minor mistakes are possible, 0.2738929340110821 where major mistakes are possible. The average cost of the 2nd best move is 0.07657959777746734
# KG has 166389 states. 0.8946685177505724 where minor mistakes are possible, 0.2776445558300128 where major mistakes are possible. The average cost of the 2nd best move is 0.06826896351321003
# AW has 51004 states. 0.8719316132068073 where minor mistakes are possible, 0.35522704101639085 where major mistakes are possible. The average cost of the 2nd best move is 0.10541485216845622
# AR has 107205 states. 0.897085024019402 where minor mistakes are possible, 0.3705144349610559 where major mistakes are possible. The average cost of the 2nd best move is 0.09950612005036819
# AH has 102959 states. 0.834215561534203 where minor mistakes are possible, 0.256723550151031 where major mistakes are possible. The average cost of the 2nd best move is 0.064537140803619
# AM has 127062 states. 0.9285388235664479 where minor mistakes are possible, 0.3554878720624577 where major mistakes are possible. The average cost of the 2nd best move is 0.03932981985172623
# AB has 141506 states. 0.8755176458948737 where minor mistakes are possible, 0.31561912569078343 where major mistakes are possible. The average cost of the 2nd best move is 0.08920259190422955
# AG has 127095 states. 0.8950234076871632 where minor mistakes are possible, 0.34700027538455486 where major mistakes are possible. The average cost of the 2nd best move is 0.08444779243872419
# WR has 116577 states. 0.9058647932267944 where minor mistakes are possible, 0.4584695094229565 where major mistakes are possible. The average cost of the 2nd best move is 0.10564725520471435
# WH has 109473 states. 0.838544663981073 where minor mistakes are possible, 0.27792241009198615 where major mistakes are possible. The average cost of the 2nd best move is 0.06918440199866574
# WM has 131808 states. 0.9256494294731731 where minor mistakes are possible, 0.40565064336003887 where major mistakes are possible. The average cost of the 2nd best move is 0.0586219758284772
# WB has 148138 states. 0.8821774291538971 where minor mistakes are possible, 0.3656252953327303 where major mistakes are possible. The average cost of the 2nd best move is 0.09083739087877417
# WG has 136916 states. 0.900238102194046 where minor mistakes are possible, 0.4139764527155336 where major mistakes are possible. The average cost of the 2nd best move is 0.0958646032603923
# RH has 203015 states. 0.8625076964756299 where minor mistakes are possible, 0.3277738098170086 where major mistakes are possible. The average cost of the 2nd best move is 0.07514314814175996
# RM has 132149 states. 0.9319858644408963 where minor mistakes are possible, 0.3970064094317778 where major mistakes are possible. The average cost of the 2nd best move is 0.04341230921156989
# RB has 64351 states. 0.8784012680455626 where minor mistakes are possible, 0.3525663936846358 where major mistakes are possible. The average cost of the 2nd best move is 0.06087876707432479
# RG has 137659 states. 0.9066243398542776 where minor mistakes are possible, 0.3824014412424905 where major mistakes are possible. The average cost of the 2nd best move is 0.07064304360775114
# HM has 225995 states. 0.905789951105113 where minor mistakes are possible, 0.30106418283590347 where major mistakes are possible. The average cost of the 2nd best move is 0.03344820155313006
# HB has 259185 states. 0.8232768100005787 where minor mistakes are possible, 0.27841503173408955 where major mistakes are possible. The average cost of the 2nd best move is 0.06473455107354893
# HG has 237834 states. 0.8658055618624755 where minor mistakes are possible, 0.3241967086287074 where major mistakes are possible. The average cost of the 2nd best move is 0.07126561551333496
# MB has 165495 states. 0.9076105018278497 where minor mistakes are possible, 0.33457204145140335 where major mistakes are possible. The average cost of the 2nd best move is 0.04017278926855498
# MG has 131094 states. 0.9299128869360916 where minor mistakes are possible, 0.3696507849329489 where major mistakes are possible. The average cost of the 2nd best move is 0.03763392969929969
# BG has 175590 states. 0.8846118799476053 where minor mistakes are possible, 0.3311635058944131 where major mistakes are possible. The average cost of the 2nd best move is 0.0703915025912628